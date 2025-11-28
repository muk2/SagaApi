from fastapi import FastAPI
from controllers import auth_controller

app = FastAPI()


app.include_router(auth_controller.router)

