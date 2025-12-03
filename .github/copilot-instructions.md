# Copilot Instructions for Nexus

> **CRITICAL: Response Protocol:**
>
> - Say "ok" when you understand instructions
> - Say "done" when finished with tasks
> - NO explanations, NO summaries, NO details unless explicitly asked
> - Minimum verbosity in ALL responses including thinking steps

> **Agent Instruction:**
> Always review and follow the latest instructions, workflow, troubleshooting steps, and update conventions in the `PROJECT_CONTEXT.md` file before making any changes or answering questions. Re-read this file after any edit or when context may have changed.

> **Verbosity & Communication:**
>
> - **DO NOT explain unless explicitly asked** - Complete tasks without explanations
> - **Keep responses as short as possible** - Verbosity set to minimum
> - **No response after completing tasks** - Just complete the work, no confirmation messages unless requested
> - **Only provide details when user asks questions** - Don't volunteer information

## Project Overview & Context

Nexus is a FastAPI-based AI news aggregation and personalization platform deployed on AWS EC2. It fetches trending Canadian news and provides personalized recommendations using session-based tracking and JWT authentication. The backend runs as a systemd service (`nexus.service`) under the `nexus` user.

## Architecture & Key Patterns

- Backend: FastAPI, async SQLAlchemy, PostgreSQL
- Frontend: Vanilla JS (`feed.js`), HTML/CSS
- API endpoints: Defined in `app/api/routes/content.py` (main, not v1)
- Business logic: `app/services/` (e.g., `article_scraper.py`, `content_recommendation.py`)
- Models: `app/models/` (e.g., `content.py`, `user.py`)
- Database setup/migrations: root scripts and `scripts/`, migrations in `alembic/versions/`
- Frontend assets: `app/static/` (e.g., `index.html`, `feed.js`)
- Session/authentication: `app/core/auth.py`, `app/services/user_service.py`

## Developer Workflow

- Build: Use VS Code build task (`msbuild`)
- Run backend: `python run_server.py` (local) or via systemd (`nexus.service`) on EC2
- Deploy: SSH to EC2 and run:
  ```powershell
  echo "" | plink -batch admin@ec2-54-167-58-129.compute-1.amazonaws.com "sudo -u nexus git -C /home/nexus/nexus pull && sudo systemctl restart nexus && echo 'Deployed'"
  ```
- Database: Use `db_setup.sh` and migration scripts for setup/updates
- Always update and push `PROJECT_CONTEXT.md` after significant changes
- After updating files, always commit and push your changes to the repository
- Test endpoint: `curl -s 'http://localhost:8000/api/v1/content/...'`
- Check logs: `sudo tail -100 /home/nexus/nexus/logs/error.log`
- Service status: `systemctl status nexus`
- Reinstall dependencies: `sudo /home/nexus/nexus/venv/bin/pip install --force-reinstall -r /home/nexus/nexus/requirements.txt`

## Conventions & Patterns

- All users (including anonymous) tracked via persistent `visitor_id` cookie; session data migrates on registration/login
- Passwords use `bcrypt_sha256` via passlib; never truncate or encode manually
- JWT tokens must be fresh for WebSocket connections; frontend must fetch a new token before opening a socket
- Debugging: Check `/home/nexus/nexus/logs/error.log` and `/access.log` on EC2; use debug logging in WebSocket handlers for token troubleshooting
- Always force a frontend WebSocket connection after deploying debug code to generate new log entries
- For endpoint or handler code not found in expected folders, always search the entire workspace for relevant keywords before proceeding

## Integration Points

- Article scraping: `app/services/article_scraper.py` (BeautifulSoup)
- Content recommendation: `app/services/content_recommendation.py`

## Examples & Patterns

- To add a new API route: update `app/api/routes/content.py` and corresponding service/model files
- For frontend changes: edit `app/static/index.html` and `feed.js`
- For database changes: update models in `app/models/` and create a migration script in `alembic/versions/`

## Troubleshooting & Recent Fixes

- Always check service status and error logs for backend issues
- Refactor async generator endpoints to standard async functions (no yield)
- Use `.all()` for result iteration in SQLAlchemy queries
- Ensure all new `ContentItem` objects have a slug
- Add debug logging to backend WebSocket handler for token troubleshooting
- Always force frontend WebSocket connection after debug deploy
- Frontend must fetch a fresh JWT token before opening a WebSocket connection
- Anonymous user tracking: persistent `visitor_id` cookie, session data migrates on registration/login
- Password hashing: use passlib’s `bcrypt_sha256`, pin `bcrypt` to 4.0.1 in requirements.txt
- Logout flow: dedicated `logged-out.html` page, POST `/api/v1/auth/logout` endpoint

---

If any section is unclear or missing, please provide feedback so instructions can be improved.
