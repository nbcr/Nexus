# Nexus Project – Copilot Instructions

## Context
- FastAPI app: `c:\Nexus`
- Main branch: `main`
- Server: Local (Windows-based, running on localhost)
- Server logs: `c:\Nexus\logs\`

## Server Access
- Local server runs via `python run_server.py`
- API accessible at `http://localhost:8000`
- Check logs: `Get-Content c:\Nexus\logs\error.log -Tail 50`

## Next Steps
- Test changes locally before committing
- Kill and restart server when needed: `taskkill /F /IM python.exe` then `python run_server.py`
- Make commits with `git add -A; git commit -m "message"` – user will handle pushing

