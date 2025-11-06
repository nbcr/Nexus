class TrendingManager {
    constructor() {
        this.enhancedTrends = [];
    }

    async loadEnhancedTrends() {
        try {
            Utils.hideError();
            const response = await Utils.apiCall('/api/v1/trending/enhanced-trends');
            this.enhancedTrends = response.trends || [];
            console.log('Received trends data:', this.enhancedTrends);
            this.renderEnhancedTrends();
        } catch (error) {
            console.error('Error loading enhanced trends:', error);
            Utils.setHTML('trending-topics', '<p class="error">Failed to load trending topics</p>');
        }
    }

    renderEnhancedTrends() {
        const container = document.getElementById('trending-topics');
        if (!container) return;

        if (this.enhancedTrends.length === 0) {
            container.innerHTML = '<p>No trending topics available. <button onclick="window.trendingManager.loadEnhancedTrends()">Refresh</button></p>';
            return;
        }

        console.log('Rendering trends:', this.enhancedTrends);
        
        container.innerHTML = this.enhancedTrends.map(trend => {
            console.log('Processing trend:', trend);
            
            const imageHtml = trend.image_url ? 
                `<img src="${trend.image_url}" alt="${trend.title}" onerror="this.style.display='none'; this.parentElement.innerHTML='<div class=\\'image-placeholder\\'></div>'">`
                : '<div class="image-placeholder"></div>';
                
            const newsItemsHtml = Array.isArray(trend.news_items) && trend.news_items.length > 0 ? 
                trend.news_items.map(news => {
                    console.log('Processing news item:', news);
                    const newsImageHtml = news.picture ? 
                        `<div class="news-item-image">
                            <img src="${news.picture}" alt="${news.title}" onerror="this.style.display='none'; this.parentElement.style.display='none';">
                        </div>` : '';
                        
                    return `<div class="news-item">
                        ${newsImageHtml}
                        <div class="news-item-content">
                            <h4>${news.title || 'News Update'}</h4>
                            ${news.snippet ? `<p>${news.snippet}</p>` : ''}
                            <div class="news-source">
                                <span class="source-name">${news.source}</span>
                                <a href="${news.url}" target="_blank" class="source-link" onclick="event.stopPropagation()">Read More</a>
                            </div>
                        </div>
                    </div>`;
                }).join('') : '<p>No additional details available</p>';

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

    renderEnhancedTrends() {
        const container = document.getElementById('trending-topics');
        if (!container) return;

        if (this.enhancedTrends.length === 0) {
            container.innerHTML = '<p>No trending topics available. <button onclick="window.trendingManager.loadEnhancedTrends()">Refresh</button></p>';
            return;
        }

        // Debug log to check the data we're working with
        console.log('Rendering trends:', this.enhancedTrends);
        
        container.innerHTML = this.enhancedTrends.map(trend => {
            console.log('Processing trend:', trend);
            
            const imageHtml = trend.image_url ? 
                `<img src="${trend.image_url}" alt="${trend.title}" onerror="this.style.display='none'; this.parentElement.innerHTML='<div class=\\'image-placeholder\\'></div>'">`
                : '<div class="image-placeholder"></div>';
                
            const newsItemsHtml = Array.isArray(trend.news_items) && trend.news_items.length > 0 ? 
                trend.news_items.map(news => {
                    console.log('Processing news item:', news);
                    const newsImageHtml = news.picture ? 
                        `<div class="news-item-image">
                            <img src="${news.picture}" alt="${news.title}" onerror="this.style.display='none'; this.parentElement.style.display='none';">
                        </div>` : '';
                        
                    return `<div class="news-item">
                        ${newsImageHtml}
                        <div class="news-item-content">
                            <h4>${news.title || 'News Update'}</h4>
                            ${news.snippet ? `<p>${news.snippet}</p>` : ''}
                            <div class="news-source">
                                <span class="source-name">${news.source}</span>
                                <a href="${news.url}" target="_blank" class="source-link" onclick="event.stopPropagation()">Read More</a>
                            </div>
                        </div>
                    </div>`;
                }).join('') : '<p>No additional details available</p>';

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
        `).join('');
    }

    preloadSummary(linkElement, url) {
        linkElement.setAttribute('title', 'Visit: ' + url);
    }

    async refreshAll() {
        await this.loadEnhancedTrends();
    }
}

// Create a global instance
window.TrendingManager = TrendingManager;
