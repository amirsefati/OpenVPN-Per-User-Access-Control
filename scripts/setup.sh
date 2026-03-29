#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="$PROJECT_DIR/.venv"
APP_USER="${APP_USER:-root}"
APP_GROUP="${APP_GROUP:-root}"

export DEBIAN_FRONTEND=noninteractive

apt-get update
apt-get install -y \
  python3 python3-venv python3-pip \
  openvpn easy-rsa ipset iptables-persistent dnsmasq curl

mkdir -p /etc/openvpn/ccd /var/log/openvpn /var/log/dnsmasq
mkdir -p /etc/openvpn/server
touch /var/log/openvpn/status.log /var/log/openvpn/openvpn.log /var/log/dnsmasq/queries.log

if ! grep -q '^net.ipv4.ip_forward=1' /etc/sysctl.conf; then
  echo 'net.ipv4.ip_forward=1' >> /etc/sysctl.conf
fi
sysctl -p

cp "$PROJECT_DIR/dnsmasq/vpn-access.conf" /etc/dnsmasq.d/vpn-access.conf
systemctl enable dnsmasq

if [ ! -d /etc/openvpn/easy-rsa/pki ]; then
  make-cadir /etc/openvpn/easy-rsa
  cd /etc/openvpn/easy-rsa
  ./easyrsa init-pki
  EASYRSA_BATCH=1 ./easyrsa build-ca nopass
  EASYRSA_BATCH=1 ./easyrsa build-server-full server nopass
  openvpn --genkey secret /etc/openvpn/ta.key
fi

install -d -m 0755 "$VENV_DIR"
python3 -m venv "$VENV_DIR"
"$VENV_DIR/bin/pip" install --upgrade pip
"$VENV_DIR/bin/pip" install -r "$PROJECT_DIR/backend/requirements.txt"

cp "$PROJECT_DIR/openvpn/server.conf.template" /etc/openvpn/server/server.conf
cp "$PROJECT_DIR/scripts/openvpn-connect.sh" /usr/local/bin/openvpn-connect.sh
cp "$PROJECT_DIR/scripts/openvpn-disconnect.sh" /usr/local/bin/openvpn-disconnect.sh
chmod +x /usr/local/bin/openvpn-connect.sh /usr/local/bin/openvpn-disconnect.sh

cp "$PROJECT_DIR/systemd/vpn-manager.service" /etc/systemd/system/vpn-manager.service
sed -i "s|__PROJECT_DIR__|$PROJECT_DIR|g" /etc/systemd/system/vpn-manager.service
sed -i "s|__APP_USER__|$APP_USER|g" /etc/systemd/system/vpn-manager.service
sed -i "s|__APP_GROUP__|$APP_GROUP|g" /etc/systemd/system/vpn-manager.service

systemctl daemon-reload
systemctl enable vpn-manager.service
systemctl restart vpn-manager.service
systemctl enable openvpn-server@server
systemctl restart openvpn-server@server
systemctl restart dnsmasq

iptables -P FORWARD DROP
iptables -C FORWARD -i tun0 ! -d 10.8.0.1 -p udp --dport 53 -j REJECT 2>/dev/null || iptables -A FORWARD -i tun0 ! -d 10.8.0.1 -p udp --dport 53 -j REJECT
iptables -C FORWARD -i tun0 ! -d 10.8.0.1 -p tcp --dport 53 -j REJECT 2>/dev/null || iptables -A FORWARD -i tun0 ! -d 10.8.0.1 -p tcp --dport 53 -j REJECT
iptables -t nat -C POSTROUTING -s 10.8.0.0/24 -o eth0 -j MASQUERADE 2>/dev/null || iptables -t nat -A POSTROUTING -s 10.8.0.0/24 -o eth0 -j MASQUERADE
iptables-save > /etc/iptables/rules.v4

echo "Setup complete. API/UI should be available on port 8000."
