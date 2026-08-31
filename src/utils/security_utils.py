"""
Centralized Input Sanitization Module for Security
Purpose: Prevent XSS and SQL injection attacks by sanitizing user input.
"""

import re
import html


def sanitize_html(input_string: str) -> str:
    """
    Sanitizes HTML tags to prevent XSS attacks.
    """
    if not isinstance(input_string, str):
        return ""
    return html.escape(input_string)


def sanitize_sql(input_string: str) -> str:
    """
    Sanitizes SQL injection attempts.
    """
    if not isinstance(input_string, str):
        return ""
    # Remove common SQL injection keywords
    dangerous_keywords = ["'", '"', " OR ", " AND ", " UNION ", " SELECT ", " DROP ", " DELETE ", " INSERT ", " UPDATE "]
    sanitized = input_string
    for keyword in dangerous_keywords:
        sanitized = sanitized.replace(keyword, "")
    return sanitized


def sanitize_user_input(input_string: str) -> str:
    """
    Combines HTML and SQL sanitization.
    """
    if not isinstance(input_string, str):
        return ""
    sanitized = sanitize_html(input_string)
    sanitized = sanitize_sql(sanitized)
    return sanitized