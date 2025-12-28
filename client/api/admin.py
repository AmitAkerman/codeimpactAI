from .client import get

def stats():
    return get("/admin/stats")

def users():
    return get("/admin/users")
