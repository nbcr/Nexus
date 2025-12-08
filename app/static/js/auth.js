// Authentication Manager
class AuthManager {
    constructor() {
        this.token = localStorage.getItem(CONFIG.TOKEN_KEY);
        this.user = JSON.parse(localStorage.getItem(CONFIG.USER_KEY) || 'null');
    }

    async login(username, password) {
        try {
            Utils.hideError();
            const formData = new URLSearchParams();
            formData.append('username', username);
            formData.append('password', password);

            const data = await Utils.apiCall('/api/v1/auth/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: formData
            });

            this.token = data.access_token;
            this.user = await this.getCurrentUser();
            
            localStorage.setItem(CONFIG.TOKEN_KEY, this.token);
            localStorage.setItem(CONFIG.USER_KEY, JSON.stringify(this.user));
            
            // Migrate session history to user
            if (this.user && globalThis.sessionManager) {
                await globalThis.sessionManager.migrateToUser(this.user.id);
            }
            
            return { success: true };
        } catch (error) {
            return { success: false, error: error.message };
        }
    }

    async register(username, email, password) {
        try {
            Utils.hideError();
            await Utils.apiCall('/api/v1/auth/register', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ username, email, password })
            });

            return { success: true, message: 'Registration successful! Please login.' };
        } catch (error) {
            return { success: false, error: error.message };
        }
    }

    async getCurrentUser() {
        if (!this.token) return null;

        try {
            return await Utils.apiCall('/api/v1/auth/me', {
                headers: {
                    'Authorization': `Bearer ${this.token}`
                }
            });
        } catch (error) {
            console.error('Failed to get user:', error);
            return null;
        }
    }

    logout() {
        this.token = null;
        this.user = null;
        localStorage.removeItem(CONFIG.TOKEN_KEY);
        localStorage.removeItem(CONFIG.USER_KEY);
    }

    isLoggedIn() {
        return !!this.user;
    }

    getAuthHeaders() {
        return this.token ? { 'Authorization': `Bearer ${this.token}` } : {};
    }
}

// Expose AuthManager globally for admin modules
globalThis.AuthManager = AuthManager;
globalThis.authManager = new AuthManager();
