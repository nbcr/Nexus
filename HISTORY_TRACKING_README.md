# Content History Tracking System

## Overview

The Content History Tracking System prevents users from seeing duplicate content in their feed and provides a comprehensive view of what they've seen and clicked. Each piece of content has a unique identifier (slug) that enables direct linking and history tracking.

## Key Features

### 1. Automatic View Tracking
- **Viewport Detection**: Content is automatically marked as "seen" when it enters the viewport (50% visible)
- **Click Tracking**: Records when users click on content to read more or visit source
- **Duplicate Prevention**: Feed excludes already-seen content from future loads
- **Session-Based**: Works for both authenticated and anonymous users via session tokens

### 2. Unique Content Identifiers
- **Slug Generation**: Each content item gets a unique slug (e.g., `trump-tariff-threats-1234-a1b2c3d4`)
- **Direct Linking**: Content accessible via `/story/{slug}` URLs
- **Shareable**: Slugs can be shared and bookmarked

### 3. History Viewer
- **Three Views**: Seen content, clicked content, and all history
- **Pagination**: Handles large history sets efficiently
- **Clear History**: Users can clear seen, clicked, or all history
- **Time Tracking**: Shows when content was viewed
- **Direct Access**: Click any history item to view the original content

## Technical Architecture

### Database Schema

#### ContentViewHistory Table
```sql
CREATE TABLE content_view_history (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),           -- NULL for anonymous
    session_token VARCHAR(255),                     -- For tracking
    content_id INTEGER REFERENCES content_items(id),
    content_slug VARCHAR(255),                      -- Denormalized for speed
    view_type VARCHAR(50),                          -- 'seen', 'clicked', 'read'
    viewed_at TIMESTAMP DEFAULT NOW(),
    time_spent_seconds INTEGER,                     -- Optional engagement metric
    
    INDEX(user_id),
    INDEX(session_token),
    INDEX(content_id),
    INDEX(content_slug)
);
```

#### ContentItem Slug Column
```sql
ALTER TABLE content_items 
ADD COLUMN slug VARCHAR(255) UNIQUE NOT NULL;
```

### Backend Components

#### 1. Models (`app/models/`)

**ContentViewHistory** (`user.py`)
- Tracks individual view events
- Links to User and ContentItem
- Stores view type and timestamp

**ContentItem** (`content.py`)
- Added `slug` field for unique identification
- Relationship to `view_history`

#### 2. API Endpoints (`app/api/v1/routes/history.py`)

**POST /api/v1/history/record**
```json
{
  "content_id": 123,
  "content_slug": "article-slug-abc123",
  "view_type": "seen",
  "time_spent_seconds": 45
}
```
- Records a view event
- Prevents duplicate "seen" records
- Returns view ID

**GET /api/v1/history/viewed**
- Query params: `view_type` (optional), `page`, `page_size`
- Returns paginated history with content titles
- Supports filtering by view type

**GET /api/v1/history/seen-ids**
- Returns array of content IDs already seen
- Used for duplicate prevention in feed

**DELETE /api/v1/history/clear**
- Query param: `view_type` (optional)
- Clears user's history

#### 3. Content Recommendation Service

**Modified `get_personalized_feed()`**
- Calls `_get_viewed_content()` to fetch seen IDs
- Excludes viewed content from query results
- Ensures users don't see duplicates

**Updated `_get_viewed_content()`**
```python
# Now uses ContentViewHistory instead of UserInteraction
query = select(ContentViewHistory.content_id).where(
    ContentViewHistory.view_type == 'seen',
    ContentViewHistory.session_token == session_token
).distinct()
```

#### 4. Slug Generation Utility (`app/utils/slug.py`)

**`generate_slug(title, content_id)`**
- Converts title to URL-safe format
- Removes special characters
- Adds MD5 hash for uniqueness
- Format: `{normalized-title}-{id}-{hash}`

### Frontend Components

#### 1. History Tracker (`history-tracker.js`)

**HistoryTracker Class**
- `init()`: Initializes IntersectionObserver
- `observeCard(element)`: Tracks when card enters viewport
- `recordView(contentId, slug, type)`: Sends view to API
- `recordClick(contentId, slug)`: Records click events
- `getHistory(viewType, page)`: Fetches history
- `clearHistory(viewType)`: Clears history

**Integration Points**
```javascript
// Initialize on page load
window.historyTracker.init();

// Observe cards
window.historyTracker.observeCard(cardElement);

// Record clicks
window.historyTracker.recordClick(contentId, slug);
```

