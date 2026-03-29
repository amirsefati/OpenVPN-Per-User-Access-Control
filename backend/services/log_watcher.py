import asyncio
import logging
import re
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.config import settings
from backend.database import SessionLocal
from backend.models import DnsLog, VpnUser


logger = logging.getLogger(__name__)
DNS_QUERY_PATTERN = re.compile(r"query\[[A-Z]+\]\s+(?P<domain>\S+)\s+from\s+(?P<ip>\d+\.\d+\.\d+\.\d+)")
DNS_REPLY_PATTERN = re.compile(r"reply\s+(?P<domain>\S+)\s+is\s+(?P<resolved_ip>\d+\.\d+\.\d+\.\d+)")


class LogWatcher:
    def __init__(self) -> None:
        self._task: asyncio.Task | None = None
        self._running = False
        self._last_domain_by_ip: dict[str, str] = {}

    async def start(self) -> None:
        self._running = True
        self._task = asyncio.create_task(self._run())

    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

    async def _run(self) -> None:
        while self._running:
            try:
                await self._poll_dns_log()
            except Exception:
                logger.exception("Failed while polling dnsmasq log")
            await asyncio.sleep(2)

    async def _poll_dns_log(self) -> None:
        path = settings.dnsmasq_log_path
        if not path.exists():
            return

        state_path = settings.data_dir / ".dnsmasq.offset"
        offset = int(state_path.read_text(encoding="utf-8").strip()) if state_path.exists() else 0
        size = path.stat().st_size
        if offset > size:
            offset = 0

        with path.open("r", encoding="utf-8", errors="ignore") as handle:
            handle.seek(offset)
            for line in handle:
                self._handle_dns_line(line.rstrip())
            state_path.parent.mkdir(parents=True, exist_ok=True)
            state_path.write_text(str(handle.tell()), encoding="utf-8")

    def _handle_dns_line(self, line: str) -> None:
        query_match = DNS_QUERY_PATTERN.search(line)
        if query_match:
            self._last_domain_by_ip[query_match.group("ip")] = query_match.group("domain")
            self._insert_dns_log(query_match.group("ip"), query_match.group("domain"), None)
            return

        reply_match = DNS_REPLY_PATTERN.search(line)
        if reply_match:
            domain = reply_match.group("domain")
            resolved_ip = reply_match.group("resolved_ip")
            self._update_last_dns_log(domain, resolved_ip)

    def _insert_dns_log(self, vpn_ip: str, domain: str, resolved_ip: str | None) -> None:
        with SessionLocal() as db:
            user = db.execute(select(VpnUser).where(VpnUser.vpn_ip == vpn_ip)).scalar_one_or_none()
            log = DnsLog(
                user_id=user.id if user else None,
                domain=domain,
                queried_at=datetime.utcnow(),
                resolved_ip=resolved_ip,
            )
            db.add(log)
            db.commit()

    def _update_last_dns_log(self, domain: str, resolved_ip: str) -> None:
        with SessionLocal() as db:
            entry = (
                db.query(DnsLog)
                .filter(DnsLog.domain == domain, DnsLog.resolved_ip.is_(None))
                .order_by(DnsLog.queried_at.desc())
                .first()
            )
            if entry:
                entry.resolved_ip = resolved_ip
                db.commit()

