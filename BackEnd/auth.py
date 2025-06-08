from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from models import Student
from utils import hash_password, verify_password
from database import SessionLocal
from pydantic import BaseModel, EmailStr

router = APIRouter()

class RegisterSchema(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    password: str
    enrollment_year: int

class LoginSchema(BaseModel):
    email: EmailStr
    password: str

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/register")
def register(data: RegisterSchema, db: Session = Depends(get_db)):
    # Check email exists
    if db.query(Student).filter_by(email=data.email).first():
        raise HTTPException(status_code=400, detail="Email already registered.")
    # Create new student
    student = Student(
        first_name=data.first_name,
        last_name=data.last_name,
        email=data.email,
        password_hash=hash_password(data.password),
        enrollment_year=data.enrollment_year
    )
    db.add(student)
    db.commit()
    db.refresh(student)
    return {"message": "Registration successful."}

@router.post("/login")
def login(data: LoginSchema, db: Session = Depends(get_db)):
    student = db.query(Student).filter_by(email=data.email).first()
    if not student or not verify_password(data.password, student.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials.")
    # For demo, just return student_id. Use JWT in production!
    return {"student_id": student.student_id, "message": "Login successful."}
