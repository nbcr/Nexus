/**
 * FeedTracking Module
 * Handles view duration tracking, hover tracking, and analytics
 */

class FeedTracking {
    constructor() {
        this.viewStartTimes = new Map(); // content_id -> timestamp
        this.viewDurations = new Map(); // content_id -> total seconds
        this.hoverTrackers = new Map(); // content_id -> HoverTracker instance
        this.globalScrollTracker = null;
    }

    initGlobalScrollTracker() {
        if (window.HoverTracker && window.GlobalScrollTracker && !this.globalScrollTracker) {
            this.globalScrollTracker = new GlobalScrollTracker();
        }
    }

    createHoverTracker(card, contentId) {
        if (window.HoverTracker && this.globalScrollTracker) {
            const tracker = new HoverTracker(card, contentId);
            this.hoverTrackers.set(contentId, tracker);
            this.globalScrollTracker.register(tracker);
            return tracker;
        }
        return null;
    }

    cleanupTracker(contentId) {
        const tracker = this.hoverTrackers.get(contentId);
        if (tracker) {
            if (this.globalScrollTracker) {
                this.globalScrollTracker.unregister(tracker);
            }
            tracker.destroy();
            this.hoverTrackers.delete(contentId);
        }
    }

    cleanupAllTrackers() {
        this.hoverTrackers.forEach(tracker => tracker.destroy());
        this.hoverTrackers.clear();
    }

    startViewTimer(contentId) {
        if (!this.viewStartTimes.has(contentId)) {
            this.viewStartTimes.set(contentId, Date.now());
            console.log(`⏱️ Started timer for content ${contentId}`);
        }
    }

    stopViewTimer(contentId) {
        if (this.viewStartTimes.has(contentId)) {
            const startTime = this.viewStartTimes.get(contentId);
            const duration = Math.floor((Date.now() - startTime) / 1000); // Convert to seconds

            // Add to accumulated duration
            const currentDuration = this.viewDurations.get(contentId) || 0;
            this.viewDurations.set(contentId, currentDuration + duration);

            this.viewStartTimes.delete(contentId);

            console.log(`⏹️ Stopped timer for content ${contentId}. Duration: ${duration}s, Total: ${currentDuration + duration}s`);

            // Send duration to server if it's significant (more than 2 seconds)
            if (currentDuration + duration >= 2) {
                this.sendDuration(contentId, currentDuration + duration);
            }
        }
    }

    async sendDuration(contentId, durationSeconds) {
        // Duration tracking disabled - endpoint not implemented yet
        return;
    }

    stopAllViewTimers() {
        // Stop all active timers and send durations
        this.viewStartTimes.forEach((startTime, contentId) => {
            this.stopViewTimer(contentId);
        });
    }

    reportHoverTracker(contentId) {
        const tracker = this.hoverTrackers.get(contentId);
        if (tracker) {
            tracker.forceReport();
        }
    }

    destroy() {
        this.cleanupAllTrackers();
        this.stopAllViewTimers();
        if (this.globalScrollTracker) {
            this.globalScrollTracker.destroy();
            this.globalScrollTracker = null;
        }
    }
}

window.FeedTracking = FeedTracking;
