/**
 * Admin Tab Navigation Module
 * 
 * Handles:
 * - Tab switching
 * - Tab content display
 * - Tab initialization
 */

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

// Initialize tabs on page load
document.addEventListener('DOMContentLoaded', function () {
    initializeTabs();
});

// Export namespace and global functions for onclick handlers
window.AdminTabs = { initializeTabs, switchTab };
window.switchTab = switchTab;
