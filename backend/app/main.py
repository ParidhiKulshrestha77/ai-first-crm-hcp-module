from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine
from app.config import get_settings
from app.routers import hcps, interactions, chat

settings = get_settings()

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="AI-First CRM — HCP Module API",
    description="Log Interaction Screen backend: FastAPI + LangGraph + Groq",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(hcps.router)
app.include_router(interactions.router)
app.include_router(chat.router)


@app.get("/api/health")
def health():
    return {"status": "ok", "environment": settings.environment}


@app.post("/api/dev/seed")
def seed_demo_data():
    """Convenience endpoint: creates a couple of demo HCPs for local testing."""
    from app.database import SessionLocal
    from app.models import HCP

    db = SessionLocal()
    try:
        if db.query(HCP).count() == 0:
            db.add_all([
                HCP(name="Dr. Anjali Mehra", specialty="Cardiology", institution="Fortis Hospital", tier="A"),
                HCP(name="Dr. Rohan Kapoor", specialty="Endocrinology", institution="Apollo Clinic", tier="B"),
            ])
            db.commit()
        return {"status": "seeded"}
    finally:
        db.close()
