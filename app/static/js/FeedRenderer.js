/**
 * FeedRenderer Module
 * Handles DOM creation and rendering of feed items and modals
 */

class FeedRenderer {
    constructor(api, tracking) {
        this.api = api;
        this.tracking = tracking;
    }

    renderContentItem(item, container, onContentClick) {
        const article = this.createArticleElement(item);
        this.populateArticleContent(article, item);
        this.setupArticleInteractions(article, item, onContentClick);
        container.appendChild(article);
    }

    populateArticleContent(article, item) {
        const imageHtml = this.buildImageHtml(item);
        const summaryHtml = this.buildSummaryHtml(item);
        const readMoreButton = this.buildReadMoreButton(item);
        
        article.innerHTML = this.buildArticleHTML(item, imageHtml, summaryHtml, readMoreButton);
        
        if (item.facts?.trim()) {
            article.dataset.snippetLoaded = 'true';
        }
    }

    setupArticleInteractions(article, item, onContentClick) {
        const isNewsArticle = FeedUtils.isNewsArticle(item);
        const isSearchQuery = FeedUtils.isSearchQuery(item);
        this.setupCardEventHandlers(article, item, isNewsArticle, isSearchQuery, onContentClick);
        this.setupCardImage(article, item);
    }

    createArticleElement(item) {
        const article = document.createElement('article');
        article.className = 'feed-item';
        article.dataset.contentId = item.content_id;
        article.dataset.contentSlug = item.slug || `content-${item.content_id}`;
        article.dataset.topicId = item.topic_id;
        return article;
    }

    buildSummaryHtml(item) {
        if (!item.facts || !item.facts.trim()) {
            return '<div class="feed-item-summary"></div>';
        }

        const cleanSummary = FeedUtils.cleanSnippet(item.facts);
        const paragraphs = cleanSummary.split('\n\n');
        const factsContent = paragraphs.map(p => {
            if (p.trim().startsWith('•')) {
                return `<li style="margin-bottom: 8px; line-height: 1.6;">${p.trim().substring(1).trim()}</li>`;
            }
            return `<p style="line-height: 1.8; margin-bottom: 12px;">${p}</p>`;
        }).join('');
        
        if (factsContent.includes('<li')) {
            return `<div class="feed-item-summary"><ul style="margin: 0; padding-left: 20px; list-style-position: inside;">${factsContent}</ul></div>`;
        }
        return `<div class="feed-item-summary">${factsContent}</div>`;
    }

    buildReadMoreButton(item) {
        const isNewsArticle = FeedUtils.isNewsArticle(item);
        const isSearchQuery = FeedUtils.isSearchQuery(item);
        
        if (isNewsArticle) {
            return `<button class="btn-read-more" data-content-id="${item.content_id}">Visit site for full story</button>`;
        }
        if (isSearchQuery) {
            return `<button class="btn-read-more" data-content-id="${item.content_id}">Show Search Context</button>`;
        }
        return '';
    }

    buildArticleHTML(item, imageHtml, summaryHtml, readMoreButton) {
        const source = item.source_metadata?.source || 'News';
        const relevanceHtml = this.buildRelevanceHtml(item);
        const tagsHtml = this.buildTagsHtml(item);
        const relatedQueriesHtml = this.buildRelatedQueriesHtml(item);

        return `
        <div class="feed-item-content">
            <div class="feed-item-header">
                ${imageHtml}
                <div class="feed-item-header-content">
                    <div class="feed-item-meta">
                        <span class="feed-item-category">${item.category || 'Trending'}</span>
                        ${relevanceHtml}
                        <span class="feed-item-source">${source}</span>
                    </div>
                    <h2 class="feed-item-title">${item.title}</h2>
                    ${item.description ? `<p class="feed-item-description">${item.description}</p>` : ''}
                    <span class="expand-indicator">▼</span>
                </div>
            </div>
            <div class="feed-item-expanded-content">
                <div class="content-inner">
                    ${summaryHtml}
                    <div class="feed-item-actions">
                        ${readMoreButton}
                        <span class="feed-item-time">${FeedUtils.formatTime(item.created_at)}</span>
                    </div>
                    ${tagsHtml}
                    ${relatedQueriesHtml}
                </div>
            </div>
        </div>`;
    }

