# Start Nexus Services
# Run as Administrator

Write-Host "Starting Nexus services..." -ForegroundColor Green

# Start PostgreSQL
Write-Host "Starting PostgreSQL..." -ForegroundColor Cyan
Start-Service postgresql-x64-18

# Wait for PostgreSQL to start
Start-Sleep -Seconds 3

# Start FastAPI server
Write-Host "Starting FastAPI server..." -ForegroundColor Cyan
cd C:\Nexus
Start-Process powershell -ArgumentList "-NoProfile -WindowStyle Hidden -Command `"cd C:\Nexus; python run_server.py`"" -PassThru | Out-Null

# Wait for FastAPI to start
Start-Sleep -Seconds 5

# Start nginx
Write-Host "Starting nginx..." -ForegroundColor Cyan
cd C:\Nexus
& "C:\ProgramData\chocolatey\lib\nginx\tools\nginx-1.29.3\nginx.exe" -c "C:\Nexus\nginx\local.conf"

Write-Host "All services started successfully!" -ForegroundColor Green
