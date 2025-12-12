/**
 * DEPRECATED: Header Navigation and Authentication
 * 
 * This file has been split into separate modules for better maintainability:
 * - HeaderAuth.js - Authentication and login/logout
 * - HeaderDarkMode.js - Dark mode toggle and initialization
 * - HeaderMenu.js - Hamburger menu and navigation
 * - HeaderSession.js - Visitor tracking and header initialization
 * - HeaderPreferences.js - Text size controls and scroll effects
 * 
 * The code below is kept for reference only. Use the modular files instead.
 * 
 * Shared Header and Navigation Functions
 * Used across all pages for consistent authentication and dark mode behavior
 * 
 * Updated: December 4, 2024
 */

console.warn('⚠️ header.js is deprecated. Please use HeaderAuth.js, HeaderDarkMode.js, HeaderMenu.js, HeaderSession.js, and HeaderPreferences.js instead.');

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
            const authBtnMobile = document.getElementById('auth-btn-mobile');
            if (welcomeEl) {
                welcomeEl.textContent = `Welcome, ${currentUser.username}!`;
                welcomeEl.style.display = 'inline';
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
                registerBtn.href = '/register';
            }
            if (registerBtnMobile) {
                registerBtnMobile.style.display = 'flex';
                registerBtnMobile.href = '/register';
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

/**
 * Initialize dark mode based on user preferences
 * Dark mode is enabled by default for all devices (no class needed)
 * Light mode requires explicit light-mode class
 */
function initDarkMode() {
    const toggleBtn = document.getElementById('dark-mode-toggle');
    const toggleLabel = document.getElementById('dark-mode-label');
    const toggleMenuBtn = document.getElementById('dark-mode-toggle-menu');

    // Use localStorage preference, default to dark mode
    const savedPreference = localStorage.getItem('darkMode');

    // Check if light mode is explicitly selected
    if (savedPreference === 'false') {
        // Light mode - add light-mode class
        document.documentElement.classList.add('light-mode');
        updateDarkModeUI(false, toggleBtn, toggleLabel, toggleMenuBtn);
    } else {
        // Dark mode is default - ensure light-mode class is removed
        document.documentElement.classList.remove('light-mode');
        if (savedPreference === null) {
            localStorage.setItem('darkMode', 'true');
        }
        updateDarkModeUI(true, toggleBtn, toggleLabel, toggleMenuBtn);
        removeFeedItemSummaryColors();
    }
}

/**
 * Update dark mode toggle UI elements
 * Button should show what it will DO, not current state
 * In dark mode: show "☀️ Light Mode" (clicking will enable light mode)
 * In light mode: show "🌙 Dark Mode" (clicking will enable dark mode)
 */
function updateDarkModeUI(isDark, toggleBtn, toggleLabel, toggleMenuBtn) {
    if (toggleBtn) {
        // Show sun when in dark mode (clicking enables light)
        // Show moon when in light mode (clicking enables dark)
        toggleBtn.textContent = isDark ? '☀️' : '🌙';
    }
    if (toggleLabel) {
        // Label shows what will happen when clicked
        toggleLabel.textContent = isDark ? 'Light Mode' : 'Dark Mode';
    }
    if (toggleMenuBtn) {
        const icon = toggleMenuBtn.querySelector('.menu-icon');
        if (icon) {
            // Show sun in dark mode (will switch to light)
            // Show moon in light mode (will switch to dark)
            icon.textContent = isDark ? '☀️' : '🌙';
        }
        const label = toggleMenuBtn.querySelector('.menu-label');
        if (label) {
            // Label shows what will happen when clicked
            label.textContent = isDark ? 'Light Mode' : 'Dark Mode';
        }
    }
}

/**
 * Remove inline color styles from feed item summaries in dark mode
 */
function removeFeedItemSummaryColors() {
    document.querySelectorAll('.feed-item-summary').forEach(function (el) {
        if (el.style.color) {
            el.style.removeProperty('color');
        }
    });
}

/**
 * Toggle between dark mode (default) and light mode (toggled on)
 */
function toggleDarkMode() {
    // Check if light mode is currently active
    const isCurrentlyLight = document.documentElement.classList.contains('light-mode');
    const willBeLight = !isCurrentlyLight;

    console.log('Toggle: Currently light?', isCurrentlyLight, '-> Will be light?', willBeLight);

    // Toggle light-mode class (dark mode is default, no class needed)
    if (willBeLight) {
        // Switch to light mode (toggled on)
        document.documentElement.classList.add('light-mode');
        document.body.classList.add('light-mode');
    } else {
        // Switch back to dark mode (default)
        document.documentElement.classList.remove('light-mode');
        document.body.classList.remove('light-mode');
        removeFeedItemSummaryColors();
    }

    // Force repaint to ensure background color updates
    document.documentElement.offsetHeight;

    console.log('After toggle - html classes:', document.documentElement.className);
    console.log('After toggle - body classes:', document.body.className);
    console.log('Computed bg color:', getComputedStyle(document.documentElement).backgroundColor);

    // Save preference (true = dark mode/default, false = light mode/toggled)
    localStorage.setItem('darkMode', willBeLight ? 'false' : 'true');

    // Update toggle button icon and label
    const toggleBtn = document.getElementById('dark-mode-toggle');
    const toggleLabel = document.getElementById('dark-mode-label');
    const toggleMenuBtn = document.getElementById('dark-mode-toggle-menu');

    // isDark = !willBeLight (if not light, then dark)
    updateDarkModeUI(!willBeLight, toggleBtn, toggleLabel, toggleMenuBtn);
}

/**
 * Initialize hamburger menu toggle with proper event handling
 */
function initHamburgerMenu() {
    const hamburger = document.getElementById('hamburger-menu');
    const navLinks = document.getElementById('nav-links');

    if (!hamburger || !navLinks) {
        return;
    }

    // Ensure hamburger bars exist
    if (hamburger.children.length === 0) {
        for (let i = 0; i < 3; i++) {
            const bar = document.createElement('span');
            bar.className = 'bar';
            hamburger.appendChild(bar);
        }
    }

    // Toggle menu on hamburger click
    hamburger.addEventListener('click', function (e) {
        e.stopPropagation();
        const nowOpen = !navLinks.classList.contains('open');
        hamburger.classList.toggle('open', nowOpen);
        navLinks.classList.toggle('open', nowOpen);
    });

    // Dark mode toggle in menu (don't close menu)
    const darkToggleMenu = document.getElementById('dark-mode-toggle-menu');
    console.log('Dark mode toggle button found:', darkToggleMenu);
    if (darkToggleMenu) {
        darkToggleMenu.addEventListener('click', function (e) {
            console.log('Dark mode button clicked!');
            e.stopPropagation();
            toggleDarkMode();
            // Don't close menu
        });
    }

    // Close menu on link/button click, EXCEPT for text size and dark mode buttons
    navLinks.querySelectorAll('a, button').forEach(function (el) {
        el.addEventListener('click', function (e) {
            // Don't close menu for text size buttons or dark mode toggle
            if (el.id === 'text-size-decrease' ||
                el.id === 'text-size-increase' ||
                el.id === 'dark-mode-toggle-menu' ||
                el.classList.contains('text-size-btn')) {
                return; // Don't close menu
            }
            // Close menu for everything else
            navLinks.classList.remove('open');
            hamburger.classList.remove('open');
        });
    });

    // Close menu when clicking outside
    document.addEventListener('click', function (e) {
        if (!hamburger.contains(e.target) && !navLinks.contains(e.target)) {
            navLinks.classList.remove('open');
            hamburger.classList.remove('open');
        }
    });
}

/**
 * Initialize header on page load
 * Call this in DOMContentLoaded
 */
function initHeader() {
    initDarkMode();
    setVisitorIdCookie();
    checkAuthStatus();
    initHamburgerMenu();
    initScrollHeader();
}

/**
 * Initialize scroll-responsive header
 * Shrinks header text when scrolling down on mobile
 */
function initScrollHeader() {
    const header = document.querySelector('.main-header');
    const headerTitle = document.querySelector('.main-header h1');

    if (!header || !headerTitle) return;

    let lastScrollTop = 0;
    let isScrolled = false;

    function handleScroll() {
        const scrollTop = window.pageYOffset || document.documentElement.scrollTop;

        // Trigger shrink after scrolling down 50px
        if (scrollTop > 50 && !isScrolled) {
            header.classList.add('scrolled');
            isScrolled = true;
        } else if (scrollTop <= 50 && isScrolled) {
            header.classList.remove('scrolled');
            isScrolled = false;
        }

        // lastScrollTop = scrollTop; // Removed unused assignment
    }

    // Throttle scroll events for performance
    let ticking = false;
    window.addEventListener('scroll', function () {
        if (!ticking) {
            window.requestAnimationFrame(function () {
                handleScroll();
                ticking = false;
            });
            ticking = true;
        }
    });
}

/**
 * Initialize text size controls
 */
function initTextSize() {
    const savedSize = localStorage.getItem('textSize');
    const baseSize = 16; // Base font size in pixels
    const minSize = 12;
    const maxSize = 24;
    let currentSize = savedSize ? parseInt(savedSize, 10) : baseSize;

    function applyTextSize(size) {
        // Clamp size between min and max
        size = Math.max(minSize, Math.min(maxSize, size));
        currentSize = size;
        localStorage.setItem('textSize', size.toString());

        // Create or update style tag for text sizing
        let styleTag = document.getElementById('dynamic-text-size');
        if (!styleTag) {
            styleTag = document.createElement('style');
            styleTag.id = 'dynamic-text-size';
            document.head.appendChild(styleTag);
        }

        // Use CSS rules with higher specificity instead of inline styles
        styleTag.textContent = `
            /* Dynamic text sizing - affects all text except headings */
            body, body * {
                font-size: ${size}px !important;
            }
            
            /* Keep headings and titles at their original size */
            h1, h2, h3, h4, h5, h6 {
                font-size: revert !important;
            }
            
            /* Site title - keep at original size */
            .main-header h1,
            header h1 {
                font-size: 32px !important;
            }
            
            /* Card titles - keep at original size */
            .feed-item-title {
                font-size: 28px !important;
            }
            
            /* Mobile adjustments */
            @media (max-width: 768px) {
                .main-header h1,
                header h1 {
                    font-size: 20px !important;
                }
                
                .feed-item-title {
                    font-size: 20px !important;
                }
            }
            
            /* Keep menu items and controls at fixed sizes */
            .nav-links.open .menu-icon,
            .nav-links .menu-icon,
            button .menu-icon,
            a .menu-icon {
                font-size: 28px !important;
            }
            
            .nav-links.open .menu-label,
            .nav-links .menu-label,
            button .menu-label,
            a .menu-label {
                font-size: 14px !important;
            }
            
            .text-size-btn,
            .text-size-label,
            .text-size-controls,
            .text-size-controls * {
                font-size: 14px !important;
            }
            
            .text-size-btn .menu-icon {
                font-size: 20px !important;
            }
            
            .text-size-btn .menu-label {
                font-size: 12px !important;
            }
            
            button:not(.btn-read-more):not(.btn-source),
            .hamburger, .header-btn,
            input, select, textarea {
                font-size: 14px !important;
            }
        `;
    }

    // Restore saved size
    if (savedSize) {
        applyTextSize(parseInt(savedSize, 10));
    }

    // Set up increase button
    const increaseBtn = document.getElementById('text-size-increase');
    if (increaseBtn) {
        increaseBtn.addEventListener('click', function () {
            applyTextSize(currentSize + 2);
        });
    }

    // Set up decrease button
    const decreaseBtn = document.getElementById('text-size-decrease');
    if (decreaseBtn) {
        decreaseBtn.addEventListener('click', function () {
            applyTextSize(currentSize - 2);
        });
    }

    // Re-apply text size when new feed items are loaded
    // Watch for new feed items being added to the DOM
    const feedContainer = document.getElementById('feed-container');
    if (feedContainer) {
        const observer = new MutationObserver(function () {
            if (savedSize) {
                applyTextSize(currentSize);
            }
        });
        observer.observe(feedContainer, { childList: true, subtree: true });
    }
}

// Auto-initialize if DOM is already loaded
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function () {
        initHeader();
        initTextSize();
    });
} else {
    initHeader();
    initTextSize();
}
