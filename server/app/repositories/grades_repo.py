from .db_mock import GRADES

def insert_grade(grade: dict):
    GRADES.append(grade)
    return grade

def list_grades():
    return GRADES
