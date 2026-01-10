from datetime import datetime

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

PROJECTS = [
    {"id": "p1", "student_id": 1, "title": "Pacman Game", "link": "https://scratch.mit.edu/projects/123",
     "status": "Pending", "submitted_at": "2024-01-01"},
    {"id": "p2", "student_id": 2, "title": "Maze Runner", "link": "https://scratch.mit.edu/projects/456",
     "status": "Pending", "submitted_at": "2024-01-02"},
]

RUBRICS = []
GRADES = []


def now_str():
    return str(datetime.now())
