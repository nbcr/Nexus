/**
 * Admin Settings & Preferences Module
 * 
 * Handles:
 * - Global tracking settings
 * - Analytics display
 * - Dark mode toggle
 * - Date range initialization
 */

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
        const authManager = globalThis.authManager || new AuthManager();
        globalThis.authManager = authManager;
        const response = await fetch('/api/v1/admin/settings/global', {
            method: 'POST',
            headers: { ...authManager.getAuthHeaders(), 'Content-Type': 'application/json' },
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
        const authManager = globalThis.authManager || new AuthManager();
        globalThis.authManager = authManager;
        const response = await fetch(`/api/v1/admin/analytics?start=${startDate}&end=${endDate}`, {
            credentials: 'include',
            headers: authManager.getAuthHeaders()
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

// Load initial settings on page load
document.addEventListener('DOMContentLoaded', async function () {
    initializeDateRange();

    try {
        const authManager = globalThis.authManager || new AuthManager();
        globalThis.authManager = authManager;
        const response = await fetch('/api/v1/admin/settings/global', {
            credentials: 'include',
            headers: authManager.getAuthHeaders()
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
});

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
        // Show moon icon (will switch to dark when clicked)
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

// Export namespace and global functions for onclick handlers
globalThis.AdminSettings = {
    saveGlobalSettings,
    resetToDefaults,
    testSettings,
    initializeDateRange,
    loadAnalytics,
    renderAnalytics,
    renderInterestChart,
    renderTopContent,
    renderHoverPatterns,
    toggleDarkMode
};
globalThis.saveGlobalSettings = saveGlobalSettings;
globalThis.resetToDefaults = resetToDefaults;
globalThis.testSettings = testSettings;
globalThis.loadAnalytics = loadAnalytics;
globalThis.toggleDarkMode = toggleDarkMode;
