#!/usr/bin/env python3
"""
Simple database connection test for UMGC Course Registration System
"""

import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError
from dotenv import load_dotenv

def test_database():
    """Test database connection step by step"""

    print("🧪 Testing Database Connection")
    print("=" * 50)

    # Load environment variables
    load_dotenv()

    # Database credentials
    db_user = os.getenv("DB_USER", "postgres")
    db_password = os.getenv("DB_PASSWORD", "123456")
    db_host = os.getenv("DB_HOST", "localhost")
    db_port = os.getenv("DB_PORT", "5432")
    db_name = os.getenv("DB_NAME", "course_registration")

    print(f"📋 Connection Details:")
    print(f"   Host: {db_host}")
    print(f"   Port: {db_port}")
    print(f"   User: {db_user}")
    print(f"   Database: {db_name}")
    print()

    # Test 1: Connect to PostgreSQL server (without specific database)
    print("🔍 Step 1: Testing PostgreSQL server connection...")

    try:
        server_url = f"postgresql+psycopg2://{db_user}:{db_password}@{db_host}:{db_port}/postgres"
        engine = create_engine(server_url)

        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            print(f"✅ PostgreSQL server connected: {version.split(',')[0]}")
    except Exception as e:
        print(f"❌ PostgreSQL server connection failed: {e}")
        print("\n💡 Troubleshooting:")
        print("   - Make sure PostgreSQL is running")
        print("   - Check username and password")
        print("   - Verify PostgreSQL is listening on port 5432")
        return False

    # Test 2: Check if database exists
    print(f"\n🔍 Step 2: Checking if database '{db_name}' exists...")

    try:
        with engine.connect() as conn:
            result = conn.execute(text(
                "SELECT 1 FROM pg_database WHERE datname = :db_name"
            ), {"db_name": db_name})

            if result.fetchone():
                print(f"✅ Database '{db_name}' exists")
            else:
                print(f"⚠️  Database '{db_name}' does not exist")
                print(f"💡 Run: python setup_database.py to create it")
                return False
    except Exception as e:
        print(f"❌ Error checking database existence: {e}")
        return False

    # Test 3: Connect to specific database
    print(f"\n🔍 Step 3: Testing connection to '{db_name}' database...")

    try:
        db_url = f"postgresql+psycopg2://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
        db_engine = create_engine(db_url)

        with db_engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print(f"✅ Successfully connected to '{db_name}' database")
    except Exception as e:
        print(f"❌ Connection to '{db_name}' failed: {e}")
        return False

    # Test 4: Check tables
    print(f"\n🔍 Step 4: Checking database tables...")

    try:
        with db_engine.connect() as conn:
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """))

            tables = [row[0] for row in result.fetchall()]

            if tables:
                print(f"✅ Found {len(tables)} tables:")
                for table in tables:
                    print(f"   • {table}")
            else:
                print("⚠️  No tables found")
                print("💡 Run: python setup_database.py to create tables")
    except Exception as e:
        print(f"❌ Error checking tables: {e}")
        return False

    print(f"\n🎉 All database tests passed!")
    print(f"🚀 Ready to start the server with: python run_server.py")
    return True

if __name__ == "__main__":
    success = test_database()
    if not success:
        sys.exit(1)