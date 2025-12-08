/**
 * Admin Authentication Module
 * 
 * Handles:
 * - Admin access verification
 * - Access denial display
 * - User state management
 */


// Ensure AuthManager is available globally
// Sync access_token from cookie to localStorage if missing
function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
    return null;
}

const cookieToken = getCookie('access_token');
const localToken = localStorage.getItem(CONFIG.TOKEN_KEY);
if (cookieToken && cookieToken !== localToken) {
    localStorage.setItem(CONFIG.TOKEN_KEY, cookieToken);
}

const authManager = globalThis.authManager || new AuthManager();
globalThis.authManager = authManager;

let currentUser = null;

// Authentication check on page load
document.addEventListener('DOMContentLoaded', async function () {
    await checkAdminAccess();
});

// Check if user has admin access
async function checkAdminAccess() {
    try {
        const response = await fetch('/api/v1/admin/verify', {
            credentials: 'include',
            headers: authManager.getAuthHeaders()
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

    globalThis.location.href = '/';
}

// Export namespace and global functions for onclick handlers
globalThis.AdminAuth = { checkAdminAccess, showAccessDenied, showAdminContent, logout };
globalThis.logout = logout;
