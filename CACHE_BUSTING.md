# Automatic Cache Busting System

This system automatically detects changes in static files and updates cache busting version strings in templates.

## How It Works

1. **File Tracking**: `scripts/update_cache_bust.py` maintains MD5 hashes of all static files in `.cache_bust_hashes.json`
2. **Change Detection**: Compares current file hashes against stored hashes to detect changes
3. **Version Update**: When changes are detected, updates all template files with new version strings
4. **Zero Manual Work**: No need to manually update version strings anymore

## Usage

### Automatic (Recommended)

Use the deployment script which runs cache busting automatically:

**On Linux/Mac:**
```bash
./scripts/deploy.sh [ec2_host] [ec2_user]
./scripts/deploy.sh ec2-35-172-220-70.compute-1.amazonaws.com admin
```

**On Windows (PowerShell):**
```powershell
.\scripts\deploy.ps1 -EC2Host "ec2-35-172-220-70.compute-1.amazonaws.com" -EC2User "admin"
```

### Manual

Run the cache busting update manually:

```bash
python scripts/update_cache_bust.py
```

This will:
- Detect any changed files in `app/static/`
- Generate a new version string (YYYYMMDDHHMM format)
- Update all template files in `app/templates/` with the new version
- Save the current file hashes for next comparison

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

This file should be committed to git so the system works correctly across different machines.

## Notes

- **First Run**: First run will detect all files as "changed" and update all templates. This is normal.
- **Incremental Updates**: Subsequent runs only update files that actually changed
- **No Template Changes**: If static files haven't changed, templates are not modified
- **Automatic Commits**: The `deploy.ps1` and `deploy.sh` scripts automatically commit template changes

## Benefits

✅ **Zero Manual Work** - No need to manually update version strings  
✅ **Smart Detection** - Only updates when files actually change  
✅ **Consistent Versioning** - Uses timestamp-based versioning  
✅ **Cross-Platform** - Works on Windows, Mac, and Linux  
✅ **Git Integration** - Automatically commits changes  
✅ **Production Safe** - Thoroughly tested regex patterns  

## Troubleshooting

**"No changes detected"** - This is correct if no static files were modified

**"File not found" errors** - Ensure you're running from the project root

**Git lock file error** - Remove `.git/index.lock` manually and try again

**Template not updating** - Check that the file path in templates matches the static directory structure
