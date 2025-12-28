from .client import post

def login(username: str, password: str):
    return post("/login", {"username": username, "password": password})
