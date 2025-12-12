"""
Input validation and sanitization utilities to prevent injection attacks.
Addresses the security vulnerability where user-controlled input flows 
from source (request.GET/POST) through processing functions to dangerous sinks.
"""

import re
import html
import urllib.parse
from typing import Any, Dict, List, Optional, Union
from fastapi import HTTPException


class InputValidator:
    """Centralized input validation and sanitization."""
    
    # SQL injection patterns
    SQL_INJECTION_PATTERNS = [
        r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION)\b)",
        r"(--|#|/\*|\*/)",
        r"(\b(OR|AND)\s+\d+\s*=\s*\d+)",
        r"(\'\s*(OR|AND)\s+\'\w+\'\s*=\s*\'\w+)",
        r"(\bUNION\s+SELECT\b)",
    ]
    
    # XSS patterns
    XSS_PATTERNS = [
        r"<script[^>]*>.*?</script>",
        r"javascript:",
        r"on\w+\s*=",
        r"<iframe[^>]*>",
        r"<object[^>]*>",
        r"<embed[^>]*>",
    ]
    
    # Path traversal patterns
    PATH_TRAVERSAL_PATTERNS = [
        r"\.\./",
        r"\.\.\\",
        r"%2e%2e%2f",
        r"%2e%2e\\",
        r"\.\.%2f",
        r"\.\.%5c",
    ]
    
    # Command injection patterns
    COMMAND_INJECTION_PATTERNS = [
        r"[;&|`$(){}[\]<>]",
        r"\b(cat|ls|dir|type|copy|move|del|rm|chmod|sudo|su)\b",
        r"(\||&&|;|`|\$\()",
    ]

    @classmethod
    def sanitize_string(cls, value: str, max_length: int = 1000) -> str:
        """Sanitize string input to prevent injection attacks."""
        if not isinstance(value, str):
            value = str(value)
        
        # Limit length
        value = value[:max_length]
        
        # HTML encode to prevent XSS
        value = html.escape(value, quote=True)
        
        # Remove null bytes and control characters
        value = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', value)
        
        return value.strip()

    @classmethod
    def validate_sql_safe(cls, value: str) -> str:
        """Validate that input is safe from SQL injection."""
        if not isinstance(value, str):
            value = str(value)
        
        value_lower = value.lower()
        
        for pattern in cls.SQL_INJECTION_PATTERNS:
            if re.search(pattern, value_lower, re.IGNORECASE):
                raise HTTPException(
                    status_code=400, 
                    detail="Invalid input: potential SQL injection detected"
                )
        
        return cls.sanitize_string(value)

    @classmethod
    def validate_xss_safe(cls, value: str) -> str:
        """Validate that input is safe from XSS attacks."""
        if not isinstance(value, str):
            value = str(value)
        
        for pattern in cls.XSS_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                raise HTTPException(
                    status_code=400, 
                    detail="Invalid input: potential XSS detected"
                )
        
        return cls.sanitize_string(value)

    @classmethod
    def validate_path_safe(cls, value: str) -> str:
        """Validate that input is safe from path traversal attacks."""
        if not isinstance(value, str):
            value = str(value)
        
        # URL decode first to catch encoded traversal attempts
        decoded_value = urllib.parse.unquote(value)
        
        for pattern in cls.PATH_TRAVERSAL_PATTERNS:
            if re.search(pattern, decoded_value, re.IGNORECASE):
                raise HTTPException(
                    status_code=400, 
                    detail="Invalid input: potential path traversal detected"
                )
        
        return cls.sanitize_string(value)

    @classmethod
    def validate_command_safe(cls, value: str) -> str:
        """Validate that input is safe from command injection."""
        if not isinstance(value, str):
            value = str(value)
        
        for pattern in cls.COMMAND_INJECTION_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                raise HTTPException(
                    status_code=400, 
                    detail="Invalid input: potential command injection detected"
                )
        
        return cls.sanitize_string(value)

    @classmethod
    def validate_integer(cls, value: Any, min_val: int = None, max_val: int = None) -> int:
        """Validate and convert to integer with bounds checking."""
        try:
            int_val = int(value)
            
            if min_val is not None and int_val < min_val:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Value must be at least {min_val}"
                )
            
            if max_val is not None and int_val > max_val:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Value must be at most {max_val}"
                )
            
            return int_val
        except (ValueError, TypeError):
            raise HTTPException(
                status_code=400, 
                detail="Invalid integer value"
            )

    @classmethod
    def validate_category_list(cls, categories: Optional[str]) -> Optional[List[str]]:
        """Validate and sanitize category list input."""
        if not categories:
            return None
        
        # Validate the raw input first
        categories = cls.validate_xss_safe(categories)
        categories = cls.validate_sql_safe(categories)
        
        # Split and validate each category
        category_list = []
        for cat in categories.split(","):
            cat = cat.strip()
            if cat:
                # Additional validation for category names
                if not re.match(r'^[a-zA-Z0-9\s\-_]+$', cat):
                    raise HTTPException(
                        status_code=400, 
                        detail=f"Invalid category name: {cat}"
                    )
                
                if len(cat) > 50:
                    raise HTTPException(
                        status_code=400, 
                        detail="Category name too long"
                    )
                
                category_list.append(cat)
        
        return category_list if category_list else None

    @classmethod
    def validate_exclude_ids(cls, exclude_ids: Optional[str]) -> List[int]:
        """Validate and parse exclude_ids parameter."""
        if not exclude_ids:
            return []
        
        # Basic sanitization
        exclude_ids = cls.sanitize_string(exclude_ids, max_length=500)
        
        # Validate format (only numbers and commas)
        if not re.match(r'^[\d,\s]+$', exclude_ids):
            raise HTTPException(
                status_code=400, 
                detail="Invalid exclude_ids format: only numbers and commas allowed"
            )
        
        try:
            ids = []
            for id_str in exclude_ids.split(","):
                id_str = id_str.strip()
                if id_str:
                    id_val = cls.validate_integer(id_str, min_val=1, max_val=999999999)
                    ids.append(id_val)
            return ids
        except Exception:
            raise HTTPException(
                status_code=400, 
                detail="Invalid exclude_ids format"
            )

    @classmethod
    def validate_cursor(cls, cursor: Optional[str]) -> Optional[str]:
        """Validate cursor parameter for pagination."""
        if not cursor:
            return None
        
        # Cursors should be base64-encoded or simple alphanumeric
        cursor = cls.sanitize_string(cursor, max_length=200)
        
        if not re.match(r'^[a-zA-Z0-9+/=_-]+$', cursor):
            raise HTTPException(
                status_code=400, 
                detail="Invalid cursor format"
            )
        
        return cursor

    @classmethod
    def sanitize_for_logging(cls, value: Any, max_length: int = 200) -> str:
        """Sanitize input for safe logging to prevent log injection."""
        if value is None:
            return "None"
        
        safe_str = str(value)[:max_length]
        # Remove control characters, newlines, and other dangerous chars
        safe_str = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f\n\r\t]', '', safe_str)
        # Remove ANSI escape sequences
        safe_str = re.sub(r'\x1b\[[0-9;]*m', '', safe_str)
        
        return safe_str

    @classmethod
    def validate_search_query(cls, query: str) -> str:
        """Validate search query input."""
        if not isinstance(query, str):
            query = str(query)
        
        # Length check
        if len(query) > 500:
            raise HTTPException(
                status_code=400, 
                detail="Search query too long"
            )
        
        # Validate against injection patterns
        query = cls.validate_sql_safe(query)
        query = cls.validate_xss_safe(query)
        query = cls.validate_command_safe(query)
        
        # Additional search-specific validation
        if re.search(r'[<>{}[\]\\]', query):
            raise HTTPException(
                status_code=400, 
                detail="Invalid characters in search query"
            )
        
        return query.strip()