    buildRelevanceHtml(item) {
        if (item?.relevance_score && globalThis.nexusDebugMode) {
            return `<span class="feed-item-relevance" title="Relevance to your interests">${Math.round(item.relevance_score * 100)}% match</span>`;
        }
        return '';
    }

    buildTagsHtml(item) {
        if (!item.tags?.length) return '';
        const tagsHtml = item.tags.map(tag => `<span class="tag">${tag}</span>`).join('');
        return `<div class="feed-item-tags">${tagsHtml}</div>`;
    }

    buildRelatedQueriesHtml(item) {
        if (!item.related_queries?.length) return '';
        const queriesHtml = item.related_queries.map(query => `<a href="${query.url}" target="_blank" rel="noopener" class="related-query">${query.title}</a>`).join('');
        const relatedSection = `<h4 class="related-title">🔍 Related Searches:</h4><div class="related-queries">${queriesHtml}</div>`;
        return `<div class="feed-item-related">${relatedSection}</div>`;
    }

    buildImageHtml(item) {
        const imageSrc = this.getImageSrc(item);
        
        if (imageSrc) {
            return `<div class="feed-item-image" style="aspect-ratio: 16/9; background: linear-gradient(90deg, #333 25%, #444 50%, #333 75%); background-size: 200% 100%; animation: shimmer 2s infinite;">
            <img src="${imageSrc}" alt="${item.title}" loading="lazy" decoding="async" crossorigin="anonymous" onerror="this.src='/static/img/placeholder.png'" style="width: 100%; height: 100%; object-fit: cover;">
        </div>`;
        }
        return `<div class="feed-item-image" style="aspect-ratio: 16/9;">
            <img src="/static/img/placeholder.png" alt="No image" loading="lazy" decoding="async" style="width: 100%; height: 100%; object-fit: cover;">
        </div>`;
    }

    getImageSrc(item) {
        if (item.content_id) {
            return `/api/v1/content/${item.content_id}/image?size=800`;
        }
        if (item.local_image_path) {
            return item.local_image_path.startsWith("/") ? item.local_image_path : `/api/v1/content/proxy/image?url=${encodeURIComponent(item.local_image_path)}&w=743&h=413`;
        }
        
        const imageUrl = item.thumbnail_url || item.source_metadata?.picture_url;
        if (imageUrl) {
            return imageUrl.startsWith("/") ? imageUrl : `/api/v1/content/proxy/image?url=${encodeURIComponent(imageUrl)}&w=743&h=413`;
        }
        return null;
    }

    setupCardEventHandlers(article, item, isNewsArticle, isSearchQuery, onContentClick) {
        this.setupHeaderClickHandler(article, item, isNewsArticle);
        this.setupReadMoreHandler(article, item);
        this.setupSourceButtonHandler(article, item);
    }

    setupHeaderClickHandler(article, item, isNewsArticle) {
        const header = article.querySelector('.feed-item-header');
        if (!header) return;

        header.addEventListener('click', async (e) => {
            if (this.shouldIgnoreHeaderClick(e)) return;

            const wasExpanded = article.classList.contains('expanded');
            article.classList.toggle('expanded');

            if (!wasExpanded) {
                await this.handleCardExpansion(article, item, isNewsArticle);
            }
        });
    }

    shouldIgnoreHeaderClick(e) {
        return e.target.closest('.feed-item-image') || 
               e.target.closest('.btn-read-more') || 
               e.target.closest('.btn-source');
    }

    async handleCardExpansion(article, item, isNewsArticle) {
        this.emitCardOpenedEvent(item.content_id);
        
        if (!article.dataset.snippetLoaded && isNewsArticle) {
            await this.loadSnippet(article, item);
        }
        
        if (!article.dataset.relatedLoaded) {
            await this.loadRelatedContent(article, item);
        }
    }

