/**
 * Infinite Scroll Feed System
 * 
 * Handles:
 * - Loading personalized content feed
 * - Infinite scroll pagination
 * - Content tracking and exclusion
 * - Category filtering
 */

class InfiniteFeed {
    constructor(containerId, options = {}) {
        this.container = document.getElementById(containerId);
        if (!this.container) {
            console.error(`Container #${containerId} not found`);
            return;
        }

        this.currentPage = 1;
        this.pageSize = options.pageSize || 20;
        this.category = options.category || null;
        this.categories = null;
        this.isLoading = false;
        this.hasMore = true;
        this.viewedContentIds = new Set();
        this.isPersonalized = options.isPersonalized !== false;
        this.cursor = null; // Timestamp cursor for pagination

        // View duration tracking
        this.viewStartTimes = new Map(); // content_id -> timestamp
        this.viewDurations = new Map(); // content_id -> total seconds
        this.cardObserver = null;

        // Advanced hover interest tracking
        this.hoverTrackers = new Map(); // content_id -> HoverTracker instance
        this.globalScrollTracker = null;

        // Callbacks
        this.onContentClick = options.onContentClick || this.defaultContentClick.bind(this);
        this.renderContentItem = options.renderContentItem || this.defaultRenderContent.bind(this);

        this.init();
    }

    init() {
        console.log('Initializing feed..');

        // Fetch user settings (including debug mode)
        this.fetchUserSettings();

        // Initialize global scroll tracker if not already created
        if (window.HoverTracker && window.GlobalScrollTracker && !this.globalScrollTracker) {
            this.globalScrollTracker = new GlobalScrollTracker();
        }

        // Initialize history tracker if available
        if (window.historyTracker && typeof window.historyTracker.init === 'function') {
            window.historyTracker.init();
        }

        // Setup TikTok-style scroll-to-top refresh behavior
        this.setupScrollRefresh();

        // Create loading indicator
        this.loadingIndicator = document.createElement('div');
        this.loadingIndicator.className = 'feed-loading';
        this.loadingIndicator.innerHTML = `
            <div class="spinner"></div>
            <p>Loading more content...</p>
        `;
        this.loadingIndicator.style.display = 'block';
        this.loadingIndicator.style.minHeight = '100px';
        this.container.after(this.loadingIndicator);
        console.log('Loading indicator created:', this.loadingIndicator);

        // Create end message
        this.endMessage = document.createElement('div');
        this.endMessage.className = 'feed-end';
        this.endMessage.innerHTML = '<p>You\'ve reached the end of the feed!</p>';
        this.endMessage.style.display = 'none';
        this.loadingIndicator.after(this.endMessage);

        // Setup intersection observer for infinite scroll
        this.setupIntersectionObserver();

        // Setup card visibility observer for duration tracking
        this.setupCardObserver();

        // Track duration before page unload
        window.addEventListener('beforeunload', () => this.sendAllDurations());

        // Load initial content
        this.loadMore();
    }

    async fetchUserSettings() {
        try {
            // Get access token from cookie or localStorage
            let accessToken = null;
            const match = document.cookie.match(/(?:^|; )access_token=([^;]*)/);
            if (match) accessToken = match[1];
            if (!accessToken && window.localStorage) {
                accessToken = localStorage.getItem('access_token');
            }
            const headers = accessToken ? { 'Authorization': `Bearer ${accessToken}` } : {};
            const response = await fetch('/api/v1/settings/hover-tracker', {
                credentials: 'include',
                headers
            });

            if (response.ok) {
                const settings = await response.json();
                // Set global debug mode flag
                window.nexusDebugMode = settings.debugMode || false;

                // If debug mode is on, add a visual indicator
                if (window.nexusDebugMode) {
                    console.log('%c🔍 DEBUG MODE ENABLED', 'background: #00ff88; color: #000; padding: 4px 8px; font-weight: bold;');
                    console.log('Interest tracking data will be visible and logged.');
                }
            }
        } catch (error) {
            // Silently fail - user not authenticated or settings unavailable
            window.nexusDebugMode = false;
        }
    }

