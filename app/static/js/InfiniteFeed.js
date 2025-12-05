/**
 * Infinite Scroll Feed System (Refactored)
 * 
 * Core feed orchestrator that coordinates:
 * - FeedApi for data fetching
 * - FeedRenderer for DOM rendering
 * - FeedTracking for analytics
 * - FeedObservers for event handling
 * - FeedArticleModal for article display
 */

class InfiniteFeed {
    constructor(containerId, options = {}) {
        this.container = document.getElementById(containerId);
        if (!this.container) {
            console.error(`Container #${containerId} not found`);
            return;
        }

        // Initialize modules
        this.api = new FeedApi();
        this.tracking = new FeedTracking();
        this.renderer = new FeedRenderer(this.api, this.tracking);
        this.observers = new FeedObservers(this);
        this.modal = new FeedArticleModal(this.api);

        // Feed state
        this.currentPage = 1;
        this.pageSize = options.pageSize || 20;
        this.category = options.category || null;
        this.categories = null;
        this.isLoading = false;
        this.hasMore = true;
        this.viewedContentIds = new Set();
        this.isPersonalized = options.isPersonalized !== false;
        this.cursor = null;

        // UI elements
        this.loadingIndicator = null;
        this.endMessage = null;

        // Callbacks
        this.onContentClick = options.onContentClick || this.defaultContentClick.bind(this);

        this.init();
    }

    async init() {
        console.log('Initializing feed..');

        // Fetch user settings (including debug mode)
        const settings = await this.api.fetchUserSettings();
        window.nexusDebugMode = settings.debugMode || false;

        if (window.nexusDebugMode) {
            console.log('%c🔍 DEBUG MODE ENABLED', 'background: #00ff88; color: #000; padding: 4px 8px; font-weight: bold;');
            console.log('Interest tracking data will be visible and logged.');
        }

        // Initialize tracking module
        this.tracking.initGlobalScrollTracker();

        // Initialize history tracker if available
        if (window.historyTracker && typeof window.historyTracker.init === 'function') {
            window.historyTracker.init();
        }

        // Setup observers
        this.observers.setupScrollRefresh();

        // Create loading indicator and end message
        this.loadingIndicator = this.renderer.renderLoadingIndicator();
        this.container.after(this.loadingIndicator);
        console.log('Loading indicator created:', this.loadingIndicator);

        this.endMessage = this.renderer.renderEndMessage();
        this.loadingIndicator.after(this.endMessage);

        // Setup intersection observers
        this.observers.setupScrollObserver(this.loadingIndicator);
        this.observers.setupCardObserver();

        // Setup article modal controls
        this.modal.setupModalControls();

        // Track duration before page unload
        window.addEventListener('beforeunload', () => this.tracking.stopAllViewTimers());

        // Load initial content
        this.loadMore();
    }

    async loadMore() {
        if (this.isLoading || !this.hasMore) {
            console.log('Skipping loadMore - isLoading:', this.isLoading, 'hasMore:', this.hasMore);
            return;
        }

        console.log('Starting loadMore with cursor:', this.cursor);
        this.isLoading = true;
        this.showLoading();

        try {
            const excludeIds = Array.from(this.viewedContentIds).join(',');

            const filters = {
                excludeIds,
                categories: this.categories,
                category: this.category,
                cursor: this.cursor,
                isPersonalized: this.isPersonalized
            };

            console.log('Fetching feed with filters:', filters);
            const data = await this.api.fetchFeed(this.currentPage, this.pageSize, filters);
            console.log('Received data:', { itemCount: data.items?.length, cursor: data.next_cursor, hasMore: data.has_more });

            // Add new content items
            if (data.items && data.items.length > 0) {
                data.items.forEach((item, index) => {
                    this.viewedContentIds.add(item.content_id);
                    this.renderContentItem(item);

                    // Insert AdSense ad every 3 articles (after 3rd, 6th, 9th, etc.)
                    if ((index + 1) % 3 === 0) {
                        this.renderer.insertAdUnit(this.container);
                    }
                });

                this.currentPage++;
                this.cursor = data.next_cursor; // Update cursor for next fetch
                this.hasMore = data.has_more;
                console.log('Updated - currentPage:', this.currentPage, 'cursor:', this.cursor, 'hasMore:', this.hasMore);
            } else {
                this.hasMore = false;
                console.log('No items returned, hasMore set to false');
            }

            // Update UI
            if (!this.hasMore) {
                this.showEndMessage();
            }

        } catch (error) {
            console.error('Error loading feed:', error);
            this.showError(error.message);
        } finally {
            this.isLoading = false;
            this.hideLoading();
        }
    }

