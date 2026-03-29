from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class LoginRequest(BaseModel):
    username: str
    password: str


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=64, pattern=r"^[a-zA-Z0-9_.-]+$")


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    vpn_ip: str
    created_at: datetime
    last_seen_at: datetime | None
    is_active: bool
    bytes_rx_total: int
    bytes_tx_total: int
    online: bool = False


class UserDetail(UserResponse):
    domains: list[str] = []


class DomainCreate(BaseModel):
    domain: str = Field(min_length=1, max_length=255)


class DomainResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    domain: str
    added_at: datetime


class DnsLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int | None
    domain: str
    queried_at: datetime
    resolved_ip: str | None


class ConnectionSessionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    real_ip: str | None
    connected_at: datetime
    disconnected_at: datetime | None
    bytes_rx: int
    bytes_tx: int


class StatusResponse(BaseModel):
    online_users: list[UserResponse]


class VpnEventConnect(BaseModel):
    common_name: str
    real_ip: str | None = None
    vpn_ip: str | None = None
    timestamp: datetime | None = None


class VpnEventDisconnect(BaseModel):
    common_name: str
    bytes_received: int = 0
    bytes_sent: int = 0
    timestamp: datetime | None = None

