from .db_mock import USERS

def find_user_by_credentials(username: str, password: str):
    return next(
        (u for u in USERS if u["username"].lower() == username.lower() and u["password"] == password),
        None
    )

def list_students():
    return [u for u in USERS if u["role"] == "student"]

def list_all_users():
    return USERS
