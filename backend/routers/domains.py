from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from backend.auth import get_current_admin
from backend.database import get_db
from backend.models import AllowedDomain, VpnUser
from backend.schemas import DomainCreate, DomainResponse
from backend.services.dns_manager import rebuild_dnsmasq_config


router = APIRouter(prefix="/users/{user_id}/domains", tags=["domains"], dependencies=[Depends(get_current_admin)])


def _get_user_or_404(user_id: int, db: Session) -> VpnUser:
    user = db.query(VpnUser).filter(VpnUser.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.get("", response_model=list[DomainResponse])
def list_domains(user_id: int, db: Session = Depends(get_db)):
    _get_user_or_404(user_id, db)
    return db.query(AllowedDomain).filter(AllowedDomain.user_id == user_id).order_by(AllowedDomain.domain.asc()).all()


@router.post("", response_model=DomainResponse, status_code=status.HTTP_201_CREATED)
def add_domain(user_id: int, payload: DomainCreate, db: Session = Depends(get_db)):
    _get_user_or_404(user_id, db)
    domain = payload.domain.strip().lower()
    existing = (
        db.query(AllowedDomain)
        .filter(AllowedDomain.user_id == user_id, AllowedDomain.domain == domain)
        .first()
    )
    if existing:
        raise HTTPException(status_code=400, detail="Domain already exists")
    row = AllowedDomain(user_id=user_id, domain=domain)
    db.add(row)
    db.commit()
    db.refresh(row)
    rebuild_dnsmasq_config(db)
    return row


@router.delete("/{domain_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_domain(user_id: int, domain_id: int, db: Session = Depends(get_db)):
    _get_user_or_404(user_id, db)
    row = db.query(AllowedDomain).filter(AllowedDomain.user_id == user_id, AllowedDomain.id == domain_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Domain not found")
    db.delete(row)
    db.commit()
    rebuild_dnsmasq_config(db)
    return Response(status_code=status.HTTP_204_NO_CONTENT)

