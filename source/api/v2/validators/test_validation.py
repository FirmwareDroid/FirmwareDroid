#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple test script to verify validation functions work correctly.
This is not a formal test framework test but a quick verification script.
"""

import sys
import os

# Add source directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))

from api.v2.validators.validation import (
    validate_email, validate_username, validate_password, validate_api_key,
    validate_regex_pattern, validate_format_name, sanitize_email,
    sanitize_username, sanitize_api_key
)


def test_email_validation():
    """Test email validation function."""
    print("Testing email validation...")
    
    # Valid emails
    valid_emails = [
        "test@example.com",
        "user.name@domain.co.uk", 
        "user+tag@example.org"
    ]
    
    for email in valid_emails:
        try:
            result = validate_email(email)
            print(f"✓ Valid email: {email}")
        except ValueError as e:
            print(f"✗ Unexpected validation error for {email}: {e}")
    
    # Invalid emails
    invalid_emails = [
        "invalid-email",
        "@example.com",
        "user@",
        "user space@example.com",
        ""
    ]
    
    for email in invalid_emails:
        try:
            validate_email(email)
            print(f"✗ Should have failed for: {email}")
        except ValueError:
            print(f"✓ Correctly rejected: {email}")


def test_username_validation():
    """Test username validation function."""
    print("\nTesting username validation...")
    
    # Valid usernames
    valid_usernames = ["user123", "test_user", "admin-user", "user.name"]
    
    for username in valid_usernames:
        try:
            result = validate_username(username)
            print(f"✓ Valid username: {username}")
        except ValueError as e:
            print(f"✗ Unexpected validation error for {username}: {e}")
    
    # Invalid usernames
    invalid_usernames = ["us", "a" * 31, "user space", "user@domain", ""]
    
    for username in invalid_usernames:
        try:
            validate_username(username)
            print(f"✗ Should have failed for: {username}")
        except ValueError:
            print(f"✓ Correctly rejected: {username}")


def test_password_validation():
    """Test password validation function."""
    print("\nTesting password validation...")
    
    # Valid passwords
    valid_passwords = ["password123", "12345678", "a" * 20]
    
    for password in valid_passwords:
        try:
            result = validate_password(password)
            print(f"✓ Valid password length: {len(password)}")
        except ValueError as e:
            print(f"✗ Unexpected validation error for password: {e}")
    
    # Invalid passwords
    invalid_passwords = ["short", "1234567", ""]
    
    for password in invalid_passwords:
        try:
            validate_password(password)
            print(f"✗ Should have failed for password length: {len(password)}")
        except ValueError:
            print(f"✓ Correctly rejected password length: {len(password)}")


def test_regex_validation():
    """Test regex pattern validation function."""
    print("\nTesting regex validation...")
    
    # Valid patterns
    valid_patterns = [
        r"\.apk$",
        r"[a-zA-Z0-9]+",
        r"^test.*\.txt$"
    ]
    
    for pattern in valid_patterns:
        try:
            result = validate_regex_pattern(pattern)
            print(f"✓ Valid regex: {pattern}")
        except ValueError as e:
            print(f"✗ Unexpected validation error for {pattern}: {e}")
    
    # Invalid patterns
    invalid_patterns = [
        "[invalid",  # Unclosed bracket
        "a" * 600,  # Too long
    ]
    
    for pattern in invalid_patterns:
        try:
            validate_regex_pattern(pattern)
            print(f"✗ Should have failed for: {pattern[:50]}...")
        except ValueError:
            print(f"✓ Correctly rejected: {pattern[:50]}...")


def test_format_name_validation():
    """Test format name validation function."""
    print("\nTesting format name validation...")
    
    # Valid format names
    valid_formats = ["mk", "bp", "MK", "BP"]
    
    for format_name in valid_formats:
        try:
            result = validate_format_name(format_name)
            print(f"✓ Valid format: {format_name} -> {result}")
        except ValueError as e:
            print(f"✗ Unexpected validation error for {format_name}: {e}")
    
    # Invalid format names
    invalid_formats = ["invalid", "xml", "", 123]
    
    for format_name in invalid_formats:
        try:
            validate_format_name(format_name)
            print(f"✗ Should have failed for: {format_name}")
        except ValueError:
            print(f"✓ Correctly rejected: {format_name}")


def test_sanitization():
    """Test sanitization functions."""
    print("\nTesting sanitization...")
    
    # Test email sanitization
    email = "  TEST@EXAMPLE.COM  "
    sanitized = sanitize_email(email)
    print(f"✓ Email sanitization: '{email}' -> '{sanitized}'")
    
    # Test username sanitization
    username = "  TestUser  "
    sanitized = sanitize_username(username)
    print(f"✓ Username sanitization: '{username}' -> '{sanitized}'")
    
    # Test API key sanitization
    api_key = "  api-key-123  "
    sanitized = sanitize_api_key(api_key)
    print(f"✓ API key sanitization: '{api_key}' -> '{sanitized}'")


if __name__ == "__main__":
    print("Running validation tests...\n")
    
    test_email_validation()
    test_username_validation()
    test_password_validation()
    test_regex_validation()
    test_format_name_validation()
    test_sanitization()
    
    print("\nValidation tests completed!")