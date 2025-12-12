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
        const accessToken = getAccessToken();
        const headers = accessToken ? { 'Authorization': `Bearer ${accessToken}` } : {};
        const response = await fetch('/api/v1/auth/me', {
            credentials: 'include',
            headers
        });

        if (response.ok) {
            currentUser = await response.json();
            updateAuthenticatedUI();
        } else {
            updateUnauthenticatedUI();
        }
    } catch (error) {
        console.error('Auth check failed:', error);
    }
}

function getAccessToken() {
    const regex = /(?:^|; )access_token=([^;]*)/;
    const match = regex.exec(document.cookie);
    if (match) return match[1];
    if (window.localStorage) {
        return localStorage.getItem('access_token');
    }
    return null;
}

function updateAuthenticatedUI() {
    updateWelcomeMessage();
    showAdminLinkIfAdmin();
    configureAuthButtons(true);
    hideRegisterButtons();
}

function updateUnauthenticatedUI() {
    hideWelcomeMessage();
    configureAuthButtons(false);
    showRegisterButtons();
}

function updateWelcomeMessage() {
    const welcomeEl = document.getElementById('user-welcome');
    if (welcomeEl) {
        welcomeEl.textContent = `Welcome, ${currentUser.username}!`;
        welcomeEl.style.display = 'inline';
    }
}

function hideWelcomeMessage() {
    const welcomeEl = document.getElementById('user-welcome');
    if (welcomeEl) {
        welcomeEl.style.display = 'none';
    }
}

function showAdminLinkIfAdmin() {
    if (currentUser.is_admin) {
        const adminLink = document.getElementById('admin-link');
        if (adminLink) {
            adminLink.style.display = 'flex';
        }
    }
}

function configureAuthButtons(isAuthenticated) {
    const authBtn = document.getElementById('auth-btn');
    const authBtnMobile = document.getElementById('auth-btn-mobile');
    
    [authBtn, authBtnMobile].forEach(btn => {
        if (!btn) return;
        
        const label = btn.querySelector('.menu-label');
        const icon = btn.querySelector('.menu-icon');
        
        if (isAuthenticated) {
            if (label) label.textContent = 'Logout';
            if (icon) icon.textContent = '🚪';
            btn.href = '#';
            btn.onclick = (e) => {
                e.preventDefault();
                handleLogout();
            };
        } else {
            if (label) label.textContent = 'Login';
            if (icon) icon.textContent = '🔐';
            btn.href = '/login';
            btn.onclick = null;
        }
        btn.style.display = 'flex';
    });
}

function hideRegisterButtons() {
    const registerBtn = document.getElementById('register-btn');
    const registerBtnMobile = document.getElementById('register-btn-mobile');
    if (registerBtn) registerBtn.style.display = 'none';
    if (registerBtnMobile) registerBtnMobile.style.display = 'none';
}

function showRegisterButtons() {
    const registerBtn = document.getElementById('register-btn');
    const registerBtnMobile = document.getElementById('register-btn-mobile');
    if (registerBtn) registerBtn.style.display = 'flex';
    if (registerBtnMobile) registerBtnMobile.style.display = 'flex';
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
function handleLogout() {
    try {
        // Call backend logout endpoint
        fetch('/api/v1/auth/logout', { method: 'POST', credentials: 'include' });

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
globalThis.HeaderAuth = { checkAuthStatus, handleAuth, handleLogout };
globalThis.checkAuthStatus = checkAuthStatus;
globalThis.handleAuth = handleLogout;
globalThis.handleLogout = handleLogout;
