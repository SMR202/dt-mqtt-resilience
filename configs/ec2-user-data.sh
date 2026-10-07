#!/usr/bin/env bash
# Prepared EC2 Ubuntu bootstrap. Requires an authorized instance launch.
# No cloud resources are provisioned by this file.
set -euo pipefail
apt-get update
DEBIAN_FRONTEND=noninteractive apt-get install -y mosquitto python3-venv git
install -d -o ubuntu -g ubuntu /opt/dt-research
sudo -u ubuntu git clone --branch research/phase2-reproduction https://github.com/SMR202/dt-mqtt-resilience.git /opt/dt-research/repo
sudo -u ubuntu python3 -m venv /opt/dt-research/venv
sudo -u ubuntu /opt/dt-research/venv/bin/pip install paho-mqtt==2.1.0
install -m 644 /opt/dt-research/repo/configs/mosquitto-cloud.conf /etc/mosquitto/dt-research.conf
cat >/etc/systemd/system/dt-research-broker.service <<'EOF'
[Unit]
Description=Isolated localhost MQTT broker for DT research
After=network-online.target
[Service]
ExecStart=/usr/sbin/mosquitto -c /etc/mosquitto/dt-research.conf
User=mosquitto
Restart=on-failure
NoNewPrivileges=true
[Install]
WantedBy=multi-user.target
EOF
systemctl daemon-reload
systemctl enable --now dt-research-broker
