import  os
from datetime import datetime
from datetime import datetime, timezone
import json 
import requests
from private_tools import *
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_qdrant import QdrantVectorStore  
from qdrant_client import QdrantClient
from system_prompts import task_specific_system_prompts
import psycopg2
from config import TASKS_DB_CONFIG
from config import tools

openai_api_key = os.getenv('open_api')

# update system prompts
chat_summary = []
def job_specific_system_prompt(job_title: str) -> dict:
    if job_title not in task_specific_system_prompts:
        raise ValueError(f"Unknown job title: {job_title}")

    return {
        "role": "system",
        "content": task_specific_system_prompts[job_title]
    }

# schedule functions 

def add_task(title: str, description: str, time_todo: str):
    try:
        task_time = datetime.fromisoformat(time_todo)
    except ValueError:
        return "Invalid time format. Use YYYY-MM-DD HH:MM:SS"

    if task_time <= datetime.now():
        return "Tasks can only be scheduled for future time"

    conn = get_tasks_conn()
    cur = conn.cursor()
    create_tasks_table()
    try:
        cur.execute(
            """
            INSERT INTO tasks (title, description, time_todo)
            VALUES (%s, %s, %s)
            ON CONFLICT (title) DO NOTHING;
            """,
            (title, description, task_time)
        )

        conn.commit()
        return "Task added successfully"

    except Exception as e:
        conn.rollback()
        return f"Could not add task: {e}"

    finally:
        cur.close()
        conn.close()

def del_task(title: str):
    conn = get_tasks_conn()
    cur = conn.cursor()

    try:
        cur.execute(
            "DELETE FROM tasks WHERE title = %s;",
            (title,)
        )
        conn.commit()

        if cur.rowcount == 0:
            return "Task not found"

        return "Task deleted successfully"

    except Exception as e:
        conn.rollback()
        return f"Could not delete task: {e}"

    finally:
        cur.close()
        conn.close()

def update_task(title: str, new_description: str, new_time_todo: str):
    try:
        new_time = datetime.fromisoformat(new_time_todo)
        new_time_utc = new_time.replace(tzinfo=timezone.utc)  # MAKE USER INPUT UTC
    except ValueError:
        return "Invalid time format. Use YYYY-MM-DD HH:MM:SS"

    if new_time_utc <= datetime.now(timezone.utc):  # BOTH UTC NOW
        return "Updated time must be in the future"

    conn = get_tasks_conn()
    cur = conn.cursor()

    try:
        cur.execute(
            """
            UPDATE tasks
            SET description = %s,
                time_todo = %s
            WHERE title = %s;
            """,
            (new_description, new_time_utc, title)  # PASS UTC TO DB
        )

        conn.commit()

        if cur.rowcount == 0:
            return "Task not found"

        return "Task updated successfully"

    except Exception as e:
        conn.rollback()
        return f"Could not update task: {e}"

    finally:
        cur.close()
        conn.close()

def fetch_task(title: str):
    conn = get_tasks_conn()
    cur = conn.cursor()

    try:
        cur.execute(
            """
            SELECT
                title,
                description,
                time_todo,
                created_at,
                CASE
                    WHEN completed = TRUE THEN 'completed'
                    WHEN time_todo < NOW() THEN 'due'
                    ELSE 'pending'
                END AS status
            FROM tasks
            WHERE title = %s;
            """,
            (title,)
        )

        row = cur.fetchone()

        if not row:
            return None

        return {
            "title": row[0],
            "description": row[1],
            "time_todo": row[2].astimezone(timezone.utc).isoformat(),  
            "created_at": row[3].astimezone(timezone.utc).isoformat(), 
            "status": row[4],     
        }

    finally:
        cur.close()
        conn.close()

def fetch_all_tasks():
    conn = get_tasks_conn()
    cur = conn.cursor()

    try:
        cur.execute(
            """
            SELECT
                title,
                description,
                time_todo,
                created_at,
                CASE
                    WHEN completed = TRUE THEN 'completed'
                    WHEN time_todo < NOW() THEN 'due'
                    ELSE 'pending'
                END AS status
            FROM tasks
            ORDER BY time_todo;
            """
        )

        rows = cur.fetchall()

        return [
            {
                "title": r[0],
                "description": r[1],
                "time_todo": r[2].astimezone(timezone.utc).isoformat(),  
                "created_at": r[3].astimezone(timezone.utc).isoformat(),  
                "status": r[4]
            }
            for r in rows
        ]

    finally:
        cur.close()
        conn.close()

def fetch_all_title():
    conn = get_tasks_conn()
    cur = conn.cursor()

    try:
        cur.execute(
            "SELECT title FROM tasks ORDER BY time_todo;"
        )

        rows = cur.fetchall()

        # rows = [('Task1',), ('Task2',)]
        return [row[0] for row in rows]

    finally:
        cur.close()
        conn.close()

def current_datetime():
    return datetime.now().isoformat()
#user profile functions

