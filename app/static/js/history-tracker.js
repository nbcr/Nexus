/**
 * Content History Tracker
 * Automatically tracks when content enters viewport and records views
 */

class HistoryTracker {
    constructor() {
        this.observer = null;
        this.seenContentIds = new Set();
        this.clickedContentIds = new Set();
        this.apiBase = '/api/v1/history';
    }

    /**
     * Initialize the history tracker with intersection observer
     */
    init() {
        // Create intersection observer to detect when cards enter viewport
        const options = {
            root: null, // viewport
            rootMargin: '0px',
            threshold: 0.5 // 50% of card must be visible
        };

        this.observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    this.handleCardVisible(entry.target);
                }
            });
        }, options);

        // Load seen IDs from server to prevent re-recording
        this.loadSeenContent();

        console.log('[HistoryTracker] Initialized');
    }

    /**
     * Load already-seen content IDs from server
     */
    async loadSeenContent() {
        try {
            const response = await fetch(`${this.apiBase}/seen-ids`, {
                credentials: 'include'
            });

            if (response.ok) {
                const data = await response.json();
                this.seenContentIds = new Set(data.seen_ids);
                console.log(`[HistoryTracker] Loaded ${this.seenContentIds.size} seen items`);
            }
        } catch (error) {
            console.error('[HistoryTracker] Failed to load seen content:', error);
        }
    }

    /**
     * Observe a card element for visibility tracking
     * @param {HTMLElement} cardElement - The card DOM element
     */
    observeCard(cardElement) {
        if (this.observer && cardElement) {
            this.observer.observe(cardElement);
        }
    }

    /**
     * Stop observing a card
     * @param {HTMLElement} cardElement - The card DOM element
     */
    unobserveCard(cardElement) {
        if (this.observer && cardElement) {
            this.observer.unobserve(cardElement);
        }
    }

    /**
     * Handle card becoming visible in viewport
     * @param {HTMLElement} cardElement - The visible card element
     */
    async handleCardVisible(cardElement) {
        const contentId = parseInt(cardElement.dataset.contentId);
        const contentSlug = cardElement.dataset.contentSlug;

        if (!contentId || !contentSlug) {
            console.warn('[HistoryTracker] Card missing content ID or slug');
            return;
        }

        // Skip if already recorded as seen
        if (this.seenContentIds.has(contentId)) {
            return;
        }

        // Record as seen
        await this.recordView(contentId, contentSlug, 'seen');
        this.seenContentIds.add(contentId);

        // Stop observing this card since it's been recorded
        this.unobserveCard(cardElement);

        console.log(`[HistoryTracker] Recorded view: ${contentSlug}`);
    }

    /**
     * Record a click on content
     * @param {number} contentId - Content item ID
     * @param {string} contentSlug - Content unique slug
     */
    async recordClick(contentId, contentSlug) {
        if (this.clickedContentIds.has(contentId)) {
            return; // Already recorded
        }

        await this.recordView(contentId, contentSlug, 'clicked');
        this.clickedContentIds.add(contentId);

        console.log(`[HistoryTracker] Recorded click: ${contentSlug}`);
    }

    /**
     * Record a view to the server
     * @param {number} contentId - Content item ID
     * @param {string} contentSlug - Content unique slug
     * @param {string} viewType - Type of view ('seen', 'clicked', 'read')
     */
    async recordView(contentId, contentSlug, viewType) {
        try {
            const response = await fetch(`${this.apiBase}/record`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                credentials: 'include',
                body: JSON.stringify({
                    content_id: contentId,
                    content_slug: contentSlug,
                    view_type: viewType
                })
            });

            if (!response.ok) {
                throw new Error(`Failed to record view: ${response.status}`);
            }
        } catch (error) {
            console.error(`[HistoryTracker] Error recording ${viewType}:`, error);
        }
    }

    /**
     * Get user's view history
     * @param {string} viewType - Optional filter ('seen', 'clicked', 'read')
     * @param {number} page - Page number
     * @returns {Promise<Object>} History response with items
     */
    async getHistory(viewType = null, page = 1) {
        try {
            let url = `${this.apiBase}/viewed?page=${page}`;
            if (viewType) {
                url += `&view_type=${viewType}`;
            }

            const response = await fetch(url, {
                credentials: 'include'
            });

            if (response.ok) {
                return await response.json();
            } else {
                throw new Error(`Failed to fetch history: ${response.status}`);
            }
        } catch (error) {
            console.error('[HistoryTracker] Error fetching history:', error);
            return { items: [], total: 0, has_more: false };
        }
    }

    /**
     * Clear user's history
     * @param {string} viewType - Optional type to clear, or all if null
     */
    async clearHistory(viewType = null) {
        try {
            let url = `${this.apiBase}/clear`;
            if (viewType) {
                url += `?view_type=${viewType}`;
            }

            const response = await fetch(url, {
                method: 'DELETE',
                credentials: 'include'
            });

            if (response.ok) {
                // Clear local cache
                if (!viewType || viewType === 'seen') {
                    this.seenContentIds.clear();
                }
                if (!viewType || viewType === 'clicked') {
                    this.clickedContentIds.clear();
                }
                console.log('[HistoryTracker] History cleared');
                return true;
            } else {
                throw new Error(`Failed to clear history: ${response.status}`);
            }
        } catch (error) {
            console.error('[HistoryTracker] Error clearing history:', error);
            return false;
        }
    }

    /**
     * Cleanup - disconnect observer
     */
    destroy() {
        if (this.observer) {
            this.observer.disconnect();
            this.observer = null;
        }
    }
}

// Create global instance
window.historyTracker = new HistoryTracker();