    setupReadMoreHandler(article, item) {
        const readMoreBtn = article.querySelector('.btn-read-more');
        if (!readMoreBtn) return;

        readMoreBtn.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();

            this.emitCardOpenedEvent(item.content_id);
            this.trackClick(article, item);

            if (item.source_urls?.length > 0) {
                globalThis.open(item.source_urls[0], '_blank', 'noopener');
            }
        });
    }

    setupSourceButtonHandler(article, item) {
        const sourceBtn = article.querySelector('.btn-source');
        if (!sourceBtn) return;

        sourceBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            this.trackClick(article, item);
        });
    }

    emitCardOpenedEvent(contentId) {
        const event = new CustomEvent('cardOpened', { detail: { contentId } });
        document.dispatchEvent(event);
    }

    trackClick(article, item) {
        if (globalThis.historyTracker) {
            const slug = article.dataset.contentSlug;
            globalThis.historyTracker.recordClick(item.content_id, slug);
        }
    }

    async loadSnippet(article, item) {
        const summaryEl = article.querySelector('.feed-item-summary');
        if (!summaryEl || article.dataset.snippetLoaded === 'true') return;

        if (this.hasExistingFacts(item)) {
            this.displayExistingFacts(summaryEl, item);
            article.dataset.snippetLoaded = 'true';
            return;
        }

        if (this.shouldFetchSnippet(item)) {
            await this.fetchAndDisplaySnippet(summaryEl, article, item);
        }
    }

    hasExistingFacts(item) {
        return item.facts?.trim() && item.facts.length > 100;
    }

    shouldFetchSnippet(item) {
        return FeedUtils.isNewsArticle(item) && !item.facts?.trim();
    }

    displayExistingFacts(summaryEl, item) {
        const factsHtml = this.formatFactsContent(item.facts);
        summaryEl.innerHTML = factsHtml.includes('<li') 
            ? `<ul style="margin: 0; padding-left: 20px; list-style-position: inside;">${factsHtml}</ul>`
            : factsHtml;
    }

    formatFactsContent(facts) {
        return facts.split('\n\n').map(p => {
            if (p.trim().startsWith('•')) {
                return `<li style="margin-bottom: 8px; line-height: 1.6;">${p.trim().substring(1).trim()}</li>`;
            }
            return `<p style="line-height: 1.8; margin-bottom: 12px;">${p}</p>`;
        }).join('');
    }

    async fetchAndDisplaySnippet(summaryEl, article, item) {
        this.showLoadingState(summaryEl);

        try {
            const data = await this.fetchSnippetData(item.content_id);
            await this.handleSnippetResponse(data, summaryEl, article, item);
        } catch (error) {
            console.error('Error loading snippet:', error);
            this.displaySnippetError(summaryEl, article, item);
        }
    }

    showLoadingState(summaryEl) {
        summaryEl.classList.add('loading-state');
        summaryEl.innerHTML = `<div class="spinner"></div><p style="margin-top: 12px; color: #666;">Fetching story facts...</p>`;
    }

    async fetchSnippetData(contentId) {
        const response = await fetch(`/api/v1/content/snippet/${contentId}/priority?timeout=10`);
        return response.json();
    }

    async handleSnippetResponse(data, summaryEl, article, item) {
        if (data.status === 'ready' && data.snippet) {
            this.displaySnippetSuccess(summaryEl, data.snippet, article);
        } else if (data.status === 'loading') {
            await this.retryAfterDelay(article, item);
        } else {
            this.displaySnippetError(summaryEl, article, item);
        }
    }

    async retryAfterDelay(article, item) {
        await new Promise(resolve => setTimeout(resolve, 1000));
        await this.loadSnippet(article, item);
    }

    displaySnippetSuccess(summaryEl, snippet, article) {
        summaryEl.classList.remove('loading-state');
        summaryEl.innerHTML = `<p style="line-height: 1.8;">${snippet}</p>`;
        article.dataset.snippetLoaded = 'true';
    }

    displaySnippetError(summaryEl, article, item) {
        summaryEl.classList.remove('loading-state');
        const buttonText = this.getErrorButtonText(article);
        
        summaryEl.innerHTML = this.buildErrorHTML(item.content_id, buttonText);
        this.attachErrorButtonHandler(summaryEl, article);
        article.dataset.snippetLoaded = 'true';
    }

    getErrorButtonText(article) {
        const readMoreBtn = article.querySelector('.btn-read-more');
        return readMoreBtn?.textContent?.trim() || 'Visit site for full story';
    }

    buildErrorHTML(contentId, buttonText) {
        return `
            <div style="text-align: center; padding: 20px;">
                <p style="color: #d32f2f; font-weight: 500; margin-bottom: 16px;">⚠️ We couldn't fetch the story facts</p>
                <button class="btn-read-more" data-content-id="${contentId}" 
                    style="background: #0078d4; color: white; border: none; padding: 10px 20px; border-radius: 4px; cursor: pointer; font-weight: 500;">
                    ${buttonText}
                </button>
            </div>
        `;
    }

    attachErrorButtonHandler(summaryEl, article) {
        const newBtn = summaryEl.querySelector('.btn-read-more');
        newBtn?.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            const originalBtn = article.querySelector('.feed-item-actions .btn-read-more');
            originalBtn?.click();
        });
    }

    async loadRelatedContent(article, item) {
        const contentInner = article.querySelector('.content-inner');
        if (!contentInner) return;

        try {
            const data = await this.api.fetchRelated(item.content_id);
            if (data.related_items && data.related_items.length > 0) {
                this.appendRelatedSection(contentInner, data.related_items);
            }
            article.dataset.relatedLoaded = 'true';
        } catch (error) {
            console.error('Error loading related content:', error);
            article.dataset.relatedLoaded = 'error';
        }
    }

    appendRelatedSection(contentInner, relatedItems) {
        const relatedSection = document.createElement('div');
        relatedSection.className = 'related-stories-section';
        relatedSection.innerHTML = `
            <h4 class="related-stories-title">📰 Same Story From Other Sources:</h4>
            <div class="related-stories-list">
                ${relatedItems.map(related => this.buildRelatedStoryCard(related)).join('')}
            </div>
        `;
        contentInner.appendChild(relatedSection);
    }

    buildRelatedStoryCard(related) {
        const linkHtml = related.source_urls && related.source_urls.length > 0 
            ? `<a href="${related.source_urls[0]}" target="_blank" rel="noopener" class="related-story-link">Read from this source →</a>`
            : '';
        
        return `
            <div class="related-story-card">
                <div class="related-story-source">${related.source || 'Unknown Source'}</div>
                <div class="related-story-title">${related.title}</div>
                ${linkHtml}
            </div>
        `;
    }

    setupCardImage(article, item) {
        this.setupImageClickHandler(article, item);
        this.setupImageColorExtraction(article);
    }

    setupImageClickHandler(article, item) {
        const imageEl = article.querySelector('.feed-item-image');
        if (!imageEl) return;

        imageEl.addEventListener('click', (e) => {
            e.stopPropagation();
            const wasExpanded = article.classList.contains('expanded');
            article.classList.toggle('expanded');
            if (!wasExpanded && !article.dataset.snippetLoaded) {
                this.loadSnippet(article, item).catch(err => console.error('Error loading snippet:', err));
            }
        });
    }

    setupImageColorExtraction(article) {
        const img = article.querySelector('.feed-item-image img');
        if (!img) {
            article.style.setProperty('--card-color', 'rgb(100, 149, 237)');
            return;
        }

        img.crossOrigin = 'anonymous';
        img.addEventListener('load', () => {
            FeedUtils.extractDominantColor(img, article);
        });
        
        if (img.complete && img.naturalHeight !== 0) {
            FeedUtils.extractDominantColor(img, article);
        }
    }

    insertAdUnit(container) {
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
        container.appendChild(adContainer);

        // Initialize the ad
        try {
            const adsbygoogle = globalThis.adsbygoogle || [];
            adsbygoogle.push({});
        } catch (e) {
            console.error('AdSense error:', e);
        }
    }

    renderArticleRelatedItems(items, container) {
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
                                ${FeedUtils.getSourceButtonTextForUrl(item.source_urls[0], item.tags || [])}
                            </a>
                        ` : ''}
                    </div>
                </div>
            </div>
        `).join('');
    }

    renderLoadingIndicator() {
        const loadingIndicator = document.createElement('div');
        loadingIndicator.className = 'feed-loading';
        loadingIndicator.innerHTML = `
            <div class="spinner"></div>
            <p>Loading more content...</p>
        `;
        loadingIndicator.style.display = 'block';
        loadingIndicator.style.minHeight = '100px';
        return loadingIndicator;
    }

    renderEndMessage() {
        const endMessage = document.createElement('div');
        endMessage.className = 'feed-end';
        endMessage.innerHTML = '<p>You\'ve reached the end of the feed!</p>';
        endMessage.style.display = 'none';
        return endMessage;
    }

    renderErrorMessage(message) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'feed-error';
        errorDiv.innerHTML = `
            <p>Error loading content: ${message}</p>
            <button onclick="location.reload()">Retry</button>
        `;
        return errorDiv;
    }
}

globalThis.FeedRenderer = FeedRenderer;
