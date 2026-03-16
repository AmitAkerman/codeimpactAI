from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import your modular routers
from server.app.api.auth import router as auth_router
from server.app.api.teacher import router as teacher_router
from server.app.api.student import router as student_router
from server.app.api.admin import router as admin_router

app = FastAPI(title="Scratch AI API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include all routers
app.include_router(auth_router)
app.include_router(teacher_router)
app.include_router(student_router)
app.include_router(admin_router)

@app.get("/")
def root():
    return {"message": "Welcome to the Scratch AI API"}