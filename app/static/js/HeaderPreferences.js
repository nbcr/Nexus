/**
 * Header Preferences Module
 * 
 * Handles:
 * - Text size adjustments
 * - Scroll-responsive header effects
 */

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

        lastScrollTop = scrollTop;
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

// Export
window.HeaderPreferences = { initTextSize, initScrollHeader };
