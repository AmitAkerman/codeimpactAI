import requests

# We might need direct requests for downloading the raw template string if not using a wrapper
from .client import API_URL
from .client import get, post_file  # Assuming post_file was added to client.py


def stats():
    return get("/admin/stats")


def users():
    return get("/admin/users")


def upload_users_csv(file_obj):
    # keys matching the FastAPI parameter name 'file'
    return post_file("/admin/users/upload", files={"file": file_obj})

def upload_teachers_csv(file_obj):
    return post_file("/admin/teachers/upload", files={"file": file_obj})

def get_csv_template():
    # Direct get to return raw text
    return requests.get(f"{API_URL}/admin/users/template").text
