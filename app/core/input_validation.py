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
    def _clean_string_content(cls, value: str) -> str:
        """Clean string content by removing dangerous characters."""
        value = html.escape(value, quote=True)
        value = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", value)
        return value.strip()

    @classmethod
    def sanitize_string(cls, value: str, max_length: int = 1000) -> str:
        """Sanitize string input to prevent injection attacks."""
        if not isinstance(value, str):
            value = str(value)

        value = value[:max_length]
        return cls._clean_string_content(value)

    @classmethod
    def _check_sql_patterns(cls, value_lower: str) -> None:
        """Check for SQL injection patterns."""
        for pattern in cls.SQL_INJECTION_PATTERNS:
            if re.search(pattern, value_lower, re.IGNORECASE):
                raise HTTPException(
                    status_code=400,
                    detail="Invalid input: potential SQL injection detected",
                )

    @classmethod
    def validate_sql_safe(cls, value: str) -> str:
        """Validate that input is safe from SQL injection."""
        if not isinstance(value, str):
            value = str(value)

        cls._check_sql_patterns(value.lower())
        return cls.sanitize_string(value)

    @classmethod
    def _check_xss_patterns(cls, value: str) -> None:
        """Check for XSS patterns."""
        for pattern in cls.XSS_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                raise HTTPException(
                    status_code=400, detail="Invalid input: potential XSS detected"
                )

    @classmethod
    def validate_xss_safe(cls, value: str) -> str:
        """Validate that input is safe from XSS attacks."""
        if not isinstance(value, str):
            value = str(value)

        cls._check_xss_patterns(value)
        return cls.sanitize_string(value)

    @classmethod
    def _check_path_patterns(cls, decoded_value: str) -> None:
        """Check for path traversal patterns."""
        for pattern in cls.PATH_TRAVERSAL_PATTERNS:
            if re.search(pattern, decoded_value, re.IGNORECASE):
                raise HTTPException(
                    status_code=400,
                    detail="Invalid input: potential path traversal detected",
                )

    @classmethod
    def validate_path_safe(cls, value: str) -> str:
        """Validate that input is safe from path traversal attacks."""
        if not isinstance(value, str):
            value = str(value)

        decoded_value = urllib.parse.unquote(value)
        cls._check_path_patterns(decoded_value)
        return cls.sanitize_string(value)

    @classmethod
    def _check_command_patterns(cls, value: str) -> None:
        """Check for command injection patterns."""
        for pattern in cls.COMMAND_INJECTION_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                raise HTTPException(
                    status_code=400,
                    detail="Invalid input: potential command injection detected",
                )

    @classmethod
    def validate_command_safe(cls, value: str) -> str:
        """Validate that input is safe from command injection."""
        if not isinstance(value, str):
            value = str(value)

        cls._check_command_patterns(value)
        return cls.sanitize_string(value)

    @classmethod
    def _check_integer_bounds(
        cls, int_val: int, min_val: int | None = None, max_val: int | None = None
    ) -> None:
        """Check integer bounds."""
        if min_val is not None and int_val < min_val:
            raise HTTPException(
                status_code=400, detail=f"Value must be at least {min_val}"
            )
        if max_val is not None and int_val > max_val:
            raise HTTPException(
                status_code=400, detail=f"Value must be at most {max_val}"
            )

    @classmethod
    def validate_integer(
        cls, value: Any, min_val: int | None = None, max_val: int | None = None
    ) -> int:
        """Validate and convert to integer with bounds checking."""
        try:
            int_val = int(value)
            cls._check_integer_bounds(int_val, min_val, max_val)
            return int_val
        except (ValueError, TypeError):
            raise HTTPException(status_code=400, detail="Invalid integer value")

    @classmethod
    def _validate_single_category(cls, cat: str) -> str:
        """Validate a single category name."""
        if not re.match(r"^[\w\s\-]+$", cat):
            raise HTTPException(status_code=400, detail=f"Invalid category name: {cat}")
        if len(cat) > 50:
            raise HTTPException(status_code=400, detail="Category name too long")
        return cat

    @classmethod
    def validate_category_list(cls, categories: Optional[str]) -> Optional[List[str]]:
        """Validate and sanitize category list input."""
        if not categories:
            return None

        categories = cls.validate_xss_safe(categories)
        categories = cls.validate_sql_safe(categories)

        category_list = []
        for cat in categories.split(","):
            cat = cat.strip()
            if cat:
                category_list.append(cls._validate_single_category(cat))

        return category_list if category_list else None

    @classmethod
    def _parse_id_string(cls, id_str: str) -> Optional[int]:
        """Parse and validate a single ID string."""
        id_str = id_str.strip()
        if id_str:
            return cls.validate_integer(id_str, min_val=1, max_val=999999999)
        return None

    @classmethod
    def validate_exclude_ids(cls, exclude_ids: Optional[str]) -> List[int]:
        """Validate and parse exclude_ids parameter."""
        if not exclude_ids:
            return []

        exclude_ids = cls.sanitize_string(exclude_ids, max_length=500)

        if not re.match(r"^[\d,\s]+$", exclude_ids):
            raise HTTPException(
                status_code=400,
                detail="Invalid exclude_ids format: only numbers and commas allowed",
            )

        try:
            ids = []
            for id_str in exclude_ids.split(","):
                parsed_id = cls._parse_id_string(id_str)
                if parsed_id is not None:
                    ids.append(parsed_id)
            return ids
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid exclude_ids format")

    @classmethod
    def _validate_cursor_format(cls, cursor: str) -> None:
        """Validate cursor format (ISO datetime or base64-like)."""
        # Allow ISO datetime format (with colons and periods) and base64-like strings
        if not re.match(r"^[a-zA-Z0-9+/=_:.\-T]+$", cursor):
            raise HTTPException(status_code=400, detail="Invalid cursor format")

    @classmethod
    def validate_cursor(cls, cursor: Optional[str]) -> Optional[str]:
        """Validate cursor parameter for pagination."""
        if not cursor:
            return None

        cursor = cls.sanitize_string(cursor, max_length=200)
        cls._validate_cursor_format(cursor)
        return cursor

    @classmethod
    def validate_visitor_id(cls, visitor_id: Optional[str]) -> Optional[str]:
        """
        Validate visitor_id to prevent injection attacks.

        Visitor IDs should be:
        - UUIDs (36 chars: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx)
        - Or hex strings (32 chars: xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx)
        - Or timestamp-based IDs (16+ chars alphanumeric)

        Args:
            visitor_id: The visitor ID to validate

        Returns:
            Validated visitor_id or None

        Raises:
            HTTPException: If visitor_id is invalid
        """
        if not visitor_id:
            return None

        visitor_id = str(visitor_id).strip()

        # Check length (UUIDs are 36 chars, hex strings 32, timestamp-based 16-64)
        if len(visitor_id) < 16 or len(visitor_id) > 64:
            raise HTTPException(status_code=400, detail="Invalid visitor ID format")

        # Only allow alphanumeric, hyphens, and underscores (valid for UUIDs and hex strings)
        if not re.match(r"^[a-zA-Z0-9\-_]+$", visitor_id):
            raise HTTPException(status_code=400, detail="Invalid visitor ID format")

        return visitor_id

    @classmethod
    def validate_session_token(cls, session_token: Optional[str]) -> Optional[str]:
        """
        Validate session_token to prevent injection attacks.

        Session tokens should be:
        - UUIDs (36 chars)
        - Or valid UUID format strings

        Args:
            session_token: The session token to validate

        Returns:
            Validated session_token or None

        Raises:
            HTTPException: If session_token is invalid
        """
        if not session_token:
            return None

        session_token = str(session_token).strip()

        # Session tokens are typically UUIDs - should be exactly 36 chars
        # But allow some flexibility for other token formats (alphanumeric, hyphens, underscores)
        if len(session_token) < 20 or len(session_token) > 64:
            raise HTTPException(status_code=400, detail="Invalid session token format")

        # Only allow alphanumeric, hyphens, and underscores
        if not re.match(r"^[a-zA-Z0-9\-_]+$", session_token):
            raise HTTPException(status_code=400, detail="Invalid session token format")

        return session_token

    @classmethod
    def _remove_control_chars(cls, safe_str: str) -> str:
        """Remove control characters and ANSI sequences."""
        safe_str = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f\n\r\t]", "", safe_str)
        safe_str = re.sub(r"\x1b\[[0-9;]*m", "", safe_str)
        return safe_str

    @classmethod
    def sanitize_for_logging(cls, value: Any, max_length: int = 200) -> str:
        """Sanitize input for safe logging to prevent log injection."""
        if value is None:
            return "None"

        safe_str = str(value)[:max_length]
        return cls._remove_control_chars(safe_str)

    @classmethod
    def _validate_search_length(cls, query: str) -> None:
        """Validate search query length."""
        if len(query) > 500:
            raise HTTPException(status_code=400, detail="Search query too long")

    @classmethod
    def _validate_search_characters(cls, query: str) -> None:
        """Validate search query characters."""
        if re.search(r"[<>{}[\]\\]", query):
            raise HTTPException(
                status_code=400, detail="Invalid characters in search query"
            )

    @classmethod
    def validate_search_query(cls, query: str) -> str:
        """Validate search query input."""
        if not isinstance(query, str):
            query = str(query)

        cls._validate_search_length(query)

        query = cls.validate_sql_safe(query)
        query = cls.validate_xss_safe(query)
        query = cls.validate_command_safe(query)

        cls._validate_search_characters(query)

        return query.strip()


