from fastapi import APIRouter
from services import auth_service


router = APIRouter()
authService = auth_service.AuthService()

@router.get("/token")
async def about():
    return {"token": authService.authenticate_user()}