from fastapi import APIRouter
from server.app.models.auth_model import LoginRequest
from server.app.services.auth_service import login

router = APIRouter()

@router.post("/login")
def login_route(creds: LoginRequest):
    return login(creds.username, creds.password)
