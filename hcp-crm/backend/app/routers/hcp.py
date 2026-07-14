from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db

router = APIRouter(prefix="/api/hcps", tags=["hcps"])


@router.get("", response_model=list[schemas.HCPOut])
def list_hcps(search: str | None = None, db: Session = Depends(get_db)):
    q = db.query(models.HCP)
    if search:
        q = q.filter(models.HCP.name.ilike(f"%{search}%"))
    return q.limit(20).all()


@router.post("", response_model=schemas.HCPOut)
def create_hcp(payload: schemas.HCPBase, db: Session = Depends(get_db)):
    hcp = models.HCP(**payload.model_dump())
    db.add(hcp)
    db.commit()
    db.refresh(hcp)
    return hcp
