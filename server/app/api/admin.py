from fastapi import APIRouter
from server.app.services.admin_service import stats, users

router = APIRouter(prefix="/admin", tags=["admin"])

@router.get("/stats")
def admin_stats():
    return stats()

@router.get("/users")
def admin_users():
    return users()
