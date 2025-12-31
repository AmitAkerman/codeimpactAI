from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from server.app.services.admin_service import stats, users, add_user

router = APIRouter(prefix="/admin", tags=["admin"])

class UserCreate(BaseModel):
    username: str
    password: str
    role: str
    full_name: str = ""
    class_name: str = ""

@router.get("/stats")
def admin_stats():
    return stats()

@router.get("/users")
def admin_users():
    return users()

@router.post("/users")
def admin_create_user(u: UserCreate):
    try:
        user = add_user(u.dict())
        if not user:
             raise HTTPException(status_code=400, detail="Failed to create user")
        return user
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))