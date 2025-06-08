from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_
from typing import List, Optional
from pydantic import BaseModel
from database import SessionLocal
from models import Course, Department, Section, Term, Instructor, Meeting, Classroom
from datetime import time

router = APIRouter()

# Pydantic schemas for API responses
class DepartmentResponse(BaseModel):
    department_id: int
    dept_code: str
    name: str

    class Config:
        from_attributes = True

class CourseResponse(BaseModel):
    course_id: int
    department_id: int
    course_number: str
    title: str
    description: Optional[str]
    credits: float
    department: DepartmentResponse

    class Config:
        from_attributes = True

class MeetingResponse(BaseModel):
    day_of_week: int
    start_time: time
    end_time: time
    building: str
    room_number: str

    class Config:
        from_attributes = True

class InstructorResponse(BaseModel):
    instructor_id: int
    first_name: str
    last_name: str
    email: str

    class Config:
        from_attributes = True

class SectionResponse(BaseModel):
    section_id: int
    section_number: str
    capacity: int
    enrolled_count: int
    available_seats: int
    instructor: InstructorResponse
    meetings: List[MeetingResponse]

    class Config:
        from_attributes = True

class CourseWithSectionsResponse(BaseModel):
    course_id: int
    department_id: int
    course_number: str
    title: str
    description: Optional[str]
    credits: float
    department: DepartmentResponse
    sections: List[SectionResponse]

    class Config:
        from_attributes = True

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_enrolled_count(db: Session, section_id: int) -> int:
    """Get the number of enrolled students in a section"""
    from models import Registration
    return db.query(Registration).filter(
        and_(
            Registration.section_id == section_id,
            Registration.status == 'enrolled'
        )
    ).count()

@router.get("/departments", response_model=List[DepartmentResponse])
def get_departments(db: Session = Depends(get_db)):
    """Get all departments"""
    departments = db.query(Department).all()
    return departments

@router.get("/", response_model=List[CourseResponse])
def get_courses(
        department_id: Optional[int] = Query(None, description="Filter by department"),
        search: Optional[str] = Query(None, description="Search in course title or description"),
        db: Session = Depends(get_db)
):
    """Get all courses with optional filtering"""
    query = db.query(Course).options(joinedload(Course.department))

    # Filter by department if specified
    if department_id:
        query = query.filter(Course.department_id == department_id)

    # Search in title or description if specified
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Course.title.ilike(search_term),
                Course.description.ilike(search_term),
                Course.course_number.ilike(search_term)
            )
        )

    courses = query.all()
    return courses

@router.get("/{course_id}", response_model=CourseResponse)
def get_course(course_id: int, db: Session = Depends(get_db)):
    """Get a specific course by ID"""
    course = db.query(Course).options(joinedload(Course.department)).filter(Course.course_id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    return course

@router.get("/{course_id}/sections", response_model=List[SectionResponse])
def get_course_sections(
        course_id: int,
        term_id: Optional[int] = Query(None, description="Filter by term"),
        db: Session = Depends(get_db)
):
    """Get all sections for a specific course"""
    # Verify course exists
    course = db.query(Course).filter(Course.course_id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    # Build query for sections
    query = db.query(Section).options(
        joinedload(Section.instructor),
        joinedload(Section.meetings).joinedload(Meeting.classroom)
    ).filter(Section.course_id == course_id)

    # Filter by term if specified
    if term_id:
        query = query.filter(Section.term_id == term_id)

    sections = query.all()

    # Build response with enrollment data
    section_responses = []
    for section in sections:
        enrolled_count = get_enrolled_count(db, section.section_id)
        available_seats = section.capacity - enrolled_count

        # Format meetings
        meetings = []
        for meeting in section.meetings:
            meetings.append(MeetingResponse(
                day_of_week=meeting.day_of_week,
                start_time=meeting.start_time,
                end_time=meeting.end_time,
                building=meeting.classroom.building,
                room_number=meeting.classroom.room_number
            ))

        section_responses.append(SectionResponse(
            section_id=section.section_id,
            section_number=section.section_number,
            capacity=section.capacity,
            enrolled_count=enrolled_count,
            available_seats=available_seats,
            instructor=InstructorResponse(
                instructor_id=section.instructor.instructor_id,
                first_name=section.instructor.first_name,
                last_name=section.instructor.last_name,
                email=section.instructor.email
            ),
            meetings=meetings
        ))

    return section_responses

@router.get("/catalog/{term_id}", response_model=List[CourseWithSectionsResponse])
def get_course_catalog(
        term_id: int,
        department_id: Optional[int] = Query(None, description="Filter by department"),
        search: Optional[str] = Query(None, description="Search in course title or description"),
        db: Session = Depends(get_db)
):
    """Get the complete course catalog for a term with all sections"""
    # Verify term exists
    term = db.query(Term).filter(Term.term_id == term_id).first()
    if not term:
        raise HTTPException(status_code=404, detail="Term not found")

    # Build base query
    query = db.query(Course).options(
        joinedload(Course.department),
        joinedload(Course.sections).joinedload(Section.instructor),
        joinedload(Course.sections).joinedload(Section.meetings).joinedload(Meeting.classroom)
    ).join(Section).filter(Section.term_id == term_id)

    # Apply filters
    if department_id:
        query = query.filter(Course.department_id == department_id)

    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Course.title.ilike(search_term),
                Course.description.ilike(search_term),
                Course.course_number.ilike(search_term)
            )
        )

    courses = query.distinct().all()

    # Build response with section data
    catalog_responses = []
    for course in courses:
        # Filter sections for this term
        term_sections = [s for s in course.sections if s.term_id == term_id]

        section_responses = []
        for section in term_sections:
            enrolled_count = get_enrolled_count(db, section.section_id)
            available_seats = section.capacity - enrolled_count

            meetings = []
            for meeting in section.meetings:
                meetings.append(MeetingResponse(
                    day_of_week=meeting.day_of_week,
                    start_time=meeting.start_time,
                    end_time=meeting.end_time,
                    building=meeting.classroom.building,
                    room_number=meeting.classroom.room_number
                ))

            section_responses.append(SectionResponse(
                section_id=section.section_id,
                section_number=section.section_number,
                capacity=section.capacity,
                enrolled_count=enrolled_count,
                available_seats=available_seats,
                instructor=InstructorResponse(
                    instructor_id=section.instructor.instructor_id,
                    first_name=section.instructor.first_name,
                    last_name=section.instructor.last_name,
                    email=section.instructor.email
                ),
                meetings=meetings
            ))

        catalog_responses.append(CourseWithSectionsResponse(
            course_id=course.course_id,
            department_id=course.department_id,
            course_number=course.course_number,
            title=course.title,
            description=course.description,
            credits=course.credits,
            department=DepartmentResponse(
                department_id=course.department.department_id,
                dept_code=course.department.dept_code,
                name=course.department.name
            ),
            sections=section_responses
        ))

    return catalog_responses

@router.get("/terms/", response_model=List[dict])
def get_terms(db: Session = Depends(get_db)):
    """Get all available terms"""
    terms = db.query(Term).all()
    return [
        {
            "term_id": term.term_id,
            "name": term.name,
            "start_date": term.start_date,
            "end_date": term.end_date
        }
        for term in terms
    ]