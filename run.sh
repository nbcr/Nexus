#!/bin/bash

# Nexus API startup script
cd /home/admin/nexus

# Activate virtual environment
source venv/bin/activate

# Create logs directory if it doesn't exist
/bin/mkdir -p logs

# Start Gunicorn with configuration
exec gunicorn -c gunicorn_conf.py app.main:app
