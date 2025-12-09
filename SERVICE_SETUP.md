# Nexus Windows Service Setup

The Nexus FastAPI server can run as a Windows service that automatically starts on boot and restarts if it crashes.

## Installation

### Method 1: Batch File (Easiest - Auto-Elevates)

1. Double-click `Fix-NexusService-Admin.bat` 
   - It will automatically request Administrator privileges
   - Will clean up any corrupted service and install fresh
   - Click **Yes** when prompted for admin access

### Method 2: PowerShell (Requires Admin)

1. **Right-click PowerShell** → Select "Run as Administrator"
2. Run:
   ```powershell
   cd C:\Nexus
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
   .\Fix-NexusService-Admin.ps1
   ```

### Method 3: Command Prompt (Requires Admin)

1. **Right-click Command Prompt** → Select "Run as Administrator"
2. Run:
   ```cmd
   cd C:\Nexus
   C:\Nexus\venv\Scripts\python.exe nexus_service.py install
   ```

## Service Management

### Easiest: Services GUI

1. Press `Win + R`, type `services.msc`, press Enter
2. Find "Nexus AI News Platform"
3. Right-click and select:
   - **Properties** → Set "Startup type" to "Automatic" → Click OK
   - **Start** to start the service

### PowerShell Method (Requires Admin)

```powershell
cd C:\Nexus

# Set to auto-start
Set-Service -Name NexusServer -StartupType Automatic

# Start the service
Start-Service -Name NexusServer

# Check service status
Get-Service -Name NexusServer

# Stop the service
Stop-Service -Name NexusServer

# Restart the service
Restart-Service -Name NexusServer

# View logs
Get-Content C:\Nexus\logs\service.log -Tail 50
```

### Command Prompt Method (Requires Admin)

```cmd
cd C:\Nexus

# Set to auto-start
sc config NexusServer start=auto

# Start the service
net start NexusServer

# Stop the service
net stop NexusServer

# View service status
sc query NexusServer
```

### Legacy PowerShell Method

```powershell
cd C:\Nexus

# Check service status
.\Manage-NexusService.ps1 -Command status

# Start the service
.\Manage-NexusService.ps1 -Command start

# Stop the service
.\Manage-NexusService.ps1 -Command stop

# Restart the service
.\Manage-NexusService.ps1 -Command restart

# Uninstall the service
.\Manage-NexusService.ps1 -Command remove
```

## Service Features

- **Auto-start on boot**: When set to "Automatic" startup type
- **Auto-restart on crash**: If the server crashes, it automatically restarts (with crash-loop protection)
- **Logging**: Service logs are written to `C:\Nexus\logs\service.log`
- **2 worker processes**: Configured for better performance and reliability
- **Port**: Listens on `http://127.0.0.1:8000`

## Monitoring

Check service logs:
```powershell
Get-Content C:\Nexus\logs\service.log -Tail 50 -Wait
```

Or in Command Prompt:
```cmd
type C:\Nexus\logs\service.log
```

## Troubleshooting

**Service won't start**
- Check logs: `Get-Content C:\Nexus\logs\service.log -Tail 50`
- Verify port 8000 is free: `netstat -aon | findstr 8000`
- Verify PostgreSQL is running: `Get-Service postgresql*`

**Service installation fails with "marked for deletion" error**
- This happens when a previous service installation/removal was interrupted
- **Solution:**
  1. Run `Fix-Service-Final.bat` in admin (will prompt to restart)
  2. Choose option 1 to restart and auto-fix
  3. OR manually restart Windows, then run `Fix-NexusService-Admin.bat`
- The system cannot fully delete the service until after restart
- Do not try to force-delete while the error persists

**Access Denied errors**
- Right-click PowerShell/CMD and select "Run as Administrator"
- Ensure you have admin privileges

**Service keeps restarting**
- Check logs for the actual error
- Verify PostgreSQL is running: `Get-Service postgresql*`
- Verify dependencies: `pip list | findstr fastapi sqlalchemy psycopg`
- Check that `app/static` and `app/templates` directories exist

## Removal

To uninstall the service:

### PowerShell (Requires Admin)
```powershell
Stop-Service -Name "NexusServer"
Remove-Service -Name "NexusServer"
```

### Command Prompt (Requires Admin)
```cmd
net stop NexusServer
sc delete NexusServer
```

### GUI
1. Open Services.msc
2. Find "Nexus AI News Platform"
3. Right-click → Delete
