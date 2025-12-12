"""
Example of how to integrate the security measures into your Nexus application.
This demonstrates the proper way to replace vulnerable patterns with secure alternatives.
"""

from fastapi import FastAPI, Request, Depends, HTTPException
from app.middleware.security_middleware import SecurityMiddleware
from app.core.input_validation import InputValidator
from app.core.secure_request_handler import SecureRequestHandler
from app.core.security_config import SecurityConfig, get_security_settings


# Example of secure application setup
def create_secure_app() -> FastAPI:
    """Create FastAPI app with security measures."""
    
    app = FastAPI(
        title="Nexus - Secure Content Platform",
        description="AI-Powered Content Personalization Engine with Security",
        version="1.0.0"
    )
    
    # Add security middleware
    app.add_middleware(SecurityMiddleware)
    
    # Add CORS with secure settings
    from fastapi.middleware.cors import CORSMiddleware
    security_settings = get_security_settings()
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=security_settings['allowed_origins'],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["*"],
    )
    
    return app


# Example of secure endpoint implementation
async def secure_search_endpoint(request: Request):
    """
    Example of how to securely handle user input in endpoints.
    Replaces the vulnerable pattern: request.GET -> _get_data_from_request -> _get_user_input -> sink
    """
    
    # SECURE APPROACH: Use validated request handler
    try:
        # Extract and validate search query safely
        search_query = await SecureRequestHandler.get_safe_user_input_from_request(
            request, 
            field_name="query", 
            default=""
        )
        
        # Additional validation for search-specific requirements
        search_query = InputValidator.validate_search_query(search_query)
        
        # Validate pagination parameters
        page = SecureRequestHandler.validate_query_param(
            request, "page", int, default=1
        )
        page_size = SecureRequestHandler.validate_query_param(
            request, "page_size", int, default=20
        )
        
        # Validate category filter
        category = SecureRequestHandler.validate_query_param(
            request, "category", str, default=None
        )
        if category:
            category_list = InputValidator.validate_category_list(category)
        else:
            category_list = None
        
        # Now safely use the validated inputs
        # These are guaranteed to be sanitized and safe for:
        # - Database queries (SQL injection prevention)
        # - File operations (path traversal prevention)  
        # - Shell commands (command injection prevention)
        # - HTML rendering (XSS prevention)
        
        # Example database query (safe because inputs are validated)
        results = await search_content_safely(
            query=search_query,
            page=page,
            page_size=page_size,
            categories=category_list
        )
        
        return {
            "query": search_query,  # Safe to return - already sanitized
            "results": results,
            "page": page,
            "page_size": page_size
        }
        
    except HTTPException:
        raise
    except Exception as e:
        # Sanitize error messages to prevent information disclosure
        safe_error = SecureRequestHandler.sanitize_error_message(str(e))
        raise HTTPException(status_code=500, detail="Search failed")


# Example of secure database query function
async def search_content_safely(query: str, page: int, page_size: int, categories: list = None):
    """
    Example of safe database querying with validated inputs.
    Since inputs are pre-validated, this function can safely use them.
    """
    
    # At this point, all inputs are guaranteed to be:
    # - SQL injection safe
    # - XSS safe  
    # - Path traversal safe
    # - Command injection safe
    
    # Safe to use in database queries
    # (Still use parameterized queries as additional defense)
    
    # Example with SQLAlchemy (parameterized query)
    from sqlalchemy import text
    
    sql_query = text("""
        SELECT id, title, description, category 
        FROM content_items 
        WHERE title ILIKE :query 
        AND (:category IS NULL OR category = :category)
        ORDER BY created_at DESC 
        LIMIT :limit OFFSET :offset
    """)
    
    # Safe to use validated inputs in parameters
    params = {
        "query": f"%{query}%",  # Safe - query is validated
        "category": categories[0] if categories else None,  # Safe - categories validated
        "limit": page_size,  # Safe - validated integer
        "offset": (page - 1) * page_size  # Safe - validated integers
    }
    
    # Execute query safely
    # result = await db.execute(sql_query, params)
    # return result.fetchall()
    
    # Placeholder return for example
    return [
        {
            "id": 1,
            "title": f"Sample result for: {query}",
            "description": "Safe sample description",
            "category": categories[0] if categories else "general"
        }
    ]