    setupScrollRefresh() {
        let lastScrollY = window.scrollY;
        let scrollUpDistance = 0;
        const REFRESH_THRESHOLD = 300; // Pixels to scroll up to trigger refresh
        const KEEP_CARDS_COUNT = 15; // Number of cards to keep after refresh

        const scrollHandler = () => {
            const currentScrollY = window.scrollY;

            // Only track upward scrolling near the top
            if (currentScrollY < lastScrollY && currentScrollY < 500) {
                scrollUpDistance += lastScrollY - currentScrollY;

                // If scrolled up enough, trigger refresh
                if (scrollUpDistance > REFRESH_THRESHOLD) {
                    this.refreshFeed(KEEP_CARDS_COUNT);
                    scrollUpDistance = 0; // Reset counter
                }
            } else if (currentScrollY > lastScrollY) {
                // Reset counter when scrolling down
                scrollUpDistance = 0;
            }

            lastScrollY = currentScrollY;
        };

        // Throttle scroll events
        let scrollTimeout;
        window.addEventListener('scroll', () => {
            if (scrollTimeout) clearTimeout(scrollTimeout);
            scrollTimeout = setTimeout(scrollHandler, 50);
        });
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
            this.stopViewTimer(contentId);

            // Cleanup hover tracker
            const tracker = this.hoverTrackers.get(contentId);
            if (tracker) {
                tracker.destroy();
                this.hoverTrackers.delete(contentId);
            }

            // Remove from viewed IDs so it can appear again in future
            this.viewedContentIds.delete(contentId);

            // Unobserve card
            if (this.cardObserver) {
                this.cardObserver.unobserve(card);
            }

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

    setupIntersectionObserver() {
        const options = {
            root: null,
            rootMargin: '200px', // Start loading 200px before reaching the bottom
            threshold: 0.1
        };

        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                const rect = entry.boundingClientRect;
                console.log('Intersection Event:', {
                    isIntersecting: entry.isIntersecting,
                    intersectionRatio: entry.intersectionRatio,
                    isLoading: this.isLoading,
                    hasMore: this.hasMore,
                    boundingRect: { top: rect.top, bottom: rect.bottom, height: rect.height }
                });
                if (entry.isIntersecting && !this.isLoading && this.hasMore) {
                    console.log('🔄 Triggering loadMore for page:', this.currentPage);
                    this.loadMore();
                }
            });
        }, options);

        observer.observe(this.loadingIndicator);
        console.log('Intersection Observer setup complete');
    }

    setupCardObserver() {
        // Observer to track when cards are visible
        const options = {
            root: null,
            rootMargin: '0px',
            threshold: 0.5 // Card is considered visible when 50% is in viewport
        };

        this.cardObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                const contentId = parseInt(entry.target.dataset.contentId);

                if (entry.isIntersecting) {
                    // Card became visible
                    this.startViewTimer(contentId);
                } else {
                    // Card left viewport
                    this.stopViewTimer(contentId);

                    // Report interest if hover tracker exists
                    const tracker = this.hoverTrackers.get(contentId);
                    if (tracker) {
                        tracker.forceReport();
                    }
                }
            });
        }, options);
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

    sendAllDurations() {
        // Stop all active timers and send durations
        this.viewStartTimes.forEach((startTime, contentId) => {
            this.stopViewTimer(contentId);
        });
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
            const endpoint = this.isPersonalized ? '/api/v1/content/feed' : '/api/v1/content/trending-feed';

            const params = new URLSearchParams({
                page: this.currentPage,
                page_size: this.pageSize
            });

            if (excludeIds) params.append('exclude_ids', excludeIds);
            // Only filter if categories/category is set (null or empty = show everything)
            if (this.categories !== null && Array.isArray(this.categories) && this.categories.length > 0) {
                params.append('categories', this.categories.join(','));
            } else if (this.category) {
                params.append('category', this.category);
            }
            // If both are null/undefined, don't add any category filter = show all
            if (this.cursor) params.append('cursor', this.cursor);

            console.log('Fetching:', `${endpoint}?${params}`);
            const response = await fetch(`${endpoint}?${params}`);

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            console.log('Received data:', { itemCount: data.items?.length, cursor: data.next_cursor, hasMore: data.has_more });

            // Add new content items
            if (data.items && data.items.length > 0) {
                data.items.forEach((item, index) => {
                    this.viewedContentIds.add(item.content_id);
                    this.renderContentItem(item);

                    // Insert AdSense ad every 3 articles (after 3rd, 6th, 9th, etc.)
                    if ((index + 1) % 3 === 0) {
                        this.insertAdUnit();
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

    defaultRenderContent(item) {
        const article = document.createElement('article');
        article.className = 'feed-item';
        article.dataset.contentId = item.content_id;
        article.dataset.contentSlug = item.slug || `content-${item.content_id}`;  // Add slug for history tracking
        article.dataset.topicId = item.topic_id;

        // Get image from source metadata
        const imageUrl = item.source_metadata?.picture_url || null;
        const source = item.source_metadata?.source || 'News';

        // Check if this is a search query or news article
        const isSearchQuery = item.category === 'Search Query' ||
            (item.source_urls && item.source_urls[0] &&
                (item.source_urls[0].includes('google.com/search') ||
                    item.source_urls[0].includes('duckduckgo.com')));
        const isNewsArticle = !isSearchQuery && (item.content_type === 'news' || item.content_type === 'news_update' || item.content_type === 'trending_analysis');

        article.innerHTML = `
            <div class="feed-item-content">
                <div class="feed-item-header">
                    ${imageUrl ? `
                        <div class="feed-item-image">
                            <img src="${imageUrl}" alt="${item.title}" loading="lazy" crossorigin="anonymous"
                                 onerror="this.parentElement.style.display='none'">
                        </div>
                    ` : ''}
                    <div class="feed-item-header-content">
                        <div class="feed-item-meta">
                            <span class="feed-item-category">${item.category || 'Trending'}</span>
                            ${item.relevance_score && window.nexusDebugMode ? `
                                <span class="feed-item-relevance" title="Relevance to your interests">
                                    ${Math.round(item.relevance_score * 100)}% match
                                </span>
                            ` : ''}
                            <span class="feed-item-source">${source}</span>
                        </div>
                        <h2 class="feed-item-title">${item.title}</h2>
                        ${item.description ? `<p class="feed-item-description">${item.description}</p>` : ''}
                        <span class="expand-indicator">▼</span>
                    </div>
                </div>
                <div class="feed-item-expanded-content">
                    <div class="content-inner">
                        ${(item.content_text || item.description) ? `
                            <p class="feed-item-summary">${this.truncateText(item.content_text || item.description, 400)}</p>
                        ` : '<p class="feed-item-summary" style="font-style: italic;">No snippet available</p>'}
                        <div class="feed-item-actions">
                            ${isNewsArticle ? `
                                <button class="btn-read-more" data-content-id="${item.content_id}">
                                    Read Facts
                                </button>
                            ` : isSearchQuery ? `
                                <button class="btn-read-more" data-content-id="${item.content_id}">
                                    Show Search Context
                                </button>
                            ` : ''}
                            ${item.source_urls && item.source_urls.length > 0 ? `
                                <a href="${item.source_urls[0]}" target="_blank" rel="noopener" 
                                   class="btn-source">
                                    ${this.getSourceButtonText(item)}
                                </a>
                            ` : ''}
                            <span class="feed-item-time">${this.formatTime(item.created_at)}</span>
                        </div>
                        ${item.tags && item.tags.length > 0 ? `
                            <div class="feed-item-tags">
                                ${item.tags.map(tag => `<span class="tag">${tag}</span>`).join('')}
                            </div>
                        ` : ''}
                        ${item.related_queries && item.related_queries.length > 0 ? `
                            <div class="feed-item-related">
                                <h4 class="related-title">🔍 Related Searches:</h4>
                                <div class="related-queries">
                                    ${item.related_queries.map(query => `
                                        <a href="${query.url}" target="_blank" rel="noopener" class="related-query">
                                            ${query.title}
                                        </a>
                                    `).join('')}
                                </div>
                            </div>
                        ` : ''}
                    </div>
                </div>
            </div>
        `;

        // Add click handler for card header to expand/collapse
        const header = article.querySelector('.feed-item-header');
        if (header) {
            header.addEventListener('click', async (e) => {
                // Don't toggle if clicking on image or buttons
                if (!e.target.closest('.feed-item-image')) {
                    const wasExpanded = article.classList.contains('expanded');
                    article.classList.toggle('expanded');

                    // If expanding for the first time and no snippet, fetch it
                    if (!wasExpanded && !article.dataset.snippetLoaded && isNewsArticle) {
                        const summaryEl = article.querySelector('.feed-item-summary');
                        if (summaryEl && (summaryEl.textContent.includes('No snippet available') || summaryEl.textContent.trim().length < 50)) {
                            summaryEl.innerHTML = '<em>📰 Fetching article content...</em>';
                            try {
                                const response = await fetch(`/api/v1/content/snippet/${item.content_id}`);
                                if (response.ok) {
                                    const data = await response.json();
                                    if (data.rate_limited) {
                                        summaryEl.innerHTML = `<div style="background: #fff3cd; border: 2px solid #ffc107; border-radius: 8px; padding: 15px; margin: 10px 0;">
                                            <p style="margin: 0; color: #856404; font-size: 16px;">😅 ${data.message}</p>
                                        </div>`;
                                        article.dataset.snippetLoaded = 'rate-limited';
                                    } else if (data.snippet) {
                                        summaryEl.innerHTML = `<p style="line-height: 1.8;">${data.snippet}</p>${data.full_content_available ? '<p style="color: #007bff; font-size: 14px; margin-top: 10px;">✓ Full article content available</p>' : ''}`;
                                        article.dataset.snippetLoaded = 'true';
                                    } else {
                                        summaryEl.innerHTML = '<em>No preview available from this source</em>';
                                    }
                                } else {
                                    summaryEl.innerHTML = '<em>Unable to load preview</em>';
                                }
                            } catch (error) {
                                console.error('Error loading snippet:', error);
                                summaryEl.innerHTML = '<em>Error loading preview</em>';
                            }
                        }
                    }

                    // Fetch and display related content if expanding for the first time
                    if (!wasExpanded && !article.dataset.relatedLoaded) {
                        const contentInner = article.querySelector('.content-inner');
                        if (contentInner) {
                            try {
                                const response = await fetch(`/api/v1/content/related/${item.content_id}`);
                                if (response.ok) {
                                    const data = await response.json();
                                    if (data.related_items && data.related_items.length > 0) {
                                        const relatedSection = document.createElement('div');
                                        relatedSection.className = 'related-stories-section';
                                        relatedSection.innerHTML = `
                                            <h4 class="related-stories-title">📰 Same Story From Other Sources:</h4>
                                            <div class="related-stories-list">
                                                ${data.related_items.map(related => `
                                                    <div class="related-story-card">
                                                        <div class="related-story-source">${related.source || 'Unknown Source'}</div>
                                                        <div class="related-story-title">${related.title}</div>
                                                        ${related.source_urls && related.source_urls.length > 0 ? `
                                                            <a href="${related.source_urls[0]}" target="_blank" rel="noopener" class="related-story-link">
                                                                Read from this source →
                                                            </a>
                                                        ` : ''}
                                                    </div>
                                                `).join('')}
                                            </div>
                                        `;
                                        contentInner.appendChild(relatedSection);
                                    }
                                    article.dataset.relatedLoaded = 'true';
                                } else {
                                    article.dataset.relatedLoaded = 'error';
                                }
                            } catch (error) {
                                console.error('Error loading related content:', error);
                                article.dataset.relatedLoaded = 'error';
                            }
                        }
                    }
                }
            });
        }

        // Add click handler for read more button
        const readMoreBtn = article.querySelector('.btn-read-more');
        if (readMoreBtn) {
            readMoreBtn.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation(); // Prevent card toggle

                // Track click in history
                if (window.historyTracker) {
                    const slug = article.dataset.contentSlug;
                    window.historyTracker.recordClick(item.content_id, slug);
                }

                this.onContentClick(item);
                this.trackView(item.content_id);
            });
        }

        // Prevent source link from toggling card
        const sourceBtn = article.querySelector('.btn-source');
        if (sourceBtn) {
            sourceBtn.addEventListener('click', (e) => {
                e.stopPropagation();

                // Track click in history
                if (window.historyTracker) {
                    const slug = article.dataset.contentSlug;
                    window.historyTracker.recordClick(item.content_id, slug);
                }
            });
        }

        this.container.appendChild(article);

        // Extract dominant color from image for hover effect
        if (imageUrl) {
            const img = article.querySelector('.feed-item-image img');
            if (img) {
                this.extractDominantColor(img, article);
            }
        }

        // Create hover tracker for this card
        if (window.HoverTracker && this.globalScrollTracker) {
            const tracker = new HoverTracker(article, item.content_id);
            this.hoverTrackers.set(item.content_id, tracker);
            this.globalScrollTracker.registerTracker(tracker);
        }

        // Observe this card for visibility tracking (view duration)
        if (this.cardObserver) {
            this.cardObserver.observe(article);
        }

        // Observe this card for history tracking (seen when in viewport)
        if (window.historyTracker) {
            window.historyTracker.observeCard(article);
        }
    }

    insertAdUnit() {
        const adContainer = document.createElement('div');
        adContainer.className = 'feed-ad-unit';
        adContainer.innerHTML = `
            <ins class="adsbygoogle"
                 style="display:block"
                 data-ad-format="fluid"
                 data-ad-layout-key="-fb+5w+4e-db+86"
                 data-ad-client="ca-pub-1529513529221142"
                 data-ad-slot="1234567890"></ins>
        `;
        this.container.appendChild(adContainer);

        // Initialize the ad
        try {
            (adsbygoogle = window.adsbygoogle || []).push({});
        } catch (e) {
            console.error('AdSense error:', e);
        }
    }

    async defaultContentClick(item) {
        // Check if this is a search query item
        const isSearchQuery = item.category === 'Search Query' || item.content_type === 'trending_analysis' ||
            (item.source_urls && item.source_urls[0] &&
                (item.source_urls[0].includes('google.com/search') ||
                    item.source_urls[0].includes('duckduckgo.com')));

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
        this.openArticleModal(item, isSearchQuery);
    }

    async openArticleModal(item, isSearchQuery = false) {
        const modal = document.getElementById('article-modal');
        const loading = modal.querySelector('.article-loading');
        const error = modal.querySelector('.article-error');
        const title = document.getElementById('article-title');
        const author = document.getElementById('article-author');
        const date = document.getElementById('article-date');
        const domain = document.getElementById('article-domain');
        const image = document.getElementById('article-image');
        const body = document.getElementById('article-body');
        const sourceLink = document.getElementById('article-source-link');
        const relatedSection = document.getElementById('article-related');
        const relatedItems = document.getElementById('article-related-items');

        // Track article open start time
        const articleOpenTime = Date.now();
        let readTracked = false;

        // 📊 Google Analytics: Track article opened (fire immediately)
        if (typeof gtag !== 'undefined') {
            gtag('event', 'article_open', {
                'article_title': item.title,
                'article_category': item.category || 'Unknown',
                'article_id': item.content_id
            });
        }

        // 📊 Track "article_read" after 10 seconds (regardless of content load success)
        setTimeout(() => {
            if (modal.classList.contains('active') && !readTracked) {
                readTracked = true;
                const timeSpent = Math.round((Date.now() - articleOpenTime) / 1000);

                if (typeof gtag !== 'undefined') {
                    gtag('event', 'article_read', {
                        'article_title': item.title,
                        'article_category': item.category || 'Unknown',
                        'article_id': item.content_id,
                        'engagement_time_seconds': timeSpent
                    });
                }
            }
        }, 10000); // 10 seconds

        // Show modal and loading state
        modal.classList.add('active');
        loading.style.display = 'block';
        loading.querySelector('p').textContent = isSearchQuery ? 'Loading search context...' : 'Loading article...';
        error.style.display = 'none';
        body.innerHTML = '';
        image.style.display = 'none';
        relatedSection.style.display = 'none';
        relatedItems.innerHTML = '';

        // Set source link for error fallback
        if (item.source_urls && item.source_urls.length > 0) {
            sourceLink.href = item.source_urls[0];
        }

        try {
            // Fetch article content
            const response = await fetch(`/api/v1/content/article/${item.content_id}`);

            if (!response.ok) {
                throw new Error('Failed to fetch article');
            }

            const article = await response.json();

            // Check if this is a fallback response (content extraction failed)
            const isFallback = article.content && article.content.includes('Unable to extract full article content');

            if (isFallback) {
                // Show error view with source link
                loading.style.display = 'none';
                error.style.display = 'block';
                title.textContent = article.title || item.title;
                return;
            }

            // Hide loading
            loading.style.display = 'none';

            // Populate modal
            title.textContent = article.title || item.title;
            author.textContent = article.author || '';
            date.textContent = article.published_date || '';
            domain.textContent = article.domain || '';

            if (article.image_url) {
                image.src = article.image_url;
                image.style.display = 'block';
            }

            // Display content as facts (already formatted with bullet points)
            const paragraphs = article.content.split('\n\n');

            // Add "Key Facts" header
            body.innerHTML = '<h3 style="margin-bottom: 16px; color: #007bff;">📋 Key Facts:</h3>';
            body.innerHTML += paragraphs.map(p => `<p>${p}</p>`).join('');

            // Add in-article ad after facts
            const inArticleAd = document.createElement('div');
            inArticleAd.className = 'article-ad-unit';
            inArticleAd.style.margin = '20px 0';
            inArticleAd.innerHTML = `
                <ins class="adsbygoogle"
                     style="display:block; text-align:center;"
                     data-ad-layout="in-article"
                     data-ad-format="fluid"
                     data-ad-client="ca-pub-1529513529221142"
                     data-ad-slot="9876543210"></ins>
            `;
            body.appendChild(inArticleAd);

            // Initialize ad
            try {
                (adsbygoogle = window.adsbygoogle || []).push({});
            } catch (e) {
                console.error('In-article ad error:', e);
            }

            // Add "Continue Reading" button if this is an excerpt
            if (article.is_excerpt || article.full_article_available) {
                const continueReadingBtn = document.createElement('div');
                continueReadingBtn.className = 'continue-reading-cta';
                continueReadingBtn.innerHTML = `
                    <p class="cta-text">
                        📚 Want the full story with context and analysis?
                    </p>
                    <a href="${item.source_urls[0]}" target="_blank" rel="noopener" 
                       class="btn-continue-reading">
                        Read Full Facts on ${article.domain || 'Source Site'} →
                    </a>
                `;
                body.appendChild(continueReadingBtn);
            }

            // Display related items if available
            if (article.related_items && article.related_items.length > 0) {
                this.renderRelatedItems(article.related_items, relatedItems);
                relatedSection.style.display = 'block';
            }

            // 📊 Track scroll depth for "article_read_complete" (only if content loaded successfully)
            const articleBody = document.querySelector('.article-modal-content');
            if (articleBody) {
                let scrollTracked = false;
                articleBody.addEventListener('scroll', () => {
                    if (scrollTracked) return;

                    const scrollPercentage = (articleBody.scrollTop + articleBody.clientHeight) / articleBody.scrollHeight;

                    if (scrollPercentage > 0.8) { // 80% scroll depth
                        scrollTracked = true;
                        const timeSpent = Math.round((Date.now() - articleOpenTime) / 1000);

                        if (typeof gtag !== 'undefined') {
                            gtag('event', 'article_read_complete', {
                                'article_title': article.title || item.title,
                                'article_category': item.category || 'Unknown',
                                'article_id': item.content_id,
                                'engagement_time_seconds': timeSpent,
                                'scroll_depth': Math.round(scrollPercentage * 100)
                            });
                        }
                    }
                });
            }

        } catch (err) {
            console.error('Error fetching article:', err);
            loading.style.display = 'none';
            error.style.display = 'block';
        }
    }

    renderRelatedItems(items, container) {
        container.innerHTML = items.map(item => `
            <div class="related-item" data-content-id="${item.content_id}">
                <div class="related-item-content">
                    <div class="related-item-meta">
                        <span class="related-item-category">${item.category || 'Trending'}</span>
                        <span class="related-item-source">${item.source}</span>
                    </div>
                    <h4 class="related-item-title">${item.title}</h4>
                    ${item.description ? `<p class="related-item-description">${item.description}</p>` : ''}
                    <div class="related-item-actions">
                        ${item.source_urls && item.source_urls.length > 0 ? `
                            <a href="${item.source_urls[0]}" target="_blank" rel="noopener" class="btn-related-source">
                                ${this.getSourceButtonTextForUrl(item.source_urls[0], item.tags || [])}
                            </a>
                        ` : ''}
                    </div>
                </div>
            </div>
        `).join('');
    }

    getSourceButtonTextForUrl(url, tags) {
        const urlLower = url.toLowerCase();

        // Check if it's a search-related item
        if (tags.includes('query') || tags.includes('search')) {
            if (urlLower.includes('google.com/search') || urlLower.includes('duckduckgo.com')) {
                return 'Search';
            }
        }

        // Check URL patterns
        if (urlLower.includes('google.com/search') || urlLower.includes('duckduckgo.com') || urlLower.includes('/search?q=')) {
            return 'Search';
        }

        if (urlLower.includes('trends.google.com')) {
            return 'View Trends';
        }

        return 'View Source';
    }

    extractDominantColor(img, card) {
        // Wait for image to load before extracting color
        if (!img.complete) {
            img.addEventListener('load', () => this.extractDominantColor(img, card));
            return;
        }

        try {
            // Create canvas to extract color
            const canvas = document.createElement('canvas');
            const ctx = canvas.getContext('2d');

            // Use small canvas for performance
            canvas.width = 50;
            canvas.height = 50;

            // Draw scaled-down image
            ctx.drawImage(img, 0, 0, 50, 50);

            // Get image data
            const imageData = ctx.getImageData(0, 0, 50, 50);
            const data = imageData.data;

            // Calculate average color (simple approach)
            let r = 0, g = 0, b = 0;
            let count = 0;

            // Sample pixels (skip some for performance)
            for (let i = 0; i < data.length; i += 16) {
                r += data[i];
                g += data[i + 1];
                b += data[i + 2];
                count++;
            }

            r = Math.floor(r / count);
            g = Math.floor(g / count);
            b = Math.floor(b / count);

            // Set the color as a CSS variable on the card
            card.style.setProperty('--card-color', `rgb(${r}, ${g}, ${b})`);
            console.debug(`Extracted color for card: rgb(${r}, ${g}, ${b})`);

        } catch (error) {
            // If color extraction fails (CORS or other issues), use a default subtle color
            console.debug('Could not extract color from image:', error.message);
            // Set a default subtle blue tint as fallback
            card.style.setProperty('--card-color', 'rgb(100, 149, 237)');
        }
    }

    async trackView(contentId) {
        try {
            await fetch(`/api/v1/session/track-view/${contentId}`, {
                method: 'POST',
                credentials: 'include'
            });
        } catch (error) {
            console.error('Failed to track view:', error);
        }
    }

    truncateText(text, maxLength) {
        if (text.length <= maxLength) return text;
        return text.substring(0, maxLength) + '...';
    }

    getSourceButtonText(item) {
        // Determine button text based on the source URL and tags
        if (!item.source_urls || item.source_urls.length === 0) {
            return 'View Source';
        }

        const url = item.source_urls[0].toLowerCase();
        const tags = item.tags || [];

        // Check if it's a search-related item
        if (tags.includes('query') || tags.includes('search')) {
            if (url.includes('google.com/search') || url.includes('duckduckgo.com')) {
                return 'Search';
            }
        }

        // Check URL patterns
        if (url.includes('google.com/search') || url.includes('duckduckgo.com') || url.includes('/search?q=')) {
            return 'Search';
        }

        if (url.includes('trends.google.com')) {
            return 'View Trends';
        }

        // Default to View Source for news articles and other content
        return 'View Source';
    }

    formatTime(isoString) {
        const date = new Date(isoString);
        const now = new Date();
        const diffMs = now - date;
        const diffMins = Math.floor(diffMs / 60000);
        const diffHours = Math.floor(diffMins / 60);
        const diffDays = Math.floor(diffHours / 24);

        if (diffMins < 60) return `${diffMins}m ago`;
        if (diffHours < 24) return `${diffHours}h ago`;
        if (diffDays < 7) return `${diffDays}d ago`;

        return date.toLocaleDateString();
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
        const errorDiv = document.createElement('div');
        errorDiv.className = 'feed-error';
        errorDiv.innerHTML = `
            <p>Error loading content: ${message}</p>
            <button onclick="location.reload()">Retry</button>
        `;
        this.container.appendChild(errorDiv);
    }

    // Public methods
    reset() {
        // Clean up all hover trackers
        this.hoverTrackers.forEach(tracker => tracker.destroy());
        this.hoverTrackers.clear();

        this.currentPage = 1;
        this.cursor = null; // Reset cursor for category changes
        this.viewedContentIds.clear();
        this.hasMore = true;
        this.container.innerHTML = '';
        this.endMessage.style.opacity = '0';
        this.endMessage.style.display = 'none'; // Hide end message
        this.loadingIndicator.style.display = 'block'; // Show loading indicator
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
        // Clean up all hover trackers
        this.hoverTrackers.forEach(tracker => tracker.destroy());
        this.hoverTrackers.clear();

        // Destroy global scroll tracker
        if (this.globalScrollTracker) {
            this.globalScrollTracker.destroy();
            this.globalScrollTracker = null;
        }

        // Send all pending durations
        this.sendAllDurations();
    }
}

// Export for use in other scripts
window.InfiniteFeed = InfiniteFeed;

// Modal controls
document.addEventListener('DOMContentLoaded', function () {
    const modal = document.getElementById('article-modal');
    const closeBtn = document.querySelector('.article-modal-close');

    if (!modal) {
        console.warn('Article modal not found');
        return;
    }

    // Close modal on close button click
    if (closeBtn) {
        closeBtn.addEventListener('click', () => {
            modal.classList.remove('active');
            document.body.style.overflow = ''; // Unlock body scroll
        });
    }

    // Close modal on background click
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            modal.classList.remove('active');
            document.body.style.overflow = ''; // Unlock body scroll
        }
    });

    // Close modal on Escape key
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && modal.classList.contains('active')) {
            modal.classList.remove('active');
            document.body.style.overflow = ''; // Unlock body scroll
        }
    });
});
