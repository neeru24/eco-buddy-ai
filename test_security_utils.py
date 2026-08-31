"""
Comprehensive Unit Tests for Security Sanitization
Tests XSS prevention, SQL injection prevention, and edge cases.
"""

import pytest
from security_utils import sanitize_html, sanitize_sql, sanitize_user_input


class TestHTMLSanitization:
    def test_script_tag_removed(self):
        """Should escape script tags."""
        result = sanitize_html("<script>alert('xss')</script>")
        assert "&lt;script&gt;" in result
        assert "<script>" not in result

    def test_basic_html_escaped(self):
        """Should escape basic HTML tags."""
        result = sanitize_html("<b>Bold</b>")
        assert "&lt;b&gt;" in result

    def test_plain_text_preserved(self):
        """Should preserve plain text."""
        assert sanitize_html("Hello World") == "Hello World"

    def test_input_with_quotes(self):
        """Should escape double quotes."""
        result = sanitize_html('He said "Hello"')
        assert "&quot;" in result

    def test_input_with_ampersand(self):
        """Should escape ampersands."""
        result = sanitize_html("Tom & Jerry")
        assert "&amp;" in result

    def test_empty_string(self):
        """Should handle empty strings."""
        assert sanitize_html("") == ""

    def test_none_input(self):
        """Should handle None input."""
        assert sanitize_html(None) == ""


class TestSQLSanitization:
    def test_removes_single_quote(self):
        """Should remove single quotes."""
        result = sanitize_sql("John's data")
        assert "'" not in result

    def test_removes_or_keyword(self):
        """Should remove OR keyword."""
        result = sanitize_sql("1 OR 1=1")
        assert "OR" not in result

    def test_removes_and_keyword(self):
        """Should remove AND keyword."""
        result = sanitize_sql("1 AND 1=1")
        assert "AND" not in result

    def test_removes_union_keyword(self):
        """Should remove UNION keyword."""
        result = sanitize_sql("SELECT * FROM users UNION SELECT * FROM admins")
        assert "UNION" not in result

    def test_removes_drop_keyword(self):
        """Should remove DROP keyword."""
        result = sanitize_sql("DROP TABLE users")
        assert "DROP" not in result

    def test_removes_select_keyword(self):
        """Should remove SELECT keyword."""
        result = sanitize_sql("SELECT * FROM users")
        assert "SELECT" not in result

    def test_plain_text_preserved(self):
        """Should preserve plain text without SQL keywords."""
        assert sanitize_sql("Hello World") == "Hello World"

    def test_empty_string(self):
        """Should handle empty strings."""
        assert sanitize_sql("") == ""

    def test_none_input(self):
        """Should handle None input."""
        assert sanitize_sql(None) == ""


class TestCombinedSanitization:
    def test_removes_script_and_sql(self):
        """Should remove both XSS and SQL injection."""
        result = sanitize_user_input("<script>DROP TABLE users</script>")
        assert "script" not in result.lower()
        assert "DROP" not in result

    def test_plain_text_preserved(self):
        """Should preserve plain text."""
        assert sanitize_user_input("This is a safe message") == "This is a safe message"

    def test_removes_quotes_and_brackets(self):
        """Should remove quotes and escape brackets."""
        result = sanitize_user_input("' OR '1'='1")
        assert "'" not in result

    def test_empty_string(self):
        """Should handle empty strings."""
        assert sanitize_user_input("") == ""

    def test_none_input(self):
        """Should handle None input."""
        assert sanitize_user_input(None) == ""


class TestAdvancedAttackVectors:
    def test_xss_attempt_with_image_tag(self):
        """Should sanitize image tag XSS attacks."""
        result = sanitize_user_input("<img src=x onerror=alert(1)>")
        assert "onerror" not in result.lower()

    def test_sql_injection_with_comments(self):
        """Should sanitize SQL injection with comments."""
        result = sanitize_user_input("1; DROP TABLE users; --")
        assert "DROP" not in result

    def test_sql_injection_with_case_insensitive(self):
        """Should sanitize uppercase SQL keywords."""
        result = sanitize_user_input("SELECT * FROM users")
        assert "SELECT" not in result

    def test_xss_attempt_with_iframe(self):
        """Should sanitize iframe XSS attacks."""
        result = sanitize_user_input("<iframe src='javascript:alert(1)'>")
        assert "iframe" not in result.lower()