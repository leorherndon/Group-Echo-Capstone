from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_
from typing import List
from pydantic import BaseModel
from database import SessionLocal
from models import Registration, Section, Course, Student, Meeting, Classroom, Department, Instructor
from datetime import datetime, time

router = APIRouter()

# Pydantic schemas
class RegistrationRequest(BaseModel):
    student_id: int
    section_id: int

class DropRequest(BaseModel):
    student_id: int
    section_id: int

class ScheduleResponse(BaseModel):
    registration_id: int
    section_id: int
    course_code: str  # e.g., "CMSC 101"
    course_title: str
    section_number: str
    credits: float
    instructor_name: str
    status: str
    registered_at: datetime
    meetings: List[dict]  # Day, time, location info

    class Config:
        from_attributes = True

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def check_schedule_conflict(db: Session, student_id: int, new_section_id: int) -> bool:
    """Check if a new section conflicts with student's current schedule"""
    # Get all enrolled sections for the student
    enrolled_registrations = db.query(Registration).filter(
        and_(
            Registration.student_id == student_id,
            Registration.status == 'enrolled'
        )
    ).all()

    # Get meetings for the new section
    new_section = db.query(Section).options(
        joinedload(Section.meetings)
    ).filter(Section.section_id == new_section_id).first()

    if not new_section:
        return True  # Section doesn't exist, conflict by default

    new_meetings = new_section.meetings

    # Check each enrolled section for conflicts
    for registration in enrolled_registrations:
        existing_section = db.query(Section).options(
            joinedload(Section.meetings)
        ).filter(Section.section_id == registration.section_id).first()

        if existing_section:
            # Check if any meetings overlap
            for existing_meeting in existing_section.meetings:
                for new_meeting in new_meetings:
                    # Same day of week?
                    if existing_meeting.day_of_week == new_meeting.day_of_week:
                        # Check time overlap
                        if (new_meeting.start_time < existing_meeting.end_time and
                                new_meeting.end_time > existing_meeting.start_time):
                            return True  # Conflict found

    return False  # No conflicts

def check_capacity(db: Session, section_id: int) -> bool:
    """Check if section has available capacity"""
    section = db.query(Section).filter(Section.section_id == section_id).first()
    if not section:
        return False

    enrolled_count = db.query(Registration).filter(
        and_(
            Registration.section_id == section_id,
            Registration.status == 'enrolled'
        )
    ).count()

    return enrolled_count < section.capacity

def is_already_registered(db: Session, student_id: int, section_id: int) -> bool:
    """Check if student is already registered for this section"""
    existing = db.query(Registration).filter(
        and_(
            Registration.student_id == student_id,
            Registration.section_id == section_id,
            Registration.status.in_(['enrolled', 'waitlisted'])
        )
    ).first()

    return existing is not None

def is_already_registered_for_course(db: Session, student_id: int, course_id: int, term_id: int) -> bool:
    """Check if student is already registered for this course in the same term"""
    existing = db.query(Registration).join(Section).filter(
        and_(
            Registration.student_id == student_id,
            Section.course_id == course_id,
            Section.term_id == term_id,
            Registration.status.in_(['enrolled', 'waitlisted'])
        )
    ).first()

    return existing is not None

