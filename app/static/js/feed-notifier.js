/**
 * WebSocket Feed Notifier
 * 
 * Handles:
 * - Real-time connection to server for feed updates
 * - New content notification UI
 * - Scroll to top functionality
 */

class FeedNotifier {
    constructor() {
        this.ws = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 2000;
        this.newContentCount = 0;
        
        this.init();
    }
    
    init() {
        this.createNotificationUI();
        this.createScrollToTopButton();
        this.connect();
        
        // Setup scroll listener for scroll-to-top button visibility
        window.addEventListener('scroll', () => this.updateScrollButtonVisibility());
    }
    
    createNotificationUI() {
        // Create notification bar
        this.notificationBar = document.createElement('div');
        this.notificationBar.className = 'feed-notification';
        this.notificationBar.style.cssText = `
            position: fixed;
            top: 70px;
            left: 50%;
            transform: translateX(-50%) translateY(-120%);
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 12px 24px;
            border-radius: 50px;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
            z-index: 9999;
            cursor: pointer;
            transition: transform 0.3s ease, opacity 0.3s ease;
            opacity: 0;
            font-weight: 600;
            font-size: 14px;
            display: flex;
            align-items: center;
            gap: 8px;
        `;
        
        this.notificationBar.innerHTML = `
            <span class="notification-icon">🔔</span>
            <span class="notification-text">New content available</span>
            <span class="notification-badge">1</span>
        `;
        
        this.notificationBar.addEventListener('click', () => {
            this.loadNewContent();
        });
        
        document.body.appendChild(this.notificationBar);
    }
    
    createScrollToTopButton() {
        this.scrollButton = document.createElement('button');
        this.scrollButton.className = 'scroll-to-top-btn';
        this.scrollButton.innerHTML = '↑';
        this.scrollButton.style.cssText = `
            position: fixed;
            bottom: 30px;
            right: 30px;
            width: 50px;
            height: 50px;
            border-radius: 50%;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            font-size: 24px;
            cursor: pointer;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
            z-index: 9998;
            opacity: 0;
            transform: scale(0);
            transition: all 0.3s ease;
            display: flex;
            align-items: center;
            justify-content: center;
        `;
        
        this.scrollButton.addEventListener('click', () => {
            window.scrollTo({ top: 0, behavior: 'smooth' });
        });
        
        document.body.appendChild(this.scrollButton);
    }
    
    connect() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        // Try to get access token from cookies
        let accessToken = null;
        if (document.cookie) {
            const match = document.cookie.match(/(?:^|; )access_token=([^;]*)/);
            if (match) accessToken = match[1];
        }
        // Fallback: try localStorage
        if (!accessToken && window.localStorage) {
            accessToken = localStorage.getItem('access_token');
        }
        let wsUrl = `${protocol}//${window.location.host}/api/v1/ws/feed-updates`;
        if (accessToken) {
            wsUrl += `?token=${encodeURIComponent(accessToken)}`;
        }
        console.log('🔌 Connecting to WebSocket:', wsUrl);
        try {
            this.ws = new WebSocket(wsUrl);
            this.ws.onopen = () => {
                console.log('✅ WebSocket connected');
                this.reconnectAttempts = 0;
                this.startHeartbeat();
            };
            this.ws.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    this.handleMessage(data);
                } catch (error) {
                    console.error('❌ Error parsing WebSocket message:', error);
                }
            };
            this.ws.onerror = (error) => {
                console.error('❌ WebSocket error:', error);
            };
            this.ws.onclose = () => {
                console.log('🔌 WebSocket disconnected');
                this.stopHeartbeat();
                this.attemptReconnect();
            };
        } catch (error) {
            console.error('❌ WebSocket connection error:', error);
            this.attemptReconnect();
        }
    }
    
    handleMessage(data) {
        console.log('📨 WebSocket message:', data);
        
        switch (data.type) {
            case 'connected':
                console.log('🎉 Connected to feed updates');
                break;
                
            case 'new_content':
                this.newContentCount += data.count || 1;
                this.showNotification();
                break;
                
            case 'pong':
                // Heartbeat response
                break;
                
            default:
                console.log('Unknown message type:', data.type);
        }
    }
    
    showNotification() {
        const badge = this.notificationBar.querySelector('.notification-badge');
        const text = this.notificationBar.querySelector('.notification-text');
        
        badge.textContent = this.newContentCount;
        text.textContent = this.newContentCount === 1 
            ? 'New content available' 
            : `${this.newContentCount} new items available`;
        
        // Show notification
        this.notificationBar.style.opacity = '1';
        this.notificationBar.style.transform = 'translateX(-50%) translateY(0)';
    }
    
    hideNotification() {
        this.notificationBar.style.opacity = '0';
        this.notificationBar.style.transform = 'translateX(-50%) translateY(-120%)';
        
        setTimeout(() => {
            this.newContentCount = 0;
        }, 300);
    }
    
    loadNewContent() {
        this.hideNotification();
        
        // Trigger feed refresh to load new content
        if (window.infiniteFeed) {
            window.infiniteFeed.refreshFeed(0); // Keep 0 cards = full refresh
            window.scrollTo({ top: 0, behavior: 'smooth' });
        } else {
            // Fallback: just reload the page
            window.location.reload();
        }
    }
    
    updateScrollButtonVisibility() {
        const scrolled = window.scrollY > 300;
        
        if (scrolled) {
            this.scrollButton.style.opacity = '1';
            this.scrollButton.style.transform = 'scale(1)';
        } else {
            this.scrollButton.style.opacity = '0';
            this.scrollButton.style.transform = 'scale(0)';
        }
    }
    
    startHeartbeat() {
        this.heartbeatInterval = setInterval(() => {
            if (this.ws && this.ws.readyState === WebSocket.OPEN) {
                this.ws.send('ping');
            }
        }, 30000); // Ping every 30 seconds
    }
    
    stopHeartbeat() {
        if (this.heartbeatInterval) {
            clearInterval(this.heartbeatInterval);
            this.heartbeatInterval = null;
        }
    }
    
    attemptReconnect() {
        if (this.reconnectAttempts >= this.maxReconnectAttempts) {
            console.log('❌ Max reconnect attempts reached');
            return;
        }
        
        this.reconnectAttempts++;
        const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);
        
        console.log(`🔄 Attempting to reconnect in ${delay}ms (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
        
        setTimeout(() => {
            this.connect();
        }, delay);
    }
    
    disconnect() {
        this.stopHeartbeat();
        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }
    }
}

// Initialize on page load
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.feedNotifier = new FeedNotifier();
    });
} else {
    window.feedNotifier = new FeedNotifier();
}
