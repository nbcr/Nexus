/**
 * FeedApi Module
 * Handles all API calls for feed operations
 */

class FeedApi {
    constructor() {
        this.accessToken = this.getAccessToken();
    }

    getAccessToken() {
        const regex = /(?:^|; )access_token=([^;]*)/;
        const match = regex.exec(document.cookie);
        if (match) return match[0];
        if (globalThis.localStorage) {
            return localStorage.getItem('access_token');
        }
        return null;
    }

    getHeaders() {
        return this.accessToken ? { 'Authorization': `Bearer ${this.accessToken}` } : {};
    }

    async fetchUserSettings() {
        try {
            const response = await fetch('/api/v1/settings/hover-tracker', {
                credentials: 'include',
                headers: this.getHeaders()
            });

            if (response.ok) {
                return await response.json();
            }
        } catch (error) {
            console.error('Error fetching user settings:', error);
        }
        return { debugMode: false };
    }

    async fetchFeed(page, pageSize, filters = {}) {
        const params = new URLSearchParams({
            page,
            page_size: pageSize
        });

        if (filters.excludeIds) params.append('exclude_ids', filters.excludeIds);
        if (filters.categories && filters.categories.length > 0) {
            params.append('categories', filters.categories.join(','));
        } else if (filters.category) {
            params.append('category', filters.category);
        }
        if (filters.cursor) params.append('cursor', filters.cursor);

        const endpoint = filters.isPersonalized ? '/api/v1/content/feed' : '/api/v1/content/trending-feed';

        const response = await fetch(`${endpoint}?${params}`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        return await response.json();
    }

    async fetchSnippet(contentId) {
        const response = await fetch(`/api/v1/content/snippet/${contentId}`);
        if (!response.ok) {
            throw new Error('Failed to fetch snippet');
        }
        return await response.json();
    }

    async fetchRelated(contentId) {
        const response = await fetch(`/api/v1/content/related/${contentId}`);
        if (!response.ok) {
            throw new Error('Failed to fetch related content');
        }
        return await response.json();
    }

    async fetchThumbnail(contentId) {
        const response = await fetch(`/api/v1/content/thumbnail/${contentId}`);
        if (!response.ok) {
            throw new Error('Failed to fetch thumbnail');
        }
        return await response.json();
    }

    async fetchArticle(contentId) {
        const response = await fetch(`/api/v1/content/article/${contentId}`);
        if (!response.ok) {
            throw new Error('Failed to fetch article');
        }
        return await response.json();
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
}

window.FeedApi = FeedApi;
