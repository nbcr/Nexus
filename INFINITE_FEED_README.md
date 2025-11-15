# Nexus Infinite Scroll Feed System

## Overview

The Nexus platform now features a sophisticated infinite scroll feed system that combines Google Trends data with personalized recommendations to deliver a continuous stream of relevant content to users.

## Architecture

### Components

1. **Content Recommendation Service** (`app/services/content_recommendation.py`)
   - Analyzes user interaction history
   - Calculates relevance scores
   - Provides personalized content recommendations
   - Supports both authenticated and anonymous users

2. **Feed API Endpoints** (`app/api/v1/routes/content.py`)
   - `/api/v1/content/feed` - Personalized feed with user preferences
   - `/api/v1/content/trending-feed` - Pure trending content (non-personalized)

3. **Frontend JavaScript** (`app/static/js/feed.js`)
   - `InfiniteFeed` class handles infinite scroll
   - Intersection Observer API for efficient loading
   - Automatic content tracking and deduplication

4. **Styling** (`app/static/css/feed.css`)
   - Responsive design for mobile and desktop
   - Dark mode support
   - Smooth animations and transitions

## How It Works

### 1. Data Flow

```
Google Trends RSS Feed
    ↓
TrendingService.fetch_canada_trends()
    ↓
Database (Topics & ContentItems with source_metadata)
    ↓
ContentRecommendationService.get_personalized_feed()
    ↓
API Endpoint (/api/v1/content/feed)
    ↓
Frontend InfiniteFeed class
    ↓
User's Browser (Infinite Scroll)
```

### 2. Personalization Algorithm

The system calculates a relevance score for each piece of content based on:

- **Category Matching** (30% weight): Compares content category against user's most-viewed categories
- **Interest Matching** (20% weight): Checks for user interest keywords in title/description
- **Tag Matching** (10% weight): Matches content tags with user interests
- **Recency Bonus** (10% weight): Newer content gets priority
- **Trend Score** (60% weight): Google Trends popularity score

**Final Score Formula:**
```
display_score = (relevance_score × 0.4) + (trend_score × 0.6)
```

### 3. Content Exclusion

The system tracks viewed content to avoid showing duplicates:
- Uses `exclude_ids` parameter to pass already-displayed content IDs
- Maintains `viewedContentIds` Set in frontend
- Queries database to filter out previously viewed items

### 4. Infinite Scroll Mechanism

- Uses Intersection Observer API to detect when user approaches bottom of feed
- Loads next page 200px before reaching the end
- Implements loading states to prevent duplicate requests
- Shows "You've reached the end" message when no more content available

## API Usage

### Get Personalized Feed

```http
GET /api/v1/content/feed?page=1&page_size=20&exclude_ids=1,2,3
```

**Parameters:**
- `page` (int, default: 1): Page number
- `page_size` (int, default: 20, max: 50): Items per page
- `category` (string, optional): Filter by category
- `exclude_ids` (string, optional): Comma-separated list of content IDs to exclude

**Response:**
```json
{
  "page": 1,
  "page_size": 20,
  "items": [
    {
      "content_id": 123,
      "topic_id": 45,
      "title": "Breaking News Story",
      "description": "Story description",
      "category": "Technology",
      "content_type": "news_update",
      "content_text": "Full content text",
      "source_urls": ["https://..."],
      "source_metadata": {
        "source": "CNN",
        "picture_url": "https://...",
        "title": "Article title"
      },
      "trend_score": 0.85,
      "relevance_score": 0.72,
      "created_at": "2025-11-15T12:00:00Z",
      "tags": ["breaking", "tech"]
    }
  ],
  "has_more": true,
  "is_personalized": true
}
```

### Get Trending Feed (Non-Personalized)

```http
GET /api/v1/content/trending-feed?page=1&page_size=20&category=Technology
```

Same parameters and response format as personalized feed, but without relevance scores.

## Frontend Integration

### Basic Setup

