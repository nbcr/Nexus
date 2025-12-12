"""Utilities for generating unique slugs."""

import re
import hashlib
from typing import Optional


def generate_slug(title: str, content_id: Optional[int] = None) -> str:
    """
    Generate a unique slug from a title.

    Args:
        title: The content title
        content_id: Optional content ID to ensure uniqueness

    Returns:
        A URL-safe slug
    """
    # Convert to lowercase and replace spaces with hyphens
    slug = title.lower().strip()

    # Remove special characters, keep only alphanumeric and hyphens
    slug = re.sub(r"[^a-z0-9\s-]", "", slug)
    slug = re.sub(r"[\s-]+", "-", slug)

    # Truncate to reasonable length
    slug = slug[:100]

    # Remove leading/trailing hyphens
    slug = slug.strip("-")

    # Add hash of full title for uniqueness
    title_hash = hashlib.md5(title.encode()).hexdigest()[:8]

    if content_id:
        return f"{slug}-{content_id}-{title_hash}"
    else:
        return f"{slug}-{title_hash}"


def generate_slug_from_url(url: str) -> str:
    """
    Generate a slug from a URL when title is not available.

    Args:
        url: Source URL

    Returns:
        A URL-safe slug
    """
    # Non-cryptographic hash for URL slugs - MD5 acceptable for this use case
    url_hash = hashlib.md5(url.encode()).hexdigest()[:12]
    return f"content-{url_hash}"
