"""
Security middleware to automatically validate and sanitize all incoming requests.
Prevents injection attacks at the application level.
"""

import logging
import time
from typing import Callable
from fastapi import Request, Response, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.input_validation import InputValidator


class SecurityMiddleware(BaseHTTPMiddleware):
    """Middleware to validate and sanitize all incoming requests."""
    
    def __init__(self, app, max_request_size: int = 10 * 1024 * 1024):  # 10MB default
        super().__init__(app)
        self.max_request_size = max_request_size
        self.logger = logging.getLogger("security")
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request through security validation."""
        start_time = time.time()
        
        try:
            self._validate_request_basics(request)
            self._validate_query_params(request)
            self._validate_headers(request)
            
            response = await call_next(request)
            
            self._add_security_headers(response)
            self._log_request(request, response, time.time() - start_time)
            
            return response
            
        except HTTPException as e:
            return self._handle_http_exception(e, request)
        except Exception as e:
            return self._handle_general_exception(e, request)
    
    def _validate_request_basics(self, request: Request) -> None:
        """Validate basic request properties."""
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > self.max_request_size:
            raise HTTPException(status_code=413, detail="Request too large")
        
        allowed_methods = ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"]
        if request.method not in allowed_methods:
            raise HTTPException(status_code=405, detail="Method not allowed")
    
    def _handle_http_exception(self, e: HTTPException, request: Request) -> JSONResponse:
        """Handle HTTP exceptions with logging."""
        self.logger.warning(
            "Security validation failed: %s for %s %s",
            e.detail, request.method, request.url.path
        )
        return JSONResponse(
            status_code=e.status_code,
            content={"detail": e.detail}
        )
    
    def _handle_general_exception(self, e: Exception, request: Request) -> JSONResponse:
        """Handle general exceptions with logging."""
        self.logger.error(
            "Security middleware error: %s for %s %s",
            str(e)[:200], request.method, request.url.path
        )
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"}
        )
    
    def _validate_query_params(self, request: Request) -> None:
        """Validate query parameters for injection attacks."""
        for key, value in request.query_params.items():
            self._validate_param_name(key)
            if isinstance(value, str):
                self._validate_param_value(value)
    
    def _validate_param_name(self, key: str) -> None:
        """Validate parameter name format."""
        if not key.replace('_', '').replace('-', '').isalnum():
            raise HTTPException(
                status_code=400,
                detail=f"Invalid parameter name: {key}"
            )
    
    def _validate_param_value(self, value: str) -> None:
        """Validate parameter value for security threats."""
        if len(value) > 5000:
            raise HTTPException(
                status_code=400,
                detail="Parameter value too long"
            )
        
        self._check_suspicious_patterns(value)
    
    def _check_suspicious_patterns(self, value: str) -> None:
        """Check for suspicious injection patterns."""
        value_lower = value.lower()
        suspicious_patterns = [
            'script>', 'javascript:', 'vbscript:', 'onload=', 'onerror=',
            'union select', 'drop table', 'insert into', 'delete from',
            '../', '..\\', '%2e%2e', 'file://', 'ftp://'
        ]
        
        for pattern in suspicious_patterns:
            if pattern in value_lower:
                raise HTTPException(
                    status_code=400,
                    detail="Potentially malicious input detected"
                )
    
    def _validate_headers(self, request: Request) -> None:
        """Validate request headers for security issues."""
        self._check_suspicious_headers(request)
        self._validate_user_agent(request)
    
    def _check_suspicious_headers(self, request: Request) -> None:
        """Check for suspicious header values."""
        suspicious_headers = ['x-forwarded-host', 'x-original-host', 'x-rewrite-url']
        
        for header in suspicious_headers:
            if header in request.headers:
                value = request.headers[header]
                if any(char in value for char in ['<', '>', '"', "'"]):
                    raise HTTPException(
                        status_code=400,
                        detail="Invalid header value"
                    )
    
    def _validate_user_agent(self, request: Request) -> None:
        """Validate User-Agent header length."""
        user_agent = request.headers.get('user-agent', '')
        if len(user_agent) > 1000:
            raise HTTPException(
                status_code=400,
                detail="User-Agent header too long"
            )
    
    def _add_security_headers(self, response: Response) -> None:
        """Add security headers to response."""
        security_headers = {
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'DENY',
            'X-XSS-Protection': '1; mode=block',
            'Referrer-Policy': 'strict-origin-when-cross-origin',
            'Content-Security-Policy': "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self' data:;",
        }
        
        for header, value in security_headers.items():
            response.headers[header] = value
    
    def _log_request(self, request: Request, response: Response, process_time: float) -> None:
        """Log request for security monitoring."""
        # Only log essential information, sanitized
        client_ip = request.client.host if request.client else "unknown"
        method = request.method
        path = request.url.path
        status_code = response.status_code
        
        # Sanitize path for logging
        safe_path = InputValidator.sanitize_for_logging(path, max_length=200)
        
        self.logger.info(
            "Request: %s %s - Status: %d - Time: %.3fs - IP: %s",
            method, safe_path, status_code, process_time, client_ip
        )
        
        # Log suspicious activity
        if status_code >= 400:
            self.logger.warning(
                "Suspicious request: %s %s - Status: %d - IP: %s",
                method, safe_path, status_code, client_ip
            )