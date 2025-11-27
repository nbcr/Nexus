# Nexus Project Context

> **Agent Instruction:**
> **ALWAYS append new changes, fixes, or updates to the BOTTOM of this file, below the most recent entry. NEVER overwrite, prepend, or modify previous information. This ensures a complete historical record and avoids accidental loss of context.**
> Re-read this file after any edit or when context may have changed.

This file tracks the current project context, architecture, deployment details, recent fixes, and any ongoing issues or changes. It should be updated after every significant change or troubleshooting step.

**Instructions:**
Always append new changes, fixes, or updates to the bottom of the file (below the most recent entry), without rewriting or modifying previous information. This ensures a complete historical record and avoids accidental loss of context.

---

## Project Context: Nexus - AI News Portal

I'm working on a FastAPI-based news aggregation platform called Nexus deployed on AWS EC2. Here's the essential context:

### Server Setup

- Host: `ec2-54-167-58-129.compute-1.amazonaws.com`
- SSH access: `admin` user via plink (PuTTY on Windows)
- Application runs as: `nexus` user
- Service: `nexus.service` (systemd service running gunicorn)

### Code Structure

- Remote repo location: `/home/nexus/nexus`
- Local repo: `c:\Users\Yot\Documents\GitHub Projects\Nexus\Nexus`
- GitHub: `nbcr/Nexus` repository (main branch)
- Virtual environment: `/home/nexus/nexus/venv`

### Deployment Pattern

```powershell
echo "" | plink -batch admin@ec2-54-167-58-129.compute-1.amazonaws.com "sudo -u nexus git -C /home/nexus/nexus pull && sudo systemctl restart nexus && echo 'Deployed'"
```

### Architecture

- Backend: FastAPI with async SQLAlchemy, PostgreSQL database
- Frontend: Vanilla JavaScript (feed.js), HTML/CSS
- Key routes: content.py (NOT the v1 version - main.py imports from `app.api.routes`, not `app.api.v1.routes`)
- Services: PyTrends integration, article scraper (BeautifulSoup), content recommendation

### Key Features

1. Infinite scroll feed - personalized content from RSS feeds and Google Trends
2. Article modal - full article view with related content suggestions
3. Search query cards - PyTrends queries that open searches in new tabs (not article modals)
4. Related content matching - links news articles with trending searches using keyword extraction and scoring

### Important Files

- Routes: content.py (active), content.py (not used)
- Frontend: index.html, feed.js
- Services: article_scraper.py, pytrends_service.py
- Logs: `/home/nexus/nexus/logs/error.log`, `/home/nexus/nexus/logs/access.log`
- Password/auth: auth.py, user_service.py, auth.py

### Current Status

The backend is running and stable after recent fixes. No crashes or critical errors are present. All major endpoints, authentication, and session management features are working as intended. Continue monitoring logs for any new issues.

### Command Patterns

- Always force frontend WebSocket connection after debug deploy to generate new log entries for analysis.
- Push local files after changes: `git add <file>; git commit -m "<message>"; git push`
- Always push PROJECT_CONTEXT.md after updating: `git add PROJECT_CONTEXT.md; git commit -m "Update context"; git push`
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
8. If endpoint or handler code is not found in expected folders, always search the entire workspace for relevant keywords (route, handler, token, feed, ws, websocket, etc.) before proceeding. This ensures dynamic or non-standard registrations are not missed.
9. Always push PROJECT_CONTEXT.md after updating to ensure context changes are tracked and synced with the remote repository.
10. Added debug logging to backend WebSocket handler to print received token and decoded payload for authentication troubleshooting. Always push context after updating.
11. Always force a frontend WebSocket connection after deploying debug code to ensure new log entries are generated for analysis. Never pause to ask for readiness; proceed automatically to the next step.
12. WebSocket 401/403 errors: Backend debug logging shows all connections rejected due to 'Signature has expired' when decoding JWT. Root cause: Frontend is sending an expired JWT token for WebSocket connections. Solution: Update frontend to always fetch a fresh JWT token before opening a WebSocket connection. After any authentication or token-related backend change, always verify frontend is sending a valid, non-expired token for WebSocket connections.
13. Anonymous user tracking: All users (including anonymous) are tracked using a persistent session token (`visitor_id` cookie). Interactions and history are stored in the backend linked to this token. When a user registers or logs in, all tracked data from their session is migrated to their new account (`migrate_session_to_user`). If a user never registers, tracking continues anonymously. Frontend always sets a persistent `visitor_id` for every user.

---

## Next Steps

- Test logout flow to confirm session is fully cleared and user is redirected as expected.
- Monitor for any further frontend/backend errors related to authentication or session management.

---

## Recent Issues Resolved & Bug Fixes

> **Append new updates below, newest at the bottom. Do not rewrite previous entries.**

### 2025-11-24 22:00:00 UTC: Logout Flow and Auth Button Fixes


- Created a dedicated `logged-out.html` page that displays a logout confirmation and auto-redirects to the homepage after a short delay.
### 2025-11-27 15:00 UTC: Hamburger Menu and UI Redesign

