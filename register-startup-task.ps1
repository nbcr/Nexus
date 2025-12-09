# Register Nexus startup task with Windows Task Scheduler
# Run this in PowerShell as Administrator

$taskName = "Nexus Services"
$scriptPath = "C:\Nexus\start-services.ps1"

# Check if task already exists
$taskExists = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue

if ($taskExists) {
    Write-Host "Task already exists. Removing old task..." -ForegroundColor Yellow
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
}

# Create trigger for system startup
$trigger = New-ScheduledTaskTrigger -AtStartup

# Create action
$action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$scriptPath`""

# Create task settings
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable

# Register the task to run as SYSTEM with highest privileges
$principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount -RunLevel Highest

Register-ScheduledTask -TaskName $taskName -Trigger $trigger -Action $action -Principal $principal -Settings $settings -Description "Automatically start PostgreSQL, FastAPI, and nginx on system startup"

Write-Host "Task registered successfully!" -ForegroundColor Green
Write-Host "The Nexus services will now start automatically when the computer boots."