#### 2. Feed Integration (`feed.js`)

**Card Rendering**
```javascript
article.dataset.contentId = item.content_id;
article.dataset.contentSlug = item.slug;  // Added for tracking
```

**Viewport Tracking**
```javascript
// After appending card to DOM
if (window.historyTracker) {
    window.historyTracker.observeCard(article);
}
```

**Click Tracking**
```javascript
readMoreBtn.addEventListener('click', (e) => {
    if (window.historyTracker) {
        window.historyTracker.recordClick(item.content_id, slug);
    }
    // ... existing logic
});
```

#### 3. History Viewer (`history.html`)

**Features**
- Three tabs: Seen, Clicked, All
- Pagination controls
- Clear history buttons
- Direct links to content via `/story/{slug}`
- Dark mode support
- Empty state handling

**API Integration**
```javascript
// Load history
fetch('/api/v1/history/viewed?page=1&view_type=seen')

// Clear history
fetch('/api/v1/history/clear?view_type=seen', { method: 'DELETE' })
```

## User Flow

### Viewing Content

1. **User scrolls feed** → Cards render with `data-content-id` and `data-content-slug`
2. **Card enters viewport** → IntersectionObserver triggers at 50% visibility
3. **HistoryTracker.handleCardVisible()** → Checks if already recorded
4. **POST /api/v1/history/record** → Saves view with type='seen'
5. **Feed refresh** → Calls `get_personalized_feed()` which excludes seen IDs
6. **No duplicates** → User only sees new content

### Clicking Content

1. **User clicks "Read More"** or source link
2. **Click handler** → Calls `historyTracker.recordClick()`
3. **POST /api/v1/history/record** → Saves view with type='clicked'
4. **Content opens** → Modal or new tab

### Viewing History

1. **User visits** `/history.html`
2. **Page loads** → Fetches history via API
3. **Three tabs** → Switch between Seen, Clicked, All
4. **Click item** → Redirects to `/story/{slug}` → Opens feed with that story
5. **Clear button** → Removes history entries

## Configuration

### Session Tracking
- Uses existing `session_token` from UserSession
- Works for both authenticated and anonymous users
- Persists across browser sessions (via cookies)

### Viewport Threshold
```javascript
const options = {
    root: null,
    rootMargin: '0px',
    threshold: 0.5  // 50% of card must be visible
};
```

### Pagination
- Default page size: 20 items
- Configurable in API calls
- Maximum: 100 items per page

## Database Migration

**Migration File**: `alembic/versions/003_add_content_view_history.py`

```bash
# Run migration on server
cd /home/nexus/nexus
source venv/bin/activate
alembic upgrade head
```

**What it does**:
1. Creates `content_view_history` table with indexes
2. Adds `slug` column to `content_items` with unique index
3. Generates slugs for existing content (format: `content-{id}`)
4. Sets slug as NOT NULL after populating

## API Reference

### Record View
```http
POST /api/v1/history/record
Content-Type: application/json

{
    "content_id": 123,
    "content_slug": "article-title-123-abc123",
    "view_type": "seen",
    "time_spent_seconds": 30
}

Response: 201 Created
{
    "message": "View recorded",
    "id": 456
}
```

### Get History
```http
GET /api/v1/history/viewed?view_type=clicked&page=1&page_size=20

Response: 200 OK
{
    "items": [
        {
            "id": 456,
            "content_id": 123,
            "content_slug": "article-title-123-abc123",
            "title": "Article Title",
            "view_type": "clicked",
            "viewed_at": "2025-11-21T10:30:00",
            "time_spent_seconds": 30
        }
    ],
    "total": 45,
    "page": 1,
    "page_size": 20,
    "has_more": true
}
```

### Get Seen IDs
```http
GET /api/v1/history/seen-ids

Response: 200 OK
{
    "seen_ids": [123, 456, 789, ...]
}
```

### Clear History
```http
DELETE /api/v1/history/clear?view_type=seen

Response: 200 OK
{
    "message": "Cleared 45 history items"
}
```

## Performance Considerations

### Indexes
- `content_id` - Fast lookup of views for specific content
- `session_token` - Fast user history queries
- `content_slug` - Fast slug-based lookups
- `user_id` - Optional for authenticated users

### Query Optimization
- Uses cursor-based pagination in feed
- Denormalizes `content_slug` in history table (avoids JOIN)
- Distinct query for seen IDs (prevents duplicates)
- `exclude_ids` uses `id.notin_()` (indexed)