@router.post("/register")
def register_for_course(request: RegistrationRequest, db: Session = Depends(get_db)):
    """Register a student for a course section"""

    # Verify student exists
    student = db.query(Student).filter(Student.student_id == request.student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    # Verify section exists
    section = db.query(Section).options(
        joinedload(Section.course)
    ).filter(Section.section_id == request.section_id).first()
    if not section:
        raise HTTPException(status_code=404, detail="Section not found")

    # Check if already registered for this section
    if is_already_registered(db, request.student_id, request.section_id):
        raise HTTPException(status_code=400, detail="Already registered for this section")

    # Check if already registered for this course in the same term
    if is_already_registered_for_course(db, request.student_id, section.course_id, section.term_id):
        raise HTTPException(status_code=400, detail="Already registered for this course in this term")

    # Check for schedule conflicts
    if check_schedule_conflict(db, request.student_id, request.section_id):
        raise HTTPException(status_code=400, detail="Schedule conflict with existing courses")

    # Check capacity and determine status
    if check_capacity(db, request.section_id):
        status = "enrolled"
    else:
        status = "waitlisted"

    # Create registration
    registration = Registration(
        student_id=request.student_id,
        section_id=request.section_id,
        status=status,
        registered_at=datetime.now()
    )

    db.add(registration)
    db.commit()
    db.refresh(registration)

    return {
        "message": f"Successfully {status} for course",
        "registration_id": registration.registration_id,
        "status": status
    }

@router.post("/drop")
def drop_course(request: DropRequest, db: Session = Depends(get_db)):
    """Drop a student from a course section"""

    # Find the registration
    registration = db.query(Registration).filter(
        and_(
            Registration.student_id == request.student_id,
            Registration.section_id == request.section_id,
            Registration.status.in_(['enrolled', 'waitlisted'])
        )
    ).first()

    if not registration:
        raise HTTPException(status_code=404, detail="Registration not found")

    # Update status to dropped
    registration.status = "dropped"
    db.commit()

    # If this was an enrolled student, check if we can promote someone from waitlist
    if registration.status == "enrolled":
        waitlisted = db.query(Registration).filter(
            and_(
                Registration.section_id == request.section_id,
                Registration.status == 'waitlisted'
            )
        ).order_by(Registration.registered_at).first()

        if waitlisted:
            waitlisted.status = "enrolled"
            db.commit()

    return {"message": "Successfully dropped from course"}

@router.get("/schedule/{student_id}", response_model=List[ScheduleResponse])
def get_student_schedule(student_id: int, term_id: int = None, db: Session = Depends(get_db)):
    """Get a student's current schedule"""

    # Verify student exists
    student = db.query(Student).filter(Student.student_id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    # Build query for registrations
    query = db.query(Registration).options(
        joinedload(Registration.section).joinedload(Section.course).joinedload(Course.department),
        joinedload(Registration.section).joinedload(Section.instructor),
        joinedload(Registration.section).joinedload(Section.meetings).joinedload(Meeting.classroom)
    ).filter(
        and_(
            Registration.student_id == student_id,
            Registration.status.in_(['enrolled', 'waitlisted'])
        )
    )

    # Filter by term if specified
    if term_id:
        query = query.join(Section).filter(Section.term_id == term_id)

    registrations = query.all()

    # Build response
    schedule = []
    for reg in registrations:
        section = reg.section
        course = section.course
        department = course.department
        instructor = section.instructor

        # Format meetings
        meetings = []
        for meeting in section.meetings:
            day_names = {1: "Monday", 2: "Tuesday", 3: "Wednesday",
                         4: "Thursday", 5: "Friday", 6: "Saturday", 7: "Sunday"}

            meetings.append({
                "day": day_names.get(meeting.day_of_week, "Unknown"),
                "start_time": meeting.start_time.strftime("%H:%M"),
                "end_time": meeting.end_time.strftime("%H:%M"),
                "location": f"{meeting.classroom.building} {meeting.classroom.room_number}"
            })

        schedule.append(ScheduleResponse(
            registration_id=reg.registration_id,
            section_id=section.section_id,
            course_code=f"{department.dept_code} {course.course_number}",
            course_title=course.title,
            section_number=section.section_number,
            credits=float(course.credits),
            instructor_name=f"{instructor.first_name} {instructor.last_name}",
            status=reg.status,
            registered_at=reg.registered_at,
            meetings=meetings
        ))

    return schedule

@router.get("/check-availability/{section_id}")
def check_section_availability(section_id: int, db: Session = Depends(get_db)):
    """Check availability for a specific section"""

    section = db.query(Section).filter(Section.section_id == section_id).first()
    if not section:
        raise HTTPException(status_code=404, detail="Section not found")

    enrolled_count = db.query(Registration).filter(
        and_(
            Registration.section_id == section_id,
            Registration.status == 'enrolled'
        )
    ).count()

    waitlisted_count = db.query(Registration).filter(
        and_(
            Registration.section_id == section_id,
            Registration.status == 'waitlisted'
        )
    ).count()

    available_seats = section.capacity - enrolled_count

    return {
        "section_id": section_id,
        "capacity": section.capacity,
        "enrolled": enrolled_count,
        "waitlisted": waitlisted_count,
        "available_seats": max(0, available_seats),
        "is_full": available_seats <= 0
    }