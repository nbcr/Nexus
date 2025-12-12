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
    const match = /(?:^|; )visitor_id=([^;]*)/.exec(document.cookie);
    if (match) visitorId = match[1];
    if (!visitorId) {
        visitorId = crypto.randomUUID ? crypto.randomUUID() : (Math.random().toString(36).substring(2, 18) + Date.now());
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

function getAccessToken() {
    const match = /(?:^|; )access_token=([^;]*)/.exec(document.cookie);
    if (match) return match[1];
    return globalThis.localStorage?.getItem('access_token') || null;
}

function setupAuthButton(btn, isLoggedIn) {
    if (!btn) return;
    const label = btn.querySelector('.menu-label');
    const icon = btn.querySelector('.menu-icon');
    
    if (isLoggedIn) {
        if (label) label.textContent = 'Logout';
        if (icon) icon.textContent = '🚪';
        btn.href = '#';
        btn.onclick = (e) => { e.preventDefault(); handleLogout(); };
    } else {
        if (label) label.textContent = 'Login';
        if (icon) icon.textContent = '🔐';
        btn.href = '/login';
        btn.onclick = null;
    }
    btn.style.display = 'flex';
}

function updateUIForAuthenticatedUser() {
    const welcomeEl = document.getElementById('user-welcome');
    if (welcomeEl) {
        welcomeEl.textContent = `Welcome, ${currentUser.username}!`;
        welcomeEl.style.display = 'inline';
    }
    
    setupAuthButton(document.getElementById('auth-btn'), true);
    setupAuthButton(document.getElementById('auth-btn-mobile'), true);
    
    const registerBtn = document.getElementById('register-btn');
    const registerBtnMobile = document.getElementById('register-btn-mobile');
    if (registerBtn) registerBtn.style.display = 'none';
    if (registerBtnMobile) registerBtnMobile.style.display = 'none';
}

function updateUIForUnauthenticatedUser() {
    const welcomeEl = document.getElementById('user-welcome');
    if (welcomeEl) welcomeEl.style.display = 'none';
    
    setupAuthButton(document.getElementById('auth-btn'), false);
    setupAuthButton(document.getElementById('auth-btn-mobile'), false);
    
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
            updateUIForAuthenticatedUser();
        } else {
            updateUIForUnauthenticatedUser();
        }
    } catch (error) {
        console.error('Auth initialization error:', error);
        updateUIForUnauthenticatedUser();
    }
}

/**
 * Handle authentication button click
 */
function handleAuth() {
    // Debug message for login button click
    // Only redirect to login if not authenticated
    globalThis.location.href = '/static/login.html';
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
        globalThis.location.href = "/logged-out.html";
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
 * Update dark mode toggle button
 */
function updateDarkModeToggleButton(isDark, toggleBtn) {
    if (!toggleBtn) return;
    toggleBtn.textContent = isDark ? '☀️' : '🌙';
}

/**
 * Update dark mode toggle label
 */
function updateDarkModeToggleLabel(isDark, toggleLabel) {
    if (!toggleLabel) return;
    toggleLabel.textContent = isDark ? 'Light Mode' : 'Dark Mode';
}

/**
 * Update dark mode menu button
 */
function updateDarkModeMenuButton(isDark, toggleMenuBtn) {
    if (!toggleMenuBtn) return;
    const icon = toggleMenuBtn.querySelector('.menu-icon');
    if (icon) {
        icon.textContent = isDark ? '☀️' : '🌙';
    }
    const label = toggleMenuBtn.querySelector('.menu-label');
    if (label) {
        label.textContent = isDark ? 'Light Mode' : 'Dark Mode';
    }
}

/**
 * Update dark mode toggle UI elements
 * Button should show what it will DO, not current state
 */
function updateDarkModeUI(isDark, toggleBtn, toggleLabel, toggleMenuBtn) {
    updateDarkModeToggleButton(isDark, toggleBtn);
    updateDarkModeToggleLabel(isDark, toggleLabel);
    updateDarkModeMenuButton(isDark, toggleMenuBtn);
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
 * Apply class changes for dark/light mode
 */
function applyModeClasses(willBeLight) {
    const htmlEl = document.documentElement;
    const bodyEl = document.body;
    if (willBeLight) {
        htmlEl.classList.add('light-mode');
        bodyEl.classList.add('light-mode');
    } else {
        htmlEl.classList.remove('light-mode');
        bodyEl.classList.remove('light-mode');
        removeFeedItemSummaryColors();
    }
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
    applyModeClasses(willBeLight);

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

function createHamburgerBars(hamburger) {
    if (hamburger.children.length === 0) {
        for (let i = 0; i < 3; i++) {
            const bar = document.createElement('span');
            bar.className = 'bar';
            hamburger.appendChild(bar);
        }
    }
}

function shouldKeepMenuOpen(element) {
    return element.id === 'text-size-decrease' ||
           element.id === 'text-size-increase' ||
           element.id === 'dark-mode-toggle-menu' ||
           element.classList.contains('text-size-btn');
}

function closeMenu(hamburger, navLinks) {
    navLinks.classList.remove('open');
    hamburger.classList.remove('open');
}

function setupMenuEventListeners(hamburger, navLinks) {
    hamburger.addEventListener('click', (e) => {
        e.stopPropagation();
        const nowOpen = !navLinks.classList.contains('open');
        hamburger.classList.toggle('open', nowOpen);
        navLinks.classList.toggle('open', nowOpen);
    });

    const darkToggleMenu = document.getElementById('dark-mode-toggle-menu');
    if (darkToggleMenu) {
        darkToggleMenu.addEventListener('click', (e) => {
            e.stopPropagation();
            toggleDarkMode();
        });
    }

    navLinks.querySelectorAll('a, button').forEach((el) => {
        el.addEventListener('click', () => {
            if (!shouldKeepMenuOpen(el)) {
                closeMenu(hamburger, navLinks);
            }
        });
    });

    document.addEventListener('click', (e) => {
        if (!hamburger.contains(e.target) && !navLinks.contains(e.target)) {
            closeMenu(hamburger, navLinks);
        }
    });
}

/**
 * Initialize hamburger menu toggle with proper event handling
 */
function initHamburgerMenu() {
    const hamburger = document.getElementById('hamburger-menu');
    const navLinks = document.getElementById('nav-links');

    if (!hamburger || !navLinks) return;

    createHamburgerBars(hamburger);
    setupMenuEventListeners(hamburger, navLinks);
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

    let isScrolled = false;

    function handleScroll() {
        const scrollTop = globalThis.pageYOffset || document.documentElement.scrollTop;

        // Trigger shrink after scrolling down 50px
        if (scrollTop > 50 && !isScrolled) {
            header.classList.add('scrolled');
            isScrolled = true;
        } else if (scrollTop <= 50 && isScrolled) {
            header.classList.remove('scrolled');
            isScrolled = false;
        }
    }

    // Throttle scroll events for performance
    let ticking = false;
    globalThis.addEventListener('scroll', function () {
        if (!ticking) {
            globalThis.requestAnimationFrame(function () {
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
    let currentSize = savedSize ? Number.parseInt(savedSize, 10) : baseSize;

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
        applyTextSize(Number.parseInt(savedSize, 10));
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
