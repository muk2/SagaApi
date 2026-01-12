from fastapi import APIRouter, HTTPException
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr
from typing import Optional
import psycopg2
from datetime import datetime
import hashlib

router = APIRouter(prefix="/auth")

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

def get_db_connection():
    return psycopg2.connect(
        host="ep-purple-glade-adlsv7d9-pooler.c-2.us-east-1.aws.neon.tech",
        database="Saga",
        user="neondb_owner",
        password="npg_9bsVixcUeu3E"
    )


def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(password: str, hashed: str) -> bool:
    return pwd_context.verify(password, hashed)


class SignUpRequest(BaseModel):
    first_name: str
    last_name: str
    phone_number: str
    email: EmailStr
    password: str
    golf_handicap: Optional[int] = None

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

@router.post("/signup")
def signup(data: SignUpRequest):
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        # 1️⃣ Check if email already exists
        cur.execute(
            "SELECT id FROM saga.user_account WHERE email = %s;",
            (data.email,)
        )
        if cur.fetchone():
            raise HTTPException(status_code=400, detail="Email already registered")

        # 2️⃣ Insert into user table
        cur.execute(
            """
            INSERT INTO saga."user"
            (first_name, last_name, phone_number, handicap)
            VALUES (%s, %s, %s, %s)
            RETURNING id;
            """,
            (data.first_name, data.last_name, data.phone_number, data.golf_handicap)
        )

        user_id = cur.fetchone()[0]

        # 3️⃣ Insert into user_account table
        cur.execute(
            """
            INSERT INTO saga.user_account
            (user_id, email, password_hash)
            VALUES (%s, %s, %s)
            RETURNING id;
            """,
            (user_id, data.email, hash_password(data.password))
        )

        user_account_id = cur.fetchone()[0]

        cur.execute(
            """
            UPDATE saga."user"
            SET user_account_id = %s
            WHERE id = %s;
            """,
            (user_account_id, user_id)
        )
        # ✅ THIS IS WHAT YOU WERE MISSING
        conn.commit()

        return {"message": "User created successfully"}

    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        cur.close()
        conn.close()


@router.post("/login")
def login(data: LoginRequest):
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute(
            """
            SELECT 
                ua.password_hash,
                u.id,
                u.first_name,
                u.last_name,
                ua.role,
                u.handicap
            FROM saga.user_account ua
            JOIN saga."user" u ON u.id = ua.user_id
            WHERE ua.email = %s;
            """,
            (data.email,)
        )

        user_row = cur.fetchone()

        if not user_row:
            raise HTTPException(status_code=401, detail="Invalid email or password")

        (
            password_hash,
            user_id,
            first_name,
            last_name,
            role,
            handicap
        ) = user_row

        if not verify_password(data.password, password_hash):
            raise HTTPException(status_code=401, detail="Invalid email or password")

        # Update last login
        cur.execute(
            "UPDATE saga.user_account SET last_logged_in = NOW() WHERE user_id = %s;",
            (user_id,)
        )
        conn.commit()

        return {
            "message": "Login successful",
            "user": {
                "id": user_id,
                "first_name": first_name,
                "last_name": last_name,
                "role": role,
                "golf_handicap": handicap
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cur.close()
        conn.close()
