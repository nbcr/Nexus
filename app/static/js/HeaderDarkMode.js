/**
 * Header Dark Mode Module
 * 
 * Handles:
 * - Dark mode initialization
 * - Dark/light mode toggle
 * - Dark mode UI updates
 */

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
    const isCurrentlyLight = document.documentElement.classList.contains('light-mode');
    const willBeLight = !isCurrentlyLight;

    console.log('Toggle: Currently light?', isCurrentlyLight, '-> Will be light?', willBeLight);

    applyModeChange(willBeLight);
    savePreference(willBeLight);
    updateUIElements(willBeLight);
    
    if (!willBeLight) {
        removeFeedItemSummaryColors();
    }
}

function applyModeChange(willBeLight) {
    if (willBeLight) {
        document.documentElement.classList.add('light-mode');
    } else {
        document.documentElement.classList.remove('light-mode');
    }
}

function savePreference(willBeLight) {
    localStorage.setItem('darkMode', String(!willBeLight));
}

function updateUIElements(willBeLight) {
    const toggleBtn = document.getElementById('dark-mode-toggle');
    const toggleLabel = document.getElementById('dark-mode-label');
    const toggleMenuBtn = document.getElementById('dark-mode-toggle-menu');
    updateDarkModeUI(!willBeLight, toggleBtn, toggleLabel, toggleMenuBtn);
}

// Export namespace and global functions
globalThis.HeaderDarkMode = { initDarkMode, toggleDarkMode };
globalThis.toggleDarkMode = toggleDarkMode;
