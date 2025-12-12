/**
 * Header Dark Mode Module
 * 
 * Handles:
 * - Dark mode initialization
 * - Dark/light mode toggle
 * - Dark mode UI updates
 */

/**
 * Get UI elements for dark mode toggle
 */
function getDarkModeElements() {
    return {
        toggleBtn: document.getElementById('dark-mode-toggle'),
        toggleLabel: document.getElementById('dark-mode-label'),
        toggleMenuBtn: document.getElementById('dark-mode-toggle-menu')
    };
}

/**
 * Apply light mode settings
 */
function applyLightMode(elements) {
    document.documentElement.classList.add('light-mode');
    updateDarkModeUI(false, elements.toggleBtn, elements.toggleLabel, elements.toggleMenuBtn);
}

/**
 * Apply dark mode settings
 */
function applyDarkMode(elements) {
    document.documentElement.classList.remove('light-mode');
    updateDarkModeUI(true, elements.toggleBtn, elements.toggleLabel, elements.toggleMenuBtn);
    removeFeedItemSummaryColors();
}

/**
 * Initialize dark mode based on user preferences
 * Dark mode is enabled by default for all devices (no class needed)
 * Light mode requires explicit light-mode class
 */
function initDarkMode() {
    const elements = getDarkModeElements();
    const savedPreference = localStorage.getItem('darkMode');

    if (savedPreference === 'false') {
        applyLightMode(elements);
    } else {
        if (savedPreference === null) {
            localStorage.setItem('darkMode', 'true');
        }
        applyDarkMode(elements);
    }
}

/**
 * Update toggle button content
 */
function updateToggleButton(toggleBtn, isDark) {
    if (toggleBtn) {
        toggleBtn.textContent = isDark ? '☀️' : '🌙';
    }
}

/**
 * Update toggle label content
 */
function updateToggleLabel(toggleLabel, isDark) {
    if (toggleLabel) {
        toggleLabel.textContent = isDark ? 'Light Mode' : 'Dark Mode';
    }
}

/**
 * Update menu button content
 */
function updateMenuButton(toggleMenuBtn, isDark) {
    if (toggleMenuBtn) {
        const icon = toggleMenuBtn.querySelector('.menu-icon');
        if (icon) {
            icon.textContent = isDark ? '☀️' : '🌙';
        }
        const label = toggleMenuBtn.querySelector('.menu-label');
        if (label) {
            label.textContent = isDark ? 'Light Mode' : 'Dark Mode';
        }
    }
}

/**
 * Update dark mode toggle UI elements
 * Button should show what it will DO, not current state
 * In dark mode: show "☀️ Light Mode" (clicking will enable light mode)
 * In light mode: show "🌙 Dark Mode" (clicking will enable dark mode)
 */
function updateDarkModeUI(isDark, toggleBtn, toggleLabel, toggleMenuBtn) {
    updateToggleButton(toggleBtn, isDark);
    updateToggleLabel(toggleLabel, isDark);
    updateMenuButton(toggleMenuBtn, isDark);
}

/**
 * Remove inline color styles from feed item summaries in dark mode
 */
function removeFeedItemSummaryColors() {
    document.querySelectorAll('.feed-item-summary').forEach(el => {
        if (el.style.color) {
            el.style.removeProperty('color');
        }
    });
}

/**
 * Apply mode change to document
 */
function applyModeChange(willBeLight) {
    if (willBeLight) {
        document.documentElement.classList.add('light-mode');
    } else {
        document.documentElement.classList.remove('light-mode');
    }
}

/**
 * Save user preference to localStorage
 */
function savePreference(willBeLight) {
    localStorage.setItem('darkMode', String(!willBeLight));
}

/**
 * Update UI elements after mode change
 */
function updateUIElements(willBeLight) {
    const toggleBtn = document.getElementById('dark-mode-toggle');
    const toggleLabel = document.getElementById('dark-mode-label');
    const toggleMenuBtn = document.getElementById('dark-mode-toggle-menu');
    updateDarkModeUI(!willBeLight, toggleBtn, toggleLabel, toggleMenuBtn);
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

// Export namespace and global functions
globalThis.HeaderDarkMode = { 
    initDarkMode, 
    toggleDarkMode, 
    applyModeChange, 
    savePreference, 
    updateUIElements 
};
globalThis.toggleDarkMode = toggleDarkMode;
