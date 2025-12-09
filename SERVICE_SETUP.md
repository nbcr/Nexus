# Nexus Windows Service Setup

The Nexus FastAPI server can run as a Windows service that automatically starts on boot and restarts if it crashes.

## Installation

### Method 1: PowerShell (Recommended)

1. Open PowerShell **as Administrator**
2. Run:
   ```powershell
   cd C:\Nexus
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
   .\Manage-NexusService.ps1 -Command install
   ```

### Method 2: Command Prompt

1. Open Command Prompt **as Administrator**
2. Run:
   ```cmd
   cd C:\Nexus
   C:\Nexus\venv\Scripts\python.exe nexus_service.py install
   ```

## Service Management

### PowerShell Method (Recommended)

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

### Command Line Method

```cmd
cd C:\Nexus

# Start the service
C:\Nexus\venv\Scripts\python.exe nexus_service.py start

# Stop the service
C:\Nexus\venv\Scripts\python.exe nexus_service.py stop
```

### Windows Services GUI

1. Open `Services.msc` (search for "Services" in Windows)
2. Find "Nexus AI News Platform" in the list
3. Right-click and select:
   - **Start** to start the service
   - **Stop** to stop the service
   - **Restart** to restart the service
   - **Properties** to configure startup behavior

To set automatic startup:
1. Open Services.msc
2. Find "Nexus AI News Platform"
3. Right-click → Properties
4. Set "Startup type" to "Automatic"
5. Click OK

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
- Check `C:\Nexus\logs\service.log` for error messages
- Ensure port 8000 is not in use: `netstat -aon | findstr 8000`
- Verify PostgreSQL is running: `Get-Service postgresql*`

**Access Denied during installation**
- Right-click PowerShell/CMD and select "Run as Administrator"
- Ensure you have admin privileges on the machine

**Service keeps restarting**
- Check logs for the actual error
- Verify all dependencies (PostgreSQL, Python packages) are installed
- Check that `app/static` and `app/templates` directories exist

## Removal

To uninstall the service:

```powershell
cd C:\Nexus
.\Manage-NexusService.ps1 -Command remove
```

Or:
```cmd
cd C:\Nexus
C:\Nexus\venv\Scripts\python.exe nexus_service.py remove
```
