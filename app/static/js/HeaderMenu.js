/**
 * Header Menu Module
 * 
 * Handles:
 * - Hamburger menu toggle
 * - Mobile navigation menu
 * - Menu item click events
 */

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

// Export
window.HeaderMenu = { initHamburgerMenu };
