#!/usr/bin/env python3
"""
Database Setup Script for UMGC Course Registration System
This script will create the database and tables if they don't exist.
"""

import psycopg2
from psycopg2 import sql
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import sys
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker


def create_database():
    """Create the course_registration database if it doesn't exist"""

    print("🔧 Setting up database...")

    # Connection parameters
    db_params = {
        'host': 'localhost',
        'port': 5432,
        'user': 'postgres',
        'password': '123456'
    }

    try:
        # Connect to PostgreSQL server (without specifying database)
        print(f"📡 Connecting to PostgreSQL server at {db_params['host']}:{db_params['port']}...")
        conn = psycopg2.connect(**db_params)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()

        # Check if database exists
        cursor.execute("SELECT 1 FROM pg_database WHERE datname = 'course_registration'")
        exists = cursor.fetchone()

        if exists:
            print("✅ Database 'course_registration' already exists")
        else:
            # Create database
            print("🏗️  Creating database 'course_registration'...")
            cursor.execute(sql.SQL("CREATE DATABASE {}").format(
                sql.Identifier('course_registration')
            ))
            print("✅ Database 'course_registration' created successfully!")

        cursor.close()
        conn.close()

        return True

    except psycopg2.Error as e:
        print(f"❌ Error connecting to PostgreSQL: {e}")
        print("\n💡 Make sure PostgreSQL is running and your credentials are correct.")
        print("   Default PostgreSQL credentials:")
        print("   - Host: localhost")
        print("   - Port: 5432")
        print("   - User: postgres")
        print("   - Password: 123456")
        return False


def create_tables():
    """Create all tables using SQLAlchemy models"""

    print("\n🏗️  Creating database tables...")

    try:
        # Import models after database is created
        from database import engine, Base
        from models import Student, Department, Course, Term, Instructor, Classroom, Section, Meeting, Prerequisite, Registration

        # Create all tables
        Base.metadata.create_all(bind=engine)
        print("✅ All database tables created successfully!")

        return True

    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        return False


def test_connection():
    """Test the database connection and display table information"""

    print("\n🧪 Testing database connection...")

    try:
        from database import engine

        with engine.connect() as conn:
            # Test basic connection
            result = conn.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            print(f"✅ Connected to PostgreSQL: {version.split(',')[0]}")

            # List tables
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """))

            tables = [row[0] for row in result.fetchall()]

            if tables:
                print(f"\n📋 Found {len(tables)} tables:")
                for table in tables:
                    print(f"   • {table}")
            else:
                print("\n⚠️  No tables found in database")

        return True

    except Exception as e:
        print(f"❌ Connection test failed: {e}")
        return False


def insert_sample_data():
    """Insert sample data for testing"""

    print("\n📊 Inserting sample data...")

    try:
        from database import SessionLocal
        from models import Department, Term, Instructor, Classroom, Course, Section, Meeting
        from datetime import date, time

        db = SessionLocal()

        # Check if data already exists
        if db.query(Department).first():
            print("ℹ️  Sample data already exists, skipping...")
            db.close()
            return True

        # Sample departments
        departments = [
            Department(dept_code="CMSC", name="Computer Science"),
            Department(dept_code="MATH", name="Mathematics"),
            Department(dept_code="ENGL", name="English"),
        ]

        for dept in departments:
            db.add(dept)

        db.flush()  # Get IDs

        # Sample terms
        terms = [
            Term(name="Fall 2025", start_date=date(2025, 8, 25), end_date=date(2025, 12, 15)),
            Term(name="Spring 2026", start_date=date(2026, 1, 15), end_date=date(2026, 5, 15)),
        ]

        for term in terms:
            db.add(term)

        db.flush()

        # Sample instructors
        instructors = [
            Instructor(first_name="John", last_name="Smith", email="jsmith@umgc.edu"),
            Instructor(first_name="Jane", last_name="Doe", email="jdoe@umgc.edu"),
            Instructor(first_name="Bob", last_name="Johnson", email="bjohnson@umgc.edu"),
        ]

        for instructor in instructors:
            db.add(instructor)

        db.flush()

        # Sample classrooms
        classrooms = [
            Classroom(building="Academic Building", room_number="101", capacity=30),
            Classroom(building="Academic Building", room_number="102", capacity=25),
            Classroom(building="Science Building", room_number="201", capacity=40),
        ]

        for classroom in classrooms:
            db.add(classroom)

        db.flush()

        # Sample courses
        courses = [
            Course(department_id=1, course_number="101", title="Introduction to Programming",
                   description="Basic programming concepts", credits=3.0),
            Course(department_id=1, course_number="495", title="Capstone Project",
                   description="Senior capstone project", credits=3.0),
            Course(department_id=2, course_number="101", title="College Algebra",
                   description="Basic algebra concepts", credits=3.0),
        ]

        for course in courses:
            db.add(course)

        db.flush()

        # Sample sections
        sections = [
            Section(course_id=1, term_id=1, section_number="001", instructor_id=1, capacity=30),
            Section(course_id=2, term_id=1, section_number="001", instructor_id=2, capacity=25),
            Section(course_id=3, term_id=1, section_number="001", instructor_id=3, capacity=40),
        ]

        for section in sections:
            db.add(section)

        db.flush()

        # Sample meetings
        meetings = [
            Meeting(section_id=1, day_of_week=1, start_time=time(9, 0), end_time=time(10, 30), classroom_id=1),
            Meeting(section_id=1, day_of_week=3, start_time=time(9, 0), end_time=time(10, 30), classroom_id=1),
            Meeting(section_id=2, day_of_week=2, start_time=time(14, 0), end_time=time(15, 30), classroom_id=2),
            Meeting(section_id=3, day_of_week=1, start_time=time(11, 0), end_time=time(12, 30), classroom_id=3),
        ]

        for meeting in meetings:
            db.add(meeting)

        db.commit()
        db.close()

        print("✅ Sample data inserted successfully!")
        return True

    except Exception as e:
        print(f"❌ Error inserting sample data: {e}")
        if 'db' in locals():
            db.rollback()
            db.close()
        return False


def main():
    """Main setup function"""

    print("=" * 60)
    print("🎓 UMGC Course Registration System - Database Setup")
    print("=" * 60)
    print("CMSC 495 Capstone Project - Group Echo")
    print()

    # Step 1: Create database
    if not create_database():
        print("\n❌ Database setup failed!")
        sys.exit(1)

    # Step 2: Create tables
    if not create_tables():
        print("\n❌ Table creation failed!")
        sys.exit(1)

    # Step 3: Test connection
    if not test_connection():
        print("\n❌ Connection test failed!")
        sys.exit(1)

    # Step 4: Insert sample data
    print("\n" + "=" * 40)
    response = input("📊 Would you like to insert sample data? (y/n): ").lower().strip()

    if response in ['y', 'yes']:
        if not insert_sample_data():
            print("\n⚠️  Sample data insertion failed, but database is ready!")
    else:
        print("ℹ️  Skipping sample data insertion")

    print("\n" + "=" * 60)
    print("🎉 Database setup completed successfully!")
    print("\n📋 Next steps:")
    print("   1. Run: python database.py (to test connection)")
    print("   2. Run: python run_server.py (to start the server)")
    print("   3. Visit: http://localhost:8000/static/index.html")
    print("=" * 60)


if __name__ == "__main__":
    main()