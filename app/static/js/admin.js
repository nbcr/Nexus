/**
 * DEPRECATED: Nexus Admin Panel JavaScript
 * 
 * This file has been split into separate modules for better maintainability:
 * - AdminAuth.js - Authentication and access control
 * - AdminTabs.js - Tab navigation
 * - AdminTracking.js - Tracking and statistics
 * - AdminUsers.js - User management
 * - AdminSettings.js - Global settings, analytics, preferences
 * 
 * The code below is kept for reference only. Use the modular files instead.
 * 
 * Security: This script requires admin authentication
 * No links or references to this page exist in the main application
 * 
 * Updated: December 4, 2024
 */

console.warn('⚠️ admin.js is deprecated. Please use AdminAuth.js, AdminTabs.js, AdminTracking.js, AdminUsers.js, and AdminSettings.js instead.');

let currentUser = null;
let trackingData = [];
let autoRefreshInterval = null;
let selectedUserId = null;

// Check if user has admin access
async function checkAdminAccess() {
    try {
        const response = await fetch('/api/v1/admin/verify', {
            credentials: 'include'
        });

        if (!response.ok) {
            showAccessDenied();
            return;
        }

        const data = await response.json();
        if (!data.is_admin) {
            showAccessDenied();
            return;
        }

        currentUser = data.user;
        showAdminContent();
        document.getElementById('admin-welcome').textContent = `Admin: ${currentUser.username}`;

    } catch (error) {
        console.error('Auth check failed:', error);
        showAccessDenied();
    }
}

function showAccessDenied() {
    document.getElementById('access-denied').style.display = 'flex';
    document.getElementById('admin-content').style.display = 'none';
}

function showAdminContent() {
    document.getElementById('access-denied').style.display = 'none';
    document.getElementById('admin-content').style.display = 'block';
}

// Tab Navigation
function initializeTabs() {
    const tabButtons = document.querySelectorAll('.tab-btn');
    tabButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            const tabName = btn.dataset.tab;
            switchTab(tabName);
        });
    });
}

function switchTab(tabName) {
    // Update buttons
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
        if (btn.dataset.tab === tabName) {
            btn.classList.add('active');
        }
    });

    // Update content
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.remove('active');
    });
    document.getElementById(`tab-${tabName}`).classList.add('active');

    // Load tab-specific data
    if (tabName === 'tracking') {
        refreshTracking();
    } else if (tabName === 'users') {
        refreshUsers();
    } else if (tabName === 'analytics') {
        loadAnalytics();
    }
}

