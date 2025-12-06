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
        const article = document.createElement('article');
        article.className = 'feed-item';
        article.dataset.contentId = item.content_id;
        article.dataset.contentSlug = item.slug || `content-${item.content_id}`;
        article.dataset.topicId = item.topic_id;

        // Build image HTML
        const imageHtml = this.buildImageHtml(item);

        const source = item.source_metadata?.source || 'News';
        const rawSummary = item.content_text || item.description || '';
        const cleanSummary = FeedUtils.cleanSnippet(rawSummary);
        const summaryHtml = cleanSummary
            ? `<p class="feed-item-summary">${FeedUtils.truncateText(cleanSummary, 400)}</p>`
            : '<p class="feed-item-summary" style="font-style: italic;">No snippet available</p>';

        const isSearchQuery = FeedUtils.isSearchQuery(item);
        const isNewsArticle = FeedUtils.isNewsArticle(item);
        
        let readMoreButton = '';
        if (isNewsArticle) {
            readMoreButton = `<button class="btn-read-more" data-content-id="${item.content_id}">
                                Visit site for full story
                            </button>`;
        } else if (isSearchQuery) {
            readMoreButton = `<button class="btn-read-more" data-content-id="${item.content_id}">
                                Show Search Context
                            </button>`;
        }

        article.innerHTML = `
        <div class="feed-item-content">
            <div class="feed-item-header">
                ${imageHtml}
                <div class="feed-item-header-content">
                    <div class="feed-item-meta">
                        <span class="feed-item-category">${item.category || 'Trending'}</span>
                        ${item.relevance_score && globalThis.nexusDebugMode ? `
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
                    ${summaryHtml}
                    <div class="feed-item-actions">
                        ${readMoreButton}
                        <span class="feed-item-time">${FeedUtils.formatTime(item.created_at)}</span>
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

        this.setupCardEventHandlers(article, item, isNewsArticle, isSearchQuery, onContentClick);
        this.setupCardImage(article, item);

        container.appendChild(article);
    }

    buildImageHtml(item) {
        const imageUrl = item.thumbnail_url || item.source_metadata?.picture_url || null;
        const proxiedImageUrl = imageUrl ? FeedUtils.buildProxyUrl(imageUrl) : null;

        if (proxiedImageUrl) {
            return `<div class="feed-item-image">
            <img src="${proxiedImageUrl}" alt="${item.title}" loading="lazy">
        </div>`;
        } else if (imageUrl) {
            return `<div class="feed-item-image">
            <img src="${imageUrl}" alt="${item.title}" loading="lazy">
        </div>`;
        } else {
            return `<div class="feed-item-image">
            <img src="/static/img/placeholder.png" alt="No image" loading="lazy" style="filter:grayscale(1);opacity:0.5;">
        </div>`;
        }
    }

    setupCardEventHandlers(article, item, isNewsArticle, isSearchQuery, onContentClick) {
        const header = article.querySelector('.feed-item-header');
        if (header) {
            header.addEventListener('click', async (e) => {
                if (e.target.closest('.feed-item-image') || e.target.closest('.btn-read-more') || e.target.closest('.btn-source')) return;

                const wasExpanded = article.classList.contains('expanded');
                article.classList.toggle('expanded');

                if (!wasExpanded && !article.dataset.snippetLoaded && isNewsArticle) {
                    await this.loadSnippet(article, item);
                }

                if (!wasExpanded && !article.dataset.relatedLoaded) {
                    await this.loadRelatedContent(article, item);
                }
            });
        }

        // Add click handler for read more button - goes to source site
        const readMoreBtn = article.querySelector('.btn-read-more');
        if (readMoreBtn) {
            readMoreBtn.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();

                if (globalThis.historyTracker) {
                    const slug = article.dataset.contentSlug;
                    globalThis.historyTracker.recordClick(item.content_id, slug);
                }

                // Go to source site instead of opening modal
                if (item.source_urls && item.source_urls.length > 0) {
                    window.open(item.source_urls[0], '_blank', 'noopener');
                }
            });
        }

        // Prevent source link from toggling card
        const sourceBtn = article.querySelector('.btn-source');
        if (sourceBtn) {
            sourceBtn.addEventListener('click', (e) => {
                e.stopPropagation();

                if (globalThis.historyTracker) {
                    const slug = article.dataset.contentSlug;
                    globalThis.historyTracker.recordClick(item.content_id, slug);
                }
            });
        }
    }

    async loadSnippet(article, item) {
        const summaryEl = article.querySelector('.feed-item-summary');
        if (summaryEl) {
            // Check if we need to load full content
            const needsFullContent = summaryEl.textContent.includes('No snippet available') 
                                   || summaryEl.textContent.trim().length < 50
                                   || !article.dataset.snippetLoaded;
            
            if (needsFullContent && item.content_text && item.content_text.length > 100) {
                // Display full facts content from database
                const paragraphs = item.content_text.split('\n\n');
                const factsHtml = paragraphs.map(p => `<p style="line-height: 1.8; margin-bottom: 12px;">${p}</p>`).join('');
                summaryEl.innerHTML = factsHtml;
                article.dataset.snippetLoaded = 'true';
            } else if (needsFullContent && item.description) {
                summaryEl.innerHTML = `<p style="line-height: 1.8;">${item.description}</p>`;
                article.dataset.snippetLoaded = 'true';
            } else if (needsFullContent) {
                summaryEl.innerHTML = '<em>No preview available from this source</em>';
            }
        }
    }

    async loadRelatedContent(article, item) {
        const contentInner = article.querySelector('.content-inner');
        if (contentInner) {
            try {
                const data = await this.api.fetchRelated(item.content_id);
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
            } catch (error) {
                console.error('Error loading related content:', error);
                article.dataset.relatedLoaded = 'error';
            }
        }
    }

    setupCardImage(article, item) {
        // Add click handler to image to toggle card open/close
        const imageEl = article.querySelector('.feed-item-image');
        if (imageEl) {
            imageEl.addEventListener('click', (e) => {
                e.stopPropagation();
                const wasExpanded = article.classList.contains('expanded');
                article.classList.toggle('expanded');
                if (!wasExpanded && !article.dataset.snippetLoaded) {
                    this.loadSnippet(article, item).catch(err => console.error('Error loading snippet:', err));
                }
            });
        }
        // Always try to fetch a thumbnail if not present
        if (!item.thumbnail_url && !item.source_metadata?.picture_url) {
            (async () => {
                try {
                    const data = await this.api.fetchThumbnail(item.content_id);
                    if (data?.picture_url) {
                        const header = article.querySelector('.feed-item-header');
                        let img = article.querySelector('.feed-item-image img');
                        const proxyUrl = FeedUtils.buildProxyUrl(data.picture_url);
                        const finalUrl = proxyUrl || data.picture_url;
                        if (img) {
                            img.src = finalUrl;
                            if (proxyUrl) img.onerror = () => { img.src = data.picture_url; };
                        } else if (header) {
                            const container = article.querySelector('.feed-item-image') || document.createElement('div');
                            container.className = 'feed-item-image';
                            const imgEl = document.createElement('img');
                            imgEl.src = finalUrl;
                            if (proxyUrl) imgEl.onerror = () => { imgEl.src = data.picture_url; };
                            imgEl.alt = item.title;
                            imgEl.loading = 'lazy';
                            container.innerHTML = '';
                            container.appendChild(imgEl);
                            if (!container.parentElement) header.insertBefore(container, header.firstChild);
                        }
                    }
                } catch (e) {
                    console.error('Error fetching thumbnail:', e);
                }
            })();
        }

        // Extract dominant color from thumbnail for card background
        const img = article.querySelector('.feed-item-image img');
        if (img) {
            img.crossOrigin = 'anonymous'; // Enable CORS for color extraction
            img.addEventListener('load', () => {
                FeedUtils.extractDominantColor(img, article);
            });
            if (img.complete) {
                FeedUtils.extractDominantColor(img, article);
            }
        } else {
            // If no image, set default color
            article.style.setProperty('--card-color', 'rgb(100, 149, 237)');
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
