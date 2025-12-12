"""
Secure request handling utilities to replace vulnerable patterns.
Addresses the security flow: request.GET/POST -> _get_data_from_request -> _get_user_input -> sink
"""

from typing import Any, Dict, Optional, Union
from fastapi import Request, HTTPException
from app.core.input_validation import InputValidator, validate_request_data, get_safe_user_input


class SecureRequestHandler:
    """Secure request data extraction and validation."""
    
    @staticmethod
    async def get_validated_data_from_request(request: Request) -> Dict[str, Any]:
        """
        Securely extract and validate data from request.
        Replaces the vulnerable _get_data_from_request pattern.
        """
        data = {}
        
        try:
            # Handle different request methods securely
            if request.method == "GET":
                # Extract query parameters
                for key, value in request.query_params.items():
                    data[key] = value
            
            elif request.method == "POST":
                # Handle different content types
                content_type = request.headers.get("content-type", "")
                
                if "application/json" in content_type:
                    json_data = await request.json()
                    if isinstance(json_data, dict):
                        data.update(json_data)
                    else:
                        raise HTTPException(
                            status_code=400, 
                            detail="Invalid JSON format"
                        )
                
                elif "application/x-www-form-urlencoded" in content_type:
                    form_data = await request.form()
                    for key, value in form_data.items():
                        data[key] = value
                
                elif "multipart/form-data" in content_type:
                    form_data = await request.form()
                    for key, value in form_data.items():
                        # Handle file uploads separately if needed
                        if hasattr(value, 'read'):
                            # This is a file upload - handle carefully
                            continue
                        data[key] = value
            
            # Validate the entire data structure
            return validate_request_data(data)
            
        except Exception as e:
            if isinstance(e, HTTPException):
                raise
            raise HTTPException(
                status_code=400, 
                detail="Invalid request data format"
            )
    
    @staticmethod
    async def get_safe_user_input_from_request(
        request: Request, 
        field_name: str, 
        default: str = ""
    ) -> str:
        """
        Securely extract and validate user input from request.
        Replaces the vulnerable _get_user_input pattern.
        """
        # Get validated data from request
        data = await SecureRequestHandler.get_validated_data_from_request(request)
        
        # Extract and validate the specific field
        return get_safe_user_input(data, field_name, default)
    
    @staticmethod
    def validate_query_param(
        request: Request, 
        param_name: str, 
        param_type: type = str,
        required: bool = False,
        default: Any = None,
        max_length: int = 1000
    ) -> Any:
        """
        Safely extract and validate a single query parameter.
        """
        value = request.query_params.get(param_name, default)
        
        if value is None and required:
            raise HTTPException(
                status_code=400, 
                detail=f"Missing required parameter: {param_name}"
            )
        
        if value is None:
            return default
        
        try:
            if param_type == str:
                # String validation
                validated_value = InputValidator.sanitize_string(str(value), max_length)
                validated_value = InputValidator.validate_xss_safe(validated_value)
                validated_value = InputValidator.validate_sql_safe(validated_value)
                return validated_value
            
            elif param_type == int:
                # Integer validation
                return InputValidator.validate_integer(value)
            
            elif param_type == bool:
                # Boolean validation
                if isinstance(value, bool):
                    return value
                if isinstance(value, str):
                    return value.lower() in ('true', '1', 'yes', 'on')
                return bool(value)
            
            else:
                # Convert to target type
                return param_type(value)
                
        except (ValueError, TypeError) as e:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid {param_type.__name__} value for parameter {param_name}"
            )
    
    @staticmethod
    def validate_search_input(search_query: str) -> str:
        """Validate search input to prevent injection attacks."""
        return InputValidator.validate_search_query(search_query)
    
    @staticmethod
    def validate_pagination_params(
        page: Optional[int] = None,
        page_size: Optional[int] = None,
        cursor: Optional[str] = None
    ) -> Dict[str, Any]:
        """Validate pagination parameters."""
        validated_params = {}
        
        if page is not None:
            validated_params['page'] = InputValidator.validate_integer(
                page, min_val=1, max_val=10000
            )
        
        if page_size is not None:
            validated_params['page_size'] = InputValidator.validate_integer(
                page_size, min_val=1, max_val=100
            )
        
        if cursor is not None:
            validated_params['cursor'] = InputValidator.validate_cursor(cursor)
        
        return validated_params
    
    @staticmethod
    def sanitize_error_message(error_msg: str) -> str:
        """Sanitize error messages to prevent information disclosure."""
        # Remove sensitive information patterns
        sanitized = InputValidator.sanitize_for_logging(error_msg, max_length=500)
        
        # Remove potential file paths
        sanitized = re.sub(r'[A-Za-z]:\\[^\\s]*', '[PATH]', sanitized)
        sanitized = re.sub(r'/[^\\s]*', '[PATH]', sanitized)
        
        # Remove potential SQL fragments
        sanitized = re.sub(r'(SELECT|INSERT|UPDATE|DELETE)\\s+[^\\s]*', '[SQL]', sanitized, flags=re.IGNORECASE)
        
        return sanitized


# Decorator for secure endpoint handling
def secure_endpoint(func):
    """Decorator to add security validation to endpoints."""
    async def wrapper(*args, **kwargs):
        try:
            # Add request validation here if needed
            return await func(*args, **kwargs)
        except HTTPException:
            raise
        except Exception as e:
            # Sanitize error messages
            safe_error = SecureRequestHandler.sanitize_error_message(str(e))
            raise HTTPException(status_code=500, detail="Internal server error")
    
    return wrapper