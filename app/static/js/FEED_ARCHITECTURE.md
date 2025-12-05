# Feed System Architecture

## Overview

The feed system has been refactored from a monolithic `feed.js` (~1200 lines) into modular, single-responsibility components. This improves maintainability, testability, and reusability.

## Module Structure

### 1. **FeedUtils.js**
**Purpose**: Shared utility functions used across the system

**Exports**:
- `cleanSnippet(html)` - Remove images/figures from HTML, extract text
- `truncateText(text, maxLength)` - Truncate text with ellipsis
- `formatTime(isoString)` - Format timestamps relative to now (e.g., "5m ago")
- `buildProxyUrl(url)` - Build image proxy URL
- `extractDominantColor(img, card)` - Extract average color from image canvas
- `getSourceButtonText(item)` - Determine button text (Search/View Source/View Trends)
- `getSourceButtonTextForUrl(url, tags)` - Same as above but with direct URL
- `isSearchQuery(item)` - Check if item is a search query
- `isNewsArticle(item)` - Check if item is a news article

**Usage**: Static utility class, called from other modules

---

### 2. **FeedApi.js**
**Purpose**: All API communication and data fetching

**Exports**:
- Constructor: `FeedApi()`
- Methods:
  - `getAccessToken()` - Extract JWT from cookie/localStorage
  - `getHeaders()` - Build auth headers
  - `fetchUserSettings()` - Get user debug mode setting
  - `fetchFeed(page, pageSize, filters)` - Fetch personalized/trending feed
  - `fetchSnippet(contentId)` - Fetch article snippet
  - `fetchRelated(contentId)` - Fetch related articles
  - `fetchThumbnail(contentId)` - Fetch article thumbnail
  - `fetchArticle(contentId)` - Fetch full article content
  - `trackView(contentId)` - Track article view

**Responsibility**: Single point of API configuration. Easy to swap endpoints or add retry logic.

---

### 3. **FeedTracking.js**
**Purpose**: All analytics and interest tracking

**Exports**:
- Constructor: `FeedTracking()`
- Methods:
  - `initGlobalScrollTracker()` - Initialize scroll tracking
  - `createHoverTracker(card, contentId)` - Create tracker for a card
  - `cleanupTracker(contentId)` - Clean up hover tracker
  - `cleanupAllTrackers()` - Clean up all trackers
  - `startViewTimer(contentId)` - Start timing content view
  - `stopViewTimer(contentId)` - Stop timer and calculate duration
  - `stopAllViewTimers()` - Stop all active timers on unload
  - `reportHoverTracker(contentId)` - Force hover report
  - `destroy()` - Clean up all tracking

**Responsibility**: Isolates telemetry from UI code. Easier to modify analytics without touching rendering.

---

### 4. **FeedObservers.js**
**Purpose**: All IntersectionObserver setup and event wiring

**Exports**:
- Constructor: `FeedObservers(feed)`
- Methods:
  - `setupScrollObserver(loadingIndicator)` - Infinite scroll trigger
  - `setupCardObserver()` - Card visibility tracking
  - `observeCard(card)` - Observe a card
  - `unobserveCard(card)` - Stop observing a card
  - `setupScrollRefresh()` - TikTok-style scroll-to-refresh
  - `destroy()` - Disconnect all observers

**Responsibility**: Event handling and observation setup. Keeps complex intersection logic separate.

---

### 5. **FeedRenderer.js**
**Purpose**: DOM creation and rendering

**Exports**:
- Constructor: `FeedRenderer(api, tracking)`
- Methods:
  - `renderContentItem(item, container, onContentClick)` - Render feed card
  - `buildImageHtml(item)` - Build image element with fallbacks
  - `setupCardEventHandlers(article, item, ...)` - Wire up click handlers
  - `loadSnippet(article, item)` - Fetch and display snippet on expand
  - `loadRelatedContent(article, item)` - Fetch and display related stories
  - `setupCardImage(article, item)` - Fetch thumbnail and extract color
  - `insertAdUnit(container)` - Insert AdSense ad
  - `renderArticleRelatedItems(items, container)` - Render related items in modal
  - `renderLoadingIndicator()` - Create loading UI
  - `renderEndMessage()` - Create "end of feed" UI
  - `renderErrorMessage(message)` - Create error UI

**Responsibility**: All DOM manipulation and HTML generation. Easy to refactor templates without touching logic.

---

### 6. **FeedArticleModal.js**
**Purpose**: Article modal display and interactions

**Exports**:
- Constructor: `FeedArticleModal(api)`
- Methods:
  - `openArticleModal(item, isSearchQuery)` - Open modal and fetch article
  - `renderRelatedItems(items, container)` - Render related items
  - `setupModalControls()` - Wire up close buttons and escape key

**Responsibility**: Modal-specific code isolated from feed logic. Easy to reuse in other contexts.

---

### 7. **InfiniteFeed.js**
**Purpose**: Core feed orchestrator - ties everything together

**Exports**:
- Constructor: `InfiniteFeed(containerId, options)`
- Properties:
  - `api`, `tracking`, `renderer`, `observers`, `modal` - Module instances
  - `currentPage`, `pageSize`, `category`, `categories` - Feed state
  - `isLoading`, `hasMore`, `viewedContentIds`, `cursor` - Pagination state
