# Google Analytics 4 - Event Configuration Guide

This guide shows you how to configure your custom events in GA4 to mark them as conversions and add descriptions.

---

## Events to Configure

We have 4 custom events that need to be configured in GA4:

1. **`article_open`** - User opens an article in the modal
2. **`article_read`** - User spends 10+ seconds reading an article
3. **`filter_category`** - User clicks a category filter button
4. **`article_read_complete`** - User scrolls 80% through article content (not yet implemented)

---

## Step-by-Step Configuration

### 1. Navigate to Events Configuration

1. Log in to https://analytics.google.com/
2. Select your **Nexus** property (Property ID: `G-NCNEQG70WC`)
3. Click **Configure** (gear icon) in the left sidebar
4. Click **Events** under "Data display"

### 2. View Your Custom Events

You should see all your events listed, including:
- `page_view` (automatic)
- `scroll` (automatic)
- `article_open` (custom)
- `article_read` (custom)
- `filter_category` (custom)

### 3. Mark Events as Conversions

For each important event, you should mark it as a conversion:

#### Mark `article_open` as Conversion
1. Find **`article_open`** in the events list
2. Toggle the **"Mark as conversion"** switch to **ON**
3. This tracks how many articles users are opening

#### Mark `article_read` as Conversion (MOST IMPORTANT)
1. Find **`article_read`** in the events list
2. Toggle the **"Mark as conversion"** switch to **ON**
3. This is your key engagement metric - users who spend 10+ seconds reading

#### Optional: Mark `filter_category` as Conversion
1. Find **`filter_category`** in the events list
2. Toggle the **"Mark as conversion"** switch to **ON** (optional)
3. This tracks category exploration behavior

---

## Event Details Reference

### Event: `article_open`
**Description**: Tracks when a user opens an article modal to read content

**Parameters:**
- `article_title` (string): Title of the article opened
- `article_category` (string): Category of the article (e.g., "General", "Trending")
- `article_id` (number): Unique content ID

**When it fires:** Immediately when user clicks "Read Full Article" button

**Business value:** Shows initial interest in content

---

### Event: `article_read`
**Description**: Tracks engaged readers who spend 10+ seconds viewing an article

**Parameters:**
- `article_title` (string): Title of the article
- `article_category` (string): Category of the article
- `article_id` (number): Unique content ID
- `engagement_time_seconds` (number): Always 10 (minimum engagement threshold)

**When it fires:** After 10 seconds of article modal being open

**Business value:** PRIMARY engagement metric - shows genuine reader interest

**💡 Recommended:** Mark as conversion and use in key metrics

---

### Event: `filter_category`
**Description**: Tracks when users filter content by category

**Parameters:**
- `category` (string): Category name selected (e.g., "Trending", "General")
- `event_label` (string): Same as category (for compatibility)

**When it fires:** When user clicks any category filter button

**Business value:** Shows user exploration patterns and category preferences

---

### Event: `article_read_complete` (Not Yet Implemented)
**Description**: Will track when users scroll 80% through article content

**Parameters (planned):**
- `article_title` (string): Title of the article
- `article_category` (string): Category of the article
- `article_id` (number): Unique content ID
- `scroll_percentage` (number): Percentage scrolled (≥80)

**When it will fire:** When user scrolls to 80% of article body content

**Business value:** Shows deep engagement and content completeness

---

## Creating Custom Dimensions (Optional)

If you want to analyze events by article properties, create custom dimensions:

### Navigate to Custom Definitions
1. **Configure** → **Custom definitions**
2. Click **Create custom dimension**

### Dimension 1: Article Category
- **Dimension name:** Article Category
- **Scope:** Event
- **Event parameter:** `article_category`
- **Description:** Category of the article being viewed

### Dimension 2: Article Title
- **Dimension name:** Article Title
- **Scope:** Event
- **Event parameter:** `article_title`
- **Description:** Title of the article being viewed

### Dimension 3: Article ID
- **Dimension name:** Article ID
- **Scope:** Event
- **Event parameter:** `article_id`
- **Description:** Unique ID of the article

---

## Setting Up Custom Reports

### Report 1: Article Engagement Funnel

**Purpose:** See the conversion from article opens to reads

1. Go to **Explore** → **Blank**
2. Add dimensions:
   - Event name
   - Article Category (custom dimension)
3. Add metrics:
   - Event count
   - Conversions
4. Visualization: Bar chart or funnel

**Expected results:**
- `article_open`: Total articles opened
- `article_read`: Articles read for 10+ seconds
- Calculate conversion rate: (article_read / article_open) × 100

### Report 2: Top Articles by Engagement

**Purpose:** See which articles get the most engagement

1. Go to **Explore** → **Blank**
2. Add dimensions:
   - Article Title (custom dimension)
   - Article Category (custom dimension)
3. Add metrics:
   - `article_open` (count)
   - `article_read` (count)
   - Conversion rate
4. Visualization: Table
5. Sort by: `article_read` (descending)

### Report 3: Category Performance

**Purpose:** See which categories drive the most engagement

1. Go to **Explore** → **Blank**
2. Add dimension:
   - Category (from `filter_category` event)
3. Add metrics:
   - Event count
   - Unique users
4. Visualization: Pie chart or bar chart

---

## Goals & Conversion Targets

### Suggested Conversion Goals:

1. **Primary Goal: Article Engagement**
   - Conversion event: `article_read`
   - Target: Increase by 20% month-over-month
   - Why: Shows genuine content engagement

2. **Secondary Goal: Content Discovery**
   - Conversion event: `article_open`
   - Target: 100+ per day
   - Why: Shows content is appealing

3. **Tertiary Goal: Category Exploration**
   - Conversion event: `filter_category`
   - Target: 50+ per day
   - Why: Shows users are exploring different topics

---

## Monitoring & Alerts

### Set Up Alerts (Optional)

1. Go to **Admin** → **Custom alerts**
2. Create alert for low engagement:
   - **Alert name:** Low Article Engagement
   - **Condition:** `article_read` events < 50 per day
   - **Recipients:** Your email
   - **Frequency:** Daily

---

## Quick Checklist

After logging into GA4, complete these tasks:

- [ ] Navigate to **Configure** → **Events**
- [ ] Mark `article_read` as a **conversion** ✅ (MOST IMPORTANT)
- [ ] Mark `article_open` as a **conversion** ✅
- [ ] Optionally mark `filter_category` as a conversion
- [ ] Create custom dimension for **Article Category**
- [ ] Create custom dimension for **Article Title**
- [ ] Set up **Article Engagement Funnel** report
- [ ] Set up **Top Articles** report
- [ ] Verify events are appearing in **Realtime** reports
- [ ] Check **Conversions** report to see conversion data

---

## Expected Results

Once configured, you should see:

1. **In Realtime Reports:**
   - Events firing in real-time as users interact
   - `article_open`, `article_read`, `filter_category` appearing

2. **In Conversions Report:**
   - `article_read` showing as a conversion
   - Conversion rate trends over time

3. **In Custom Reports:**
   - Article engagement funnel
   - Top performing articles
   - Category performance breakdown

---

## Troubleshooting

**Problem:** Events not showing as conversions
- **Solution:** Make sure you toggled the "Mark as conversion" switch
- **Note:** It may take a few minutes for conversion status to update

**Problem:** Can't find custom dimensions
- **Solution:** Go to **Configure** → **Custom definitions** → Create custom dimensions

**Problem:** Not enough data in reports
- **Solution:** Wait 24-48 hours for data to accumulate; GA4 needs time to collect data

---

**Last Updated:** December 1, 2025
**Property ID:** G-NCNEQG70WC

