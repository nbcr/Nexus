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
        const response = await fetch('/api/v1/auth/me', {
            credentials: 'include'
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
        }
    } catch (error) {
        // User not authenticated - leave default login button
    }
}

/**
 * Handle authentication button click
 */
function handleAuth() {
    if (currentUser) {
        handleLogout();
    } else {
        window.location.href = '/static/login.html';
    }
}

/**
 * Handle user logout
 */
async function handleLogout() {
    try {
        // Clear cookies
        document.cookie.split(";").forEach(function(c) { 
            document.cookie = c.replace(/^ +/, "").replace(/=.*/, "=;expires=" + new Date().toUTCString() + ";path=/"); 
        });
        
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
        
        // Reload current page to refresh content
        window.location.reload();
    } catch (error) {
        console.error('Logout error:', error);
    }
}

/**
 * Initialize dark mode based on device and user preferences
 */
function initDarkMode() {
    const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
    const toggleBtn = document.getElementById('dark-mode-toggle');
    
    if (isMobile) {
        // Hide toggle button on mobile
        if (toggleBtn) toggleBtn.style.display = 'none';
        
        // Use system preference
        if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
            document.body.classList.add('dark-mode');
        }
        
        // Listen for system preference changes
        window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', e => {
            if (e.matches) {
                document.body.classList.add('dark-mode');
            } else {
                document.body.classList.remove('dark-mode');
            }
        });
    } else {
        // Desktop: use localStorage preference
        if (localStorage.getItem('darkMode') === 'true') {
            document.body.classList.add('dark-mode');
            if (toggleBtn) toggleBtn.textContent = '☀️';
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
    
    // Update toggle button icon
    const toggleBtn = document.getElementById('dark-mode-toggle');
    if (toggleBtn) {
        toggleBtn.textContent = isDark ? '☀️' : '🌙';
    }
}

/**
 * Initialize header on page load
 * Call this in DOMContentLoaded
 */
function initHeader() {
    initDarkMode();
    checkAuthStatus();
}

// Auto-initialize if DOM is already loaded
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initHeader);
} else {
    initHeader();
}
