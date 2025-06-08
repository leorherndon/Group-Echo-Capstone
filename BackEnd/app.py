from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from database import SessionLocal, engine
from models import Base
import auth
import courses
import registration


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully!")
    yield
    # Shutdown
    print("Application shutting down...")


# Create FastAPI app with lifespan
app = FastAPI(
    title="Online Course Registration System",
    description="A web-based course registration system for students",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:8080",
        "http://127.0.0.1:8080",
        "http://localhost:5500",  # Live Server default port
        "http://127.0.0.1:5500"   # Live Server default port
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files (for frontend)
app.mount("/static", StaticFiles(directory="../frontend"), name="static")

# Dependency to get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(courses.router, prefix="/api/courses", tags=["Courses"])
app.include_router(registration.router, prefix="/api/registration", tags=["Registration"])

# Root endpoint
@app.get("/")
def read_root():
    return {
        "message": "Online Course Registration System API",
        "version": "1.0.0",
        "status": "active",
        "docs": "/docs",
        "frontend": "/static/index.html"
    }

# Health check endpoint
@app.get("/health")
def health_check():
    return {"status": "healthy"}

# API info endpoint
@app.get("/api")
def api_info():
    return {
        "message": "Online Course Registration API",
        "version": "1.0.0",
        "endpoints": {
            "auth": "/api/auth",
            "courses": "/api/courses",
            "registration": "/api/registration"
        }
    }


if __name__ == "__main__":
    import uvicorn
    print("Starting UMGC Course Registration System...")
    print("Frontend available at: http://localhost:8000/static/index.html")
    print("API documentation at: http://localhost:8000/docs")
    uvicorn.run(
        "app:app",  # Use import string format
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )