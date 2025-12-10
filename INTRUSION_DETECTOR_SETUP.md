# Windows Intrusion Detection Setup

## Overview
This intrusion detector monitors access logs and blocks malicious IPs via Cloudflare, preventing attackers from consuming your internet bandwidth.

## Setup

### 1. Environment Variables
Set Cloudflare credentials in your system environment:
```powershell
# PowerShell (as Administrator)
[Environment]::SetEnvironmentVariable("CLOUDFLARE_API_KEY", "your-api-key-here", "User")
[Environment]::SetEnvironmentVariable("CLOUDFLARE_ZONE_ID", "your-zone-id-here", "User")
```

Or add to your `.env` file and load before running.

### 2. Configuration
Edit `config_ids.json`:
- `threshold`: Suspicious requests per minute before blocking (default: 10)
- `block_duration`: Block duration in seconds (default: 3600 = 1 hour)
- `whitelist`: List of IPs to never block (add your office/home IP)

### 3. Log File Path
Modify `intrusion_detector.py` or pass log path to `IntrusionDetector()`:

**For Nginx on Windows:**
```
C:\nginx\logs\access.log
```

**For IIS:**
```
C:\inetpub\logs\LogFiles\W3SVC1\access.log
```

**For FastAPI/Uvicorn with file logging:**
```
C:\Nexus\logs\access.log
```

### 4. Running the Detector

**Standalone:**
```powershell
python intrusion_detector.py
```

**As a Windows Service (using NSSM):**
```powershell
# Install NSSM if not already installed
# Download from: https://nssm.cc/

# Create service
nssm install NexusIDS "C:\Nexus\venv\Scripts\python.exe" "C:\Nexus\intrusion_detector.py"

# Start service
nssm start NexusIDS

# View logs
nssm edit NexusIDS
```

**As a Scheduled Task:**
```powershell
# Create task that runs on startup
$action = New-ScheduledTaskAction -Execute "C:\Nexus\venv\Scripts\python.exe" -Argument "C:\Nexus\intrusion_detector.py"
$trigger = New-ScheduledTaskTrigger -AtStartup
Register-ScheduledTask -Action $action -Trigger $trigger -TaskName "NexusIDS" -RunLevel Highest
```

## How It Works

1. **Monitors access logs** - Watches your web server log file for new entries
2. **Detects attacks** - Matches patterns for:
   - Directory traversal (`../..`)
   - Admin panel probes (`/wp-admin`, `/phpmyadmin`)
   - SQL injection attempts
   - XSS payloads
   - Code execution attempts
   - Brute force (30+ requests/minute)
3. **Blocks via Cloudflare** - When threshold is exceeded, blocks IP at edge (prevents bandwidth waste)
4. **Auto-unblocks** - Removes Cloudflare rules when block duration expires

## Database
SQLite database `intrusion_data.db` stores:
- Suspicious IPs and their request counts
- Attack logs with details (timestamp, URL, attack type, severity)
- Cloudflare rule IDs for easy unblocking

## Logging
Logs to both console and `intrusion_detector.log`:
```
2024-12-10 10:15:22 - INFO - [INFO] Starting intrusion detection on C:\logs\access.log
2024-12-10 10:15:45 - WARNING - [ALERT] SQL Injection from 192.168.1.100 - /api/users?id=1 OR 1=1
2024-12-10 10:15:46 - INFO - [BLOCKED] IP 192.168.1.100 blocked until 2024-12-10 11:15:46
2024-12-10 10:15:47 - INFO - [CLOUDFLARE] IP 192.168.1.100 blocked successfully (Rule ID: abc123)
```

## Manual IP Management
```python
from intrusion_detector import IntrusionDetector

detector = IntrusionDetector('C:\\logs\\access.log')

# Manually block an IP immediately
detector.block_ip('192.168.1.100')

# Manually unblock (if stored in DB)
detector.unblock_ip('192.168.1.100')
```

## Security Notes
- Never commit Cloudflare credentials to git
- Whitelist your own IPs to avoid self-blocking
- Review `intrusion_data.db` periodically for false positives
- Test with a low threshold first (1-2 requests) to verify it works
