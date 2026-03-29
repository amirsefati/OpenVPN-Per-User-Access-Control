from ipaddress import IPv4Address
from pathlib import Path

from backend.config import settings
from backend.services.system import run_command


def _next_vpn_ip(taken_ips: set[str]) -> str:
    base = "10.8.0."
    for suffix in range(settings.vpn_ip_start, settings.vpn_ip_end + 1):
        candidate = f"{base}{suffix}"
        if candidate not in taken_ips:
            return candidate
    raise ValueError("No available VPN IPs left in configured range")


def allocate_vpn_ip(taken_ips: set[str]) -> str:
    ip = _next_vpn_ip(taken_ips)
    IPv4Address(ip)
    return ip


def write_ccd(username: str, vpn_ip: str) -> Path:
    settings.ccd_dir.mkdir(parents=True, exist_ok=True)
    ccd_path = settings.ccd_dir / username
    ccd_path.write_text(f"ifconfig-push {vpn_ip} 255.255.255.0\n", encoding="utf-8")
    return ccd_path


def create_user(username: str, vpn_ip: str) -> None:
    settings.client_output_dir.mkdir(parents=True, exist_ok=True)
    write_ccd(username, vpn_ip)
    run_command(
        [str(settings.easy_rsa_dir / "easyrsa"), "build-client-full", username, "nopass"],
        cwd=settings.easy_rsa_dir,
        env={"EASYRSA_BATCH": "1"},
    )


def revoke_user(username: str) -> None:
    run_command(
        [str(settings.easy_rsa_dir / "easyrsa"), "--batch", "revoke", username],
        cwd=settings.easy_rsa_dir,
        env={"EASYRSA_BATCH": "1"},
    )
    run_command(
        [str(settings.easy_rsa_dir / "easyrsa"), "gen-crl"],
        cwd=settings.easy_rsa_dir,
        env={"EASYRSA_BATCH": "1"},
    )


def remove_ccd(username: str) -> None:
    ccd_path = settings.ccd_dir / username
    if ccd_path.exists():
        ccd_path.unlink()


def _read_required(path: Path, label: str) -> str:
    if not path.exists():
        raise FileNotFoundError(f"Missing {label}: {path}")
    return path.read_text(encoding="utf-8").strip()


def generate_ovpn(username: str) -> str:
    pki_dir = settings.easy_rsa_dir / "pki"
    ca = _read_required(pki_dir / "ca.crt", "CA certificate")
    cert = _read_required(pki_dir / "issued" / f"{username}.crt", "client certificate")
    key = _read_required(pki_dir / "private" / f"{username}.key", "client key")
    tls_auth = _read_required(settings.openvpn_base_dir / "ta.key", "tls-auth key")

    return f"""client
dev tun
proto udp
remote YOUR_SERVER_IP 1194
nobind
persist-key
persist-tun
remote-cert-tls server
verb 3
auth SHA256
cipher AES-256-GCM
key-direction 1

<ca>
{ca}
</ca>
<cert>
{cert}
</cert>
<key>
{key}
</key>
<tls-auth>
{tls_auth}
</tls-auth>
"""
