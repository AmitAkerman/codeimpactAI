import requests
import streamlit as st

API_URL = st.secrets.get("API_URL", "http://127.0.0.1:8000")

class APIError(Exception):
    pass

def _handle(res: requests.Response):
    if res.status_code >= 400:
        try:
            detail = res.json()
        except Exception:
            detail = {"detail": res.text}
        raise APIError(detail)
    return res.json()

def get(path: str):
    return _handle(requests.get(f"{API_URL}{path}"))

def post(path: str, json: dict):
    return _handle(requests.post(f"{API_URL}{path}", json=json))

def put(path: str, json: dict):
    return _handle(requests.put(f"{API_URL}{path}", json=json))

def delete(path: str):
    return _handle(requests.delete(f"{API_URL}{path}"))

def post_file(path: str, files: dict):
    return _handle(requests.post(f"{API_URL}{path}", files=files))

def update_project(project_id, project_data, token):
    headers = {"Authorization": f"Bearer {token}"}
    try:
        response = requests.put(
            f"{API_URL}/projects/{project_id}",
            json=project_data,
            headers=headers
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return None