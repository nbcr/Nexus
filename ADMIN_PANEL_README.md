## Admin Authentication Troubleshooting & Lessons Learned (Dec 2025)

If you encounter persistent 401 Unauthorized errors on admin API endpoints, follow this checklist:

### 1. Token Format in localStorage
- The token in `localStorage` (usually under `access_token`) must be a plain JWT string (no quotes, no `Bearer ` prefix).

### 2. Authorization Header in Requests
- All admin API requests must include the `Authorization` header, formatted as `Bearer <token>`.
- Use a shared helper (e.g., `authManager.getAuthHeaders()`) to construct headers for all fetch/XHR calls.

### 3. Token Sync Logic
- If syncing from a cookie, always strip quotes and the `Bearer ` prefix before saving to `localStorage`.

### 4. Frontend Debugging
- In browser console, run `localStorage.getItem('access_token')` to check the token value.
- Run `authManager.getAuthHeaders()` to see the Authorization header that will be sent.
- Inspect network requests in browser dev tools (Network tab) to confirm the header is present and correct.
- If the header is missing, check that the fetch/XHR code uses `authManager.getAuthHeaders()`.

### 5. Backend Debugging
- If the header is present and correct, but you still get 401, check backend logs for token validation errors.

### 6. Proxy Issues
- If all else fails, check Nginx or other proxy configs to ensure they are not stripping the `Authorization` header.

#### Lessons Learned
- All admin JS modules must use a shared helper to add the Authorization header.
- Token sync logic must always sanitize the token before saving to localStorage.
- 401 errors are almost always due to missing/malformed Authorization header or token format issues.
- Use browser dev tools to confirm both the token value and the presence of the header in requests.
- If the frontend is correct, backend logs will reveal if the token is expired, malformed, or rejected for another reason.

#### Example Debugging Workflow
1. Log out and log back in to get a fresh token.
2. In browser console:
  - `localStorage.getItem('access_token')` → should be a JWT (no quotes, no Bearer)
  - `authManager.getAuthHeaders()` → should return `{ Authorization: 'Bearer <token>' }`
3. Make an admin API request and inspect the Network tab:
  - Confirm the `Authorization` header is present and correct.
4. If 401 persists, check backend logs for error details.

#### Common Pitfalls
- Storing the token with quotes or the `Bearer ` prefix in `localStorage`.
- Not including the `Authorization` header in fetch requests.
- Backend rejecting requests due to missing/malformed header.
- Nginx or other proxies stripping headers (check proxy config if all else fails).
# Nexus Admin Panel

## 🔒 Security Notice

The admin panel is a **secure, hidden interface** designed for system administrators only. It is intentionally obscured from:

- Regular users (no links in the main application)
- Search engines (robots.txt exclusion)
- API documentation (excluded from OpenAPI schema)
- Web crawlers (comprehensive meta tags)

## Access

**URL:** `/static/admin.html` or direct file access only

**Authentication:** Requires admin-level user account with `is_admin=True` flag in database

**Default:** Dark mode (easier on the eyes during late-night monitoring)

## Features

### 📊 Real-Time Interest Tracking

Monitor user engagement with content cards in real-time:

- **Live Events Stream**: See hover events as they happen
- **Interest Levels**: High (≥70), Medium (50-69), Low (<50)
- **Detailed Metrics**: Score, duration, movement, slowdowns, clicks, AFK status
- **Auto-Refresh**: Updates every 5 seconds (toggleable)
- **Statistics Dashboard**: Total events, distribution by interest level

### ⚙️ Global Settings Management

Configure default hover tracking parameters for all users:

- **Minimum Hover Duration** (default: 1500ms)
- **AFK Threshold** (default: 5000ms) 
- **Movement Threshold** (default: 5px)
- **Micro-Movement Threshold** (default: 20px)
- **Slowdown Velocity Threshold** (default: 0.3 px/ms)
- **Velocity Sample Rate** (default: 100ms)
- **Interest Score Threshold** (default: 50)
- **Scroll Slowdown Threshold** (default: 2.0 px/ms)

Actions:
- Save settings for all users
- Reset to default values
- Test current configuration

### 👥 User Management

View and manage all registered users:

- **User List**: Searchable grid with interaction counts
- **User Details**: Click any user card for detailed statistics
- **Per-User Settings**: Override global settings for specific users
- **Statistics**:
  - Total interactions
  - High interest events
  - Average hover duration
  - Last active timestamp
- **Custom Configuration**: Enable custom hover tracking settings per user

### 📈 Analytics Dashboard

Analyze user engagement patterns over time:

- **Date Range Selector**: Custom time period analysis
- **Interest Distribution**: Visual breakdown of High/Medium/Low interest
- **Top Content**: Most engaged content items with view counts
- **User Engagement Timeline**: Activity patterns over time
- **Hover Patterns**: Average duration, slowdowns, movement rates, AFK statistics

## Interface

### Dark Mode (Default)

The admin panel defaults to a dark, high-contrast theme optimized for:
- Reduced eye strain during extended monitoring
- Professional "dark web" aesthetic (non-indexed, secure)
- Better visibility of interest metrics and charts
- Power efficiency on OLED displays

Toggle to light mode if needed with the 🌙 button in the header.

### Tab Navigation

- **📊 Interest Tracking**: Real-time event monitoring
- **⚙️ Global Settings**: System-wide configuration
- **👥 User Management**: User administration
- **📈 Analytics**: Historical data analysis

## Security Features

### Authentication
- Admin verification on page load
- 403 Access Denied screen for non-admin users
- Session-based authentication with httponly cookies
- No bypass possible without database-level admin flag

