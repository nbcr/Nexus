# Jinja2 Templating Setup for Nexus

## Overview
This guide explains how to set up Jinja2 templating in FastAPI so the header only needs to be maintained in one place.

## Benefits
- ✅ **Single source of truth**: Header defined once in `base.html`
- ✅ **No duplication**: Changes propagate to all pages automatically
- ✅ **Server-side rendering**: Better SEO than client-side includes
- ✅ **Template inheritance**: Reuse layouts, headers, footers
- ✅ **Dynamic content**: Pass variables from backend to templates

## Implementation Steps

### 1. Install Jinja2 (if not already installed)
```bash
pip install jinja2
```

### 2. Configure Jinja2 in FastAPI (`app/main.py`)

Add at the top of `app/main.py`:
```python
from fastapi.templating import Jinja2Templates

# Configure Jinja2 templates
templates = Jinja2Templates(directory="app/templates")
```

### 3. Create Base Template (`app/templates/base.html`)

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}Nexus - The AI News Portal{% endblock %}</title>
    <link rel="icon" type="image/png" href="/static/favicon.png">
    
    <!-- CSS -->
    <link rel="stylesheet" href="/static/css/base.css?v=202512010100">
    <link rel="stylesheet" href="/static/css/header.css?v=202512010100">
    <link rel="stylesheet" href="/static/css/components.css?v=202512010100">
    {% block extra_css %}{% endblock %}
</head>
<body {% block body_class %}{% endblock %}>
    <!-- SHARED HEADER - Edit once, applies everywhere -->
    <header class="main-header">
        <div class="container">
            <a href="/" class="header-title-link">
                <h1><img src="/static/favicon.png" alt="Nexus" class="site-logo"> Nexus - The Ai News Portal</h1>
            </a>
            <nav>
                <span id="user-welcome" class="user-welcome"></span>
                <button class="hamburger" id="hamburger-menu" aria-label="Open menu">
                    <span class="bar"></span>
                    <span class="bar"></span>
                    <span class="bar"></span>
                </button>
                <!-- Desktop auth buttons -->
                <div class="header-auth-buttons" id="header-auth-buttons">
                    <a href="/login" id="auth-btn" class="header-btn"><span class="menu-icon">🔐</span><span class="menu-label">Login</span></a>
                    <a href="/register" id="register-btn" class="header-btn"><span class="menu-icon">📝</span><span class="menu-label">Register</span></a>
                </div>
                <div class="nav-links" id="nav-links">
                    <a href="/" class="menu-quick"><span class="menu-icon">🏠</span><span class="menu-label">Feed</span></a>
                    <a href="/settings" class="menu-quick"><span class="menu-icon">⚙️</span><span class="menu-label">Settings</span></a>
                    <button id="dark-mode-toggle-menu"><span class="menu-icon">🌙</span><span class="menu-label">Dark Mode</span></button>
                    
                    <!-- Mobile auth buttons -->
                    <a href="/login" class="auth-btn-mobile" id="auth-btn-mobile"><span class="menu-icon">🔐</span><span class="menu-label">Login</span></a>
                    <a href="/register" class="auth-btn-mobile" id="register-btn-mobile"><span class="menu-icon">📝</span><span class="menu-label">Register</span></a>
                    
                    <!-- Text size controls -->
                    <div class="text-size-controls">
                        <button id="text-size-decrease" class="text-size-btn" aria-label="Decrease text size">➖</button>
                        <span class="text-size-label">
                            <span class="text-size-line1">Text</span>
                            <span class="text-size-line2">Size</span>
                        </span>
                        <button id="text-size-increase" class="text-size-btn" aria-label="Increase text size">➕</button>
                    </div>
                </div>
            </nav>
        </div>
    </header>
    
    <!-- Page content goes here -->
    {% block content %}{% endblock %}
    
    <!-- Shared scripts -->
    <script src="/static/js/header.js"></script>
    {% block extra_js %}{% endblock %}
</body>
</html>
```

### 4. Create Page Templates

**Example: `app/templates/index.html`**
```html
{% extends "base.html" %}

{% block extra_css %}
<link rel="stylesheet" href="/static/css/feed.css?v=202512010100">
{% endblock %}

{% block content %}
<div class="feed-controls">
    <h2>Your Personalized Feed</h2>
    <div class="category-filter" id="category-filter"></div>
</div>

<div id="feed-container"></div>
{% endblock %}

{% block extra_js %}
<script src="/static/js/feed.js?v=202511230700"></script>
<script src="/static/js/feed-notifier.js?v=202511210700"></script>
<script src="/static/js/history-tracker.js"></script>
<script>
    // Feed initialization code
</script>
{% endblock %}
```

**Example: `app/templates/login.html`**
```html
{% extends "base.html" %}

{% block title %}Login - Nexus{% endblock %}

{% block body_class %}class="login-page"{% endblock %}

{% block extra_css %}
<link rel="stylesheet" href="/static/css/auth.css?v=202512010100">
{% endblock %}

{% block content %}
<div class="login-container">
    <h2>Login to Nexus</h2>
    <!-- Login form content -->
</div>
{% endblock %}
```

### 5. Update FastAPI Routes

**In `app/main.py`**, change from `FileResponse` to template rendering:

```python
from fastapi import Request
from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="app/templates")

@app.get("/")
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/login")
async def login_page(request: Request):
    # Check auth logic here
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/register")
async def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@app.get("/settings")
async def settings_page(request: Request):
    return templates.TemplateResponse("settings.html", {"request": request})
```

### 6. Pass Data to Templates (Optional)

You can pass data from backend to templates:

```python
@app.get("/")
async def home(request: Request):
    # Get user info, featured content, etc.
    context = {
        "request": request,
        "username": "John Doe",
        "featured_articles": get_featured_articles(),
        "debug_mode": settings.debug
    }
    return templates.TemplateResponse("index.html", context)
```

Access in template:
```html
{% if username %}
<p>Welcome, {{ username }}!</p>
{% endif %}
```

## Migration Checklist

- [ ] Install jinja2
- [ ] Add Jinja2Templates to `app/main.py`
- [ ] Create `app/templates/` directory
- [ ] Create `base.html` with shared header
- [ ] Convert `index.html` to template
- [ ] Convert `login.html` to template
- [ ] Convert `register.html` to template
- [ ] Convert `settings.html` to template
- [ ] Update routes to use `templates.TemplateResponse()`
- [ ] Test all pages
- [ ] Remove old static HTML files (optional, keep as backup)

## Benefits After Migration

1. **Update header once**: Change logo, menu, etc. in one place
2. **Add new menu items**: Edit `base.html`, all pages update
3. **Consistent styling**: All pages automatically use same header HTML
4. **Dynamic content**: Pass user info, auth status, etc. from backend
5. **Template blocks**: Create reusable footer, sidebar, etc.

## Future Enhancements

- Create `components/` directory for reusable parts (cards, buttons, etc.)
- Add template filters for formatting dates, numbers, etc.
- Use template inheritance for different layouts (e.g., `auth_layout.html`)
- Add macros for repeated HTML patterns

## Troubleshooting

**Template not found**: Check directory path is `app/templates/`
**Variables not rendering**: Make sure to pass `{"request": request}` context
**CSS not loading**: Use absolute paths `/static/css/...` not relative `../css/`

## Need Help?

This is a common pattern in FastAPI. More info:
- https://fastapi.tiangolo.com/advanced/templates/
- https://jinja.palletsprojects.com/en/3.1.x/templates/

