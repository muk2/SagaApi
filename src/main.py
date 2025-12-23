from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from controllers import auth_controller
import psycopg2
from pydantic import BaseModel
from typing import List

app = FastAPI()

origins = [
    "https://sagafe.vercel.app",
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_controller.router)


class Events(BaseModel):
    township: str
    golf_course: str
    # Add other fields as per your database schema

# Function to get a database connection
def get_db_connection():
    try:
        conn = psycopg2.connect(
            host="ep-purple-glade-adlsv7d9-pooler.c-2.us-east-1.aws.neon.tech",
            database="Saga",
            user="neondb_owner",
            password="npg_9bsVixcUeu3E"
        )
        return conn
    except psycopg2.OperationalError as e:
        raise HTTPException(status_code=500, detail=f"Database connection failed: {e}")

# API endpoint to fetch data
@app.get("/api/items", response_model=List[Events])
def get_items():
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Execute a query (replace 'items' with your table name and 'name' with a column name)
    cur.execute('SELECT township, golf_course FROM saga.event;') 
    records = cur.fetchall()
    
    cur.close()
    conn.close()

    # Format data into a list of dictionaries that match the Pydantic model
    items_list = [{"township": row[0], "golf_course": row[1]} for row in records]
    return items_list
