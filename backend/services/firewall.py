import re

from backend.config import settings
from backend.services.system import run_command


def sanitize_username(username: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_-]", "_", username)


def ipset_name(username: str) -> str:
    return f"user_{sanitize_username(username)}_allowed"


def create_user_ipset(username: str) -> str:
    name = ipset_name(username)
    run_command(["ipset", "create", name, "hash:ip", "-exist"])
    return name


def add_forward_rule(username: str, vpn_ip: str) -> None:
    name = ipset_name(username)
    run_command(
        [
            "iptables",
            "-C",
            "FORWARD",
            "-s",
            vpn_ip,
            "-m",
            "set",
            "--match-set",
            name,
            "dst",
            "-j",
            "ACCEPT",
        ],
        check=False,
    )
    run_command(
        [
            "iptables",
            "-I",
            "FORWARD",
            "1",
            "-s",
            vpn_ip,
            "-m",
            "set",
            "--match-set",
            name,
            "dst",
            "-j",
            "ACCEPT",
        ]
    )


def delete_user_resources(username: str, vpn_ip: str) -> None:
    name = ipset_name(username)
    run_command(
        [
            "iptables",
            "-D",
            "FORWARD",
            "-s",
            vpn_ip,
            "-m",
            "set",
            "--match-set",
            name,
            "dst",
            "-j",
            "ACCEPT",
        ],
        check=False,
    )
    run_command(["ipset", "flush", name], check=False)
    run_command(["ipset", "destroy", name], check=False)


def ensure_base_rules() -> None:
    commands = [
        ["iptables", "-P", "FORWARD", "DROP"],
        [
            "iptables",
            "-C",
            "FORWARD",
            "-i",
            settings.tun_interface,
            "!",
            "-d",
            settings.vpn_server_ip,
            "-p",
            "udp",
            "--dport",
            "53",
            "-j",
            "REJECT",
        ],
        [
            "iptables",
            "-C",
            "FORWARD",
            "-i",
            settings.tun_interface,
            "!",
            "-d",
            settings.vpn_server_ip,
            "-p",
            "tcp",
            "--dport",
            "53",
            "-j",
            "REJECT",
        ],
    ]
    for command in commands:
        run_command(command, check=False)