# Example of VULNERABLE vs SECURE patterns
def vulnerable_pattern_example():
    """
    VULNERABLE PATTERN (DO NOT USE):
    
    def _get_data_from_request(request):
        data = {}
        if request.method == "GET":
            data.update(request.GET)  # Raw user input
        elif request.method == "POST":
            data.update(request.POST)  # Raw user input
        return data  # Unsanitized data
    
    def _get_user_input(request):
        data = _get_data_from_request(request)  # Gets raw data
        return data.get("user_input", "")  # Returns unsanitized input
    
    # DANGEROUS USAGE:
    user_input = _get_user_input(request)  # Unsanitized
    
    # SQL Injection risk:
    query = f"SELECT * FROM users WHERE name = '{user_input}'"
    
    # XSS risk:
    html = f"<div>Hello {user_input}</div>"
    
    # Path traversal risk:
    file_path = f"/uploads/{user_input}"
    
    # Command injection risk:
    os.system(f"process_file {user_input}")
    """
    pass


def secure_pattern_example():
    """
    SECURE PATTERN (USE THIS):
    
    # Replace _get_data_from_request with:
    validated_data = await SecureRequestHandler.get_validated_data_from_request(request)
    
    # Replace _get_user_input with:
    user_input = await SecureRequestHandler.get_safe_user_input_from_request(
        request, "user_input", default=""
    )
    
    # Or use individual validators:
    user_input = InputValidator.validate_sql_safe(raw_input)
    user_input = InputValidator.validate_xss_safe(user_input)
    user_input = InputValidator.validate_path_safe(user_input)
    user_input = InputValidator.validate_command_safe(user_input)
    
    # SAFE USAGE:
    # SQL safe (still use parameterized queries):
    query = "SELECT * FROM users WHERE name = ?"
    params = [user_input]  # Safe - validated input
    
    # XSS safe:
    html = f"<div>Hello {user_input}</div>"  # Safe - HTML escaped
    
    # Path safe:
    file_path = os.path.join("/uploads", user_input)  # Safe - no traversal
    
    # Command safe:
    # Don't use os.system - use subprocess with validated args
    subprocess.run(["process_file", user_input], check=True)  # Safe
    """
    pass


# Integration with existing FastAPI app
def integrate_security_into_existing_app(app: FastAPI):
    """How to add security to existing Nexus app."""
    
    # 1. Add security middleware
    app.add_middleware(SecurityMiddleware)
    
    # 2. Update existing endpoints to use secure patterns
    # Replace direct request.query_params access with:
    # SecureRequestHandler.validate_query_param()
    
    # 3. Add input validation to all user inputs
    # Use InputValidator methods before processing any user data
    
    # 4. Add security headers
    @app.middleware("http")
    async def add_security_headers(request: Request, call_next):
        response = await call_next(request)
        for header, value in SecurityConfig.SECURITY_HEADERS.items():
            response.headers[header] = value
        return response
    
    return app


if __name__ == "__main__":
    """
    To integrate these security measures into your Nexus application:
    
    1. Add the security middleware to your main FastAPI app
    2. Replace all direct request parameter access with SecureRequestHandler methods
    3. Use InputValidator for all user input validation
    4. Update your content.py and other route files to use the secure patterns
    5. Test thoroughly to ensure functionality is preserved
    
    The key is replacing the vulnerable flow:
    request.GET/POST -> _get_data_from_request -> _get_user_input -> dangerous_sink
    
    With the secure flow:
    request -> SecureRequestHandler -> InputValidator -> safe_processing
    """
    
    # Example of creating secure app
    app = create_secure_app()
    
    # Add your existing routes with security updates
    # app.include_router(content_router, prefix="/api/v1/content")
    
    print("Security integration example completed.")
    print("Apply these patterns to your existing Nexus application.")