// Set persistent visitor_id cookie if not present
function setVisitorIdCookie() {
    let visitorId = null;
    const match = document.cookie.match(/(?:^|; )visitor_id=([^;]*)/);
    if (match) visitorId = match[1];
    if (!visitorId) {
        visitorId = crypto.randomUUID ? crypto.randomUUID() : (Math.random().toString(36).substr(2, 16) + Date.now());
        const expires = new Date(Date.now() + 2 * 365 * 24 * 60 * 60 * 1000).toUTCString(); // 2 years
        document.cookie = `visitor_id=${visitorId}; expires=${expires}; path=/; SameSite=Lax`;
    }
    return visitorId;
}
/**
 * Shared Header and Navigation Functions
 * Used across all pages for consistent authentication and dark mode behavior
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
            if (welcomeEl) {
                welcomeEl.textContent = `Welcome, ${currentUser.username}!`;
                welcomeEl.style.display = 'inline';
            }
            if (authBtn) {
                authBtn.textContent = 'Logout';
                authBtn.onclick = handleLogout;
            }
            const registerBtn = document.getElementById('register-btn');
            if (registerBtn) {
                registerBtn.style.display = 'none';
            }
        } else {
            // User not authenticated - show login button and handler
            const authBtn = document.getElementById('auth-btn');
            if (authBtn) {
                authBtn.textContent = 'Login';
                authBtn.onclick = handleAuth;
            }
            const registerBtn = document.getElementById('register-btn');
            if (registerBtn) {
                registerBtn.style.display = '';
            }
        }
    } catch (error) {
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
        document.cookie.split(';').forEach(function(c) {
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

/**
 * Initialize dark mode based on device and user preferences
 * Dark mode is enabled by default
 */
function initDarkMode() {
    const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
    const toggleBtn = document.getElementById('dark-mode-toggle');
    const toggleLabel = document.getElementById('dark-mode-label');
    
    if (isMobile) {
        // Hide toggle button and label on mobile
        if (toggleBtn) toggleBtn.style.display = 'none';
        if (toggleLabel) toggleLabel.style.display = 'none';
        
        // Use system preference
        if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
            document.body.classList.add('dark-mode');
            // Remove inline color from .feed-item-summary in dark mode
            document.querySelectorAll('.feed-item-summary').forEach(function(el) {
                if (el.style.color) {
                    el.style.removeProperty('color');
                }
            });
        }
        
        // Listen for system preference changes
        window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', e => {
            if (e.matches) {
                document.body.classList.add('dark-mode');
                document.querySelectorAll('.feed-item-summary').forEach(function(el) {
                    if (el.style.color) {
                        el.style.removeProperty('color');
                    }
                });
            } else {
                document.body.classList.remove('dark-mode');
            }
        });
    } else {
        // Desktop: use localStorage preference, default to dark mode
        const savedPreference = localStorage.getItem('darkMode');
        
        // If no preference saved, default to dark mode (true)
        if (savedPreference === null) {
            document.body.classList.add('dark-mode');
            localStorage.setItem('darkMode', 'true');
            if (toggleBtn) toggleBtn.textContent = '☀️';
            if (toggleLabel) toggleLabel.textContent = 'Dark Mode: On';
            document.querySelectorAll('.feed-item-summary').forEach(function(el) {
                if (el.style.color) {
                    el.style.removeProperty('color');
                }
            });
        } else if (savedPreference === 'true') {
            document.body.classList.add('dark-mode');
            if (toggleBtn) toggleBtn.textContent = '☀️';
            if (toggleLabel) toggleLabel.textContent = 'Dark Mode: On';
            document.querySelectorAll('.feed-item-summary').forEach(function(el) {
                if (el.style.color) {
                    el.style.removeProperty('color');
                }
            });
        } else {
            if (toggleBtn) toggleBtn.textContent = '🌙';
            if (toggleLabel) toggleLabel.textContent = 'Dark Mode: Off';
        }
    }
}

/**
 * Toggle dark mode on/off
 */
function toggleDarkMode() {
    document.body.classList.toggle('dark-mode');
    const isDark = document.body.classList.contains('dark-mode');
    localStorage.setItem('darkMode', isDark);
    
    // Update toggle button icon and label
    const toggleBtn = document.getElementById('dark-mode-toggle');
    const toggleLabel = document.getElementById('dark-mode-label');
    
    if (toggleBtn) {
        toggleBtn.textContent = isDark ? '☀️' : '🌙';
    }

    // Remove inline color from .feed-item-summary in dark mode
    if (isDark) {
        document.querySelectorAll('.feed-item-summary').forEach(function(el) {
            if (el.style.color) {
                el.style.removeProperty('color');
            }
        });
    }
    
    if (toggleLabel) {
        toggleLabel.textContent = isDark ? 'Dark Mode: On' : 'Dark Mode: Off';
    }
}

/**
 * Initialize header on page load
 * Call this in DOMContentLoaded
 */
function initHeader() {
    initDarkMode();
    setVisitorIdCookie();
    checkAuthStatus();

    // Hamburger menu toggle logic is handled in index.html
    // Removed duplicate setup to avoid conflicts
}

// Auto-initialize if DOM is already loaded
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initHeader);
} else {
    initHeader();
}
