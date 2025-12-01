# Google Analytics Troubleshooting Guide

## Problem: GA Events Not Showing Up (Cache Issue)

### Root Cause
The nginx server is serving old JavaScript files from November 21st due to 30-day cache headers:
```nginx
location /static/js/ {
    expires 30d;  # ← Browser caches for 30 days!
    add_header Cache-Control "public, no-transform";
}
```

### Solution: Cache-Busting Version Parameters

We've updated all JS and CSS files to use version parameter `v=202512010100`:

**Updated Files:**
- `/static/js/header.js?v=202512010100`
- `/static/js/hover-tracker.js?v=202512010100`
- `/static/js/history-tracker.js?v=202512010100`
- `/static/js/feed.js?v=202512010100` ← **This one has the GA tracking code!**
- `/static/js/auth.js?v=202512010100`
- `/static/js/feed-notifier.js?v=202512010100`

## Deployment Steps

### 1. Commit and Push Changes (Local Machine)
```bash
git add app/templates/base.html app/templates/index.html
git commit -m "fix: Update cache-busting version parameters for GA analytics (Dec 1)"
git push origin main
```

### 2. Deploy to Production Server
```bash
# SSH into server
ssh nexus@nexus.comdat.ca

# Run deployment script
cd /home/nexus/nexus
git pull origin main
sudo systemctl restart nexus

# Verify service is running
sudo systemctl status nexus
```

### 3. Clear Browser Cache (CRITICAL!)

**Option A: Hard Refresh (Recommended)**
- Windows/Linux: `Ctrl + F5` or `Ctrl + Shift + R`
- Mac: `Cmd + Shift + R`

**Option B: DevTools Cache Clear**
1. Open DevTools (F12)
2. Right-click the Refresh button
3. Select "Empty Cache and Hard Reload"

**Option C: Manual Cache Clear**
1. Browser Settings → Privacy → Clear browsing data
2. Select "Cached images and files"
3. Clear data

## Testing GA Events

### 1. Open Browser DevTools
Press `F12` and go to Console tab

### 2. Check if GA is Loaded
Look for these in console:
```javascript
// Good: No errors
// Bad: "gtag is not defined" or "dataLayer is not defined"
```

### 3. Verify JS File Version
1. Go to Network tab
2. Filter by "feed.js"
3. Check the URL includes `?v=202512010100`
4. If it shows `?v=202511210100` → Cache not cleared!

### 4. Trigger Events Manually
Open Console and type:
```javascript
// Test if gtag is available
typeof gtag
// Should return: "function"

// Trigger test event
gtag('event', 'test_event', {
    'test_param': 'test_value'
});
```

### 5. Test Real Events

**Event 1: `article_open`**
- Click any article card to open the modal
- Should fire immediately when modal opens

**Event 2: `article_read`**
- Keep the article modal open for 10+ seconds
- Should fire once after 10 seconds

**Event 3: `article_read_complete`**
- Scroll 80% of the way through an article
- Should fire when you reach 80% scroll

**Event 4: `filter_category`**
- Click any category filter button at the top
- Should fire immediately

### 6. Verify in GA4 Realtime Reports

1. Go to: https://analytics.google.com/
2. Select Nexus property (G-NCNEQG70WC)
3. Go to Reports → Realtime
4. Look for events appearing in the last 30 minutes
5. Check event names: `article_open`, `article_read`, `filter_category`

### 7. Check DebugView (Advanced)

1. Install [Google Analytics Debugger](https://chrome.google.com/webstore/detail/google-analytics-debugger/) Chrome extension
2. Enable the extension
3. Refresh the page
4. Go to GA4 → Configure → DebugView
5. Look for your events in real-time with full parameters

## Common Issues & Solutions

### Issue 1: "gtag is not defined"
**Cause:** Google Analytics tag not loading
**Solution:** 
- Check base.html has the GA tag in `<head>`
- Verify no ad blockers are active
- Check Network tab for `gtag/js?id=G-NCNEQG70WC`

### Issue 2: Old JS file still loading
**Cause:** Browser cache not cleared
**Solution:**
- Do a HARD refresh (Ctrl+F5)
- Or clear all browser cache
- Verify in Network tab that `feed.js?v=202512010100` loads

### Issue 3: Events not appearing in GA4
**Cause:** May take 1-2 minutes to appear
**Solution:**
- Wait 2-3 minutes
- Try DebugView instead of Realtime (instant)
- Check browser console for JavaScript errors

### Issue 4: "Failed to load resource: net::ERR_BLOCKED_BY_CLIENT"
**Cause:** Ad blocker blocking GA
**Solution:**
- Disable ad blocker temporarily for testing
- Or test in Incognito mode without extensions

### Issue 5: Service not restarting on server
**Cause:** systemd service issue
**Solution:**
```bash
# Check service status
sudo systemctl status nexus

# Check logs
sudo journalctl -u nexus -f

# Force restart
sudo systemctl stop nexus
sudo systemctl start nexus
```

## Event Implementation Details

### Location in Code: `app/static/js/feed.js`

```javascript
// Event 1: article_open (line ~666)
if (typeof gtag !== 'undefined') {
    gtag('event', 'article_open', {
        'article_title': item.title,
        'article_category': item.category || 'Unknown',
        'article_id': item.content_id
    });
}

// Event 2: article_read (line ~674)
setTimeout(() => {
    if (!readTracked && typeof gtag !== 'undefined') {
        gtag('event', 'article_read', {
            'article_title': item.title,
            'article_category': item.category || 'Unknown',
            'article_id': item.content_id,
            'read_duration': 10
        });
        readTracked = true;
    }
}, 10000);

// Event 3: article_read_complete (line ~690)
if (scrollPercentage >= 80 && typeof gtag !== 'undefined') {
    gtag('event', 'article_read_complete', {
        'article_title': item.title,
        'article_category': item.category || 'Unknown',
        'article_id': item.content_id,
        'scroll_percentage': scrollPercentage
    });
}

// Event 4: filter_category (line ~172 in index.html)
gtag('event', 'filter_category', {
    'category': category,
    'event_label': category
});
```

## Quick Test Checklist

- [ ] Git pull on server completed
- [ ] Service restarted successfully
- [ ] Browser cache cleared (hard refresh)
- [ ] Network tab shows `feed.js?v=202512010100`
- [ ] Console shows no "gtag is not defined" errors
- [ ] Clicked an article (article_open)
- [ ] Waited 10+ seconds (article_read)
- [ ] Scrolled 80% (article_read_complete)
- [ ] Clicked category filter (filter_category)
- [ ] Events appear in GA4 Realtime or DebugView

## Success Criteria

✅ All 4 event types appear in GA4 Realtime reports
✅ Events include correct parameters (title, category, etc.)
✅ No JavaScript errors in browser console
✅ Network tab shows correct version parameters

---

**Last Updated:** December 1, 2025
**Fixed By:** Cache-busting version parameter update

