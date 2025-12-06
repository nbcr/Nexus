# Automated deployment with automatic cache busting
# Usage: .\scripts\deploy.ps1 [-EC2Host "host"] [-EC2User "user"] [-SSHKey "path"]

param(
    [string]$EC2Host = "ec2-35-172-220-70.compute-1.amazonaws.com",
    [string]$EC2User = "admin",
    [string]$SSHKey = "$env:USERPROFILE\.ssh\nexus_ec2.pem"
)

$ErrorActionPreference = "Stop"

Write-Host "🚀 Nexus Deployment Script" -ForegroundColor Cyan
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "🖥️  Target: $EC2User@$EC2Host" -ForegroundColor Yellow
Write-Host "📍 Path: /home/nexus/nexus" -ForegroundColor Yellow
Write-Host ""

# Step 1: Update cache busting locally
Write-Host "📦 Step 1/4: Updating cache busting versions..." -ForegroundColor Cyan
python scripts/update_cache_bust.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ Cache busting update failed" -ForegroundColor Red
    exit 1
}
Write-Host ""

# Step 2: Commit changes if any
Write-Host "💾 Step 2/4: Committing changes..." -ForegroundColor Cyan
$status = git status --porcelain
if ($status) {
    git add app/templates/
    git commit -m "Auto: Update cache busting versions" -ErrorAction Continue
    Write-Host "✓ Changes committed" -ForegroundColor Green
}
else {
    Write-Host "✓ No changes to commit" -ForegroundColor Green
}
Write-Host ""

# Step 3: Push to remote
Write-Host "⬆️  Step 3/4: Pushing to repository..." -ForegroundColor Cyan
git push origin main -ErrorAction Continue
Write-Host "✓ Pushed to remote" -ForegroundColor Green
Write-Host ""

# Step 4: Deploy to EC2
Write-Host "🌐 Step 4/4: Deploying to EC2..." -ForegroundColor Cyan
$deployScript = @'
set -e
cd /home/nexus/nexus
echo "  Pulling latest changes..."
sudo -u nexus git pull
echo "  Restarting service..."
sudo systemctl restart nexus
echo "  ✓ Service restarted"
sleep 2
if sudo systemctl is-active --quiet nexus; then
    echo "  ✅ Service is running"
else
    echo "  ⚠️  Service check failed"
    sudo systemctl status nexus || true
fi
'@

ssh -o StrictHostKeyChecking=accept-new -i $SSHKey "$EC2User@$EC2Host" $deployScript
if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ Deployment failed" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "✨ Deployment complete!" -ForegroundColor Green
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Green
Write-Host "🌍 Live at: https://comdat.ca" -ForegroundColor Green
