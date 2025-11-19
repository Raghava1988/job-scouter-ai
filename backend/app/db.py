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
    Get a new database connection for each request.
    Uses RealDictCursor so FastAPI returns dict-like rows.
    Autocommit ensures inserts/updates are saved immediately.
    """
    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASS,
        cursor_factory=RealDictCursor
    )

    conn.autocommit = True
    return conn
