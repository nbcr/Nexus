// UI Manager
class UIManager {
    currentView = 'home';

    initializeUI() {
        this.renderAuthSection();
        this.updateUI();
        this.attachEventListeners();
    }

    renderAuthSection() {
        Utils.setHTML('auth-section', `
            <div class="auth-form">
                <h3>Login to Nexus</h3>
                <div id="login-form">
                    <form id="login-form-element">
                        <input type="text" id="login-username" placeholder="Username" required autocomplete="username">
                        <input type="password" id="login-password" placeholder="Password" required autocomplete="current-password">
                        <button type="submit">Login</button>
                        <button type="button" id="show-register-btn">Register</button>
                    </form>
                </div>
                
                <div id="register-form" style="display: none;">
                    <form id="register-form-element">
                        <input type="text" id="register-username" placeholder="Username" required autocomplete="username">
                        <input type="email" id="register-email" placeholder="Email" required autocomplete="email">
                        <input type="password" id="register-password" placeholder="Password" required autocomplete="new-password">
                        <button type="submit">Register</button>
                        <button type="button" id="show-login-btn">Back to Login</button>
                    </form>
                </div>
            </div>
        `);
    }

    updateUI() {
        if (window.auth?.isLoggedIn()) {
            Utils.hideElement('auth-section');
            Utils.showElement('user-section');
            Utils.setHTML('user-info', `Welcome, ${window.auth.user.username}!`);
        } else {
            Utils.showElement('auth-section');
            Utils.hideElement('user-section');
        }
        
        if (window.sessionManager) {
            window.sessionManager.updateSessionWarning();
        }
    }

    attachEventListeners() {
        // Login form
        document.getElementById('login-form-element')?.addEventListener('submit', this.handleLogin.bind(this));
        document.getElementById('register-form-element')?.addEventListener('submit', this.handleRegister.bind(this));
        
        // Form toggle buttons
        document.getElementById('show-register-btn')?.addEventListener('click', this.showRegister.bind(this));
        document.getElementById('show-login-btn')?.addEventListener('click', this.showLogin.bind(this));
        
        // Logout button
        document.getElementById('logout-btn')?.addEventListener('click', this.handleLogout.bind(this));
    }

    async handleLogin(event) {
        event.preventDefault();
        const username = document.getElementById('login-username').value;
        const password = document.getElementById('login-password').value;
        
        const result = await window.auth.login(username, password);
        if (result.success) {
            alert('Login successful!');
            this.showLogin(); // Reset to login form
            this.updateUI();
            await window.contentManager.refresh();
        } else {
            alert('Login failed: ' + result.error);
        }
    }

    async handleRegister(event) {
        event.preventDefault();
        const username = document.getElementById('register-username').value;
        const email = document.getElementById('register-email').value;
        const password = document.getElementById('register-password').value;
        
        const result = await window.auth.register(username, email, password);
        if (result.success) {
            alert(result.message);
            this.showLogin();
        } else {
            alert('Registration failed: ' + result.error);
        }
    }

    handleLogout() {
        window.auth.logout();
        alert('Logged out successfully!');
        this.updateUI();
        window.contentManager.refresh();
    }

    showLogin() {
        Utils.showElement('login-form');
        Utils.hideElement('register-form');
    }

    showRegister() {
        Utils.hideElement('login-form');
        Utils.showElement('register-form');
    }

    showLoading() {
        Utils.setHTML('app', '<div class="loading">Loading...</div>');
    }

    showError(message) {
        Utils.showError(message);
    }
}