def fetch_user_profile():
    conn = get_tasks_conn()
    cur = conn.cursor()

    try:
        cur.execute(
            """
            SELECT
                name,
                personality,
                preferences,
                profession,
                extra_info
            FROM user_profile
            LIMIT 1;
            """
        )

        row = cur.fetchone()

        # If profile does not exist yet
        if not row:
            return {
                "name": None,
                "personality": None,
                "preferences": None,
                "profession": None,
                "extra_info": {}
            }

        return {
            "name": row[0],
            "personality": row[1],
            "preferences": row[2],
            "profession": row[3],
            "extra_info": row[4]
        }

    finally:
        cur.close()
        conn.close()

def update_user_profile(
    name: str, 
    personality: str, 
    preferences: str, 
    profession: str, 
    extra_info: dict = None
):
    conn = get_tasks_conn()
    cur = conn.cursor()

    try:
        cur.execute(
            """
            INSERT INTO user_profile (id, name, personality, preferences, profession, extra_info)
            VALUES (1, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO UPDATE SET
                name = EXCLUDED.name,
                personality = EXCLUDED.personality,
                preferences = EXCLUDED.preferences,
                profession = EXCLUDED.profession,
                extra_info = EXCLUDED.extra_info;
            """,
            (
                name, 
                personality, 
                preferences, 
                profession, 
                json.dumps(extra_info or {})
            )
        )

        conn.commit()
        return "User profile replaced successfully"

    except Exception as e:
        conn.rollback()
        return f"Could not update profile: {e}"
    finally:
        cur.close()
        conn.close()
# file functions

def ingest_pdf(
    pdf_path: str,
    collection_name: str,
    chunk_size: int,
    chunk_overlap: int,
    embedding_model:str
):
    try:
        docs = load_pdf(pdf_path)
        chunks = split_docs(docs, chunk_size, chunk_overlap)
        embedder = create_embeddings(openai_api_key,embedding = embedding_model)
        store_vectors(
            docs=chunks,
            embeddings=embedder,
            path="./qdrant", #TODO change the path
            collection=collection_name
        )

        return {
            "status": "success",
            "message": "PDF ingested successfully",
            "collection": collection_name,
            "embedding_model":embedding_model
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }

def pdf_similarity_search(
    query: str,
    collection: str,
    embedder:str,
    k: int = 4,
):
    if not query.strip():
        return {
            "status": "error",
            "message": "Empty query"
        }

    try:
        results = pdf_similarity_search_internal(query = query, collection = collection, k = k, embedder = embedder)
    except Exception as e:
        return {
            "status": "error",
            "step": "vector_search",
            "message": str(e)
        }

    if not results:
        return {
            "status": "no_results",
            "message": "No relevant documents found"
        }

    return {
        "status": "success",
        "results": results
    }

def doc_size(doc_path:str,doc_type:str):
    pass
# model changing
def save_chat_summary(summary:str):
    chat_summary.append(summary)

def get_chat_summary():
    if not chat_summary:
        return {'role': 'assistant', 'content': 'No prior conversation context.'}
    return {'role': 'assistant', 'content': 'PREVIOUS CHAT SUMMARY:\n' + '\n'.join(chat_summary[-3:])}

def change_model(model:str ,messages:list):
    if model not in ("gpt-4o-mini", "gpt-4o"):
        return {"error": "Invalid model specified"}
    while True:
        user_query = input('\n> ')
        messages.append({ "role": "user", "content": user_query })
        while True:
            response = get_client().chat.completions.create(
                model=model,
                messages=messages,
                tools=tools,
                parallel_tool_calls=False 
            )
            
            response_message = response.choices[0].message
            messages.append(response_message) 

            # Check if the model is done
            if not response_message.tool_calls:
                print(response_message.content)
                break
            else:
                for tool_call in response_message.tool_calls:
                    try:
                        # Execute logic
                        args = json.loads(tool_call.function.arguments)
                        result = fn_registry[tool_call.function.name](**args)
                        
                        messages.append({
                            "tool_call_id": tool_call.id,
                            "role": "tool",
                            "name": tool_call.function.name,
                            "content": json.dumps(result),
                        })
                    except Exception as e:
                        # Send error back to model to let it "self-correct"
                        messages.append({
                            "tool_call_id": tool_call.id,
                            "role": "tool",
                            "name": tool_call.function.name,
                            "content": f"Error: {str(e)}",
                        })
 
def report_task_completion(summary: str, confidence: int = 1):
    system_prompt = get_system_prompt()
    chat_summary_msg = get_chat_summary()
    messages = [
        {"role": "system", "content": system_prompt},
        chat_summary_msg,  # Context injection
        {"role": "assistant", "content": f"SUMMARY (confidence {confidence}): {summary}"}
    ]
    change_model(model='gpt-4o-mini', messages=messages) # ressurecting Johnny router


fn_registry = {
    "add_task": add_task,
    "del_task": del_task,
    "update_task": update_task,
    "fetch_task": fetch_task,
    "fetch_all_tasks": fetch_all_tasks,
    "fetch_all_title": fetch_all_title,
    "fetch_user_profile": fetch_user_profile,
    "ingest_pdf": ingest_pdf,
    "pdf_similarity_search": pdf_similarity_search,
    "job_specific_system_prompt": job_specific_system_prompt,
    "change_model": change_model,
    "update_user_profile": update_user_profile,
    "current_datetime":current_datetime,
    "report_task_completion":report_task_completion,
    "save_caht_summary":save_chat_summary,
}