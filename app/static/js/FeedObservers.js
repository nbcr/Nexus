/**
 * FeedObservers Module
 * Manages all IntersectionObservers for infinite scroll and card visibility
 */

class FeedObservers {
    constructor(feed) {
        this.feed = feed;
        this.scrollObserver = null;
        this.cardObserver = null;
        this.lastScrollY = globalThis.scrollY;
        this.scrollUpDistance = 0;
        this.scrollTimeout = null;
    }

    setupScrollObserver(loadingIndicator) {
        const options = {
            root: null,
            rootMargin: '200px', // Start loading 200px before reaching the bottom
            threshold: 0.1
        };

        this.scrollObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                const rect = entry.boundingClientRect;
                console.log('Intersection Event:', {
                    isIntersecting: entry.isIntersecting,
                    intersectionRatio: entry.intersectionRatio,
                    isLoading: this.feed.isLoading,
                    hasMore: this.feed.hasMore,
                    boundingRect: { top: rect.top, bottom: rect.bottom, height: rect.height }
                });
                if (entry.isIntersecting && !this.feed.isLoading && this.feed.hasMore) {
                    console.log('🔄 Triggering loadMore for page:', this.feed.currentPage);
                    this.feed.loadMore();
                }
            });
        }, options);

        this.scrollObserver.observe(loadingIndicator);
        console.log('Intersection Observer setup complete');
    }

    setupCardObserver() {
        // Observer to track when cards are visible
        const options = {
            root: null,
            rootMargin: '0px',
            threshold: 0.1
        };

        this.cardObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                const contentId = Number.parseInt(entry.target.dataset.contentId, 10);

                if (entry.isIntersecting) {
                    // Card became visible
                    this.feed.tracking.startViewTimer(contentId);
                } else {
                    // Card left viewport
                    this.feed.tracking.stopViewTimer(contentId);

                    // Report interest if hover tracker exists
                    this.feed.tracking.reportHoverTracker(contentId);
                }
            });
        }, options);
    }

    observeCard(card) {
        if (this.cardObserver) {
            this.cardObserver.observe(card);
        }
    }

    unobserveCard(card) {
        if (this.cardObserver) {
            this.cardObserver.unobserve(card);
        }
    }

    setupScrollRefresh() {
        const REFRESH_THRESHOLD = 300; // Pixels to scroll up to trigger refresh
        const KEEP_CARDS_COUNT = 15; // Number of cards to keep after refresh

        const scrollHandler = () => {
            const currentScrollY = globalThis.scrollY;

            // Only track upward scrolling near the top
            if (currentScrollY < this.lastScrollY && currentScrollY < 500) {
                this.scrollUpDistance += this.lastScrollY - currentScrollY;

                // If scrolled up enough, trigger refresh
                if (this.scrollUpDistance > REFRESH_THRESHOLD) {
                    this.feed.refreshFeed(KEEP_CARDS_COUNT);
                    this.scrollUpDistance = 0; // Reset counter
                }
            } else if (currentScrollY > this.lastScrollY) {
                // Reset counter when scrolling down
                this.scrollUpDistance = 0;
            }

            this.lastScrollY = currentScrollY;
        };

        // Throttle scroll events
        globalThis.addEventListener('scroll', () => {
            if (this.scrollTimeout) clearTimeout(this.scrollTimeout);
            this.scrollTimeout = setTimeout(scrollHandler, 50);
        });
    }

    destroy() {
        if (this.scrollObserver) {
            this.scrollObserver.disconnect();
            this.scrollObserver = null;
        }
        if (this.cardObserver) {
            this.cardObserver.disconnect();
            this.cardObserver = null;
        }
        if (this.scrollTimeout) {
            clearTimeout(this.scrollTimeout);
        }
    }
}

globalThis.FeedObservers = FeedObservers;
