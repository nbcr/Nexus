# Automated Deployment Setup

This project uses GitHub webhooks for automated deployments.

## Infrastructure:
- Webhook URL: `https://webhook.nexus.comdat.ca/webhook`
- Deployment user: `nexus`
- Systemd service: `nexus-webhook`
- Nginx proxy on port 5000

## How it works:
1. Push to main branch triggers GitHub webhook
2. Server verifies signature using WEBHOOK_SECRET
3. Server pulls latest changes
4. Installs new dependencies if needed
5. Restarts the application

## Files:
- `webhook_listener.py` - Flask app that handles webhooks
- `/etc/systemd/system/nexus-webhook.service` - Service definition
- Nginx config for webhook.nexus.comdat.ca
