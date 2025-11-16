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
        this.isLoading = false;
        this.hasMore = true;
        this.viewedContentIds = new Set();
        this.isPersonalized = options.isPersonalized !== false;
        this.cursor = null; // Timestamp cursor for pagination
        
        // View duration tracking
        this.viewStartTimes = new Map(); // content_id -> timestamp
        this.viewDurations = new Map(); // content_id -> total seconds
        this.cardObserver = null;
        
        // Callbacks
        this.onContentClick = options.onContentClick || this.defaultContentClick.bind(this);
        this.renderContentItem = options.renderContentItem || this.defaultRenderContent.bind(this);
        
        this.init();
    }
    
    init() {
        console.log('Initializing feed..');
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
        try {
            await fetch(`/api/v1/session/track-view/${contentId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                credentials: 'include',
                body: JSON.stringify({
                    duration_seconds: Math.round(durationSeconds)
                })
            });
            console.log(`✅ Sent duration for content ${contentId}: ${durationSeconds}s`);
        } catch (error) {
            console.error(`❌ Failed to send duration for content ${contentId}:`, error);
        }
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
            if (this.category) params.append('category', this.category);
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
                data.items.forEach(item => {
                    this.viewedContentIds.add(item.content_id);
                    this.renderContentItem(item);
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
        article.dataset.topicId = item.topic_id;
        
        // Get image from source metadata
        const imageUrl = item.source_metadata?.picture_url || null;
        const source = item.source_metadata?.source || 'News';
        
        article.innerHTML = `
            <div class="feed-item-content">
                ${imageUrl ? `
                    <div class="feed-item-image">
                        <img src="${imageUrl}" alt="${item.title}" loading="lazy" 
                             onerror="this.parentElement.style.display='none'">
                    </div>
                ` : ''}
                <div class="feed-item-body">
                    <div class="feed-item-meta">
                        <span class="feed-item-category">${item.category || 'Trending'}</span>
                        ${item.relevance_score ? `
                            <span class="feed-item-relevance" title="Relevance to your interests">
                                ${Math.round(item.relevance_score * 100)}% match
                            </span>
                        ` : ''}
                        <span class="feed-item-source">${source}</span>
                    </div>
                    <h2 class="feed-item-title">${item.title}</h2>
                    <p class="feed-item-description">${item.description || ''}</p>
                    ${item.content_text ? `
                        <p class="feed-item-summary">${this.truncateText(item.content_text, 200)}</p>
                    ` : ''}
                    <div class="feed-item-actions">
                        <button class="btn-read-more" data-content-id="${item.content_id}">
                            Read More
                        </button>
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
        `;
        
        // Add click handler for read more
        const readMoreBtn = article.querySelector('.btn-read-more');
        if (readMoreBtn) {
            readMoreBtn.addEventListener('click', (e) => {
                e.preventDefault();
                this.onContentClick(item);
                this.trackView(item.content_id);
            });
        }
        
        this.container.appendChild(article);
        
        // Observe this card for visibility tracking
        if (this.cardObserver) {
            this.cardObserver.observe(article);
        }
    }
    
    async defaultContentClick(item) {
        // Check if this is a search query (pytrends) item
        const isPytrends = item.tags && item.tags.includes('pytrends');
        const isSearchQuery = item.category === 'Search Query' || (item.source_urls && item.source_urls[0] && 
                              (item.source_urls[0].includes('google.com/search') || 
                               item.source_urls[0].includes('duckduckgo.com')));
        
        console.log('🔍 Content click:', {
            content_id: item.content_id,
            title: item.title,
            category: item.category,
            tags: item.tags,
            source_url: item.source_urls?.[0],
            isPytrends,
            isSearchQuery
        });
        
        // For search queries, just open the search in a new tab
        if (isPytrends || isSearchQuery) {
            console.log('✅ Opening search in new tab');
            if (item.source_urls && item.source_urls.length > 0) {
                window.open(item.source_urls[0], '_blank');
            }
            return;
        }
        
        console.log('📰 Opening article modal');
        // For news articles, open modal and fetch article content
        this.openArticleModal(item);
    }
    
    async openArticleModal(item) {
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
        
        // Show modal and loading state
        modal.classList.add('active');
        loading.style.display = 'block';
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
            
            // Split content into paragraphs
            const paragraphs = article.content.split('\n\n');
            body.innerHTML = paragraphs.map(p => `<p>${p}</p>`).join('');
            
            // Display related items if available
            if (article.related_items && article.related_items.length > 0) {
                this.renderRelatedItems(article.related_items, relatedItems);
                relatedSection.style.display = 'block';
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
        if (tags.includes('pytrends') || tags.includes('query') || tags.includes('search')) {
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
        if (tags.includes('pytrends') || tags.includes('query') || tags.includes('search')) {
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
        this.currentPage = 1;
        this.viewedContentIds.clear();
        this.hasMore = true;
        this.container.innerHTML = '';
        this.endMessage.style.opacity = '0';
        this.loadMore();
    }
    
    setCategory(category) {
        this.category = category;
        this.reset();
    }
}

// Export for use in other scripts
window.InfiniteFeed = InfiniteFeed;

// Modal controls
document.addEventListener('DOMContentLoaded', function() {
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
        });
    }
    
    // Close modal on background click
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            modal.classList.remove('active');
        }
    });
    
    // Close modal on Escape key
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && modal.classList.contains('active')) {
            modal.classList.remove('active');
        }
    });
});
