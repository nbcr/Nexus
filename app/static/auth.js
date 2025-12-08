class AuthManager {
    constructor() {
        this.token = localStorage.getItem('nexus_token');
        this.user = JSON.parse(localStorage.getItem('nexus_user') || 'null');
        this.updateUI();
    }

    async login(username, password) {
        try {
            const formData = new URLSearchParams();
            formData.append('username', username);
            formData.append('password', password);

            const response = await fetch('/api/v1/auth/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: formData
            });

            if (response.ok) {
                const data = await response.json();
                this.token = data.access_token;
                this.user = await this.getCurrentUser();
                
                localStorage.setItem('nexus_token', this.token);
                localStorage.setItem('nexus_user', JSON.stringify(this.user));
                
                this.updateUI();
                return { success: true };
            } else {
                return { success: false, error: 'Login failed' };
            }
        } catch (error) {
            return { success: false, error: error.message };
        }
    }

    async register(username, email, password) {
        try {
            const response = await fetch('/api/v1/auth/register', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ username, email, password })
            });

            if (response.ok) {
                return { success: true, message: 'Registration successful! Please login.' };
            } else {
                const error = await response.json();
                return { success: false, error: error.detail || 'Registration failed' };
            }
        } catch (error) {
            return { success: false, error: error.message };
        }
    }

    async getCurrentUser() {
        if (!this.token) return null;

        try {
            const response = await fetch('/api/v1/auth/me', {
                headers: {
                    'Authorization': `Bearer ${this.token}`
                }
            });

            if (response.ok) {
                return await response.json();
            }
        } catch (error) {
            console.error('Failed to get user:', error);
        }
        return null;
    }

    logout() {
        this.token = null;
        this.user = null;
        localStorage.removeItem('nexus_token');
        localStorage.removeItem('nexus_user');
        this.updateUI();
    }

    updateUI() {
        const authSection = document.getElementById('auth-section');
        const userSection = document.getElementById('user-section');
        
        if (this.user) {
            authSection.style.display = 'none';
            userSection.style.display = 'block';
            document.getElementById('user-info').textContent = 
                `Welcome, ${this.user.username}!`;
        } else {
            authSection.style.display = 'block';
            userSection.style.display = 'none';
        }
    }

    getAuthHeaders() {
        return this.token ? { 'Authorization': `Bearer ${this.token}` } : {};
    }
}

// Global auth instance - delayed until CONFIG is defined
let auth;
function initAuthManager() {
    if (typeof CONFIG === 'undefined') {
        console.warn('CONFIG not defined yet, retrying auth initialization...');
        setTimeout(initAuthManager, 100);
        return;
    }
    if (!auth) {
        auth = new AuthManager();
    }
}

// Try to initialize immediately, but will retry if CONFIG not ready
if (typeof CONFIG !== 'undefined') {
    auth = new AuthManager();
} else {
    document.addEventListener('DOMContentLoaded', initAuthManager);
}

// Auth form handlers
function showLogin() {
    document.getElementById('login-form').style.display = 'block';
    document.getElementById('register-form').style.display = 'none';
}

function showRegister() {
    document.getElementById('login-form').style.display = 'none';
    document.getElementById('register-form').style.display = 'block';
}

async function handleLogin(event) {
    event.preventDefault();
    const username = document.getElementById('login-username').value;
    const password = document.getElementById('login-password').value;
    
    const result = await auth.login(username, password);
    if (result.success) {
        alert('Login successful!');
        document.getElementById('login-form').style.display = 'none';
    } else {
        alert('Login failed: ' + result.error);
    }
}

async function handleRegister(event) {
    event.preventDefault();
    const username = document.getElementById('register-username').value;
    const email = document.getElementById('register-email').value;
    const password = document.getElementById('register-password').value;
    
    const result = await auth.register(username, email, password);
    if (result.success) {
        alert(result.message);
        showLogin();
    } else {
        alert('Registration failed: ' + result.error);
    }
}

function handleLogout() {
    auth.logout();
    alert('Logged out successfully!');
}
