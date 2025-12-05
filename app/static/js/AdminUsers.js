/**
 * Admin User Management Module
 * 
 * Handles:
 * - User list display
 * - User search/filtering
 * - User modal for settings
 * - Per-user debug mode and custom settings
 */

let selectedUserId = null;

// Utility function - move from global
function formatRelativeTime(date) {
    date = new Date(date);
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

// Load users on tab switch
document.addEventListener('DOMContentLoaded', function () {
    const userUseCustom = document.getElementById('user-use-custom');
    const userDebugMode = document.getElementById('user-debug-mode');

    if (userUseCustom) {
        userUseCustom.addEventListener('change', function (e) {
            if (e.target.checked) {
                showCustomSettings();
            } else {
                hideCustomSettings();
            }
        });
    }

    if (userDebugMode) {
        userDebugMode.addEventListener('change', function (e) {
            if (e.target.checked) {
                document.getElementById('debug-warning').style.display = 'block';
            } else {
                document.getElementById('debug-warning').style.display = 'none';
            }
        });
    }
});

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

async function saveUserSettings() {
    if (!selectedUserId) return;

    const debugMode = document.getElementById('user-debug-mode').checked;
    const useCustom = document.getElementById('user-use-custom').checked;
    const settings = useCustom ? {
        minHoverDuration: parseInt(document.getElementById('user-minHoverDuration').value),
        afkThreshold: parseInt(document.getElementById('user-afkThreshold').value),
        interestScoreThreshold: parseInt(document.getElementById('user-interestScoreThreshold').value)
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

function showCustomSettings() {
    document.getElementById('user-custom-settings').style.display = 'grid';
}

function hideCustomSettings() {
    document.getElementById('user-custom-settings').style.display = 'none';
}

// Export namespace and global functions for onclick handlers
window.AdminUsers = { 
    refreshUsers, 
    renderUsers, 
    filterUsers,
    openUserModal,
    closeUserModal,
    saveUserSettings,
    showCustomSettings,
    hideCustomSettings,
    formatRelativeTime
};
window.refreshUsers = refreshUsers;
window.filterUsers = filterUsers;
window.openUserModal = openUserModal;
window.closeUserModal = closeUserModal;
window.saveUserSettings = saveUserSettings;