def _validate_key_name(key: str) -> None:
    """Validate parameter key name."""
    if not isinstance(key, str) or not re.match(r"^[a-zA-Z_][\w]*$", key):
        raise HTTPException(status_code=400, detail=f"Invalid parameter name: {key}")


def _sanitize_value(value: Any) -> Any:
    """Sanitize a single value based on its type."""
    if isinstance(value, str):
        return InputValidator.sanitize_string(value)
    elif isinstance(value, (int, float, bool)):
        return value
    elif isinstance(value, list):
        return [
            InputValidator.sanitize_string(item) if isinstance(item, str) else item
            for item in value
        ]
    else:
        return InputValidator.sanitize_string(str(value))


def validate_request_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate and sanitize request data dictionary.
    This replaces the vulnerable _get_data_from_request pattern.
    """
    if not isinstance(data, dict):
        raise HTTPException(status_code=400, detail="Invalid request data format")

    validated_data = {}
    for key, value in data.items():
        _validate_key_name(key)
        validated_data[key] = _sanitize_value(value)

    return validated_data


def _apply_security_validations(user_input: str) -> str:
    """Apply all security validations to user input."""
    user_input = InputValidator.validate_sql_safe(user_input)
    user_input = InputValidator.validate_xss_safe(user_input)
    user_input = InputValidator.validate_path_safe(user_input)
    user_input = InputValidator.validate_command_safe(user_input)
    return user_input


def get_safe_user_input(
    data: Dict[str, Any], field_name: str, default: str = ""
) -> str:
    """
    Safely extract and validate user input from request data.
    This replaces the vulnerable _get_user_input pattern.
    """
    validated_data = validate_request_data(data)
    user_input = validated_data.get(field_name, default)

    if not isinstance(user_input, str):
        user_input = str(user_input)

    return _apply_security_validations(user_input)
