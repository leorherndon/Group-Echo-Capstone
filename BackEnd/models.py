from sqlalchemy import Column, Integer, String, Date, Numeric, ForeignKey, Text, CheckConstraint, UniqueConstraint, Time, SmallInteger, TIMESTAMP
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base

class Student(Base):
    __tablename__ = 'students'
    student_id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    enrollment_year = Column(Integer, nullable=False)

    # Relationships
    registrations = relationship("Registration", back_populates="student")

    __table_args__ = (
        CheckConstraint('enrollment_year BETWEEN 1900 AND 2100', name='chk_year'),
    )

class Department(Base):
    __tablename__ = 'departments'
    department_id = Column(Integer, primary_key=True)
    dept_code = Column(String(10), unique=True, nullable=False)
    name = Column(Text, nullable=False)

    # Relationships
    courses = relationship("Course", back_populates="department")

class Course(Base):
    __tablename__ = 'courses'
    course_id = Column(Integer, primary_key=True)
    department_id = Column(Integer, ForeignKey('departments.department_id'), nullable=False)
    course_number = Column(String(10), nullable=False)
    title = Column(Text, nullable=False)
    description = Column(Text)
    credits = Column(Numeric(2, 1), nullable=False, default=3.0)

    # Relationships
    department = relationship("Department", back_populates="courses")
    sections = relationship("Section", back_populates="course")
    prerequisites = relationship("Course",
                                 secondary="prerequisites",
                                 primaryjoin="Course.course_id==prerequisites.c.course_id",
                                 secondaryjoin="Course.course_id==prerequisites.c.prerequisite_course_id",
                                 back_populates="required_for")
    required_for = relationship("Course",
                                secondary="prerequisites",
                                primaryjoin="Course.course_id==prerequisites.c.prerequisite_course_id",
                                secondaryjoin="Course.course_id==prerequisites.c.course_id",
                                back_populates="prerequisites")

    __table_args__ = (UniqueConstraint('department_id', 'course_number', name='unique_course'),)

class Term(Base):
    __tablename__ = 'terms'
    term_id = Column(Integer, primary_key=True)
    name = Column(String(30), unique=True, nullable=False)  # e.g. 'Fall 2025'
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)

    # Relationships
    sections = relationship("Section", back_populates="term")

class Instructor(Base):
    __tablename__ = 'instructors'
    instructor_id = Column(Integer, primary_key=True)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    email = Column(String(100), unique=True, nullable=False)

    # Relationships
    sections = relationship("Section", back_populates="instructor")

class Classroom(Base):
    __tablename__ = 'classrooms'
    classroom_id = Column(Integer, primary_key=True)
    building = Column(String(50), nullable=False)
    room_number = Column(String(10), nullable=False)
    capacity = Column(Integer)

    # Relationships
    meetings = relationship("Meeting", back_populates="classroom")

class Section(Base):
    __tablename__ = 'sections'
    section_id = Column(Integer, primary_key=True)
    course_id = Column(Integer, ForeignKey('courses.course_id', ondelete='CASCADE'), nullable=False)
    term_id = Column(Integer, ForeignKey('terms.term_id', ondelete='CASCADE'), nullable=False)
    section_number = Column(String(10), nullable=False)  # e.g. '001', 'A'
    instructor_id = Column(Integer, ForeignKey('instructors.instructor_id'), nullable=False)
    capacity = Column(Integer, nullable=False, default=30)

    # Relationships
    course = relationship("Course", back_populates="sections")
    term = relationship("Term", back_populates="sections")
    instructor = relationship("Instructor", back_populates="sections")
    meetings = relationship("Meeting", back_populates="section")
    registrations = relationship("Registration", back_populates="section")

    __table_args__ = (UniqueConstraint('course_id', 'term_id', 'section_number', name='unique_section'),)

class Meeting(Base):
    __tablename__ = 'meetings'
    meeting_id = Column(Integer, primary_key=True)
    section_id = Column(Integer, ForeignKey('sections.section_id', ondelete='CASCADE'), nullable=False)
    day_of_week = Column(SmallInteger, nullable=False)  # 1=Monday … 7=Sunday
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    classroom_id = Column(Integer, ForeignKey('classrooms.classroom_id'), nullable=False)

    # Relationships
    section = relationship("Section", back_populates="meetings")
    classroom = relationship("Classroom", back_populates="meetings")

    __table_args__ = (
        CheckConstraint('end_time > start_time', name='chk_meeting_time'),
    )

class Prerequisite(Base):
    __tablename__ = 'prerequisites'
    course_id = Column(Integer, ForeignKey('courses.course_id', ondelete='CASCADE'), primary_key=True)
    prerequisite_course_id = Column(Integer, ForeignKey('courses.course_id', ondelete='CASCADE'), primary_key=True)

    __table_args__ = (
        CheckConstraint('course_id != prerequisite_course_id', name='chk_self_prerequisite'),
    )

class Registration(Base):
    __tablename__ = 'registrations'
    registration_id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey('students.student_id', ondelete='CASCADE'), nullable=False)
    section_id = Column(Integer, ForeignKey('sections.section_id', ondelete='CASCADE'), nullable=False)
    registered_at = Column(TIMESTAMP, nullable=False, default=func.now())
    status = Column(String(20), nullable=False)

    # Relationships
    student = relationship("Student", back_populates="registrations")
    section = relationship("Section", back_populates="registrations")

    __table_args__ = (
        UniqueConstraint('student_id', 'section_id', name='unique_registration'),
        CheckConstraint("status IN ('enrolled', 'waitlisted', 'dropped')", name='chk_registration_status'),
    )