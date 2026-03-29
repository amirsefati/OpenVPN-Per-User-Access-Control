from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session, selectinload

from backend.auth import get_current_admin
from backend.database import get_db
from backend.models import AllowedDomain, VpnUser
from backend.schemas import UserCreate, UserDetail, UserResponse
from backend.services.dns_manager import rebuild_dnsmasq_config
from backend.services.firewall import add_forward_rule, create_user_ipset, delete_user_resources
from backend.services.openvpn import allocate_vpn_ip, create_user, generate_ovpn, remove_ccd, revoke_user
from backend.state import online_usernames


router = APIRouter(prefix="/users", tags=["users"], dependencies=[Depends(get_current_admin)])


@router.get("", response_model=list[UserResponse])
def list_users(db: Session = Depends(get_db)):
    users = db.query(VpnUser).order_by(VpnUser.created_at.desc()).all()
    return [
        UserResponse.model_validate(user, from_attributes=True).model_copy(update={"online": user.username in online_usernames})
        for user in users
    ]


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_vpn_user(payload: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(VpnUser).filter(VpnUser.username == payload.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username already exists")

    taken_ips = {row.vpn_ip for row in db.query(VpnUser.vpn_ip).all()}
    vpn_ip = allocate_vpn_ip(taken_ips)
    user = VpnUser(username=payload.username, vpn_ip=vpn_ip)
    db.add(user)
    db.commit()
    db.refresh(user)

    create_user(user.username, user.vpn_ip)
    create_user_ipset(user.username)
    add_forward_rule(user.username, user.vpn_ip)
    return UserResponse.model_validate(user, from_attributes=True)


@router.get("/{user_id}", response_model=UserDetail)
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = (
        db.query(VpnUser)
        .options(selectinload(VpnUser.domains))
        .filter(VpnUser.id == user_id)
        .first()
    )
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    detail = UserDetail.model_validate(user, from_attributes=True)
    detail.domains = [domain.domain for domain in user.domains]
    detail.online = user.username in online_usernames
    return detail


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(VpnUser).filter(VpnUser.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    revoke_user(user.username)
    delete_user_resources(user.username, user.vpn_ip)
    remove_ccd(user.username)
    user.is_active = False
    db.commit()
    rebuild_dnsmasq_config(db)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{user_id}/config")
def download_config(user_id: int, db: Session = Depends(get_db)):
    user = db.query(VpnUser).filter(VpnUser.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    content = generate_ovpn(user.username)
    headers = {"Content-Disposition": f'attachment; filename="{user.username}.ovpn"'}
    return Response(content=content, media_type="application/x-openvpn-profile", headers=headers)