### Caching Strategy
- Frontend caches seen IDs in `Set()` for session
- Reduces API calls for already-tracked content
- Reloads on page refresh via `loadSeenContent()`

## Testing

### Manual Testing Checklist

**Viewport Tracking**
- [ ] Card marked as seen when scrolling
- [ ] Card NOT marked if scrolled past quickly (<50% visible)
- [ ] Refresh feed excludes seen cards
- [ ] Seen IDs persist across page reload

**Click Tracking**
- [ ] "Read More" button records click
- [ ] Source link records click
- [ ] Click appears in history with correct timestamp

**History Viewer**
- [ ] Seen tab shows viewed content
- [ ] Clicked tab shows clicked content
- [ ] All tab shows both types
- [ ] Pagination works correctly
- [ ] Clear history removes items
- [ ] Direct links work (`/story/{slug}`)

**Duplicate Prevention**
- [ ] Seen content doesn't reappear in feed
- [ ] New content still loads correctly
- [ ] Cleared history allows content to reappear

### Database Queries

```sql
-- Check recent views
SELECT * FROM content_view_history 
ORDER BY viewed_at DESC 
LIMIT 10;

-- Count views by type
SELECT view_type, COUNT(*) 
FROM content_view_history 
GROUP BY view_type;

-- Find users with most history
SELECT session_token, COUNT(*) as view_count
FROM content_view_history
GROUP BY session_token
ORDER BY view_count DESC
LIMIT 10;

-- Check for duplicates (should be none for 'seen')
SELECT content_id, session_token, COUNT(*)
FROM content_view_history
WHERE view_type = 'seen'
GROUP BY content_id, session_token
HAVING COUNT(*) > 1;
```

## Troubleshooting

### Issue: Content still showing duplicates
**Check**:
1. History tracker initialized? (`window.historyTracker` exists)
2. Session token valid? (Check cookies)
3. IntersectionObserver working? (Check browser support)
4. API recording views? (Check network tab)

**Fix**: Reload page, check console for errors

### Issue: History not loading
**Check**:
1. User has session? (Check `/api/v1/session/info`)
2. API endpoint accessible? (Check `/api/v1/history/viewed`)
3. Database migration ran? (Check `alembic current`)

**Fix**: Restart server, run migration

### Issue: Slugs not unique
**Check**:
1. Migration created unique index?
2. Slug generation working? (Check `app/utils/slug.py`)
3. Existing content has slugs? (Query database)

**Fix**: Run `UPDATE content_items SET slug = 'content-' || id WHERE slug IS NULL`

## Future Enhancements

### Planned Features
- [ ] Time-based history expiration (auto-clear after 30 days)
- [ ] Export history as JSON/CSV
- [ ] Search within history
- [ ] Filter by date range
- [ ] Analytics dashboard (most viewed categories, time of day patterns)
- [ ] Share history collections with other users
- [ ] "Read later" list (separate from history)
- [ ] Reading progress tracking (for long articles)

### Performance Improvements
- [ ] Redis cache for frequently accessed seen IDs
- [ ] Batch history recording (reduce API calls)
- [ ] IndexedDB for offline history sync
- [ ] Lazy load history in chunks

## Related Documentation

- [HOVER_TRACKING_README.md](./HOVER_TRACKING_README.md) - Interest detection system
- [ADMIN_PANEL_README.md](./ADMIN_PANEL_README.md) - Admin interface
- [INFINITE_FEED_README.md](./INFINITE_FEED_README.md) - Feed pagination system

## Files Modified/Created

### Backend
- ✅ `alembic/versions/003_add_content_view_history.py` - Database migration
- ✅ `app/models/user.py` - ContentViewHistory model
- ✅ `app/models/content.py` - Added slug field
- ✅ `app/api/v1/routes/history.py` - History API endpoints
- ✅ `app/services/content_recommendation.py` - Duplicate prevention
- ✅ `app/utils/slug.py` - Slug generation utility
- ✅ `app/main.py` - Added history routes

### Frontend
- ✅ `app/static/js/history-tracker.js` - Tracking client
- ✅ `app/static/js/feed.js` - Integration with feed
- ✅ `app/static/history.html` - History viewer UI
- ✅ `app/static/index.html` - Added history link and script

## Deployment Status

✅ **Deployed to Production**: November 21, 2025
- Server: nexus.comdat.ca
- Database migration: Completed (003)
- All endpoints: Active
- History viewer: Accessible at `/history.html`
