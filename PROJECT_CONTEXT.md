# Nexus Project Context

This file tracks the current project context, architecture, deployment details, recent fixes, and any ongoing issues or changes. It should be updated after every significant change or troubleshooting step.

---

**Project Context: Nexus - AI News Portal**

I'm working on a FastAPI-based news aggregation platform called Nexus deployed on AWS EC2. Here's the essential context:

**Server Setup:**
- Host: `ec2-54-167-58-129.compute-1.amazonaws.com`
- SSH access: `admin` user via plink (PuTTY on Windows)
- Application runs as: `nexus` user
- Service: `nexus.service` (systemd service running gunicorn)

**Code Structure:**
- Remote repo location: `/home/nexus/nexus`
- Local repo: `c:\Users\Yot\Documents\GitHub Projects\Nexus\Nexus`
- GitHub: `nbcr/Nexus` repository (main branch)
- Virtual environment: `/home/nexus/nexus/venv`

**Deployment Pattern:**
```powershell
echo "" | plink -batch admin@ec2-54-167-58-129.compute-1.amazonaws.com "sudo -u nexus git -C /home/nexus/nexus pull && sudo systemctl restart nexus && echo 'Deployed'"
```

**Architecture:**
- Backend: FastAPI with async SQLAlchemy, PostgreSQL database
- Frontend: Vanilla JavaScript (feed.js), HTML/CSS
- Key routes: content.py (NOT the v1 version - main.py imports from `app.api.routes`, not `app.api.v1.routes`)
- Services: PyTrends integration, article scraper (BeautifulSoup), content recommendation

**Key Features:**
1. Infinite scroll feed - personalized content from RSS feeds and Google Trends
2. Article modal - full article view with related content suggestions
3. Search query cards - PyTrends queries that open searches in new tabs (not article modals)
4. Related content matching - links news articles with trending searches using keyword extraction and scoring

**Recent Issues Resolved & New Fixes:**
- Fixed content endpoint returning 500 errors (NULL titles in database, needed `.all()` for result iteration, topic serialization)
- Article endpoint was missing from old routes file - added manually
- Article scraper returns fallback message when content extraction fails
- Search query detection: checks for `pytrends` tag or search engine URLs to open in new tab vs. article modal
- **Password hashing/authentication:**  
  - Resolved persistent bcrypt 72-byte errors by switching to passlib’s `bcrypt_sha256` scheme for all password operations (OWASP-recommended).
  - Removed all manual password encoding/truncation logic; always pass password as string.
  - Pinned `bcrypt` to version 4.0.1 in requirements.txt to avoid compatibility issues with newer versions.
  - Reinstalled dependencies and restarted backend service after pinning bcrypt.
- **Categories Endpoint:**  
  - Refactored `/categories` endpoint to a normal async function (no generator).
  - Cleaned up imports and response models.
  - Ensured all new `ContentItem` objects have a slug.
  - Restarted backend service and checked logs after each fix.

**Important Files:**
- Routes: content.py (active), content.py (not used)
- Frontend: index.html, feed.js
- Services: article_scraper.py, pytrends_service.py
- Logs: `/home/nexus/nexus/logs/error.log`, `/home/nexus/nexus/logs/access.log`
- Password/auth: auth.py, user_service.py, auth.py

**Current State:**
The site is functional with working feed, article modals (with fallback for scraping issues), and search query handling. Related content feature implemented but needs testing with actual related items.  
Password registration and login now support any length/character set, with no bcrypt errors.  
Categories endpoint and slug integrity are now robust, but backend is currently crashing with `status=3/NOTIMPLEMENTED` (pending fix).

**Command Patterns:**
- Test endpoint: `curl -s 'http://localhost:8000/api/v1/content/...'`
- Check logs: `sudo tail -100 /home/nexus/nexus/logs/error.log`
- Service status: `systemctl status nexus`
- Reinstall dependencies: `sudo /home/nexus/nexus/venv/bin/pip install --force-reinstall -r /home/nexus/nexus/requirements.txt`
- Push local files after changes: `git add <file>; git commit -m "<message>"; git push`

---

This file should be updated after every significant change, fix, or troubleshooting step to ensure context is always current.

---

## Troubleshooting Steps (Nov 24, 2025)

1. Checked service status and error logs for backend crash (`status=3/NOTIMPLEMENTED`).
2. Identified root cause: Python SyntaxError due to 'return' in async generator in /categories endpoint and get_db dependency.
3. Refactored /categories endpoint and get_db to be standard async functions (no yield).
4. Pushed local changes to remote repository after each code edit.
5. Restarted backend service after code changes.
6. Checked logs after restart to confirm service is running and errors are resolved.
7. Updated PROJECT_CONTEXT.md with new command pattern and troubleshooting steps.
