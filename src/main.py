from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import events

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://sagafe.vercel.app",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(events.router)