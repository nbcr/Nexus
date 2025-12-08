# Copilot Instructions for Nexus

> - GitHub Actions handles pulling files and restarting `nexus` service automatically

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
- **Deploy**: Commit and push to GitHub → GitHub Actions restarts service automatically (~40 seconds to complete)
- **DO NOT SSH to EC2 to restart service or pull files** - Always use GitHub push
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
- Password hashing: use passlib's `bcrypt_sha256`, pin `bcrypt` to 4.0.1 in requirements.txt
- Logout flow: dedicated `logged-out.html` page, POST `/api/v1/auth/logout` endpoint

## Content Scraping System (Spinner & Facts Display)

### How It Works (User Perspective)

1. **Feed loads instantly** - User sees article titles + RSS descriptions in collapsed cards (feed.css, FeedRenderer.js)
2. **Background scraping runs silently** - `/api/v1/content/feed` endpoint triggers `background_scrape_articles()` via `asyncio.create_task()` for up to 5 articles (non-blocking, separate Gunicorn worker)
3. **User clicks card** - Card expands, shows RSS description initially; if facts already scraped, displays `item.content_text`
4. **If facts not ready** - Shows spinner (CSS variables: `--accent` for rotating border-top, `--bg-tertiary` for base border)
5. **Spinner triggers on-demand scrape** - `loadSnippet()` in FeedRenderer.js calls `/api/v1/content/snippet/{id}/priority?timeout=10` with 10-second timeout
6. **Polling at 1-second intervals** - Frontend polls until `status: ready` (facts found), `failed` (timeout), or user navigates away
7. **Display facts or error** - Replace spinner with facts if scraped, or "Scraping took too long" error if timeout

### Code Locations

- **Spinner CSS:** `app/static/css/feed.css` - `.spinner` class with @keyframes spin animation
  - **Critical:** Uses `border-top-color: var(--accent)` and `border: var(--bg-tertiary)` - these CSS variables MUST be defined globally in base.css
- **Frontend rendering:** `app/static/js/FeedRenderer.js`
  - `renderContentItem()` - Shows facts if `item.content_text` exists; otherwise leaves expanded section empty (description shown in collapsed header)
  - `loadSnippet()` - Shows spinner on-demand, polls `/priority` endpoint, displays error if timeout
- **Backend scraping endpoints:** `app/api/routes/content.py`
  - `GET /feed` - Returns immediately with content, triggers `background_scrape_articles()` via `asyncio.create_task()`
  - `GET /snippet/{id}` - Returns immediately with description, triggers background scrape
  - `GET /snippet/{id}/priority` - Attempts immediate scrape with 10s timeout via `asyncio.wait_for()`, returns `{status: "ready"|"loading"|"failed", content_text?: string}`
- **Scraping logic:** `app/services/article_scraper.py` - BeautifulSoup extraction
- **Scraped metadata:** `app/models/content.py` - ContentItem has `source_metadata` JSON column; tracks `scraped_at` timestamp (set immediately on scraping attempt, not just on success)

### Key Implementation Details

- **RSS feeds always provide content** - Via `app/services/trending/rss_fetcher.py` and `app/utils/async_rss_parser.py`, descriptions are extracted and returned as `item.description` in feed
- **Never display description twice** - Show it once in collapsed header only; expanded section shows facts/spinner/error or remains empty
- **Background vs on-demand trade-off:** Background scraping is non-blocking but may miss articles if EC2 restarts; on-demand scraping guarantees attempt but has 10s timeout
- **Gunicorn config:** 2 UvicornWorkers with 120s timeout; allows one worker to serve API responses while other handles background scraping tasks
- **Memory constraints:** 1GB RAM + 2GB swap on EC2; background scraping non-blocking, on-demand scraping timeout-enforced (no backfill operations)

### If Spinner Doesn't Display

1. Check CSS variables in `app/static/css/base.css` - ensure `--accent` and `--bg-tertiary` are defined
2. Verify FeedRenderer.js `loadSnippet()` is called when card expanded
3. Check console for `/priority` endpoint errors (use `/api/v1/...` not `/api/...`)
4. Ensure `article_scraper.py` BeautifulSoup extraction logic is working (test with specific URLs)
5. Verify `source_metadata["scraped_at"]` is being set in `_scrape_and_store_article()` (even on failure)

---

If any section is unclear or missing, please provide feedback so instructions can be improved.