// Interest Tracking Functions
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
document.getElementById('auto-refresh')?.addEventListener('change', function (e) {
    if (e.target.checked) {
        startAutoRefresh();
    } else {
        stopAutoRefresh();
    }
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

// Start auto-refresh by default
startAutoRefresh();

// Global Settings Functions
async function saveGlobalSettings() {
    const settings = {
        minHoverDuration: Number.parseInt(document.getElementById('minHoverDuration').value),
        afkThreshold: Number.parseInt(document.getElementById('afkThreshold').value),
        movementThreshold: Number.parseInt(document.getElementById('movementThreshold').value),
        microMovementThreshold: Number.parseInt(document.getElementById('microMovementThreshold').value),
        slowdownVelocityThreshold: Number.parseFloat(document.getElementById('slowdownVelocityThreshold').value),
        velocitySampleRate: Number.parseInt(document.getElementById('velocitySampleRate').value),
        interestScoreThreshold: Number.parseInt(document.getElementById('interestScoreThreshold').value),
        scrollSlowdownThreshold: Number.parseFloat(document.getElementById('scrollSlowdownThreshold').value)
    };

    try {
        const response = await fetch('/api/v1/admin/settings/global', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify(settings)
        });

        if (!response.ok) throw new Error('Failed to save settings');

        alert('Global settings saved successfully! Users will receive updated settings on next page load.');

    } catch (error) {
        console.error('Failed to save settings:', error);
        alert('Failed to save settings');
    }
}

function resetToDefaults() {
    if (!confirm('Reset all settings to default values?')) return;

    document.getElementById('minHoverDuration').value = 1500;
    document.getElementById('afkThreshold').value = 5000;
    document.getElementById('movementThreshold').value = 5;
    document.getElementById('microMovementThreshold').value = 20;
    document.getElementById('slowdownVelocityThreshold').value = 0.3;
    document.getElementById('velocitySampleRate').value = 100;
    document.getElementById('interestScoreThreshold').value = 50;
    document.getElementById('scrollSlowdownThreshold').value = 2;
}

function testSettings() {
    const settings = {
        minHoverDuration: Number.parseInt(document.getElementById('minHoverDuration').value),
        afkThreshold: Number.parseInt(document.getElementById('afkThreshold').value),
        movementThreshold: Number.parseInt(document.getElementById('movementThreshold').value),
        interestScoreThreshold: Number.parseInt(document.getElementById('interestScoreThreshold').value)
    };

    alert(`Current Settings:\n\n${JSON.stringify(settings, null, 2)}\n\nThese settings will be used for all users by default.`);
}

// User Management Functions
async function refreshUsers() {
    try {
        const response = await fetch('/api/v1/admin/users', {
            credentials: 'include'
        });

        if (!response.ok) throw new Error('Failed to fetch users');

        const data = await response.json();
        renderUsers(data.users || []);

    } catch (error) {
        console.error('Failed to refresh users:', error);
    }
}

function renderUsers(users) {
    const usersList = document.getElementById('users-list');

    if (users.length === 0) {
        usersList.innerHTML = '<div style="text-align: center; color: #808080; padding: 40px;">No users found</div>';
        return;
    }

    usersList.innerHTML = users.map(user => `
        <div class="user-card" onclick="openUserModal(${user.id})">
            <div class="user-card-header">
                <div class="user-card-name">${user.username}</div>
                <div class="user-card-badge ${user.is_admin ? 'admin' : 'user'}">
                    ${user.is_admin ? 'Admin' : 'User'}
                </div>
            </div>
            <div style="color: #b0b0b0; font-size: 13px; margin: 5px 0;">
                ${user.email || 'No email'}
            </div>
            <div class="user-card-stats">
                <div class="user-stat">
                    <div class="user-stat-label">Interactions</div>
                    <div class="user-stat-value">${user.interaction_count || 0}</div>
                </div>
                <div class="user-stat">
                    <div class="user-stat-label">Last Active</div>
                    <div class="user-stat-value" style="font-size: 12px;">
                        ${user.last_login ? formatRelativeTime(user.last_login) : 'Never'}
                    </div>
                </div>
            </div>
        </div>
    `).join('');
}

function filterUsers() {
    const searchTerm = document.getElementById('user-search').value.toLowerCase();
    const userCards = document.querySelectorAll('.user-card');

    userCards.forEach(card => {
        const text = card.textContent.toLowerCase();
        card.style.display = text.includes(searchTerm) ? 'block' : 'none';
    });
}

// User Modal Functions
async function openUserModal(userId) {
    selectedUserId = userId;

    try {
        const response = await fetch(`/api/v1/admin/users/${userId}`, {
            credentials: 'include'
        });

        if (!response.ok) throw new Error('Failed to fetch user details');

        const user = await response.json();

        document.getElementById('modal-username').textContent = user.username;
        document.getElementById('user-debug-mode').checked = user.debug_mode || false;
        document.getElementById('user-use-custom').checked = user.custom_settings !== null;

        // Show debug warning if enabled
        if (user.debug_mode) {
            document.getElementById('debug-warning').style.display = 'block';
        } else {
            document.getElementById('debug-warning').style.display = 'none';
        }

        if (user.custom_settings) {
            showCustomSettings();
            document.getElementById('user-minHoverDuration').value = user.custom_settings.minHoverDuration || 1500;
            document.getElementById('user-afkThreshold').value = user.custom_settings.afkThreshold || 5000;
            document.getElementById('user-interestScoreThreshold').value = user.custom_settings.interestScoreThreshold || 50;
        }

        // Render user stats
        const statsHtml = `
            <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 15px;">
                <div class="user-stat">
                    <div class="user-stat-label">Total Interactions</div>
                    <div class="user-stat-value">${user.stats?.total_interactions || 0}</div>
                </div>
                <div class="user-stat">
                    <div class="user-stat-label">High Interest</div>
                    <div class="user-stat-value">${user.stats?.high_interest || 0}</div>
                </div>
                <div class="user-stat">
                    <div class="user-stat-label">Avg Duration</div>
                    <div class="user-stat-value">${user.stats?.avg_duration || 0}s</div>
                </div>
                <div class="user-stat">
                    <div class="user-stat-label">Last Active</div>
                    <div class="user-stat-value" style="font-size: 14px;">
                        ${user.last_login ? formatRelativeTime(user.last_login) : 'Never'}
                    </div>
                </div>
            </div>
        `;
        document.getElementById('user-stats').innerHTML = statsHtml;

        document.getElementById('user-settings-modal').classList.add('active');

    } catch (error) {
        console.error('Failed to open user modal:', error);
        alert('Failed to load user details');
    }
}

function closeUserModal() {
    document.getElementById('user-settings-modal').classList.remove('active');
    selectedUserId = null;
}

document.getElementById('user-use-custom')?.addEventListener('change', function (e) {
    if (e.target.checked) {
        showCustomSettings();
    } else {
        hideCustomSettings();
    }
});

document.getElementById('user-debug-mode')?.addEventListener('change', function (e) {
    if (e.target.checked) {
        document.getElementById('debug-warning').style.display = 'block';
    } else {
        document.getElementById('debug-warning').style.display = 'none';
    }
});

function showCustomSettings() {
    document.getElementById('user-custom-settings').style.display = 'grid';
}

function hideCustomSettings() {
    document.getElementById('user-custom-settings').style.display = 'none';
}

async function saveUserSettings() {
    if (!selectedUserId) return;

    const debugMode = document.getElementById('user-debug-mode').checked;
    const useCustom = document.getElementById('user-use-custom').checked;
    const settings = useCustom ? {
        minHoverDuration: Number.parseInt(document.getElementById('user-minHoverDuration').value),
        afkThreshold: Number.parseInt(document.getElementById('user-afkThreshold').value),
        interestScoreThreshold: Number.parseInt(document.getElementById('user-interestScoreThreshold').value)
    } : null;

    try {
        const response = await fetch(`/api/v1/admin/users/${selectedUserId}/settings`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({
                debug_mode: debugMode,
                custom_settings: settings
            })
        });

        if (!response.ok) throw new Error('Failed to save user settings');

        alert('User settings saved successfully!');
        closeUserModal();
        refreshUsers();

    } catch (error) {
        console.error('Failed to save user settings:', error);
        alert('Failed to save user settings');
    }
}

