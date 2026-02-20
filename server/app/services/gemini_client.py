import os
from google import genai

_client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

def generate_text(prompt: str) -> str:
    response = _client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
    )
    return response.text or ""
