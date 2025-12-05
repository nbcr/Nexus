/**
 * Header Session & Visitor Tracking Module
 * 
 * Handles:
 * - Visitor ID cookie persistence
 * - Header initialization
 * - Main DOMContentLoaded listener
 */

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
 * Initialize header on page load
 * Call this in DOMContentLoaded
 */
function initHeader() {
    initDarkMode();
    setVisitorIdCookie();
    checkAuthStatus();
    initHamburgerMenu();
    initScrollHeader();
    initTextSize();
}

/**
 * Initialize on DOM content loaded
 */
document.addEventListener('DOMContentLoaded', function () {
    initHeader();
});

// Export namespace and global functions
window.HeaderSession = { setVisitorIdCookie, initHeader };
window.initHeader = initHeader;
window.setVisitorIdCookie = setVisitorIdCookie;
