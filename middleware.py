from psycopg2 import pool
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv() 

conn_pool = pool.SimpleConnectionPool(
    minconn=1,
    maxconn=5,
    user=os.getenv('DB_USER'),
    password=os.getenv('DB_PASSWORD'),
    host=os.getenv('DB_HOST'),
    port=os.getenv('DB_PORT'),
    database=os.getenv('DB_NAME')
)

def get_connection():
    """Get a connection from the pool."""
    return conn_pool.getconn()

def put_connection(conn):
    conn_pool.putconn(conn)