// Analytics Functions
function initializeDateRange() {
    const today = new Date();
    const weekAgo = new Date(today);
    weekAgo.setDate(weekAgo.getDate() - 7);

    document.getElementById('end-date').valueAsDate = today;
    document.getElementById('start-date').valueAsDate = weekAgo;
}

async function loadAnalytics() {
    const startDate = document.getElementById('start-date').value;
    const endDate = document.getElementById('end-date').value;

    try {
        const response = await fetch(`/api/v1/admin/analytics?start=${startDate}&end=${endDate}`, {
            credentials: 'include'
        });

        if (!response.ok) throw new Error('Failed to fetch analytics');

        const data = await response.json();
        renderAnalytics(data);

    } catch (error) {
        console.error('Failed to load analytics:', error);
    }
}

function renderAnalytics(data) {
    // Render interest distribution
    renderInterestChart(data.interest_distribution);

    // Render top content
    renderTopContent(data.top_content);

    // Render hover patterns
    renderHoverPatterns(data.hover_patterns);
}

function renderInterestChart(distribution) {
    const canvas = document.getElementById('interest-chart');
    const ctx = canvas.getContext('2d');

    // Simple bar chart
    const labels = ['High', 'Medium', 'Low'];
    const values = [
        distribution.high || 0,
        distribution.medium || 0,
        distribution.low || 0
    ];
    const colors = ['#ff4444', '#ffaa00', '#00aaff'];

    // Clear canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Simple visualization (you can integrate Chart.js for better charts)
    const maxValue = Math.max(...values, 1);
    const barWidth = canvas.width / labels.length - 20;

    values.forEach((value, i) => {
        const height = (value / maxValue) * (canvas.height - 40);
        const x = i * (barWidth + 20) + 10;
        const y = canvas.height - height - 20;

        ctx.fillStyle = colors[i];
        ctx.fillRect(x, y, barWidth, height);

        ctx.fillStyle = '#e0e0e0';
        ctx.font = '14px sans-serif';
        ctx.textAlign = 'center';
        ctx.fillText(labels[i], x + barWidth / 2, canvas.height - 5);
        ctx.fillText(value, x + barWidth / 2, y - 5);
    });
}

