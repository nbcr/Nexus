/**
 * Global Scroll Tracker
 * 
 * Coordinates scroll velocity across all HoverTracker instances.
 * Detects when user is scrolling slowly (potentially reading) vs quickly (browsing).
 */

class GlobalScrollTracker {
    constructor() {
        this.lastScrollTime = Date.now();
        this.lastScrollTop = 0;
        this.scrollVelocity = 0;
        this.scrollTrackers = [];
        this.throttleTimeout = null;

        this.handleScroll = this.handleScroll.bind(this);
        this.attachListener();
    }

    attachListener() {
        window.addEventListener('scroll', this.handleScroll, { passive: true });
    }

    detachListener() {
        window.removeEventListener('scroll', this.handleScroll);
        if (this.throttleTimeout) {
            clearTimeout(this.throttleTimeout);
        }
    }

    handleScroll() {
        // Throttle scroll events to 100ms
        if (this.throttleTimeout) return;

        this.throttleTimeout = setTimeout(() => {
            this.throttleTimeout = null;
            this.updateScrollVelocity();
        }, 100);
    }

    updateScrollVelocity() {
        const now = Date.now();
        const scrollTop = window.scrollY || document.documentElement.scrollTop;

        const timeDelta = now - this.lastScrollTime;
        const distanceDelta = Math.abs(scrollTop - this.lastScrollTop);

        // Calculate velocity (pixels per millisecond)
        this.scrollVelocity = timeDelta > 0 ? distanceDelta / timeDelta : 0;

        // Propagate velocity to all registered trackers
        for (let tracker of this.scrollTrackers) {
            tracker.updateScrollVelocity(this.scrollVelocity);
        }

        this.lastScrollTime = now;
        this.lastScrollTop = scrollTop;
    }

    register(hoverTracker) {
        if (!this.scrollTrackers.includes(hoverTracker)) {
            this.scrollTrackers.push(hoverTracker);
        }
    }

    unregister(hoverTracker) {
        const index = this.scrollTrackers.indexOf(hoverTracker);
        if (index > -1) {
            this.scrollTrackers.splice(index, 1);
        }
    }

    getVelocity() {
        return this.scrollVelocity;
    }

    destroy() {
        this.detachListener();
        this.scrollTrackers = [];
    }
}

// Export
window.GlobalScrollTracker = GlobalScrollTracker;
