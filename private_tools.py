import  os
from datetime import datetime
import json 
import requests
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_qdrant import QdrantVectorStore  
from qdrant_client import QdrantClient
from langchain.embeddings.base import Embeddings
import psycopg2
from config import TASKS_DB_CONFIG

def get_tasks_conn():
    return psycopg2.connect(**TASKS_DB_CONFIG)

def create_tasks_table():
    conn = get_tasks_conn()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id SERIAL PRIMARY KEY,
            title TEXT UNIQUE NOT NULL,
            description TEXT,
            time_todo TIMESTAMP NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed BOOLEAN NOT NULL DEFAULT FALSE
        );
    """)

    conn.commit()
    cur.close()
    conn.close()

def create_user_profile_table():
    conn = get_tasks_conn()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS user_profile (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            name TEXT,
            personality TEXT,
            preferences TEXT,
            profession TEXT,
            extra_info JSONB,
            updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
        );
    """ )
    conn.commit()
    cur.close()
    conn.close() 

def load_pdf(path: str):
    return PyPDFLoader(file_path=path).load()

def split_docs(docs, chunk_size: int, overlap: int):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=overlap
    )
    return splitter.split_documents(docs)

def create_embeddings(api_key: str, model: str):
    return OpenAIEmbeddings(api_key=api_key, model=model)

def store_vectors(docs, embeddings, path: str, collection: str):
    return QdrantVectorStore.from_documents(
        documents=docs,
        embedding=embeddings,
        path=path,
        collection_name=collection
    )

def pdf_similarity_search_internal(query, collection, k,embedder):
    vectordb = QdrantVectorStore(
        path="./qdrant",
        collection_name=collection,
        embedding=embedder 
    )

    docs = vectordb.similarity_search(query, k=k)

    return [
        {
            "content": doc.page_content,
            "metadata": doc.metadata
        }
        for doc in docs
    ]

def get_client():
    from main import client
    return(client)

def get_system_prompt():
    from main import system_prompt
    return system_prompt