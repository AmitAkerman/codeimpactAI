import requests
import streamlit as st  # <--- NEW IMPORT

# This tells the app: "Look for a cloud secret first. If not found, use my laptop."
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


def post_file(path: str, files: dict):
    # Determine if we are sending other data or just files.
    # For this specific case, we usually just send the file.
    return _handle(requests.post(f"{API_URL}{path}", files=files))