### Obscurity
- No navigation links from main application
- Not included in sitemap
- Excluded from robots.txt
- Hidden from OpenAPI documentation
- Comprehensive meta tags preventing indexing
- Direct file access only (no public routing)

### Authorization
All API endpoints require:
```python
admin: User = Depends(verify_admin)
```

Failed authentication returns HTTP 403 immediately.

## API Endpoints

All endpoints are prefixed with `/api/v1/admin/` and **excluded from OpenAPI docs**.

### Authentication
- `GET /verify` - Verify admin access

### Tracking
- `GET /tracking-log?limit=100` - Get recent tracking events
- `POST /clear-tracking` - Clear all tracking data (destructive)

### Settings
- `GET /settings/global` - Get current global settings
- `POST /settings/global` - Save global settings

### Users
- `GET /users` - List all users with stats
- `GET /users/{user_id}` - Get user details
- `POST /users/{user_id}/settings` - Save user-specific settings

### Analytics
- `GET /analytics?start=YYYY-MM-DD&end=YYYY-MM-DD` - Get analytics data

## Usage Examples

### Adjusting Sensitivity

To make the system **more sensitive** (detect more interest):
1. Lower `Interest Score Threshold` (e.g., 30 instead of 50)
2. Lower `Minimum Hover Duration` (e.g., 1000ms instead of 1500ms)
3. Lower `AFK Threshold` (e.g., 3000ms instead of 5000ms)

To make the system **less sensitive** (reduce false positives):
1. Raise `Interest Score Threshold` (e.g., 70 instead of 50)
2. Raise `Minimum Hover Duration` (e.g., 2000ms instead of 1500ms)
3. Lower `Movement Threshold` (require more movement to count as active)

### Per-User Customization

For a power user who reads slowly:
1. Navigate to User Management tab
2. Click on the user
3. Enable "Use custom settings"
4. Increase `Min Hover Duration` to 3000ms
5. Increase `AFK Threshold` to 10000ms
6. Save settings

The user will now receive these custom parameters instead of global defaults.

### Monitoring Campaign Performance

1. Launch new content campaign
2. Go to Analytics tab
3. Set date range to campaign period
4. Check:
   - Interest distribution (High interest %)
   - Top content items (which performed best)
   - Hover patterns (engagement quality)

### Clearing Test Data

During development or testing:
1. Go to Interest Tracking tab
2. Click "🗑️ Clear All"
3. Confirm deletion
4. All tracking events are removed from database

## Technical Details

### Frontend
- **HTML**: `app/static/admin.html`
- **CSS**: `app/static/css/admin.css`
- **JavaScript**: `app/static/js/admin.js`

### Backend
- **Routes**: `app/api/v1/routes/admin.py`
- **Auth**: `app/api/v1/deps.py` (verify_admin dependency)

### Data Storage
- Interest events: `user_interactions` table
- User settings: TODO - dedicated settings table
- Global settings: TODO - system settings table

### Future Enhancements
- [ ] Persistent settings storage in database
- [ ] Real-time WebSocket updates for live tracking
- [ ] Advanced charts (Chart.js integration)
- [ ] Export analytics to CSV/JSON
- [ ] User role management (super admin, moderator, etc.)
- [ ] Activity audit log
- [ ] A/B testing framework for settings
- [ ] Machine learning insights

## Troubleshooting

### Cannot Access Admin Panel

**Symptom**: 403 Access Denied screen

**Solutions**:
1. Verify your user account has `is_admin=True` in database
2. Check you're logged in (check cookies)
3. Try logging out and back in
4. Verify session is valid

### Settings Not Applying

**Symptom**: Changed settings but users don't see them

**Cause**: Settings are currently in-memory only (not persisted)

**Solution**: Settings will be stored in database in future update. For now, settings are defaults only.

### Tracking Events Not Appearing

**Symptom**: No events in tracking log

**Possible Causes**:
1. No users are browsing content
2. Interest threshold is too high
3. Database connection issue
4. Frontend hover-tracker.js not loaded

**Solutions**:
1. Test with your own browsing
2. Lower interest threshold temporarily
3. Check server logs for errors
4. Verify hover-tracker.js is loaded before feed.js

### Auto-Refresh Stopped Working

**Symptom**: Events stop updating automatically

**Solution**: 
1. Check "Auto-refresh" checkbox is enabled
2. Switch to another tab and back to reset
3. Manually click "🔄 Refresh" button
4. Check browser console for errors

## Browser Compatibility

Tested on:
- Chrome/Edge 100+
- Firefox 90+
- Safari 14+

Requires:
- ES6 JavaScript
- CSS Grid
- Fetch API
- Modern CSS (CSS variables, flexbox, grid)

## Performance

The admin panel is optimized for:
- **Low latency**: Real-time updates every 5s
- **Efficient queries**: Indexed database lookups
- **Minimal load**: Only fetches recent events (default limit: 100)
- **Responsive design**: Works on tablets and desktops

## Keyboard Shortcuts

- `Esc` - Close user modal
- `Ctrl/Cmd + F` - Search users (browser find)

## Maintenance

### Regular Tasks
- Monitor tracking log for anomalies
- Review top content weekly
- Check user engagement patterns
- Adjust settings based on analytics

### Monthly Tasks
- Review user statistics
- Identify inactive users
- Analyze interest distribution trends
- Backup analytics data

### Quarterly Tasks
- Evaluate settings effectiveness
- A/B test different thresholds
- Review per-user customizations
- Plan feature enhancements

---

**Remember**: This is a powerful administrative tool. Use responsibly and keep access credentials secure.

Built with 🔒 for secure administration of the Nexus platform.
