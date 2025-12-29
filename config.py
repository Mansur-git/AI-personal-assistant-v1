import os
EMBEDDING_MODELS = (
    "text-embedding-3-small",
    "text-embedding-3-large",
)

GPT_MODELS = (
    "gpt-4o-mini",
    "gpt-4o",
)


# db_config.py
TASKS_DB_CONFIG = {
    "dbname": "task_db",
    "user": "postgres",
    "password":os.getenv('db_password'),
    "host": "localhost",
    "port": 5432
}

tools = [
    {
        "type": "function",
        "function": {
            "name": "add_task",
            "description": "Add a new scheduled task or reminder.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Short title of the task"},
                    "description": {"type": "string", "description": "Detailed description of the task"},
                    "time_todo": {"type": "string", "description": "ISO datetime (YYYY-MM-DD HH:MM:SS)"}
                },
                "required": ["title", "description", "time_todo"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "del_task",
            "description": "Delete a scheduled task by title.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Title of the task to delete"}
                },
                "required": ["title"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "update_task",
            "description": "Update an existing scheduled task.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Title of the task to update"},
                    "new_description": {"type": "string", "description": "Updated description"},
                    "new_time_todo": {"type": "string", "description": "Updated ISO datetime"}
                },
                "required": ["title", "new_description", "new_time_todo"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "fetch_task",
            "description": "Fetch details of a single scheduled task.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Title of the task"}
                },
                "required": ["title"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "fetch_all_tasks",
            "description": "Fetch all scheduled tasks.",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "fetch_user_profile",
            "description": "Retrieve the user's name, profession, and preferences.",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "ingest_pdf",
            "description": "Ingest a PDF file into a vector database.",
            "parameters": {
                "type": "object",
                "properties": {
                    "pdf_path": {"type": "string"},
                    "collection_name": {"type": "string"},
                    "chunk_size": {"type": "integer"},
                    "chunk_overlap": {"type": "integer"},
                    "embedding_model": {"type": "string"}
                },
                "required": ["pdf_path", "collection_name", "chunk_size", "chunk_overlap", "embedding_model"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "pdf_similarity_search",
            "description": "Search an ingested PDF collection for relevant content.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "collection": {"type": "string"},
                    "embedder": {"type": "string"},
                    "k": {"type": "integer", "default": 4}
                },
                "required": ["query", "collection", "embedder"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "job_specific_system_prompt",
            "description": "Returns a system prompt suitable for a specific job title.",
            "parameters": {
                "type": "object",
                "properties": {
                    "job_title": {"type": "string"}
                },
                "required": ["job_title"]
            }
        }
    },
    {
    "type": "function",
    "function": {
      "name": "update_user_profile",
      "description": "Replace the existing user profile with new information. Note: This overwrites old data.",
      "parameters": {
        "type": "object",
        "properties": {
          "name": {"type": "string"},
          "personality": {"type": "string"},
          "preferences": {"type": "string"},
          "profession": {"type": "string"},
          "extra_info": {"type": "object"}
        },
        "required": ["name", "personality", "preferences", "profession"]
      }
    }
},
{
    "type": "function",
    "function": {
      "name": "fetch_all_title",
      "description": "Retrieve a list of all existing task titles sorted by their scheduled time. Useful for a quick overview of the agenda.",
      "parameters": {
        "type": "object",
        "properties": {}
      }
    }
},
 {
        "type": "function",
        "function": {
            "name": "current_datetime",
            "description": "returns current datetime in iso format",
            "parameters": {"type": "object", "properties": {}}
        }
    },
{
    "type": "function",
    "function": {
        "name": "change_model",
        "description": "Switches to a specific LLM model optimized for the current task. Use 'gpt-4o' for complex reasoning/legal/medical and 'gpt-4o-mini' for simple tasks.",
        "parameters": {
            "type": "object",
            "properties": {
                "model": {
                    "type": "string",
                    "enum": ["gpt-4o", "gpt-4o-mini"],
                    "description": "The target model name."
                },
                "messages": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "description": "A message object containing 'role' and 'content'."
                    },
                    "description": "The full conversation history to pass to the new model to maintain context."
                }
            },
            "required": ["model", "messages"]
        }
    }
},
{
  "type":"function",
  "function":{
  "name": "report_task_completion",
  "description": "Report that the assigned specialist task appears complete and provide a concise summary for the router.",
  "parameters": {
    "type": "object",
    "properties": {
      "summary": {
        "type": "string",
        "description": "Brief summary of the user queries handled and the responses provided."
      },
      "confidence": {
        "type": "number",
        "description": "Confidence (1-10) that the task is fully complete."
      }
    },
    "required": ["summary"]
  }
}
},
{
    "type": "function",
    "function": {
        "name": "save_chat_summary",
        "description": "Save a conversation summary to persistent memory before model handoff. Keeps context across specialist switches.",
        "parameters": {
            "type": "object",
            "properties": {
                "summary": {
                    "type": "string",
                    "description": "Bullet point summary of recent conversation (max 100 words)"
                }
            },
            "required": ["summary"]
        }
    }
},

]