- Methods:
  - `init()` - Initialize all modules
  - `loadMore()` - Fetch and render next page
  - `renderContentItem(item)` - Delegate to renderer
  - `refreshFeed(keepCount)` - TikTok-style refresh
  - `defaultContentClick(item)` - Handle card click
  - `reset()`, `setCategory()`, `setCategories()`, `destroy()` - Public API

**Responsibility**: Orchestration only. No rendering, API calls, or tracking logic. Just coordinates modules.

---

## Benefits of Modular Architecture

| Aspect | Monolithic | Modular |
|--------|-----------|---------|
| **File Size** | ~1200 lines | 150-300 lines each |
| **Testability** | Difficult - tight coupling | Easy - each module independently testable |
| **Reusability** | Hard to extract pieces | FeedApi/FeedRenderer/FeedArticleModal reusable |
| **Maintainability** | Change one thing, understand all | Change tracking? Only touch FeedTracking.js |
| **API Changes** | Modify multiple methods | Modify one module (FeedApi) |
| **Template Updates** | Mixed with logic | Isolated in FeedRenderer.renderContentItem() |
| **Analytics Changes** | Search entire file | Isolated in FeedTracking.js |

---

## Usage in HTML

```html
<!-- Load modules in order -->
<script src="/static/js/FeedUtils.js"></script>
<script src="/static/js/FeedApi.js"></script>
<script src="/static/js/FeedTracking.js"></script>
<script src="/static/js/FeedObservers.js"></script>
<script src="/static/js/FeedRenderer.js"></script>
<script src="/static/js/FeedArticleModal.js"></script>
<script src="/static/js/InfiniteFeed.js"></script>

<!-- Use as before -->
<div id="feed-container"></div>
<script>
    const feed = new InfiniteFeed('feed-container', {
        pageSize: 20,
        isPersonalized: true,
        onContentClick: (item) => console.log('Clicked:', item)
    });
</script>
```

---

## API Changes: Before and After

### Before (Monolithic)
```javascript
class InfiniteFeed {
    async fetchUserSettings() { ... }
    async fetchFeed() { ... }
    async fetchSnippet() { ... }
    cleanSnippet() { ... }
    formatTime() { ... }
    // ... 100+ more methods
}
```

### After (Modular)
```javascript
// If you need to change API endpoint:
class CustomFeedApi extends FeedApi {
    async fetchFeed(page, pageSize, filters) {
        // Custom endpoint
        return fetch(`/custom/api/feed?...`).then(r => r.json());
    }
}

const feed = new InfiniteFeed('container', {});
feed.api = new CustomFeedApi(); // Swap in custom API
```

---

## Extending the System

### Example: Add custom tracking
```javascript
class CustomTracking extends FeedTracking {
    async sendDuration(contentId, duration) {
        await fetch('/custom/analytics', {
            method: 'POST',
            body: JSON.stringify({ contentId, duration })
        });
    }
}

const feed = new InfiniteFeed('container', {});
feed.tracking = new CustomTracking();
```

### Example: Change card rendering
```javascript
class CustomRenderer extends FeedRenderer {
    renderContentItem(item, container) {
        // Custom HTML structure
        const card = document.createElement('div');
        card.className = 'custom-card';
        card.innerHTML = `<h3>${item.title}</h3>...`;
        container.appendChild(card);
    }
}

const feed = new InfiniteFeed('container', {});
feed.renderer = new CustomRenderer(feed.api, feed.tracking);
```

---

## Testing

Each module can now be unit tested independently:

```javascript
// Test FeedUtils
describe('FeedUtils', () => {
    it('should format time correctly', () => {
        const now = new Date();
        const fiveMinutesAgo = new Date(now - 5 * 60 * 1000);
        expect(FeedUtils.formatTime(fiveMinutesAgo)).toBe('5m ago');
    });
});

// Test FeedApi (mock fetch)
describe('FeedApi', () => {
    it('should fetch feed', async () => {
        global.fetch = jest.fn(() => 
            Promise.resolve({ ok: true, json: () => ({ items: [] }) })
        );
        const api = new FeedApi();
        const data = await api.fetchFeed(1, 20);
        expect(data.items).toBeDefined();
    });
});

// Test FeedTracking (no DOM needed)
describe('FeedTracking', () => {
    it('should track view duration', () => {
        const tracking = new FeedTracking();
        tracking.startViewTimer(123);
        tracking.stopViewTimer(123);
        expect(tracking.viewDurations.get(123)).toBeGreaterThanOrEqual(0);
    });
});
```

---

## Migration Guide

If you have code using the old monolithic feed.js:

```javascript
// Old way (still works - just use InfiniteFeed.js instead of feed.js)
// <script src="/static/js/feed.js"></script>
// const feed = new InfiniteFeed('container');

// New way (recommended)
// <script src="/static/js/FeedUtils.js"></script>
// <script src="/static/js/FeedApi.js"></script>
// ... load all 7 modules
// const feed = new InfiniteFeed('container');
```

The API is identical - no code changes needed!

---

## Future Improvements

With modular architecture, you can now easily:

1. **Add caching layer** - Create `CachedFeedApi extends FeedApi`
2. **Add error recovery** - Create `ResilientFeedApi extends FeedApi` with retry logic
3. **Switch analytics** - Replace FeedTracking with custom implementation
4. **Add virtual scrolling** - Create `VirtualFeedObservers extends FeedObservers`
5. **Add different card styles** - Create alternative renderers for desktop/mobile
6. **Migrate to different modal system** - Swap FeedArticleModal implementation
7. **Unit test everything** - Each module testable in isolation