    renderContentItem(item) {
        this.renderer.renderContentItem(item, this.container, this.onContentClick);

        // Get the newly created article
        const article = this.container.querySelector(`[data-content-id="${item.content_id}"]`);
        if (article) {
            // Register hover tracker
            this.tracking.createHoverTracker(article, item.content_id);

            // Observe card for visibility tracking
            this.observers.observeCard(article);

            // Observe card for history tracking
            if (window.historyTracker) {
                window.historyTracker.observeCard(article);
            }
        }
    }

    refreshFeed(keepCount = 15) {
        if (this.isLoading) return;

        console.log(`🔄 Refreshing feed, keeping ${keepCount} cards`);

        // Get all current cards
        const cards = Array.from(this.container.querySelectorAll('.feed-item'));

        // Determine cards to remove
        const cardsToRemove = keepCount === 0 ? cards : cards.slice(keepCount);

        // If no cards to remove, exit
        if (cardsToRemove.length === 0 && keepCount > 0) {
            console.log('Not enough cards to refresh');
            return;
        }

        // Clean up removed cards
        cardsToRemove.forEach(card => {
            const contentId = parseInt(card.dataset.contentId);

            // Stop view timer
            this.tracking.stopViewTimer(contentId);

            // Cleanup hover tracker
            this.tracking.cleanupTracker(contentId);

            // Remove from viewed IDs so it can appear again in future
            this.viewedContentIds.delete(contentId);

            // Unobserve card
            this.observers.unobserveCard(card);

            // Remove from DOM
            card.remove();
        });

        // Reset pagination to allow loading more
        this.hasMore = true;
        this.currentPage = 1;
        this.cursor = null;

        // If full refresh (keepCount = 0), clear viewed IDs and reload
        if (keepCount === 0) {
            this.viewedContentIds.clear();
            this.loadMore();
        }

        // Scroll to top smoothly
        window.scrollTo({ top: 0, behavior: 'smooth' });

        console.log(`✅ Feed refreshed - removed ${cardsToRemove.length} cards, kept ${keepCount}`);
    }

    async defaultContentClick(item) {
        // Check if this is a search query item
        const isSearchQuery = FeedUtils.isSearchQuery(item);

        console.log('🔍 Content click:', {
            content_id: item.content_id,
            title: item.title,
            category: item.category,
            content_type: item.content_type,
            tags: item.tags,
            source_url: item.source_urls?.[0],
            isSearchQuery
        });

        // For both search queries and news articles, open modal to show content
        console.log('📰 Opening modal for:', isSearchQuery ? 'search context' : 'article');
        this.modal.openArticleModal(item, isSearchQuery);
    }

    showLoading() {
        const spinner = this.loadingIndicator.querySelector('.spinner');
        const text = this.loadingIndicator.querySelector('p');
        if (spinner) spinner.style.display = 'block';
        if (text) text.style.display = 'block';
    }

    hideLoading() {
        const spinner = this.loadingIndicator.querySelector('.spinner');
        const text = this.loadingIndicator.querySelector('p');
        if (spinner) spinner.style.display = 'none';
        if (text) text.style.display = 'none';
    }

    showEndMessage() {
        this.endMessage.style.display = 'block';
        this.hideLoading();
    }

    showError(message) {
        const errorDiv = this.renderer.renderErrorMessage(message);
        this.container.appendChild(errorDiv);
    }

    // Public API methods
    reset() {
        this.tracking.cleanupAllTrackers();
        this.currentPage = 1;
        this.cursor = null;
        this.viewedContentIds.clear();
        this.hasMore = true;
        this.container.innerHTML = '';
        this.endMessage.style.opacity = '0';
        this.endMessage.style.display = 'none';
        this.loadingIndicator.style.display = 'block';
        this.loadMore();
    }

    setCategory(category) {
        this.category = category;
        this.categories = null;
        this.reset();
    }

    setCategories(categories) {
        // null = show everything; array = filter by those categories
        this.categories = (categories === null || (Array.isArray(categories) && categories.length > 0)) ? categories : null;
        this.category = null;
        this.reset();
    }

    destroy() {
        this.tracking.destroy();
        this.observers.destroy();
        window.removeEventListener('beforeunload', () => this.tracking.stopAllViewTimers());
    }
}

// Export for use in other scripts
window.InfiniteFeed = InfiniteFeed;

// Setup modal controls on page load
document.addEventListener('DOMContentLoaded', function () {
    // Modal controls will be set up by FeedArticleModal.setupModalControls()
    // Called during InfiniteFeed initialization
});
