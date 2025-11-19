# backend/app/db.py
import os
import psycopg2
from psycopg2.extras import RealDictCursor

DB_HOST = os.getenv("POSTGRES_HOST", "db")
DB_NAME = os.getenv("POSTGRES_DB", "jobautomation")
DB_USER = os.getenv("POSTGRES_USER", "jobuser")
DB_PASS = os.getenv("POSTGRES_PASSWORD", "jobpass")
DB_PORT = int(os.getenv("POSTGRES_PORT", "5432"))


def get_conn():
    """
    Simple helper to get a new DB connection.
    FastAPI will open+close per request for now (fine for our use).
    """
    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASS,
        cursor_factory=RealDictCursor,
    )
    return conn
