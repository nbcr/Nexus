/**
 * FeedUtils Module
 * Utility functions for text processing, formatting, and helpers
 */

class FeedUtils {
    static cleanSnippet(html) {
        if (!html) return '';
        const temp = document.createElement('div');
        temp.innerHTML = html;
        temp.querySelectorAll('img, picture, figure').forEach(el => el.remove());
        const text = temp.textContent || temp.innerText || '';
        return text.trim();
    }

    static truncateText(text, maxLength) {
        if (text.length <= maxLength) return text;
        return text.substring(0, maxLength) + '...';
    }

    static formatTime(isoString) {
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

    static buildProxyUrl(url) {
        return url ? `/api/v1/content/proxy/image?url=${encodeURIComponent(url)}` : null;
    }

    static extractDominantColor(img, card) {
        // Wait for image to load before extracting color
        if (!img.complete) {
            img.addEventListener('load', () => FeedUtils.extractDominantColor(img, card));
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

            // Convert RGB to HSL and boost saturation
            const { h, s, l } = this.rgbToHsl(r, g, b);
            // Increase saturation and ensure it's vibrant (min 60%)
            const boostedS = Math.max(s * 1.5, 60);
            // Slightly adjust lightness for better vibrancy
            const boostedL = Math.min(l, 55);
            const boostedRgb = this.hslToRgb(h, boostedS, boostedL);
            
            card.style.setProperty('--card-color', `rgb(${boostedRgb.r}, ${boostedRgb.g}, ${boostedRgb.b})`);
            console.debug(`Extracted color for card: rgb(${boostedRgb.r}, ${boostedRgb.g}, ${boostedRgb.b})`);

        } catch (error) {
            // If color extraction fails (CORS or other issues), use a default subtle color
            console.debug('Could not extract color from image:', error.message);
            // Set a default subtle blue tint as fallback
            card.style.setProperty('--card-color', 'rgb(100, 149, 237)');
        }
    }

    static rgbToHsl(r, g, b) {
        r /= 255;
        g /= 255;
        b /= 255;
        const max = Math.max(r, g, b);
        const min = Math.min(r, g, b);
        let h = 0, s = 0;
        const l = (max + min) / 2;

        if (max !== min) {
            const d = max - min;
            s = l > 0.5 ? d / (2 - max - min) : d / (max + min);
            switch (max) {
                case r: h = ((g - b) / d + (g < b ? 6 : 0)) / 6; break;
                case g: h = ((b - r) / d + 2) / 6; break;
                case b: h = ((r - g) / d + 4) / 6; break;
            }
        }
        return { h: h * 360, s: s * 100, l: l * 100 };
    }

    static hslToRgb(h, s, l) {
        h /= 360;
        s /= 100;
        l /= 100;
        let r, g, b;

        if (s === 0) {
            r = g = b = l;
        } else {
            const hue2rgb = (p, q, t) => {
                if (t < 0) t += 1;
                if (t > 1) t -= 1;
                if (t < 1/6) return p + (q - p) * 6 * t;
                if (t < 1/2) return q;
                if (t < 2/3) return p + (q - p) * (2/3 - t) * 6;
                return p;
            };
            const q = l < 0.5 ? l * (1 + s) : l + s - l * s;
            const p = 2 * l - q;
            r = hue2rgb(p, q, h + 1/3);
            g = hue2rgb(p, q, h);
            b = hue2rgb(p, q, h - 1/3);
        }

        return {
            r: Math.round(r * 255),
            g: Math.round(g * 255),
            b: Math.round(b * 255)
        };
    }

    static getSourceButtonText(item) {
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

    static getSourceButtonTextForUrl(url, tags) {
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

    static isSearchQuery(item) {
        return item.content_type === 'search_query' || item.category === 'Search Query';
    }

    static isNewsArticle(item) {
        if (FeedUtils.isSearchQuery(item)) return false;
        const type = item.content_type;
        return !type || ['news', 'news_update'].includes(type);
    }
}

globalThis.FeedUtils = FeedUtils;