function renderTopContent(topContent) {
    const container = document.getElementById('top-content');

    if (!topContent || topContent.length === 0) {
        container.innerHTML = '<div style="color: #808080; padding: 20px;">No data available</div>';
        return;
    }

    container.innerHTML = topContent.map((item, index) => `
        <div style="padding: 12px; background: var(--bg-secondary); margin-bottom: 10px; border-radius: 6px; border-left: 3px solid var(--accent-primary);">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div style="flex: 1;">
                    <div style="font-weight: 600; color: var(--text-primary);">${index + 1}. ${item.title}</div>
                    <div style="font-size: 12px; color: var(--text-secondary); margin-top: 4px;">
                        ID: ${item.content_id} | Views: ${item.view_count}
                    </div>
                </div>
                <div style="text-align: right; color: var(--accent-primary); font-size: 18px; font-weight: 700;">
                    ${item.avg_score || 0}
                </div>
            </div>
        </div>
    `).join('');
}

function renderHoverPatterns(patterns) {
    const container = document.getElementById('hover-patterns');

    if (!patterns) {
        container.innerHTML = '<div style="color: #808080; padding: 20px;">No data available</div>';
        return;
    }

    container.innerHTML = `
        <div style="display: grid; gap: 15px;">
            <div class="user-stat">
                <div class="user-stat-label">Avg Hover Duration</div>
                <div class="user-stat-value">${(patterns.avg_duration || 0).toFixed(1)}s</div>
            </div>
            <div class="user-stat">
                <div class="user-stat-label">Avg Slowdowns</div>
                <div class="user-stat-value">${(patterns.avg_slowdowns || 0).toFixed(1)}</div>
            </div>
            <div class="user-stat">
                <div class="user-stat-label">Movement Rate</div>
                <div class="user-stat-value">${(patterns.movement_rate || 0).toFixed(0)}%</div>
            </div>
            <div class="user-stat">
                <div class="user-stat-label">AFK Rate</div>
                <div class="user-stat-value">${(patterns.afk_rate || 0).toFixed(0)}%</div>
            </div>
        </div>
    `;
}

// Utility Functions
function formatRelativeTime(dateString) {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;

    return date.toLocaleDateString();
}

async function loadInitialData() {
    await refreshTracking();

    // Load global settings from server
    try {
        const response = await fetch('/api/v1/admin/settings/global', {
            credentials: 'include'
        });

        if (response.ok) {
            const settings = await response.json();
            Object.keys(settings).forEach(key => {
                const element = document.getElementById(key);
                if (element) {
                    element.value = settings[key];
                }
            });
        }
    } catch (error) {
        console.error('Failed to load global settings:', error);
    }
}

// Dark mode toggle
function toggleDarkMode() {
    // Toggle light-mode class (dark mode is default, no class needed)
    const isCurrentlyLight = document.documentElement.classList.contains('light-mode');

    if (isCurrentlyLight) {
        // Switch back to dark mode (default)
        document.documentElement.classList.remove('light-mode');
        localStorage.setItem('adminDarkMode', 'true');
        // Show sun icon (will switch to light mode when clicked)
        document.getElementById('dark-mode-toggle').textContent = '☀️';
    } else {
        // Switch to light mode
        document.documentElement.classList.add('light-mode');
        localStorage.setItem('adminDarkMode', 'false');
        // Show moon icon (will switch to dark mode when clicked)
        document.getElementById('dark-mode-toggle').textContent = '🌙';
    }
}

// Initialize dark mode from localStorage (default to dark)
const savedAdminDarkMode = localStorage.getItem('adminDarkMode');
if (savedAdminDarkMode === 'false') {
    document.documentElement.classList.add('light-mode');
    const toggleBtn = document.getElementById('dark-mode-toggle');
    // In light mode, show moon icon (will switch to dark when clicked)
    if (toggleBtn) toggleBtn.textContent = '🌙';
} else {
    // In dark mode, show sun icon (will switch to light when clicked)
    const toggleBtn = document.getElementById('dark-mode-toggle');
    if (toggleBtn) toggleBtn.textContent = '☀️';
}

// Logout
async function logout() {
    try {
        await fetch('/api/v1/auth/logout', {
            method: 'POST',
            credentials: 'include'
        });
    } catch (error) {
        console.error('Logout error:', error);
    }

    window.location.href = '/';
}

// Prevent accidental page close with unsaved changes
window.addEventListener('beforeunload', (e) => {
    if (autoRefreshInterval) {
        stopAutoRefresh();
    }
});