```html
<!DOCTYPE html>
<html>
<head>
    <link rel="stylesheet" href="/static/css/feed.css">
</head>
<body>
    <div id="feed-container"></div>
    
    <script src="/static/js/feed.js"></script>
    <script>
        const feed = new InfiniteFeed('feed-container', {
            pageSize: 20,
            isPersonalized: true,
            onContentClick: function(item) {
                // Handle content click
                console.log('Clicked:', item.title);
            }
        });
    </script>
</body>
</html>
```

### Custom Rendering

```javascript
const feed = new InfiniteFeed('feed-container', {
    renderContentItem: function(item) {
        // Custom rendering logic
        const element = document.createElement('div');
        element.innerHTML = `<h2>${item.title}</h2>`;
        this.container.appendChild(element);
    }
});
```

### Category Filtering

```javascript
// Change category dynamically
feed.setCategory('Technology');

// Clear category filter
feed.setCategory(null);

// Reset feed completely
feed.reset();
```

## User Experience Features

### For Anonymous Users
- Session-based tracking via `nexus_session` cookie
- Personalization based on viewing history
- Automatic migration of history upon registration

### For Registered Users
- Full personalization based on:
  - Interaction history
  - Declared interests
  - Preferred categories
  - Reading preferences
- History persists across devices
- More accurate recommendations over time

### Content Diversity
- Every 3rd page shows diverse content (not category-filtered)
- Ensures users discover new topics
- Prevents filter bubbles

## Performance Optimizations

1. **Lazy Loading Images**: All images use `loading="lazy"` attribute
2. **Intersection Observer**: Efficient scroll detection with 200px margin
3. **Database Indexing**: Optimized queries with proper indexes on:
   - `content_items.is_published`
   - `topics.trend_score`
   - `user_interactions.user_id`, `session_id`
4. **Pagination**: Server-side pagination reduces data transfer
5. **Content Deduplication**: Client and server-side exclusion prevents duplicates

## Mobile Responsiveness

The feed automatically adapts to different screen sizes:
- **Desktop**: Full-width images, side-by-side buttons
- **Mobile**: Smaller images, stacked buttons, optimized spacing
- **Touch-friendly**: Larger tap targets for mobile devices

## Dark Mode Support

Automatic dark mode based on system preferences:
```css
@media (prefers-color-scheme: dark) {
    /* Dark mode styles applied automatically */
}
```

## Future Enhancements

1. **Real-time Updates**: WebSocket support for live content updates
2. **AI Summarization**: Generate custom summaries based on user reading level
3. **Collaborative Filtering**: Recommend based on similar users' preferences
4. **Video Content**: Support for trending video content
5. **Bookmark/Save**: Allow users to save stories for later
6. **Share Functionality**: Social sharing integration
7. **Reading Time Estimates**: Show estimated reading time
8. **Content Clustering**: Group related stories together

## Troubleshooting

### Feed Not Loading
- Check browser console for JavaScript errors
- Verify API endpoint is accessible
- Ensure database has content with `is_published=True`

### Personalization Not Working
- Verify user has interaction history
- Check that session cookie is being set
- Ensure `UserInteraction` records are being created

### Images Not Showing
- Verify `source_metadata.picture_url` is valid
- Check CORS settings for external images
- Implement image proxy if needed

## Database Schema Updates

If migrating from an older version, run:

```sql
-- Add source_metadata column to content_items
ALTER TABLE content_items 
ADD COLUMN source_metadata JSON DEFAULT '{}';

-- Add profile fields to user_interest_profiles
ALTER TABLE user_interest_profiles 
ADD COLUMN bio VARCHAR(500),
ADD COLUMN avatar_url VARCHAR(255),
ADD COLUMN social_links JSON DEFAULT '{}',
ADD COLUMN expertise JSON DEFAULT '[]';
```

## Testing

Test the feed with:
```bash
# Start the server
python run_server.py

# Visit the feed page
http://localhost:8000/static/feed.html

# Or use curl to test API
curl "http://localhost:8000/api/v1/content/feed?page=1&page_size=10"
```

## Contributing

When adding new features:
1. Update the recommendation algorithm in `content_recommendation.py`
2. Add new API endpoints in `content.py`
3. Extend frontend functionality in `feed.js`
4. Update styles in `feed.css`
5. Document changes in this README
