# Automatic Cache Busting System

This system automatically detects changes in static files and updates cache busting version strings in templates. It integrates with GitHub Actions for automatic deployment.

## How It Works

### File Tracking
`scripts/update_cache_bust.py` maintains MD5 hashes of all static files in `.cache_bust_hashes.json`

### Automatic GitHub Actions Integration
When you push to `main` branch:

1. **GitHub Actions Pre-Deploy Job** runs `scripts/update_cache_bust.py`
2. **Cache busting versions are updated** automatically in templates
3. **Changes are committed back** to the repository
4. **EC2 deployment job** runs and pulls the latest code

### Change Detection
- Compares current file hashes against stored hashes to detect changes
- Only updates version strings when files actually change
- Zero manual work needed

## Usage

### Automatic (Recommended - Always Use This)

Just push to main branch - GitHub Actions handles everything:

```bash
git add <your-changes>
git commit -m "Your commit message"
git push origin main
```

**What happens automatically:**
1. ✅ Cache busting script detects file changes
2. ✅ Version strings updated in all templates
3. ✅ Changes committed and pushed back to repo
4. ✅ Deploy job pulls latest and restarts service
5. ✅ Service health check confirms deployment

### Manual (Local Testing Only)

If you want to test locally before pushing:

```bash
# Update cache busting locally
python scripts/update_cache_bust.py

# Then commit and push
git add app/templates/
git commit -m "Auto: Update cache busting versions"
git push
```

## GitHub Actions Workflow

The workflow (`.github/workflows/deploy.yml`) has two jobs:

### Job 1: `pre-deploy` 
- Checks out code
- Runs cache busting update script
- Automatically commits template changes
- Pushes changes back to main

### Job 2: `deploy` (depends on pre-deploy)
- Waits for pre-deploy to complete
- Sets up SSH connection to EC2
- Pulls latest changes (including auto-updated templates)
- Restarts the Nexus service
- Verifies service is running

## Setup Required

### GitHub Secrets
Add these secrets to your GitHub repository settings:

1. **EC2_HOST** - Your EC2 instance hostname
   ```
   ec2-35-172-220-70.compute-1.amazonaws.com
   ```

2. **EC2_USER** - SSH user (usually `admin`)
   ```
   admin
   ```

3. **SSH_PRIVATE_KEY** - Your EC2 SSH private key (full contents)
   ```
   -----BEGIN OPENSSH PRIVATE KEY-----
   ... (full key contents)
   -----END OPENSSH PRIVATE KEY-----
   ```

### How to Add Secrets

1. Go to GitHub repository Settings
2. Click "Secrets and variables" → "Actions"
3. Click "New repository secret"
4. Add each secret with the name and value

## What Gets Updated

The system updates version strings for:
- **CSS Files**: All `.css` files in `app/static/css/`
- **JavaScript Files**: All `.js` files in `app/static/js/`
- **Templates**: All `.html` files in `app/templates/`

Example transformation:
```html
<!-- Before -->
<script src="/static/js/FeedApi.js?v=202512060200"></script>

<!-- After (if FeedApi.js changed) -->
<script src="/static/js/FeedApi.js?v=202512061545"></script>
```

## Version String Format

Version strings use format: `YYYYMMDDHHMM`
- `YYYY` = Year (2025)
- `MM` = Month (12)
- `DD` = Day (06)
- `HH` = Hour (15)
- `MM` = Minute (45)

Example: `202512061545` = Dec 6, 2025 at 3:45 PM

## Storage

Cache hashes are stored in `scripts/.cache_bust_hashes.json`
```json
{
  "css/feed.css": "a1b2c3d4",
  "css/base.css": "e5f6g7h8",
  "js/FeedApi.js": "i9j0k1l2"
}
```

This file should be committed to git so the system works correctly across different machines and CI/CD runs.

## Monitoring Deployments

### View GitHub Actions
1. Go to repository "Actions" tab
2. Click on latest workflow run
3. View pre-deploy and deploy job logs
4. See real-time deployment progress

### View EC2 Logs
SSH into EC2 and check:
```bash
sudo tail -100 /home/nexus/nexus/logs/error.log
sudo systemctl status nexus
```

## Notes

- **First Run**: First run will detect all files as "changed". This is normal.
- **Incremental Updates**: Subsequent runs only update files that changed
- **No Changes**: If static files haven't changed, templates are not modified
- **Automatic Everything**: No manual version string updates ever needed
- **Atomic Deployments**: All jobs run as one atomic transaction via GitHub Actions

## Benefits

✅ **Zero Manual Work** - Everything automatic on push  
✅ **Smart Detection** - Only updates when files change  
✅ **Consistent Versioning** - Timestamp-based versioning  
✅ **Cross-Platform** - Runs in GitHub's Ubuntu environment  
✅ **Git Integration** - Auto-commits changes  
✅ **Production Safe** - Thoroughly tested  
✅ **No Webhook Listener** - No long-running processes needed  
✅ **Full Logging** - View everything in GitHub Actions UI  

## Troubleshooting

**Workflow failing?**
- Check GitHub Actions tab for error logs
- Verify secrets are set correctly in repository settings
- Check EC2 SSH key is valid

**"No changes detected"** 
- This is correct if no static files were modified

**Service not restarting**
- SSH into EC2: `sudo systemctl status nexus`
- Check logs: `sudo tail -100 /home/nexus/nexus/logs/error.log`

**Template not updating**
- Verify file path matches between static and templates
- Check workflow logs in GitHub Actions
