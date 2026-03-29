from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.auth import get_current_admin
from backend.database import get_db
from backend.models import ConnectionSession, DnsLog
from backend.schemas import ConnectionSessionResponse, DnsLogResponse


router = APIRouter(prefix="/logs", tags=["logs"], dependencies=[Depends(get_current_admin)])


@router.get("/dns", response_model=list[DnsLogResponse])
def list_dns_logs(
    user_id: int | None = None,
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    query = db.query(DnsLog)
    if user_id is not None:
        query = query.filter(DnsLog.user_id == user_id)
    return query.order_by(DnsLog.queried_at.desc()).limit(limit).all()


@router.get("/connections", response_model=list[ConnectionSessionResponse])
def list_connection_logs(
    user_id: int | None = None,
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    query = db.query(ConnectionSession)
    if user_id is not None:
        query = query.filter(ConnectionSession.user_id == user_id)
    return query.order_by(ConnectionSession.connected_at.desc()).limit(limit).all()

