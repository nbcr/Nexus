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
    const regex = /(?:^|; )visitor_id=([^;]*)/;
    const match = regex.exec(document.cookie);
    if (match) visitorId = match[1];
    if (!visitorId) {
        visitorId = crypto.randomUUID ? crypto.randomUUID() : (Math.random().toString(36).substring(2, 18) + Date.now());
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
globalThis.HeaderSession = { setVisitorIdCookie, initHeader };
globalThis.initHeader = initHeader;
globalThis.setVisitorIdCookie = setVisitorIdCookie;
