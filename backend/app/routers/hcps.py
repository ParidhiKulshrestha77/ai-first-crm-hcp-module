from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas

router = APIRouter(prefix="/api/hcps", tags=["hcps"])


@router.get("", response_model=list[schemas.HCPOut])
def list_hcps(db: Session = Depends(get_db)):
    return db.query(models.HCP).order_by(models.HCP.name).all()


@router.post("", response_model=schemas.HCPOut, status_code=201)
def create_hcp(payload: schemas.HCPCreate, db: Session = Depends(get_db)):
    hcp = models.HCP(**payload.model_dump())
    db.add(hcp)
    db.commit()
    db.refresh(hcp)
    return hcp


@router.get("/{hcp_id}", response_model=schemas.HCPOut)
def get_hcp(hcp_id: str, db: Session = Depends(get_db)):
    hcp = db.get(models.HCP, hcp_id)
    if not hcp:
        raise HTTPException(404, "HCP not found")
    return hcp
