# Expanded RSS Feed Options for Nexus

## Current Status
- **Google Trends Canada RSS**: 10-20 items
- **Reddit JSON API**: Currently blocked (403 errors)

## Recommended RSS Feed Additions

### Canadian News Sources

#### National News
- **CBC News**: https://www.cbc.ca/cmlink/rss-topstories
- **CBC Canada**: https://www.cbc.ca/cmlink/rss-canada
- **Global News**: https://globalnews.ca/feed/
- **CTV News**: https://www.ctvnews.ca/rss/ctvnews-ca-top-stories-public-rss-1.822009
- **The Globe and Mail**: https://www.theglobeandmail.com/arc/outboundfeeds/rss/
- **National Post**: https://nationalpost.com/feed/

#### Regional Coverage
- **Toronto Star**: https://www.thestar.com/feed/
- **The Vancouver Sun**: https://vancouversun.com/feed/
- **Montreal Gazette**: https://montrealgazette.com/feed/

### Sports (Canadian Focus)
- **TSN**: https://www.tsn.ca/rss
- **Sportsnet**: https://www.sportsnet.ca/feed/
- **The Athletic Canada**: (Requires subscription)
- **NHL.com**: https://www.nhl.com/news/rss

### Technology & Business
- **BetaKit** (Canadian tech): https://betakit.com/feed/
- **IT World Canada**: https://www.itworldcanada.com/feed
- **Financial Post**: https://business.financialpost.com/feed/

### Entertainment
- **Entertainment Tonight Canada**: (Check for RSS)
- **Variety**: https://variety.com/feed/
- **Hollywood Reporter**: https://www.hollywoodreporter.com/feed/

### International (For diversity)
- **BBC News**: https://feeds.bbci.co.uk/news/rss.xml
- **Reuters**: https://www.reutersagency.com/feed/
- **Associated Press**: https://apnews.com/apf-topnews

## Implementation Strategy

### Option 1: Add Multiple RSS Feeds
```python
self.rss_feeds = {
    'google_trends': 'https://trends.google.com/trending/rss?geo=CA',
    'cbc_top': 'https://www.cbc.ca/cmlink/rss-topstories',
    'cbc_canada': 'https://www.cbc.ca/cmlink/rss-canada',
    'global_news': 'https://globalnews.ca/feed/',
    'tsn': 'https://www.tsn.ca/rss',
    'betakit': 'https://betakit.com/feed/',
}
```

### Option 2: Category-Specific Feeds
```python
self.feeds_by_category = {
    'News': ['CBC', 'Global News', 'CTV'],
    'Sports': ['TSN', 'Sportsnet', 'NHL'],
    'Tech': ['BetaKit', 'IT World Canada'],
    'Entertainment': ['Variety', 'Hollywood Reporter']
}
```

### Option 3: Weighted/Priority System
- Google Trends (High priority - trending)
- Canadian national news (Medium priority - reliable)
- Specialized feeds (Lower priority - niche)

## Benefits
1. **More Content**: 100-300+ items per fetch instead of 10-20
2. **Better Coverage**: Balanced mix of trending + news + specialized
3. **Reduced Duplicates**: More diverse sources = less repetition
4. **Category Accuracy**: Source-specific feeds naturally categorize
5. **Reddit Backup**: If Reddit API fails, still have plenty of content

## Considerations
- **Rate Limiting**: Add delays between feed fetches
- **Deduplication**: More sources = more duplicate checking needed
- **Storage**: More content = larger database
- **Processing Time**: Will take longer to fetch all feeds
- **Maintenance**: Some feeds may change/break over time

## Next Steps
1. Add 5-10 major Canadian RSS feeds
2. Test fetch speed and duplicate handling
3. Monitor database growth
4. Fine-tune which feeds provide best content
5. Consider adding feed-specific categorization hints
