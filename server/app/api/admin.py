from fastapi import APIRouter
from pydantic import BaseModel

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


from fastapi import HTTPException, UploadFile, File
from fastapi.responses import PlainTextResponse
from server.app.services.admin_service import stats, users, add_user, \
    bulk_add_teachers_from_csv


@router.post("/teachers/upload")
async def upload_teachers_csv(file: UploadFile = File(...)):
    try:
        content = await file.read()
        csv_str = content.decode("utf-8")
        # Call the new service function
        result = bulk_add_teachers_from_csv(csv_str)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/users/template", response_class=PlainTextResponse)
def get_users_template():
    return "username,password,role,full_name,class_name\nstudent1,123,student,Student One,Class 5A"
