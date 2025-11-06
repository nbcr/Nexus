class TrendingManager {
    constructor() {
        this.enhancedTrends = [];
        this.currentPage = 1;
        this.pageSize = 10;
        this.hasMore = true;
        this.isLoading = false;
        this.includeHistorical = true;
        this.setupInfiniteScroll();
    }

    async loadEnhancedTrends(append = false) {
        if (this.isLoading || (!append && !this.hasMore)) return;
        
        try {
            this.isLoading = true;
            Utils.hideError();
            
            // Show loading indicator
            if (!append) {
                Utils.setHTML('trending-topics', '<div class="loading">Loading trending topics...</div>');
            } else {
                document.querySelector('#trending-topics .loading')?.remove();
                const loadingDiv = document.createElement('div');
                loadingDiv.className = 'loading';
                loadingDiv.textContent = 'Loading more...';
                document.getElementById('trending-topics').appendChild(loadingDiv);
            }
            
            const response = await Utils.apiCall(
                `/api/v1/trending/enhanced-trends?page=${this.currentPage}&page_size=${this.pageSize}&include_historical=${this.includeHistorical}`
            );
            
            const newTrends = response.trends || [];
            this.hasMore = response.has_more;
            
            if (append) {
                this.enhancedTrends = [...this.enhancedTrends, ...newTrends];
            } else {
                this.enhancedTrends = newTrends;
            }
            
            console.log('Received trends data:', this.enhancedTrends);
            this.renderEnhancedTrends(append);
            
            if (this.hasMore) {
                this.currentPage++;
            }
        } catch (error) {
            console.error('Error loading enhanced trends:', error);
            if (!append) {
                Utils.setHTML('trending-topics', '<p class="error">Failed to load trending topics</p>');
            }
        } finally {
            this.isLoading = false;
            document.querySelector('#trending-topics .loading')?.remove();
        }
    }

    setupInfiniteScroll() {
        // Throttle scroll handler
        let scrollTimeout;
        window.addEventListener('scroll', () => {
            if (scrollTimeout) clearTimeout(scrollTimeout);
            scrollTimeout = setTimeout(() => {
                const scrollPosition = window.innerHeight + window.scrollY;
                const totalHeight = document.documentElement.scrollHeight;
                const buffer = 200; // Load more content when within 200px of bottom
                
                if (totalHeight - scrollPosition < buffer && this.hasMore && !this.isLoading) {
                    this.loadEnhancedTrends(true);
                }
            }, 100);
        });
    }

    renderEnhancedTrends(append = false) {
        const container = document.getElementById('trending-topics');
        if (!container) return;

        if (this.enhancedTrends.length === 0) {
            container.innerHTML = '<p>No trending topics available. <button onclick="window.trendingManager.loadEnhancedTrends()">Refresh</button></p>';
            return;
        }
        
        const trendsHtml = this.enhancedTrends.map(trend => {
            // Existing trend rendering code...
        }).join('');

        console.log('Rendering trends:', this.enhancedTrends);
        
        container.innerHTML = this.enhancedTrends.map(trend => {
            console.log('Processing trend:', trend);
            
            const imageHtml = trend.image_url ? 
                `<img src="${trend.image_url}" alt="${trend.title}" onerror="this.style.display='none'; this.parentElement.innerHTML='<div class=\\'image-placeholder\\'></div>'">`
                : '<div class="image-placeholder"></div>';
                
            // Create a default news item from the trend itself if no news items exist
            const defaultNewsItem = {
                title: trend.title,
                snippet: trend.description || '',
                url: trend.url,
                picture: trend.image_url,
                source: trend.source
            };

            // Use trend's own data if no news items are available
            const newsItems = (Array.isArray(trend.news_items) && trend.news_items.length > 0) 
                ? trend.news_items 
                : [defaultNewsItem];

            console.log('News items for rendering:', newsItems);

            const newsItemsHtml = newsItems.map(news => {
                console.log('Processing news item:', news);
                const newsImageHtml = news.picture ? 
                    `<div class="news-item-image">
                        <img src="${news.picture}" alt="${news.title}" onerror="this.style.display='none'; this.parentElement.style.display='none';">
                    </div>` : '';
                    
                return `<div class="news-item">
                    ${newsImageHtml}
                    <div class="news-item-content">
                        <h4><a href="${news.url}" target="_blank" onclick="event.stopPropagation()">${news.title || 'News Update'}</a></h4>
                        ${news.snippet ? `<p>${news.snippet}</p>` : ''}
                        <div class="news-source">
                            ${news.source ? `<span class="source-name">${news.source}</span>` : ''}
                            <a href="${news.url}" target="_blank" class="source-link" onclick="event.stopPropagation()">Read More</a>
                        </div>
                    </div>
                </div>`;
            }).join('');

            return `<div class="trending-card" onclick="this.classList.toggle('expanded')">
                <div class="trending-card-header">
                    <div class="trending-image">${imageHtml}</div>
                    <h3 class="trending-title">${trend.title}</h3>
                    ${trend.source !== 'News' ? `<span class="source-flair">${trend.source}</span>` : ''}
                </div>
                <div class="trending-card-content">
                    <div class="content-inner">
                        ${trend.description ? `<p class="trending-description">${trend.description}</p>` : ''}
                        <div class="news-items">${newsItemsHtml}</div>
                    </div>
                </div>
            </div>`;
        }).join('');
    }

    preloadSummary(linkElement, url) {
        linkElement.setAttribute('title', 'Visit: ' + url);
    }

    async refreshAll() {
        await this.loadEnhancedTrends();
    }
}

// Make TrendingManager available globally
window.TrendingManager = TrendingManager;
