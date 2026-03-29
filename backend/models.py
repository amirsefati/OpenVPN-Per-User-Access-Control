from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base


class VpnUser(Base):
    __tablename__ = "vpn_users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    vpn_ip: Mapped[str] = mapped_column(String(32), unique=True, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    bytes_rx_total: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    bytes_tx_total: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    domains: Mapped[list["AllowedDomain"]] = relationship(
        "AllowedDomain", back_populates="user", cascade="all, delete-orphan"
    )
    dns_logs: Mapped[list["DnsLog"]] = relationship("DnsLog", back_populates="user")
    sessions: Mapped[list["ConnectionSession"]] = relationship("ConnectionSession", back_populates="user")


class AllowedDomain(Base):
    __tablename__ = "allowed_domains"
    __table_args__ = (UniqueConstraint("user_id", "domain", name="uq_user_domain"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("vpn_users.id", ondelete="CASCADE"), nullable=False, index=True)
    domain: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    added_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    user: Mapped[VpnUser] = relationship("VpnUser", back_populates="domains")


class DnsLog(Base):
    __tablename__ = "dns_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("vpn_users.id"), nullable=True, index=True)
    domain: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    queried_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    resolved_ip: Mapped[str | None] = mapped_column(String(64), nullable=True)

    user: Mapped[VpnUser | None] = relationship("VpnUser", back_populates="dns_logs")


class ConnectionSession(Base):
    __tablename__ = "connection_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("vpn_users.id"), nullable=False, index=True)
    real_ip: Mapped[str | None] = mapped_column(String(64), nullable=True)
    connected_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    disconnected_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    bytes_rx: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    bytes_tx: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    user: Mapped[VpnUser] = relationship("VpnUser", back_populates="sessions")


class AdminConfig(Base):
    __tablename__ = "admin_config"

    key: Mapped[str] = mapped_column(String(128), primary_key=True)
    value: Mapped[str] = mapped_column(Text, nullable=False)

