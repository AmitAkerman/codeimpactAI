import requests

API_URL = "http://127.0.0.1:8000"

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
