# Advanced Hover Interest Tracking System

## Overview

The hover interest tracking system intelligently monitors user engagement with content cards to distinguish between genuine interest and incidental interactions. This sophisticated system helps improve content recommendations by understanding what users actually care about.

## Key Features

### 1. **Smart Hover Detection**
- Tracks when users hover over cards with mouse or touch
- Monitors hover duration and patterns
- Distinguishes between intentional reading and accidental hovering

### 2. **Movement Analysis**
- **Active Reading Detection**: Tracks mouse movement to confirm user is actively engaged
- **Micro-Movement Filtering**: Ignores small movements (<20px) to avoid counting mouse repositioning
- **Velocity Tracking**: Monitors mouse speed to detect slowdowns (user reading carefully)
- **Scroll Velocity**: Tracks scroll speed changes near cards

### 3. **AFK (Away From Keyboard) Detection**
- Detects when user is inactive for >5 seconds
- Applies negative scoring to avoid inflating interest from forgotten tabs
- Resets when movement is detected again

### 4. **Click Tracking**
- Tracks explicit click events as strong interest signals
- Adds significant weight to interest score (+30 points per click)

### 5. **Interest Scoring Algorithm**

The system calculates an interest score (0-100+) based on:

#### Positive Signals:
- **Hover Duration**: +2 points per second (capped at 30s to prevent AFK inflation)
- **Movement Detection**: +10 points (confirms active engagement)
- **Slowdowns**: +5 points each (user reading carefully)
- **Clicks**: +30 points each (strong explicit interest)
- **Scroll Slowdowns**: +3 points each (user slowing down near content)

#### Negative Signals:
- **Excessive Micro-movements**: -5 points (likely just repositioning mouse)
- **AFK Time**: -3 points per second
- **Very Short Hover**: -10 points if <1.5s with no movement (accidental hover)

#### Interest Levels:
- **High Interest** (≥70): Strong engagement, highly relevant content
- **Medium Interest** (50-69): Moderate engagement
- **Low Interest** (<50): Brief or accidental interaction

## Configuration Options

The `HoverTracker` class accepts these configuration options:

```javascript
{
    // Minimum hover time to consider as interest (milliseconds)
    minHoverDuration: 1500,
    
    // Time window for detecting AFK (milliseconds)
    afkThreshold: 5000,
    
    // Movement threshold to consider as "active" (pixels)
    movementThreshold: 5,
    
    // Micro-movement threshold for repositioning (pixels)
    microMovementThreshold: 20,
    
    // Velocity threshold for "slowdown" detection (pixels/ms)
    slowdownVelocityThreshold: 0.3,
    
    // Sample rate for velocity calculation (milliseconds)
    velocitySampleRate: 100,
    
    // Interest score threshold to report as "interested"
    interestScoreThreshold: 50,
    
    // Scroll velocity threshold (pixels/ms)
    scrollSlowdownThreshold: 2.0,
    
    // Show visual feedback during tracking
    showVisualFeedback: true
}
```

## Implementation Details

### Frontend Components

#### 1. **hover-tracker.js**
- `HoverTracker` class: Tracks individual card interactions
- `GlobalScrollTracker` class: Monitors scroll velocity across all cards
- Event listeners for mouse, touch, and scroll events
- Automatic cleanup on viewport exit

#### 2. **feed.js Integration**
- Creates `HoverTracker` instance for each card
- Registers trackers with global scroll tracker
- Reports interest when cards leave viewport
- Cleanup on page unload or feed reset

#### 3. **Visual Feedback (feed.css)**
- Subtle animated border at top of card during tracking
- Optional, can be disabled via configuration
- Uses CSS animations for smooth transitions

### Backend Components

#### 1. **API Endpoint** (`/api/v1/session/track-interest`)
Receives detailed interest data:
```json
{
    "content_id": 123,
    "interest_score": 75,
    "hover_duration_ms": 4500,
    "movement_detected": true,
    "slowdowns_detected": 3,
    "clicks_detected": 1,
    "was_afk": false,
    "trigger": "hover",
    "timestamp": "2025-11-21T12:34:56.789Z"
}
```

#### 2. **Session Service** (`session_service.py`)
- Stores interactions with type: `interest_high`, `interest_medium`, or `interest_low`
- Links to anonymous sessions or registered users
- Logs detailed metadata for future analysis

#### 3. **Database Storage**
- Stores in `user_interactions` table
- Tracks interaction type and duration
- Links to session for anonymous users
- Can be migrated to user account on registration

## Usage Examples

### Basic Usage (Automatic)

The system is automatically initialized when the feed loads:

```javascript
// In feed.js initialization
feed = new InfiniteFeed('feed-container', {
    pageSize: 20,
    isPersonalized: true
});
```

