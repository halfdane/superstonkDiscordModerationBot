#/bin/bash
set -eu

ENVIRONMENT=$1
echo "Installing service file for [${ENVIRONMENT}]"

cat >/etc/systemd/system/superstonkModerationBot_${ENVIRONMENT}.service <<EOF
[Unit]
Description=The Superstonk Moderation Bot [${ENVIRONMENT}]
# never stop trying to restart
StartLimitIntervalSec=0
After=multi-user.target

[Service]
# Command to execute when the service is started
Type=simple
WorkingDirectory=/home/${ENVIRONMENT}/superstonkDiscordModerationBot
ExecStart=/usr/bin/make
Restart=always
RestartSec=1

[Install]
WantedBy=default.target
EOF

systemctl daemon-reload
systemctl enable superstonkModerationBot_${ENVIRONMENT}.service
systemctl start superstonkModerationBot_${ENVIRONMENT}.service
