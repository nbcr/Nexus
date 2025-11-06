// Session Manager
class SessionManager {
    constructor() {
        this.sessionToken = localStorage.getItem(CONFIG.SESSION_KEY) || Utils.generateSessionToken();
        localStorage.setItem(CONFIG.SESSION_KEY, this.sessionToken);
    }

    async trackContentView(contentId) {
        try {
            Utils.hideError();
            await Utils.apiCall(`/api/v1/session/track-view/${contentId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            });
            
            this.loadHistory(); // Refresh history
        } catch (error) {
            console.error('Failed to track view:', error);
        }
    }

    async loadHistory() {
        try {
            Utils.hideError();
            const data = await Utils.apiCall('/api/v1/session/history');
            
            if (data.history && data.history.length > 0) {
                Utils.setHTML('history', data.history.map(item => `
                    <div class="history-item">
                        <strong>${item.content.topic.title}</strong> - ${item.content.content_type}
                        <br><small>Viewed: ${new Date(item.viewed_at).toLocaleString()}</small>
                    </div>
                `).join(''));
            } else {
                Utils.setHTML('history', '<p>No viewing history yet. Start exploring content!</p>');
            }
            
            this.updateSessionWarning();
        } catch (error) {
            console.error('Failed to load history:', error);
        }
    }

    updateSessionWarning() {
        const warningElement = document.getElementById('session-warning');
        if (warningElement) {
            if (window.auth && !window.auth.isLoggedIn()) {
                warningElement.style.display = 'block';
            } else {
                warningElement.style.display = 'none';
            }
        }
    }

    async migrateToUser(userId) {
        try {
            Utils.hideError();
            const result = await Utils.apiCall(`/api/v1/session/migrate-to-user/${userId}`, {
                method: 'POST'
            });
            
            alert(`Migrated ${result.migrated_count} history items to your account!`);
            this.loadHistory();
        } catch (error) {
            console.error('Migration failed:', error);
        }
    }
}
