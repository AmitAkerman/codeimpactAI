from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import uvicorn
import random
from datetime import datetime
from supabase import create_client, Client

app = FastAPI()

# --- 1. CONFIGURATION ---
# Using the credentials from your working snippet
SUPABASE_URL = "https://hmouoztlgrsotauzohgm.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imhtb3VvenRsZ3Jzb3RhdXpvaGdtIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjQzMjgwNjUsImV4cCI6MjA3OTkwNDA2NX0.7lICVEIkYaG_629xN_nVPUJspUgkhRswkKJKTF2TNBg"

# Initialize Supabase
try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception as e:
    print(f"Error connecting to Supabase: {e}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- 2. DATA MODELS ---
class LoginRequest(BaseModel):
    username: str
    password: str


class ProjectSubmit(BaseModel):
    student_id: str
    assignment_id: str
    link: str


class RubricCreate(BaseModel):
    teacher_id: str
    title: str
    class_name: str
    criteria: List[Dict]


class AIAnalysisRequest(BaseModel):
    project_url: str
    rubric_id: str


class GradeSubmit(BaseModel):
    project_id: str
    rubric_id: str
    total_score: int
    feedback: str
    details: Dict[str, Any]


# --- 3. ENDPOINTS ---

@app.post("/login")
def login(creds: LoginRequest):
    print(f"🔍 Login attempt for: {creds.username}")

    # 1. Fetch by Username ONLY (Matches your working Streamlit logic)
    response = supabase.table("users").select("*").eq("username", creds.username).execute()

    if not response.data:
        print("❌ User not found in DB")
        raise HTTPException(status_code=400, detail="Invalid Credentials")

    user = response.data[0]

    # 2. Check Password in Python
    # Note: In a real app, use hashing! For now, we compare plain text as per your setup.
    if str(user.get("password")) != creds.password:
        print("❌ Wrong password")
        raise HTTPException(status_code=400, detail="Invalid Credentials")

    print("✅ Login Success")
    return {
        "id": user["id"],
        "username": user["username"],
        "role": user["role"],
        "name": user.get("full_name"),
        "class_name": user.get("class_name")
    }


# === STUDENT WINDOWS ===

@app.get("/student/dashboard/{student_id}")
def get_student_dashboard(student_id: str, class_name: str):
    # 1. Get Assignments for this class
    assigns_res = supabase.table("assignments").select("*").eq("class_name", class_name).execute()
    assigns = assigns_res.data if assigns_res.data else []

    # 2. Get Submissions for this student
    subs_res = supabase.table("submissions").select("*").eq("student_id", student_id).execute()
    subs = subs_res.data if subs_res.data else []

    # Map submissions by assignment_id
    sub_map = {s["assignment_id"]: s for s in subs}

    results = []
    for a in assigns:
        item = {
            "assignment_id": a["id"],
            "title": a["title"],
            "is_submitted": False,
            "status": "To Do",
            "score": None,
            "feedback": None,
            "link": ""
        }

        if a["id"] in sub_map:
            s = sub_map[a["id"]]
            item["is_submitted"] = True
            item["status"] = s["status"]
            item["link"] = s["link"]
            item["score"] = s.get("final_score")
            item["feedback"] = s.get("feedback")

        results.append(item)

    return results


@app.post("/student/submit")
def submit_project(proj: ProjectSubmit):
    data = {
        "student_id": proj.student_id,
        "assignment_id": proj.assignment_id,
        "link": proj.link,
        "status": "Pending",
        "submitted_at": datetime.now().isoformat()
    }
    supabase.table("submissions").insert(data).execute()
    return {"message": "Submitted"}


# === TEACHER WINDOWS ===

@app.get("/teacher/students")
def get_students():
    # Get all students
    response = supabase.table("users").select("*").eq("role", "student").execute()
    students = response.data if response.data else []

    # Simple count of submissions for UI
    for s in students:
        subs = supabase.table("submissions").select("id", count="exact").eq("student_id", s["id"]).execute()
        s["project_count"] = subs.count
        s["name"] = s.get("full_name", s["username"])

    return students


@app.get("/teacher/student/{student_id}/projects")
def get_student_work(student_id: str):
    # Join submissions with assignments to get titles
    response = supabase.table("submissions").select("*, assignments(title)").eq("student_id", student_id).execute()

    results = []
    if response.data:
        for row in response.data:
            results.append({
                "id": row["id"],
                "title": row["assignments"]["title"] if row.get("assignments") else "Unknown",
                "status": row["status"],
                "link": row["link"],
                "score": row.get("final_score"),
                "feedback": row.get("feedback")
            })
    return results


@app.post("/teacher/rubrics")
def create_rubric(r: RubricCreate):
    data = {
        "teacher_id": r.teacher_id,
        "title": r.title,
        "class_name": r.class_name,
        "rubric": r.criteria
    }
    supabase.table("assignments").insert(data).execute()
    return {"message": "Rubric Created"}


@app.get("/teacher/rubrics")
def get_rubrics():
    response = supabase.table("assignments").select("*").execute()
    return [{"id": a["id"], "title": a["title"], "criteria": a["rubric"]} for a in
            response.data] if response.data else []


# *** AI ANALYSIS ***
@app.post("/teacher/analyze_ai")
def analyze_with_ai(req: AIAnalysisRequest):
    response = supabase.table("assignments").select("*").eq("id", req.rubric_id).execute()
    if not response.data:
        return {"error": "Rubric not found"}

    rubric_criteria = response.data[0]["rubric"]

    # Mock AI Logic
    ai_results = {}
    total_score = 0
    feedback_lines = []

    for crit in rubric_criteria:
        score = random.randint(70, 100)
        weighted_score = score * (crit["weight"] / 100)
        ai_results[crit["name"]] = score
        total_score += weighted_score
        feedback_lines.append(f"- **{crit['name']}**: Good implementation, but check edge cases.")

    final_feedback = "### AI Assessment:\n" + "\n".join(feedback_lines)

    return {
        "suggested_score": int(total_score),
        "suggested_feedback": final_feedback,
        "details": ai_results
    }


@app.post("/teacher/grade")
def submit_final_grade(g: GradeSubmit):
    data = {
        "final_score": g.total_score,
        "feedback": g.feedback,
        "status": "Graded"
    }
    supabase.table("submissions").update(data).eq("id", g.project_id).execute()
    return {"message": "Grade Saved"}


# === ADMIN WINDOWS ===

@app.get("/admin/users")
def get_all_users():
    return supabase.table("users").select("*").execute().data


@app.get("/admin/stats")
def get_stats():
    users = supabase.table("users").select("*").execute().data
    projects = supabase.table("assignments").select("id", count="exact").execute()
    graded = supabase.table("submissions").select("id", count="exact").eq("status", "Graded").execute()

    return {
        "students": len([u for u in users if u["role"] == "student"]),
        "projects": projects.count,
        "graded": graded.count,
        "teachers": len([u for u in users if u["role"] == "teacher"])
    }