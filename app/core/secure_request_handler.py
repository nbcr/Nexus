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
    def _extract_query_params(request: Request) -> Dict[str, Any]:
        """Extract query parameters from GET request."""
        return dict(request.query_params.items())

    @staticmethod
    async def _extract_json_data(request: Request) -> Dict[str, Any]:
        """Extract JSON data from POST request."""
        json_data = await request.json()
        if not isinstance(json_data, dict):
            raise HTTPException(status_code=400, detail="Invalid JSON format")
        return json_data

    @staticmethod
    async def _extract_form_data(request: Request) -> Dict[str, Any]:
        """Extract form data from POST request."""
        form_data = await request.form()
        data = {}
        for key, value in form_data.items():
            if not hasattr(value, 'read'):  # Skip file uploads
                data[key] = value
        return data

    @staticmethod
    async def _handle_post_request(request: Request) -> Dict[str, Any]:
        """Handle POST request data extraction."""
        content_type = request.headers.get("content-type", "")
        
        if "application/json" in content_type:
            return await SecureRequestHandler._extract_json_data(request)
        elif "application/x-www-form-urlencoded" in content_type:
            return await SecureRequestHandler._extract_form_data(request)
        elif "multipart/form-data" in content_type:
            return await SecureRequestHandler._extract_form_data(request)
        else:
            return {}

    @staticmethod
    async def get_validated_data_from_request(request: Request) -> Dict[str, Any]:
        """
        Securely extract and validate data from request.
        Replaces the vulnerable _get_data_from_request pattern.
        """
        try:
            if request.method == "GET":
                data = SecureRequestHandler._extract_query_params(request)
            elif request.method == "POST":
                data = await SecureRequestHandler._handle_post_request(request)
            else:
                data = {}
            
            return validate_request_data(data)
            
        except Exception as e:
            if isinstance(e, HTTPException):
                raise
            raise HTTPException(status_code=400, detail="Invalid request data format")
    
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
    def _validate_string_param(value: str, max_length: int) -> str:
        """Validate string parameter."""
        validated_value = InputValidator.sanitize_string(str(value), max_length)
        validated_value = InputValidator.validate_xss_safe(validated_value)
        return InputValidator.validate_sql_safe(validated_value)

    @staticmethod
    def _validate_bool_param(value: Any) -> bool:
        """Validate boolean parameter."""
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.lower() in ('true', '1', 'yes', 'on')
        return bool(value)

    @staticmethod
    def _convert_param_value(value: Any, param_type: type, param_name: str, max_length: int) -> Any:
        """Convert parameter value to target type."""
        try:
            if param_type == str:
                return SecureRequestHandler._validate_string_param(value, max_length)
            elif param_type == int:
                return InputValidator.validate_integer(value)
            elif param_type == bool:
                return SecureRequestHandler._validate_bool_param(value)
            else:
                return param_type(value)
        except (ValueError, TypeError):
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid {param_type.__name__} value for parameter {param_name}"
            )

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
        
        return SecureRequestHandler._convert_param_value(value, param_type, param_name, max_length)
    
    @staticmethod
    def validate_search_input(search_query: str) -> str:
        """Validate search input to prevent injection attacks."""
        return InputValidator.validate_search_query(search_query)
    
    @staticmethod
    def _validate_page_param(page: int) -> int:
        """Validate page parameter."""
        return InputValidator.validate_integer(page, min_val=1, max_val=10000)

    @staticmethod
    def _validate_page_size_param(page_size: int) -> int:
        """Validate page_size parameter."""
        return InputValidator.validate_integer(page_size, min_val=1, max_val=100)

    @staticmethod
    def validate_pagination_params(
        page: Optional[int] = None,
        page_size: Optional[int] = None,
        cursor: Optional[str] = None
    ) -> Dict[str, Any]:
        """Validate pagination parameters."""
        validated_params = {}
        
        if page is not None:
            validated_params['page'] = SecureRequestHandler._validate_page_param(page)
        
        if page_size is not None:
            validated_params['page_size'] = SecureRequestHandler._validate_page_size_param(page_size)
        
        if cursor is not None:
            validated_params['cursor'] = InputValidator.validate_cursor(cursor)
        
        return validated_params
    
    @staticmethod
    def _remove_file_paths(sanitized: str) -> str:
        """Remove file paths from error messages."""
        sanitized = re.sub(r'[A-Za-z]:\\[^\\s]*', '[PATH]', sanitized)
        return re.sub(r'/[^\\s]*', '[PATH]', sanitized)

    @staticmethod
    def _remove_sql_fragments(sanitized: str) -> str:
        """Remove SQL fragments from error messages."""
        return re.sub(r'(SELECT|INSERT|UPDATE|DELETE)\\s+[^\\s]*', '[SQL]', sanitized, flags=re.IGNORECASE)

    @staticmethod
    def sanitize_error_message(error_msg: str) -> str:
        """Sanitize error messages to prevent information disclosure."""
        sanitized = InputValidator.sanitize_for_logging(error_msg, max_length=500)
        sanitized = SecureRequestHandler._remove_file_paths(sanitized)
        return SecureRequestHandler._remove_sql_fragments(sanitized)


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