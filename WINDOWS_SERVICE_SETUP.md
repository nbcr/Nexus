# Windows Service Setup for Nexus

## Prerequisites
- PowerShell running as **Administrator**
- Python installed with virtualenv in `C:\Nexus\venv`

## Installation Steps

### 1. Install the Service (Admin Required)

Open **PowerShell as Administrator** and run:

```powershell
cd C:\Nexus
C:\Nexus\venv\Scripts\python.exe nexus_service.py install
```

This creates a Windows Service named "Nexus" that:
- Starts automatically on boot
- Restarts automatically if it crashes
- Logs all output to `C:\Nexus\logs\service.log`

### 2. Start the Service

Either through Services.msc:
- Press `Win+R`, type `services.msc`
- Find "Nexus" in the list
- Right-click → Start

Or via PowerShell:
```powershell
C:\Nexus\venv\Scripts\python.exe nexus_service.py start
```

### 3. Check Status & Logs

**Service logs:**
```powershell
Get-Content C:\Nexus\logs\service.log -Tail 50
```

**Server logs:**
```powershell
Get-Content C:\Nexus\server.log -Tail 50
```

**Test the API:**
```powershell
curl http://localhost:8000/api/v1/content/feed
```

### 4. Uninstall the Service (No Reboot Required)

**Option 1: PowerShell (Recommended)**
```powershell
# Run as Administrator
powershell -ExecutionPolicy Bypass -File C:\Nexus\uninstall-service.ps1
```

**Option 2: Batch File**
```cmd
# Run as Administrator
C:\Nexus\uninstall-service.bat
```

**Option 3: Manual Command**
```powershell
# Run as Administrator
sc.exe delete Nexus
```

All options remove the service immediately with no reboot needed.

## Troubleshooting

### Service won't start
1. Check `C:\Nexus\logs\service.log` for errors
2. Ensure Python is installed: `"C:\Program Files\Python312\python.exe" --version`
3. Verify port 8000 is not in use: `netstat -ano | findstr :8000`

### Feed is stuck loading
1. Verify service is running: `Get-Service Nexus`
2. Check if API is accessible: `curl http://localhost:8000/`
3. Review logs for import or database errors

### Reinstall service
```powershell
# Stop and remove old service
C:\Nexus\venv\Scripts\python.exe nexus_service.py remove

# Reinstall fresh
C:\Nexus\venv\Scripts\python.exe nexus_service.py install
C:\Nexus\venv\Scripts\python.exe nexus_service.py start
```

## Running Without Service (Development)

For testing without admin privileges:

```powershell
cd C:\Nexus
C:\Nexus\venv\Scripts\python.exe run_server.py
```

This starts the server directly without Windows Service wrapping.