- Refactored hamburger menu to use icon-above-text layout, touch-friendly spacing, and grid layout (2 icons per row, no borders).
- Moved Privacy Policy, Terms, and History links to a new sidebar-based settings page (`settings.html`).
- Added quick links to Feed, Settings, Profile, and Admin in the menu.
- Added a dark mode toggle to the hamburger menu for mobile; ensured only one toggle is visible at a time.
- Fixed CSS: moved all `.nav-links.open` child rules to top-level selectors and duplicated styles for each selector for browser compatibility.
- Updated menu item styles for proper spacing, alignment, and responsiveness.
- Updated TODO.md to include profile page and settings page tasks.
- Committed and pushed all changes after each edit; stopped auto-restarting the service after every change.
- Updated frontend logout logic to always redirect to `/logged-out.html` after logout, instead of the login page or reloading.
- Changed the auth button in `index.html` from `<a href="/login">` to `<button>`, so JS controls navigation and prevents unwanted redirects.
- Ensured the JS handler for the auth button always triggers the correct login/logout logic and label.
- Verified and deployed these changes; logout now works as intended.
- Fixed content endpoint returning 500 errors (NULL titles in database, needed `.all()` for result iteration, topic serialization).
- Article endpoint was missing from old routes file - added manually.
- Article scraper returns fallback message when content extraction fails.
- Search query detection: checks for `pytrends` tag or search engine URLs to open in new tab vs. article modal.

#### Password Hashing/Authentication

- Resolved persistent bcrypt 72-byte errors by switching to passlib’s `bcrypt_sha256` scheme for all password operations (OWASP-recommended).
- Removed all manual password encoding/truncation logic; always pass password as string.
- Pinned `bcrypt` to version 4.0.1 in requirements.txt to avoid compatibility issues with newer versions.
- Reinstalled dependencies and restarted backend service after pinning bcrypt.

#### Categories Endpoint

- Refactored `/categories` endpoint to a normal async function (no generator).
- Cleaned up imports and response models.
- Ensured all new `ContentItem` objects have a slug.
- Restarted backend service and checked logs after each fix.

- Fixed JS error in `logged-out.html` by moving dark mode and redirect script to end of file, ensuring `document.body` is available before accessing `.classList`.
- Added POST `/api/v1/auth/logout` endpoint to backend (`auth.py`) to clear access/refresh tokens for proper logout support.
- Committed, pushed, and redeployed backend changes. Logout endpoint is now live and should resolve frontend 404 errors.

### 2025-11-24 22:00:00 UTC: Header and Logged Out Button Styling

- Created a dedicated `.btn-hdr` class for header buttons in `index.css` and applied it to all header buttons in `index.html` for consistent styling.
- Updated the logged out page button to use `.btn-hdr` for visual consistency with header buttons.
- Removed previous generic `.btn` and `.logged-out-btn` classes from these buttons to avoid style conflicts.
- Verified button alignment and appearance across header and logged out page.

### 2025-11-24 22:15:00 UTC: Modal Text Color Fix (Dark Mode)

- Removed the last hardcoded inline color (`#333`) from modal summary rendering in `feed.js`.
- Modal and error message text color now fully relies on CSS for both light and dark modes.
- Verified modal readability in dark mode; no inline color overrides remain.

---

# 2025-11-27 18:00 UTC: CSS Cleanup and Consolidation

- Removed all duplicate blocks for .main-header, .main-header .container, .main-header nav, .nav-links, .nav-links.open, button, and .hamburger in index.css, keeping only the most complete and correct version for each selector.
- Removed all !important rules from these blocks to allow proper JS and CSS control.
- Fixed color contrast by removing global body { color: #fff; } and setting .main-header .container { color: #000; } to prevent white text on white backgrounds.
- Consolidated button styles for consistency and removed unnecessary overrides.
- Verified no CSS errors remain after cleanup.
- Committed and pushed changes as per workflow; service restart is handled automatically by the push.

# 2025-11-27 18:10 UTC: CSS .nav-links !important Fix

- Removed !important from .nav-links { display: none; } in index.css to allow JavaScript toggling to work correctly and ensure the menu can be shown/hidden as intended.
- Committed and pushed the change as per workflow.

---

## [2025-11-27] CSS Selector Comma Fixes & Syntax Cleanup
- Fixed selectors in `index.css` that ended in a comma but had no rule block, by copying the rules from the group below to each such selector.
- Ensured all selectors (e.g., `.nav-links.open a,`, `.main-header nav a,`) have their own rule blocks for clarity and maintainability.
- Removed stray property blocks and closing braces that caused CSS syntax errors.
- Verified that all lint/compile errors are resolved and CSS is valid.
- Committed and pushed changes to the repo as per workflow.

# 2025-11-27 20:00 UTC: Hamburger Menu Toggle Bug Fixes
- Investigated double toggling of the hamburger menu due to duplicate event listeners in the inline script in `index.html`.
- Removed the duplicate hamburger click event listener, ensuring only one listener is present for correct menu open/close behavior.
- Verified that the menu now toggles correctly with a single click.
- Restored the correct event listener after user feedback, ensuring menu functionality is preserved.

# 2025-11-27 21:00 UTC: Menu Layout and Cleanup
- Updated `.nav-links.open` in `index.css` to use flexbox with wrapping and 50% width for child items, resulting in two items per row for improved menu layout.
- Removed the dark mode label and moon icon button from the menu in `index.html` for a cleaner appearance.
- Committed and pushed all changes to the repository to maintain a clear history for easy reversion.

# 2025-11-27 21:15 UTC: Menu Layout CSS Fixes
- Noticed and removed a stray closing brace in `index.css` that was causing a lint error.
- Verified that the menu layout now uses flexbox for two items per row, with icons above labels and no horizontal lines between items.
- Committed and pushed the CSS fix to the repository immediately after the edit to maintain a clear history.
- Will continue to document and push all changes and fixes as they are made.

# Next: Menu Layout Update
- User requested to update the menu layout so that menu items display two per row.
- Will update CSS for `.nav-links.open` to use a grid layout with two columns, ensuring all menu items are arranged in two-item rows for improved usability and appearance.
