"""
Security configuration and utilities for the Nexus application.
Centralizes security settings and provides secure defaults.
"""

from typing import Dict, List, Set
import os


class SecurityConfig:
    """Security configuration settings."""
    
    # Input validation limits
    MAX_STRING_LENGTH = 5000
    MAX_QUERY_PARAM_LENGTH = 1000
    MAX_REQUEST_SIZE = 10 * 1024 * 1024  # 10MB
    MAX_FILE_SIZE = 50 * 1024 * 1024     # 50MB
    
    # Rate limiting
    DEFAULT_RATE_LIMIT = 100  # requests per minute
    STRICT_RATE_LIMIT = 20    # for sensitive endpoints
    
    # Allowed file extensions for uploads
    ALLOWED_IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
    ALLOWED_DOCUMENT_EXTENSIONS = {'.pdf', '.txt', '.md'}
    
    # Blocked patterns for input validation
    SQL_INJECTION_PATTERNS = [
        r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION)\b)",
        r"(--|#|/\*|\*/)",
        r"(\b(OR|AND)\s+\d+\s*=\s*\d+)",
        r"(\'\s*(OR|AND)\s+\'\w+\'\s*=\s*\'\w+)",
        r"(\bUNION\s+SELECT\b)",
        r"(\bDROP\s+TABLE\b)",
        r"(\bINSERT\s+INTO\b)",
        r"(\bDELETE\s+FROM\b)",
    ]
    
    XSS_PATTERNS = [
        r"<script[^>]*>.*?</script>",
        r"javascript:",
        r"vbscript:",
        r"on\w+\s*=",
        r"<iframe[^>]*>",
        r"<object[^>]*>",
        r"<embed[^>]*>",
        r"<link[^>]*>",
        r"<meta[^>]*>",
    ]
    
    PATH_TRAVERSAL_PATTERNS = [
        r"\.\./",
        r"\.\.\\",
        r"%2e%2e%2f",
        r"%2e%2e\\",
        r"\.\.%2f",
        r"\.\.%5c",
        r"file://",
        r"ftp://",
    ]
    
    COMMAND_INJECTION_PATTERNS = [
        r"[;&|`$(){}[\]<>]",
        r"\b(cat|ls|dir|type|copy|move|del|rm|chmod|sudo|su|wget|curl)\b",
        r"(\||&&|;|`|\$\()",
        r"(\bnc\b|\bnetcat\b)",
        r"(\bpowershell\b|\bcmd\b|\bbash\b|\bsh\b)",
    ]
    
    # Blocked domains and IPs for SSRF protection
    BLOCKED_DOMAINS = {
        'localhost',
        '127.0.0.1',
        '0.0.0.0',
        '::1',
        'metadata.google.internal',
        'metadata',
        'consul',
        'vault',
    }
    
    BLOCKED_DOMAIN_PATTERNS = [
        r'\.local$',
        r'\.internal$',
        r'\.corp$',
        r'\.lan$',
        r'^10\.',
        r'^172\.(1[6-9]|2[0-9]|3[01])\.',
        r'^192\.168\.',
        r'^169\.254\.',
    ]
    
    # Security headers
    SECURITY_HEADERS = {
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'DENY',
        'X-XSS-Protection': '1; mode=block',
        'Referrer-Policy': 'strict-origin-when-cross-origin',
        'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
        'Content-Security-Policy': (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' data:; "
            "connect-src 'self'; "
            "frame-ancestors 'none';"
        ),
    }
    
    # Sensitive endpoints that require extra protection
    SENSITIVE_ENDPOINTS = {
        '/api/v1/auth/login',
        '/api/v1/auth/register',
        '/api/v1/auth/reset-password',
        '/api/v1/admin/',
    }
    
    # Endpoints that should be rate limited more strictly
    STRICT_RATE_LIMIT_ENDPOINTS = {
        '/api/v1/auth/login',
        '/api/v1/auth/register',
        '/api/v1/content/snippet/',
        '/api/v1/content/article/',
    }
    
    @classmethod
    def is_sensitive_endpoint(cls, path: str) -> bool:
        """Check if endpoint is sensitive and needs extra protection."""
        return any(path.startswith(endpoint) for endpoint in cls.SENSITIVE_ENDPOINTS)
    
    @classmethod
    def needs_strict_rate_limit(cls, path: str) -> bool:
        """Check if endpoint needs strict rate limiting."""
        return any(path.startswith(endpoint) for endpoint in cls.STRICT_RATE_LIMIT_ENDPOINTS)
    
    @classmethod
    def get_allowed_origins(cls) -> List[str]:
        """Get allowed CORS origins from environment."""
        origins = os.getenv('ALLOWED_ORIGINS', 'http://localhost:8000,http://127.0.0.1:8000')
        return [origin.strip() for origin in origins.split(',')]
    
    @classmethod
    def is_development_mode(cls) -> bool:
        """Check if running in development mode."""
        return os.getenv('ENVIRONMENT', 'development').lower() == 'development'


class SecurityUtils:
    """Security utility functions."""
    
    @staticmethod
    def is_safe_redirect_url(url: str, allowed_domains: Set[str]) -> bool:
        """Check if redirect URL is safe."""
        from urllib.parse import urlparse
        
        try:
            parsed = urlparse(url)
            
            # Only allow HTTP/HTTPS
            if parsed.scheme not in ('http', 'https'):
                return False
            
            # Check if domain is in allowed list
            if parsed.netloc.lower() not in allowed_domains:
                return False
            
            return True
        except Exception:
            return False
    
    @staticmethod
    def generate_csrf_token() -> str:
        """Generate CSRF token."""
        import secrets
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password securely."""
        import bcrypt
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    @staticmethod
    def verify_password(password: str, hashed: str) -> bool:
        """Verify password against hash."""
        import bcrypt
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    
    @staticmethod
    def generate_secure_filename(filename: str) -> str:
        """Generate secure filename."""
        import re
        import secrets
        
        # Remove path components
        filename = os.path.basename(filename)
        
        # Remove dangerous characters
        filename = re.sub(r'[^a-zA-Z0-9._-]', '', filename)
        
        # Limit length
        name, ext = os.path.splitext(filename)
        name = name[:50]
        
        # Add random component to prevent conflicts
        random_suffix = secrets.token_hex(4)
        
        return f"{name}_{random_suffix}{ext}"


# Environment-specific security settings
def get_security_settings() -> Dict:
    """Get security settings based on environment."""
    base_settings = {
        'max_request_size': SecurityConfig.MAX_REQUEST_SIZE,
        'rate_limit': SecurityConfig.DEFAULT_RATE_LIMIT,
        'allowed_origins': SecurityConfig.get_allowed_origins(),
        'security_headers': SecurityConfig.SECURITY_HEADERS,
    }
    
    if SecurityConfig.is_development_mode():
        # Relaxed settings for development
        base_settings.update({
            'rate_limit': 1000,  # Higher limit for development
            'debug_mode': True,
        })
    else:
        # Strict settings for production
        base_settings.update({
            'rate_limit': SecurityConfig.DEFAULT_RATE_LIMIT,
            'debug_mode': False,
            'require_https': True,
        })
    
    return base_settings