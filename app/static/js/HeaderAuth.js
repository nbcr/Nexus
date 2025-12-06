/**
 * Header Authentication Module
 * 
 * Handles:
 * - Authentication status checking
 * - Login/logout functionality
 * - User welcome display
 */

let currentUser = null;

/**
 * Check if user is authenticated and update header accordingly
 */
async function checkAuthStatus() {
    try {
        // Get access token from cookie or localStorage
        let accessToken = null;
        const match = document.cookie.match(/(?:^|; )access_token=([^;]*)/);
        if (match) accessToken = match[1];
        if (!accessToken && window.localStorage) {
            accessToken = localStorage.getItem('access_token');
        }
        const headers = accessToken ? { 'Authorization': `Bearer ${accessToken}` } : {};
        const response = await fetch('/api/v1/auth/me', {
            credentials: 'include',
            headers
        });

        if (response.ok) {
            currentUser = await response.json();
            const welcomeEl = document.getElementById('user-welcome');
            const authBtn = document.getElementById('auth-btn');
            const authBtnMobile = document.getElementById('auth-btn-mobile');
            if (welcomeEl) {
                welcomeEl.textContent = `Welcome, ${currentUser.username}!`;
                welcomeEl.style.display = 'inline';
            }
            
            // Show admin link if user is admin
            if (currentUser.is_admin) {
                const adminLink = document.getElementById('admin-link');
                if (adminLink) {
                    adminLink.style.display = 'flex';
                }
            }
            
            if (authBtn) {
                const label = authBtn.querySelector('.menu-label');
                const icon = authBtn.querySelector('.menu-icon');
                if (label) label.textContent = 'Logout';
                if (icon) icon.textContent = '🚪';
                authBtn.href = '#';
                authBtn.onclick = function (e) {
                    e.preventDefault();
                    handleLogout();
                };
                authBtn.style.display = 'flex';
            }
            if (authBtnMobile) {
                const label = authBtnMobile.querySelector('.menu-label');
                const icon = authBtnMobile.querySelector('.menu-icon');
                if (label) label.textContent = 'Logout';
                if (icon) icon.textContent = '🚪';
                authBtnMobile.href = '#';
                authBtnMobile.onclick = function (e) {
                    e.preventDefault();
                    handleLogout();
                };
                authBtnMobile.style.display = 'flex';
            }
            const registerBtn = document.getElementById('register-btn');
            const registerBtnMobile = document.getElementById('register-btn-mobile');
            if (registerBtn) {
                registerBtn.style.display = 'none';
            }
            if (registerBtnMobile) {
                registerBtnMobile.style.display = 'none';
            }
        } else {
            // User not authenticated - show login and register buttons
            const welcomeEl = document.getElementById('user-welcome');
            if (welcomeEl) {
                welcomeEl.style.display = 'none';
            }
            const authBtn = document.getElementById('auth-btn');
            const authBtnMobile = document.getElementById('auth-btn-mobile');
            if (authBtn) {
                const label = authBtn.querySelector('.menu-label');
                const icon = authBtn.querySelector('.menu-icon');
                if (label) label.textContent = 'Login';
                if (icon) icon.textContent = '🔐';
                authBtn.href = '/login';
                authBtn.onclick = null;
                authBtn.style.display = 'flex';
            }
            if (authBtnMobile) {
                const label = authBtnMobile.querySelector('.menu-label');
                const icon = authBtnMobile.querySelector('.menu-icon');
                if (label) label.textContent = 'Login';
                if (icon) icon.textContent = '🔐';
                authBtnMobile.href = '/login';
                authBtnMobile.onclick = null;
                authBtnMobile.style.display = 'flex';
            }
            const registerBtn = document.getElementById('register-btn');
            const registerBtnMobile = document.getElementById('register-btn-mobile');
            if (registerBtn) {
                registerBtn.style.display = 'flex';
            }
            if (registerBtnMobile) {
                registerBtnMobile.style.display = 'flex';
            }
        }
    } catch (error) {
        console.error('Auth check failed:', error);
    }
}

/**
 * Handle authentication button click
 */
function handleAuth() {
    // Debug message for login button click
    // Only redirect to login if not authenticated
    window.location.href = '/static/login.html';
}

/**
 * Handle user logout
 */
async function handleLogout() {
    try {
        // Call backend logout endpoint
        await fetch('/api/v1/auth/logout', { method: 'POST', credentials: 'include' });

        // Clear cookies
        document.cookie.split(';').forEach(function (c) {
            document.cookie = c.replace(/^ +/, '').replace(/=.*/, '=;expires=' + new Date().toUTCString() + ';path=/');
        });

        // Clear localStorage
        localStorage.removeItem('access_token');
        localStorage.removeItem('user');
        localStorage.removeItem('darkMode');

        currentUser = null;

        const welcomeEl = document.getElementById('user-welcome');
        const authBtn = document.getElementById('auth-btn');

        if (welcomeEl) {
            welcomeEl.style.display = 'none';
        }

        if (authBtn) {
            authBtn.textContent = 'Login';
            authBtn.onclick = handleAuth;
        }

        // Redirect to dedicated logged out page
        window.location.href = "/logged-out.html";
    } catch (error) {
        console.error('Logout error:', error);
    }
}

// Export namespace and global functions
window.HeaderAuth = { checkAuthStatus, handleAuth, handleLogout };
window.checkAuthStatus = checkAuthStatus;
window.handleAuth = handleAuth;
window.handleLogout = handleLogout;
