# AI Content Recommendation System

## Overview

Nexus uses an intelligent recommendation system to learn what users like to read and automatically discover relevant content from RSS feeds and trending sources.

## How It Works

### 1. **User Preference Analysis**

The system tracks user behavior to understand reading preferences:

- **Categories**: Tracks which categories users read most (Sports, Technology, Entertainment, etc.)
- **Keywords**: Identifies common themes in content users engage with
- **Reading Duration**: Measures how long users spend reading different content
- **Content Types**: Learns whether users prefer news updates, trending analysis, or other formats
- **Interaction Patterns**: Analyzes clicks, views, and engagement over the last 30 days

### 2. **RSS Feed Discovery**

Based on learned preferences, the system discovers relevant RSS feeds:

#### Curated Feed Database
We maintain a curated list of high-quality RSS feeds organized by category:
- **Technology**: TechCrunch, The Verge, Wired, Ars Technica, CNET
- **Business**: Bloomberg, CNBC, Forbes, Reuters
- **Sports**: ESPN, Sportsnet, CBC Sports
- **Entertainment**: Variety, Hollywood Reporter, Rolling Stone
- **Politics**: Politico, CBC Politics, Globe and Mail
- **Health**: Health.com, CBC Health, NPR Health
- **Science**: Science Daily, Scientific American, Space.com
- **World News**: BBC, Al Jazeera, CBC World

#### Automatic Feed Discovery (NEW!)
The system automatically searches for new RSS feeds based on your interests:

**Discovery Strategies:**
1. **Common RSS Patterns**: Searches FeedBurner, Reddit, Medium for feeds
2. **Google News RSS**: Creates custom Google News feeds for your topics
3. **Keyword-Based Search**: Uses your top keywords to find relevant feeds
4. **Category Matching**: Searches feeds in your preferred categories

**Feed Quality Scoring:**
Every discovered feed is scored (0-1) based on:
- **Update Frequency**: How recent the latest posts are (20% weight)
- **Content Quality**: Length and substance of articles (15% weight)
- **Feed Size**: Number of available entries (10% weight)
- **Metadata**: Completeness of feed information (10% weight)

Feeds with scores > 0.7 are considered high-quality and recommended to users.

#### Smart Matching
The system matches users to feeds based on:
1. **Category Alignment**: Prioritizes feeds in user's top 3-5 categories
2. **Relevance Scoring**: Assigns scores (0-1) based on match quality
3. **Explicit Interests**: Uses user profile interests if available
4. **Usage Patterns**: Adapts to changing preferences over time
5. **Automatic Discovery**: Finds new feeds as your interests evolve

### 3. **Content Aggregation**

The system fetches and aggregates content from multiple sources:

1. **Parallel Fetching**: Retrieves content from top 10 relevant feeds simultaneously
2. **Parsing & Extraction**: Extracts title, description, URL, author, tags, and publish date
3. **Relevance Sorting**: Orders content by relevance score
4. **Deduplication**: Removes duplicate articles across feeds

### 4. **Personalized Feed Generation**

The main feed combines:
- **Trending Content**: From Google Trends, Reddit, PyTrends
- **RSS Feed Content**: From personalized feed discovery
- **Category-Based Content**: Filtered by user preferences
- **Recency Bonus**: Prioritizes fresh content (< 24 hours old)

#### Relevance Scoring Algorithm

Each content item receives a relevance score (0-1) based on:
```
Base Score: 0.5
+ Category Match: +0.3 (higher for top categories)
+ Interest Match: +0.2 (keywords in title/description)
+ Tag Match: +0.1 (matching user interests)
+ Recency Bonus: +0.1 (for content < 24 hours old)
= Final Relevance Score (max 1.0)
```

## API Endpoints

### Analyze User Preferences
```
GET /api/content/preferences/analyze
```
Returns user's reading patterns, top categories, and keywords.

**Response:**
```json
{
  "top_categories": ["Technology", "Business", "Sports"],
  "keywords": ["ai", "startup", "hockey", "innovation"],
  "avg_reading_duration": 120,
  "content_type_preferences": {
    "news_update": 15,
    "trending_analysis": 8
  },
  "total_interactions": 23
}
```

### Discover RSS Feeds
```
GET /api/content/rss/discover
```
Returns personalized RSS feed recommendations.