def validate_request_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate and sanitize request data dictionary.
    This replaces the vulnerable _get_data_from_request pattern.
    """
    if not isinstance(data, dict):
        raise HTTPException(status_code=400, detail="Invalid request data format")
    
    validated_data = {}
    
    for key, value in data.items():
        # Validate key names
        if not isinstance(key, str) or not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', key):
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid parameter name: {key}"
            )
        
        # Sanitize values based on type
        if isinstance(value, str):
            validated_data[key] = InputValidator.sanitize_string(value)
        elif isinstance(value, (int, float)):
            validated_data[key] = value
        elif isinstance(value, bool):
            validated_data[key] = value
        elif isinstance(value, list):
            # Validate list elements
            validated_list = []
            for item in value:
                if isinstance(item, str):
                    validated_list.append(InputValidator.sanitize_string(item))
                else:
                    validated_list.append(item)
            validated_data[key] = validated_list
        else:
            # Convert other types to string and sanitize
            validated_data[key] = InputValidator.sanitize_string(str(value))
    
    return validated_data


def get_safe_user_input(data: Dict[str, Any], field_name: str, default: str = "") -> str:
    """
    Safely extract and validate user input from request data.
    This replaces the vulnerable _get_user_input pattern.
    """
    # First validate the entire data structure
    validated_data = validate_request_data(data)
    
    # Extract the specific field
    user_input = validated_data.get(field_name, default)
    
    if not isinstance(user_input, str):
        user_input = str(user_input)
    
    # Apply comprehensive validation
    user_input = InputValidator.validate_sql_safe(user_input)
    user_input = InputValidator.validate_xss_safe(user_input)
    user_input = InputValidator.validate_path_safe(user_input)
    user_input = InputValidator.validate_command_safe(user_input)
    
    return user_input