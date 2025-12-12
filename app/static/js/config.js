// Configuration
const CONFIG = {
    API_BASE_URL: globalThis.location.origin,
    SESSION_KEY: 'nexus_session',
    TOKEN_KEY: 'nexus_token',
    USER_KEY: 'nexus_user'
};

// Utility functions
const Utils = {
    // Show error message
    showError(message) {
        const errorElement = document.getElementById('error-message');
        const errorText = document.getElementById('error-text');
        if (errorElement && errorText) {
            errorText.textContent = message;
            errorElement.style.display = 'block';
        }
        console.error('App Error:', message);
    },

    // Hide error message
    hideError() {
        const errorElement = document.getElementById('error-message');
        if (errorElement) {
            errorElement.style.display = 'none';
        }
    },

    // API call wrapper
    async apiCall(endpoint, options = {}) {
        try {
            const url = `${CONFIG.API_BASE_URL}${endpoint}`;
            const response = await fetch(url, options);
            
            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(`HTTP ${response.status}: ${errorText}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error(`API call failed to ${endpoint}:`, error);
            this.showError(`Connection error: ${error.message}`);
            throw error;
        }
    },

    // Generate session token
    generateSessionToken() {
        return 'session_' + Math.random().toString(36).substring(2, 11);
    },

    // Show/hide elements
    showElement(id) {
        const element = document.getElementById(id);
        if (element) element.style.display = 'block';
    },

    hideElement(id) {
        const element = document.getElementById(id);
        if (element) element.style.display = 'none';
    },

    // Set element content
    setHTML(id, html) {
        const element = document.getElementById(id);
        if (element) element.innerHTML = html;
    }
};
