from typing import Optional, Literal

from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    role: Literal["student", "faculty"]
    email: EmailStr
    password: str
    studentId: Optional[str] = None
    department: Optional[str] = None
    remember: Optional[bool] = False


class LoginResponse(BaseModel):
    message: str
    redirect: Optional[str] = None
    token: Optional[str] = None


app = FastAPI(title="University Portal API")

# Allow cross-origin requests during development. Adjust origins for production.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=False,
)


@app.exception_handler(HTTPException)
async def custom_http_exception_handler(_, exc: HTTPException):
    # Ensure error responses use { "message": ... } for frontend
    return JSONResponse(status_code=exc.status_code, content={"message": exc.detail})


@app.post("/api/login", response_model=LoginResponse)
def login(payload: LoginRequest, response: Response) -> LoginResponse:
    user_role = payload.role

    # Role-specific validation
    if user_role == "student" and not (payload.studentId and payload.studentId.strip()):
        raise HTTPException(status_code=400, detail="Please enter your Student ID.")

    # Demo credential checks
    is_student_demo = (
        user_role == "student"
        and payload.email.lower() == "student01@university.edu"
        and payload.password == "Password123!"
        and (payload.studentId or "").upper() == "S0001234"
    )

    is_faculty_demo = (
        user_role == "faculty"
        and payload.email.lower() == "prof.jane@university.edu"
        and payload.password == "ProfPass!"
    )

    if not (is_student_demo or is_faculty_demo):
        # In a real app, verify hashed passwords from your user store
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    redirect_path = "/student/dashboard" if user_role == "student" else "/faculty/dashboard"
    token = "demo-student-token" if user_role == "student" else "demo-faculty-token"

    # Optionally set a session cookie the client can use
    max_age_seconds = 60 * 60 * 24 * 30 if payload.remember else None
    response.set_cookie(
        key="session",
        value=token,
        max_age=max_age_seconds,
        path="/",
        httponly=True,
        secure=False,  # Set True behind HTTPS in production
        samesite="lax",
    )

    return LoginResponse(message="Signed in successfully", redirect=redirect_path, token=token)


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}
