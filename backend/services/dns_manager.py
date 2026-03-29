from collections import defaultdict

from sqlalchemy.orm import Session

from backend.config import settings
from backend.models import AllowedDomain, VpnUser
from backend.services.firewall import ipset_name
from backend.services.system import run_command


def rebuild_dnsmasq_config(db: Session) -> None:
    domain_map: dict[str, list[str]] = defaultdict(list)
    rows = (
        db.query(AllowedDomain, VpnUser)
        .join(VpnUser, AllowedDomain.user_id == VpnUser.id)
        .filter(VpnUser.is_active.is_(True))
        .all()
    )
    for domain_entry, user in rows:
        domain_map[domain_entry.domain.lower()].append(ipset_name(user.username))

    lines = [
        "# Managed by OpenVPN Access Manager",
        *[
            f"ipset=/{domain}/" + ",".join(sorted(set(ipsets)))
            for domain, ipsets in sorted(domain_map.items())
        ],
        "",
    ]
    settings.dnsmasq_config_path.parent.mkdir(parents=True, exist_ok=True)
    settings.dnsmasq_config_path.write_text("\n".join(lines), encoding="utf-8")
    run_command(["systemctl", "reload", "dnsmasq"], check=False)