### Manual Tracker Creation

```javascript
// Create tracker for a specific element
const tracker = new HoverTracker(
    document.getElementById('card-123'),
    123,  // content_id
    {
        minHoverDuration: 2000,  // 2 seconds
        interestScoreThreshold: 60,  // Higher threshold
        showVisualFeedback: false  // Disable visual feedback
    }
);

// Get current state for debugging
console.log(tracker.getState());

// Force report interest
tracker.forceReport();

// Cleanup when done
tracker.destroy();
```

### Global Scroll Tracking

```javascript
// Already initialized automatically in feed.js
const globalScrollTracker = new GlobalScrollTracker();

// Register additional trackers
globalScrollTracker.registerTracker(myTracker);

// Cleanup
globalScrollTracker.destroy();
```

## Console Logging

The system provides detailed console logging for debugging:

- `👆 Hover started on card {id}` - User starts hovering
- `🖱️ Click detected on card {id}` - User clicks card
- `🐌 Slowdown detected on card {id}` - User slows down while reading
- `📜 Scroll slowdown detected near card {id}` - User slows scroll near card
- `😴 AFK detected on card {id}` - No movement for >5 seconds
- `👋 Hover ended on card {id}` - Hover ends with full metrics
- `✅ Interest reported for card {id}` - Successfully sent to server

## Mobile Support

The system fully supports mobile devices:
- Touch events (`touchstart`, `touchend`) tracked
- Scroll velocity monitoring works on mobile
- Optimized thresholds for touch interactions
- No visual feedback clutter on small screens

## Performance Considerations

1. **Throttled Updates**: Velocity calculations run every 100ms, not on every mousemove
2. **Efficient Storage**: Only recent positions (last 1 second) kept in memory
3. **Lazy Reporting**: Interest only reported when threshold is met
4. **Automatic Cleanup**: Trackers destroyed when cards leave viewport
5. **Background Timers**: All timers cleaned up properly to prevent memory leaks

## Future Enhancements

Potential improvements to consider:

1. **Machine Learning**: Use collected data to train ML model for better scoring
2. **A/B Testing**: Test different thresholds and scoring algorithms
3. **Database Metadata**: Store full metadata in JSON column for analysis
4. **Analytics Dashboard**: Visualize user engagement patterns
5. **Personalized Thresholds**: Adjust scoring based on individual user behavior
6. **Heat Maps**: Generate visual heat maps of mouse movement on cards
7. **Eye Tracking**: Integrate with eye tracking hardware for ultimate precision

## Testing

To test the system:

1. Open browser console on the feed page
2. Hover over cards slowly (should see slowdown detection)
3. Hover briefly and move away (should not trigger reporting)
4. Leave mouse still for 5+ seconds (should detect AFK)
5. Click on cards (should see click detection)
6. Scroll quickly then slowly (should detect scroll slowdown)

Example test output:
```
👆 Hover started on card 42
🐌 Slowdown detected on card 42. Velocity: 0.234 px/ms
📜 Scroll slowdown detected near card 42. Interest score: 18
🖱️ Click detected on card 42. Interest score: 48
👋 Hover ended on card 42. Duration: 3450ms, Total: 3450ms, Interest Score: 65
✅ Interest reported for card 42
```

## Troubleshooting

### Interest Not Being Tracked

1. Check console for errors
2. Verify `hover-tracker.js` is loaded before `feed.js`
3. Ensure API endpoint is responding
4. Check network tab for `/track-interest` requests

### False Positives (AFK counted as interest)

- System should already handle this with AFK detection
- Adjust `afkThreshold` if needed (default 5000ms)
- Check console for `😴 AFK detected` messages

### False Negatives (Real interest not detected)

- Lower `interestScoreThreshold` (default 50)
- Reduce `minHoverDuration` (default 1500ms)
- Check that movement is being detected

## API Response Examples

### Successful Interest Tracking
```json
{
    "status": "tracked",
    "interest_score": "75",
    "interaction_type": "interest_high"
}
```

### Error Response
```json
{
    "detail": "Interest tracking failed: [error details]"
}
```

## Privacy Considerations

- All tracking is session-based (anonymous by default)
- No personal data collected
- Session token stored in httponly cookie
- Can be cleared by user at any time
- Full transparency in console logging
- No third-party tracking services used

## Browser Compatibility

Tested and working on:
- Chrome/Edge (Latest)
- Firefox (Latest)
- Safari (Latest)
- Mobile browsers (iOS Safari, Chrome Android)

Requires:
- ES6 JavaScript support
- Intersection Observer API
- Fetch API
- CSS animations

---

Built with ❤️ for intelligent content recommendation in Nexus.
