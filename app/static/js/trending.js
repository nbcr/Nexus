// Trending Content Manager
class TrendingManager {
    constructor() {
        this.enhancedTrends = [];
    }

    async loadEnhancedTrends() {
        try {
            Utils.hideError();
            const response = await Utils.apiCall('/api/v1/trending/enhanced-trends');
            this.enhancedTrends = response.trends || [];
            console.log('Received trends data:', this.enhancedTrends);  // Debug log
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

        container.innerHTML = this.enhancedTrends.map(trend => `
            <div class="trending-card" onclick="this.classList.toggle('expanded')">
                <div class="trending-card-header">
                    <div class="trending-image">
                        ${trend.image_url ? 
                            `<img src="${trend.image_url}" alt="${trend.title}" onerror="this.style.display='none'; this.parentElement.innerHTML='<div class=\\'image-placeholder\\'></div>'">` : 
                            '<div class="image-placeholder"></div>'
                        }
                    </div>
                    <h3 class="trending-title">${trend.title}</h3>
                    ${trend.source !== 'News' ? `<span class="source-flair">${trend.source}</span>` : ''}
                </div>
                <div class="trending-card-content">
                    ${trend.description ? `<p class="trending-description">${trend.description}</p>` : ''}
                    ${trend.news_items && trend.news_items.length > 0 ? `
                        <div class="news-items">
                            ${trend.news_items.map(news => `
                                <div class="news-item">
                                    ${news.picture ? `
                                        <div class="news-item-image">
                                            <img src="${news.picture}" alt="${news.title}" onerror="this.style.display='none'; this.parentElement.style.display='none';">
                                        </div>
                                    ` : ''}
                                    <div class="news-item-content">
                                        <h4>${news.title || 'News Update'}</h4>
                                        ${news.snippet ? `<p>${news.snippet}</p>` : ''}
                                        <div class="news-source">
                                            <span class="source-name">${news.source}</span>
                                            <a href="${news.url}" target="_blank" class="source-link">Read More</a>
                                        </div>
                                    </div>
                                </div>
                            `).join('')}
                        </div>
                    ` : ''}
                </div>
            </div>
        `).join('');
    }

    preloadSummary(linkElement, url) {
        // This would be where you could preload a summary
        // For now, we'll just add a tooltip with the full URL
        linkElement.title = `Visit: ${url}`;
    }

    async refreshAll() {
        await this.loadEnhancedTrends();
    }
}
