from fastapi import HTTPException
from server.app.repositories.users_repo import find_user_by_credentials

def login(username: str, password: str):
    user = find_user_by_credentials(username, password)
    if user:
        return user
    raise HTTPException(status_code=400, detail="Invalid Credentials")
