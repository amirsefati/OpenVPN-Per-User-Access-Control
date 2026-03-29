import asyncio
from datetime import datetime

from fastapi import APIRouter, Depends, Header, HTTPException, WebSocket, WebSocketDisconnect, status
from sqlalchemy.orm import Session

from backend.auth import get_current_admin
from backend.config import settings
from backend.database import get_db
from backend.models import ConnectionSession, VpnUser
from backend.schemas import StatusResponse, UserResponse, VpnEventConnect, VpnEventDisconnect
from backend.state import online_connections, online_usernames


router = APIRouter(tags=["status"])


def _current_online(db: Session) -> list[UserResponse]:
    users = db.query(VpnUser).filter(VpnUser.username.in_(list(online_usernames))).all() if online_usernames else []
    return [
        UserResponse.model_validate(user, from_attributes=True).model_copy(update={"online": True})
        for user in users
    ]


async def broadcast_online_users(db: Session) -> None:
    payload = StatusResponse(online_users=_current_online(db)).model_dump(mode="json")
    stale = []
    for socket in online_connections:
        try:
            await socket.send_json(payload)
        except RuntimeError:
            stale.append(socket)
    for socket in stale:
        online_connections.discard(socket)


@router.get("/status/online", response_model=StatusResponse, dependencies=[Depends(get_current_admin)])
def get_online_status(db: Session = Depends(get_db)):
    return StatusResponse(online_users=_current_online(db))


@router.websocket("/ws/status")
async def ws_status(websocket: WebSocket):
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    await websocket.accept()
    online_connections.add(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        online_connections.discard(websocket)


def _verify_internal_key(internal_key: str | None) -> None:
    if internal_key != settings.internal_api_key:
        raise HTTPException(status_code=401, detail="Invalid internal key")


@router.post("/internal/vpn-event/connect")
async def vpn_connect_event(
    payload: VpnEventConnect,
    db: Session = Depends(get_db),
    x_internal_key: str | None = Header(default=None),
):
    _verify_internal_key(x_internal_key)
    user = db.query(VpnUser).filter(VpnUser.username == payload.common_name).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    online_usernames.add(user.username)
    user.last_seen_at = payload.timestamp or datetime.utcnow()
    session = ConnectionSession(
        user_id=user.id,
        real_ip=payload.real_ip,
        connected_at=payload.timestamp or datetime.utcnow(),
    )
    db.add(session)
    db.commit()
    await broadcast_online_users(db)
    return {"status": "ok"}


@router.post("/internal/vpn-event/disconnect")
async def vpn_disconnect_event(
    payload: VpnEventDisconnect,
    db: Session = Depends(get_db),
    x_internal_key: str | None = Header(default=None),
):
    _verify_internal_key(x_internal_key)
    user = db.query(VpnUser).filter(VpnUser.username == payload.common_name).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    online_usernames.discard(user.username)
    session = (
        db.query(ConnectionSession)
        .filter(ConnectionSession.user_id == user.id, ConnectionSession.disconnected_at.is_(None))
        .order_by(ConnectionSession.connected_at.desc())
        .first()
    )
    if session:
        session.disconnected_at = payload.timestamp or datetime.utcnow()
        session.bytes_rx = payload.bytes_received
        session.bytes_tx = payload.bytes_sent
    user.bytes_rx_total += payload.bytes_received
    user.bytes_tx_total += payload.bytes_sent
    user.last_seen_at = payload.timestamp or datetime.utcnow()
    db.commit()
    await broadcast_online_users(db)
    return {"status": "ok"}

