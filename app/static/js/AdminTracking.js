/**
 * Admin Tracking Module
 * 
 * Handles:
 * - Interest tracking display
 * - Real-time tracking log
 * - Auto-refresh tracking data
 * - Tracking statistics
 */

let trackingData = [];
let autoRefreshInterval = null;

// Refresh tracking data
async function refreshTracking() {
    try {
        const response = await fetch('/api/v1/admin/tracking-log', {
            credentials: 'include'
        });

        if (!response.ok) throw new Error('Failed to fetch tracking data');

        const data = await response.json();
        trackingData = data.events || [];

        updateTrackingStats();
        renderTrackingLog();

    } catch (error) {
        console.error('Failed to refresh tracking:', error);
    }
}

function updateTrackingStats() {
    const total = trackingData.length;
    const high = trackingData.filter(e => e.interaction_type === 'interest_high').length;
    const medium = trackingData.filter(e => e.interaction_type === 'interest_medium').length;
    const low = trackingData.filter(e => e.interaction_type === 'interest_low').length;

    document.getElementById('total-events').textContent = total;
    document.getElementById('high-interest').textContent = high;
    document.getElementById('medium-interest').textContent = medium;
    document.getElementById('low-interest').textContent = low;
}

function renderTrackingLog() {
    const logContainer = document.getElementById('tracking-log');

    if (trackingData.length === 0) {
        logContainer.innerHTML = '<div style="text-align: center; color: #808080; padding: 40px;">No tracking events yet. Events will appear here in real-time.</div>';
        return;
    }

    // Sort by most recent first
    const sorted = [...trackingData].sort((a, b) =>
        new Date(b.created_at) - new Date(a.created_at)
    );

    logContainer.innerHTML = sorted.map(event => {
        const interestLevel = event.interaction_type.replace('interest_', '');
        const metadata = event.metadata || {};
        const timestamp = new Date(event.created_at).toLocaleString();

        return `
            <div class="log-entry ${interestLevel}">
                <div class="log-entry-main">
                    <div class="log-entry-title">
                        <span class="log-entry-badge ${interestLevel}">${interestLevel.toUpperCase()}</span>
                        Content ID: ${event.content_item_id}
                        ${event.session_id ? `| Session: ${event.session_id}` : ''}
                        ${event.user_id ? `| User: ${event.user_id}` : ''}
                    </div>
                    <div class="log-entry-details">
                        Score: ${metadata.interest_score || 'N/A'} | 
                        Duration: ${metadata.hover_duration_ms ? (metadata.hover_duration_ms / 1000).toFixed(1) + 's' : event.duration_seconds + 's'} |
                        Movement: ${metadata.movement_detected ? '✓' : '✗'} |
                        Slowdowns: ${metadata.slowdowns_detected || 0} |
                        Clicks: ${metadata.clicks_detected || 0} |
                        AFK: ${metadata.was_afk ? '✓' : '✗'} |
                        Trigger: ${metadata.trigger || 'unknown'}
                    </div>
                </div>
                <div class="log-entry-timestamp">${timestamp}</div>
            </div>
        `;
    }).join('');
}

async function clearTracking() {
    if (!confirm('Are you sure you want to clear all tracking data? This cannot be undone.')) {
        return;
    }

    try {
        const response = await fetch('/api/v1/admin/clear-tracking', {
            method: 'POST',
            credentials: 'include'
        });

        if (!response.ok) throw new Error('Failed to clear tracking');

        trackingData = [];
        updateTrackingStats();
        renderTrackingLog();
        alert('Tracking data cleared successfully');

    } catch (error) {
        console.error('Failed to clear tracking:', error);
        alert('Failed to clear tracking data');
    }
}

// Auto-refresh toggle
document.addEventListener('DOMContentLoaded', function () {
    const autoRefreshCheckbox = document.getElementById('auto-refresh');
    if (autoRefreshCheckbox) {
        autoRefreshCheckbox.addEventListener('change', function (e) {
            if (e.target.checked) {
                startAutoRefresh();
            } else {
                stopAutoRefresh();
            }
        });
    }

    // Initial load of tracking data
    refreshTracking();
    startAutoRefresh();
});

function startAutoRefresh() {
    stopAutoRefresh(); // Clear any existing interval
    autoRefreshInterval = setInterval(() => {
        if (document.querySelector('.tab-btn[data-tab="tracking"]').classList.contains('active')) {
            refreshTracking();
        }
    }, 5000); // Refresh every 5 seconds
}

function stopAutoRefresh() {
    if (autoRefreshInterval) {
        clearInterval(autoRefreshInterval);
        autoRefreshInterval = null;
    }
}

// Cleanup on page unload
window.addEventListener('beforeunload', (e) => {
    if (autoRefreshInterval) {
        stopAutoRefresh();
    }
});

// Export namespace and global functions for onclick handlers
window.AdminTracking = { 
    refreshTracking, 
    updateTrackingStats, 
    renderTrackingLog, 
    clearTracking,
    startAutoRefresh,
    stopAutoRefresh
};
window.refreshTracking = refreshTracking;
window.clearTracking = clearTracking;