/**
 * FeedArticleModal Module
 * Handles article modal display and interactions
 */

class FeedArticleModal {
    constructor(api) {
        this.api = api;
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
            const article = await this.api.fetchArticle(item.content_id);

            // Check if this is a fallback response (content extraction failed)
            const isFallback = article.content && article.content.includes('Unable to extract facts');

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
                        📚 Want the facts with context and analysis?
                    </p>
                    <a href="${item.source_urls[0]}" target="_blank" rel="noopener" 
                       class="btn-continue-reading">
                        Read full article on ${article.domain || 'Source Site'} →
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
                                ${FeedUtils.getSourceButtonTextForUrl(item.source_urls[0], item.tags || [])}
                            </a>
                        ` : ''}
                    </div>
                </div>
            </div>
        `).join('');
    }

    setupModalControls() {
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
    }
}

window.FeedArticleModal = FeedArticleModal;
