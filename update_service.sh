#!/bin/bash
# Update systemd service to include DATABASE_URL from .env file

echo "Reading DATABASE_URL from .env file..."
if [ -f .env ]; then
    source .env
    echo "Found DATABASE_URL in .env"
else
    echo "ERROR: No .env file found!"
    exit 1
fi

# Make sure it has the asyncpg driver
if [[ "$DATABASE_URL" != *"+asyncpg"* ]]; then
    echo "ERROR: DATABASE_URL must use asyncpg driver (postgresql+asyncpg://...)"
    echo "Current: $DATABASE_URL"
    exit 1
fi

echo "Creating updated service file..."
sudo tee /etc/systemd/system/nexus.service > /dev/null << EOF
[Unit]
Description=Nexus API Service
After=network.target

[Service]
Type=simple
User=admin
Group=admin
WorkingDirectory=/home/admin/nexus
Environment="PATH=/home/admin/nexus/venv/bin"
Environment="DATABASE_URL=$DATABASE_URL"
ExecStart=/home/admin/nexus/run.sh
Restart=always
RestartSec=10

# Logging
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

echo "✅ Service file updated"
echo "Reloading systemd..."
sudo systemctl daemon-reload

echo "Restarting service..."
sudo systemctl restart nexus.service

echo ""
echo "✅ Done! Check status with:"
echo "sudo systemctl status nexus.service"
