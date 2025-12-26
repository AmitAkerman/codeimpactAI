from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
import uvicorn
import uuid
import random
from datetime import datetime

app = FastAPI()

# --- 1. CONFIGURATION ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 2. MOCK DATABASE ---
USERS = [
    {"id": 1, "username": "student", "password": "123", "role": "student", "name": "Alex Student",
     "email": "alex@school.com"},
    {"id": 2, "username": "student2", "password": "123", "role": "student", "name": "Jamie Code",
     "email": "jamie@school.com"},
    {"id": 3, "username": "teacher", "password": "123", "role": "teacher", "name": "Mr. Smith",
     "email": "smith@school.com"},
    {"id": 4, "username": "admin", "password": "123", "role": "admin", "name": "Principal Skinner",
     "email": "admin@school.com"},
]

# We pre-fill some data so the "Windows" aren't empty when you login
PROJECTS = [
    {"id": "p1", "student_id": 1, "title": "Pacman Game", "link": "https://scratch.mit.edu/projects/123",
     "status": "Pending", "submitted_at": "2024-01-01"},
    {"id": "p2", "student_id": 2, "title": "Maze Runner", "link": "https://scratch.mit.edu/projects/456",
     "status": "Pending", "submitted_at": "2024-01-02"},
]
RUBRICS = []
GRADES = []


# --- 3. DATA MODELS ---
class LoginRequest(BaseModel):
    username: str
    password: str


class ProjectSubmit(BaseModel):
    student_id: int
    title: str
    link: str


class RubricCreate(BaseModel):
    teacher_id: int
    title: str
    criteria: List[Dict]  # e.g., [{"name": "Logic", "weight": 50, "sub_criteria": ["Loops", "Variables"]}]


class AIAnalysisRequest(BaseModel):
    project_url: str
    rubric_id: str


class GradeSubmit(BaseModel):
    project_id: str
    rubric_id: str
    total_score: int
    feedback: str
    details: Dict[str, int]


# --- 4. ENDPOINTS ---

@app.post("/login")
def login(creds: LoginRequest):
    # Case-insensitive login
    user = next(
        (u for u in USERS if u["username"].lower() == creds.username.lower() and u["password"] == creds.password), None)
    if user: return user
    raise HTTPException(status_code=400, detail="Invalid Credentials")


# === STUDENT WINDOWS ===

@app.get("/student/{student_id}/projects")
def get_my_projects(student_id: int):
    # Join Projects with Grades
    my_projs = [p for p in PROJECTS if p["student_id"] == student_id]
    results = []
    for p in my_projs:
        grade = next((g for g in GRADES if g["project_id"] == p["id"]), None)
        p_data = p.copy()
        if grade:
            p_data["status"] = "Graded"
            p_data["score"] = grade["total_score"]
            p_data["feedback"] = grade["feedback"]
        else:
            p_data["status"] = "Pending"
        results.append(p_data)
    return results


@app.post("/student/submit")
def submit_project(proj: ProjectSubmit):
    new_p = {
        "id": str(uuid.uuid4())[:8],
        "student_id": proj.student_id,
        "title": proj.title,
        "link": proj.link,
        "status": "Pending",
        "submitted_at": str(datetime.now())
    }
    PROJECTS.append(new_p)
    return {"message": "Submitted"}


# === TEACHER WINDOWS ===

@app.get("/teacher/students")
def get_students():
    # Helper to count projects for each student
    students = [u for u in USERS if u["role"] == "student"]
    for s in students:
        s["project_count"] = len([p for p in PROJECTS if p["student_id"] == s["id"]])
    return students


@app.get("/teacher/student/{student_id}/projects")
def get_student_work(student_id: int):
    return get_my_projects(student_id)


@app.post("/teacher/rubrics")
def create_rubric(r: RubricCreate):
    new_r = {"id": str(uuid.uuid4())[:8], "teacher_id": r.teacher_id, "title": r.title, "criteria": r.criteria}
    RUBRICS.append(new_r)
    return {"message": "Rubric Created"}


@app.get("/teacher/rubrics")
def get_rubrics():
    return RUBRICS


# *** NEW: AI ANALYSIS SIMULATION ***
@app.post("/teacher/analyze_ai")
def analyze_with_ai(req: AIAnalysisRequest):
    """
    Simulates the AI reading the Scratch code and generating a grade
    based on the specific Rubric provided.
    """
    # 1. Find the Rubric
    rubric = next((r for r in RUBRICS if r["id"] == req.rubric_id), None)
    if not rubric:
        return {"error": "Rubric not found"}

    # 2. Mock AI Logic (Randomly generates scores for demo)
    ai_results = {}
    total_score = 0
    feedback_lines = []

    for crit in rubric["criteria"]:
        # AI "thinks" about the code...
        score = random.randint(70, 100)  # Mock score
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
    # Teacher reviews AI suggestion and submits final
    GRADES.append(g.dict())

    # Update project status
    for p in PROJECTS:
        if p["id"] == g.project_id:
            p["status"] = "Graded"

    return {"message": "Grade Saved"}


# === ADMIN WINDOWS ===

@app.get("/admin/users")
def get_all_users():
    return USERS


@app.get("/admin/stats")
def get_stats():
    return {
        "students": len([u for u in USERS if u["role"] == "student"]),
        "projects": len(PROJECTS),
        "graded": len(GRADES),
        "teachers": len([u for u in USERS if u["role"] == "teacher"])
    }


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)