from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "OpenVPN Access Manager"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    secret_key: str = "change-me"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 720
    internal_api_key: str = "change-internal-key"
    admin_username: str = "admin"
    admin_password: str = "admin123"

    database_url: str = f"sqlite:///{BASE_DIR / 'data' / 'app.db'}"
    data_dir: Path = BASE_DIR / "data"
    frontend_dir: Path = BASE_DIR / "frontend"

    openvpn_base_dir: Path = Path("/etc/openvpn")
    ccd_dir: Path = Path("/etc/openvpn/ccd")
    easy_rsa_dir: Path = Path("/etc/openvpn/easy-rsa")
    client_output_dir: Path = BASE_DIR / "data" / "clients"
    dnsmasq_config_path: Path = Path("/etc/dnsmasq.d/vpn-users.conf")
    dnsmasq_base_config_path: Path = BASE_DIR / "dnsmasq" / "vpn-access.conf"
    dnsmasq_log_path: Path = Path("/var/log/dnsmasq/queries.log")
    openvpn_status_path: Path = Path("/var/log/openvpn/status.log")
    openvpn_log_path: Path = Path("/var/log/openvpn/openvpn.log")

    vpn_subnet: str = "10.8.0.0/24"
    vpn_server_ip: str = "10.8.0.1"
    vpn_ip_start: int = 10
    vpn_ip_end: int = 250
    tun_interface: str = "tun0"
    wan_interface: str = "eth0"

    dry_run_system: bool = Field(default=True, description="Skip privileged system commands when true")


settings = Settings()

