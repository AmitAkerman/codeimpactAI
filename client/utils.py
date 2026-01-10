import re
import requests
import json

def get_scratch_json_from_url(url):
    project_id_match = re.search(r'projects/(\d+)', url)
    if not project_id_match:
        return {"error": "Invalid Scratch URL"}
    
    project_id = project_id_match.group(1)
    
    api_url = f"https://api.scratch.mit.edu/projects/{project_id}"
    
    try:
        response = requests.get(api_url)
        if response.status_code == 200:
            return response.json()
        return {"error": "Project not found"}
    except Exception as e:
        return {"error": str(e)}
