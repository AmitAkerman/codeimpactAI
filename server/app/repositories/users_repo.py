from .db import supabase


def _map_user(u):
    """Helper to match DB columns to Python User model"""
    if not u: return None
    return {
        "id": u.get("id"),
        "username": u.get("username"),
        "password": u.get("password"),
        "role": u.get("role"),
        "name": u.get("full_name"),
        "email": u.get("username"),
        "class_name": u.get("class_name")
    }


def find_user_by_credentials(username: str, password: str):
    print(f"🔍 DEBUG: Attempting login for user: '{username}' with password: '{password}'")

    try:
        # executing the query
        response = supabase.table("users").select("*") \
            .eq("username", username) \
            .eq("password", password) \
            .execute()

        print(f"📨 DEBUG: Supabase Response Data: {response.data}")

        if not response.data:
            print("❌ DEBUG: No user found in database with these credentials.")
            return None

        print("✅ DEBUG: User found!")
        return _map_user(response.data[0])

    except Exception as e:
        print(f"🔥 DEBUG: Supabase Connection Error: {e}")
        return None


def list_students():
    response = supabase.table("users").select("*").eq("role", "student").execute()
    return [_map_user(u) for u in response.data]


def list_all_users():
    response = supabase.table("users").select("*").execute()
    return [_map_user(u) for u in response.data]

def create_user(user_data: dict):
    response = supabase.table("users").insert(user_data).execute()
    return _map_user(response.data[0]) if response.data else None