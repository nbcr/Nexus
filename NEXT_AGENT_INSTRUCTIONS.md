# Nexus Project – Copilot Instructions

## Context
- FastAPI app in `c:\Users\Yot\Documents\GitHub Projects\Nexus\Nexus`
- Main branch: `main`
- SSH config: `C:\Users\Yot\.ssh\config-nexus` (alias: `nexus-server`)
- Server logs: `/home/nexus/nexus/logs/`

## Recent Work
- Fixed circular import between `app/main.py` and `app/api/routes/logged_out.py`:
  - `logged_out.py` now uses `APIRouter` and imports `templates` directly.
  - `main.py` imports and includes the router.
- Changes committed: `Refactor logged_out route to use APIRouter and fix circular import with main.py`
- No errors in affected files.

## Server Access
- SSH:  
  `ssh -F $env:USERPROFILE\.ssh\config-nexus nexus-server`
- Check logs (example):  
  `ssh -F $env:USERPROFILE\.ssh\config-nexus nexus-server "tail -50 /home/nexus/nexus/logs/error.log"`

## Next Steps
- Check server logs as needed.
- Restart server to apply changes if deploying.
- Run `git push` if you need to push changes to remote.
