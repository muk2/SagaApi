from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from controllers import auth_controller

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

