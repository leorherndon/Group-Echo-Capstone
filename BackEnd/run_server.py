#!/usr/bin/env python3
"""
UMGC Course Registration System - Server Startup Script
Run this script to start the development server properly.
"""

import uvicorn
import sys
import os
from pathlib import Path

def main():
    print("=" * 60)
    print("🎓 UMGC Course Registration System")
    print("=" * 60)
    print("CMSC 495 Capstone Project - Group Echo")
    print()

    # Ensure we're in the right directory
    backend_dir = Path(__file__).parent
    os.chdir(backend_dir)

    print(f"📁 Working directory: {backend_dir}")
    print(f"🐍 Python version: {sys.version.split()[0]}")
    print()

    print("🚀 Starting server...")
    print("📊 API Documentation: http://localhost:8000/docs")
    print("🌐 Frontend: http://localhost:8000/static/index.html")
    print("❤️  Health Check: http://localhost:8000/health")
    print()
    print("Press Ctrl+C to stop the server")
    print("=" * 60)

    try:
        uvicorn.run(
            "app:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="info",
            reload_excludes=["*.pyc", "__pycache__"],
            access_log=True
        )
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except Exception as e:
        print(f"\n❌ Error starting server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()