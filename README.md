# OpenVPN Per-User Access Control

Self-contained Ubuntu 22.04 setup for:

- OpenVPN with static per-user IPs
- `iptables` + `ipset` allowlists
- `dnsmasq` domain-to-ipset population
- FastAPI backend with SQLite
- Static admin UI served by FastAPI

## Quick start

1. Copy the repo to the Ubuntu server.
2. Create an `.env` file in the project root:

```env
SECRET_KEY=replace-this
ADMIN_PASSWORD=replace-this
INTERNAL_API_KEY=replace-this
DRY_RUN_SYSTEM=false
```

3. Run:

```bash
sudo bash scripts/setup.sh
```

4. Open `http://SERVER_IP:8000/`

## Notes

- In local development, leave `DRY_RUN_SYSTEM=true` so OpenVPN, `iptables`, `ipset`, and `dnsmasq` commands are logged instead of executed.
- The generated client config uses `YOUR_SERVER_IP`; replace it or extend `generate_ovpn()` to inject the public hostname.
- The setup script assumes the WAN interface is `eth0`. Adjust if your server uses another name.