**Response:**
```json
{
  "feeds": [
    {
      "url": "https://techcrunch.com/feed/",
      "category": "Technology",
      "relevance_score": 1.0,
      "source": "curated"
    },
    ...
  ],
  "count": 15
}
```

### Get RSS Content
```
GET /api/content/rss/content?max_items=20
```
Returns aggregated content from personalized RSS feeds.

**Response:**
```json
{
  "items": [
    {
      "title": "Article Title",
      "description": "Article summary...",
      "url": "https://...",
      "published": "2025-12-02T12:00:00",
      "author": "Author Name",
      "tags": ["tech", "ai"],
      "category": "Technology",
      "relevance_score": 0.95
    },
    ...
  ],
  "count": 20
}
```

### Get Topic Suggestions
```
GET /api/content/suggestions/topics
```
Returns topic keywords for search/exploration based on user history.

**Response:**
```json
{
  "suggestions": [
    "technology",
    "artificial intelligence",
    "startup",
    "innovation",
    "machine learning"
  ]
}
```

### Search RSS Feeds by Keyword
```
GET /api/content/rss/search?keyword=<term>&max_results=5
```
Search for RSS feeds matching a keyword using multiple discovery strategies.

**Response:**
```json
{
  "keyword": "artificial intelligence",
  "feeds": [
    {
      "url": "https://medium.com/feed/tag/artificial-intelligence",
      "title": "Artificial Intelligence on Medium",
      "description": "Latest stories tagged with...",
      "quality_score": 0.95,
      "total_entries": 10,
      "last_updated": "Wed, 03 Dec 2025 02:14:25 GMT",
      "language": "en"
    }
  ],
  "count": 1
}
```

### Auto-Discover Feeds
```
GET /api/content/rss/auto-discover?max_feeds=10
```
Automatically discover new RSS feeds based on user's reading preferences.
Searches for feeds matching user's top keywords and categories.

**Response:**
```json
{
  "discovered_feeds": [
    {
      "url": "https://news.google.com/rss/search?q=technology&hl=en-CA",
      "title": "\"technology\" - Google News",
      "quality_score": 1.0,
      "total_entries": 100,
      "last_updated": "Wed, 03 Dec 2025 02:23:35 GMT"
    }
  ],
  "count": 5,
  "message": "Discovered 5 new feeds based on your preferences"
}
```

## Privacy & Data

- **Anonymous Tracking**: Works for both logged-in users and anonymous visitors via session tokens
- **30-Day Window**: Only analyzes last 30 days of interaction history
- **No External Sharing**: All preference data stays within Nexus
- **User Control**: Users can clear history and preferences at any time

## Future Enhancements

1. **Advanced ML Models**: Train ML models on user behavior for better predictions
2. **Collaborative Filtering**: "Users like you also read..." recommendations
3. **Topic Modeling**: Use NLP to discover hidden topics in user preferences
4. **Real-time Updates**: WebSocket-based live content updates
5. **Content Embeddings**: Use semantic similarity for better matching
6. **A/B Testing**: Test different recommendation algorithms
7. **Feed Quality Monitoring**: Continuous monitoring and removal of low-quality feeds
8. **User Feedback Loop**: Allow users to rate discovered feeds
9. **Multi-language Support**: Discover feeds in user's preferred language

## Technical Stack

- **Language**: Python 3.11+ (async/await)
- **Framework**: FastAPI
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Feed Parsing**: `feedparser` library
- **HTTP Client**: `aiohttp` for async requests
- **Analysis**: Custom algorithms with Counter/statistics

## Performance

- **Feed Discovery**: < 100ms (cached curated list)
- **Preference Analysis**: < 200ms (optimized SQL queries)
- **RSS Content Fetch**: 2-5s (parallel fetching from 10 feeds)
- **Relevance Scoring**: < 50ms per item

## Example User Journey

1. **New User** → Gets default feeds (Tech, Business, Sports)
2. **Clicks on AI article** → System notes interest in Technology + "ai" keyword
3. **Reads 3 more tech articles** → Technology becomes top category
4. **Next visit** → Feed prioritizes tech RSS feeds (TechCrunch, Wired, etc.)
5. **Discovers startup article** → System adds "startup" to keywords
6. **Ongoing** → Feed continuously adapts to evolving interests
