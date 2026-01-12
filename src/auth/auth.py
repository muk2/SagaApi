from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from main import User, UserAccount, get_db_connection
from main import SignUpRequest, LoginRequest, UserResponse
from passlib.context import CryptContext
from datetime import datetime
import jwt

SECRET_KEY = "Spongebob_23"  # Replace with a strong secret
ALGORITHM = "HS256"

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
router = APIRouter()

# Hash password
def hash_password(password: str):
    return pwd_context.hash(password)

# Verify password
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

# Generate JWT token
def create_access_token(data: dict):
    return jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)

@router.post("/signup", response_model=UserResponse)
def signup(request: SignUpRequest, db: Session = Depends(get_db_connection)):
    # Check if email exists
    if db.query(UserAccount).filter(UserAccount.email == request.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    # Create user
    new_user = User(
        first_name=request.first_name,
        last_name=request.last_name,
        golf_handicap=request.golf_handicap
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Create account with hashed password
    new_account = UserAccount(
        user_id=new_user.id,
        email=request.email,
        password=hash_password(request.password)
    )
    db.add(new_account)
    db.commit()
    db.refresh(new_account)

    return new_user

@router.post("/login")
def login(request: LoginRequest, db: Session = Depends(get_db_connection)):
    account = db.query(UserAccount).filter(UserAccount.email == request.email).first()
    if not account or not verify_password(request.password, account.password):
        raise HTTPException(status_code=400, detail="Invalid credentials")

    # Update last_logged_in
    account.last_logged_in = datetime.utcnow()
    account.user.last_logged_in = datetime.utcnow()
    db.commit()

    # Create JWT token
    token = create_access_token({"user_id": account.user.id})
    return {"access_token": token, "user": {"first_name": account.user.first_name, "last_name": account.user.last_name, "role": account.user.role}}

