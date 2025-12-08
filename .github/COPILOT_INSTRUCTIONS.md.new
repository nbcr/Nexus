
# Copilot Instructions for Nexus Project
# This file provides context and recent changes for GitHub Copilot or any automation agent working on this repository.

# Context
# - FastAPI app in `c:\Users\Yot\Documents\GitHub Projects\Nexus\Nexus`
# - Main branch: `main`
# - SSH config: `C:\Users\Yot\.ssh\config-nexus` (alias: `nexus-server`)
# - Server logs: `/home/nexus/nexus/logs/`

# Recent Work
# - Fixed circular import between `app/main.py` and `app/api/routes/logged_out.py`:
#   - `logged_out.py` now uses `APIRouter` and imports `templates` directly.
#   - `main.py` imports and includes the router.
# - Changes committed: `Refactor logged_out route to use APIRouter and fix circular import with main.py`
# - No errors in affected files.
#
# - **Admin Authentication Debugging (Dec 2025):**
#   - Persistent 401 errors on admin API endpoints were traced to issues with the Authorization header and token format.
#   - All admin JS modules now use a shared helper to add the Authorization header (`Bearer <token>`).
#   - Token sync logic was fixed to ensure only the plain JWT (no quotes, no `Bearer ` prefix) is stored in localStorage.
#   - Troubleshooting steps and lessons learned are documented in `ADMIN_PANEL_README.md` (see: Admin Authentication Troubleshooting section).
#   - If 401 persists, check that the frontend sends the correct header and inspect backend logs for token validation errors.

# Server Access
# - SSH:  
#   ssh -F $env:USERPROFILE\.ssh\config-nexus nexus-server
# - Check logs (example):  
#   ssh -F $env:USERPROFILE\.ssh\config-nexus nexus-server "tail -50 /home/nexus/nexus/logs/error.log"

# Next Steps
# - Check server logs as needed.
# - Restart server to apply changes if deploying.
# - Run `git push` if you need to push changes to remote.
