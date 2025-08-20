#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Integration test to demonstrate the sanitize_and_validate decorator working.
This tests the actual decorator functionality with various parameter combinations.
"""

import sys
import os

# Add source directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))

from api.v2.validators.validation import (
    sanitize_and_validate, validate_email, validate_username, 
    validate_password, sanitize_email, sanitize_username
)


# Mock function to test the decorator
@sanitize_and_validate(
    validators={
        'email': validate_email,
        'username': validate_username,
        'password': validate_password
    },
    sanitizers={
        'email': sanitize_email,
        'username': sanitize_username
    }
)
def mock_create_user(email, username, password, **kwargs):
    """Mock function that simulates creating a user."""
    return {
        'email': email,
        'username': username,
        'password': password,
        'status': 'success'
    }


def test_decorator_success():
    """Test that the decorator works with valid inputs."""
    print("Testing decorator with valid inputs...")
    
    try:
        result = mock_create_user(
            email="  TEST@EXAMPLE.COM  ",  # Should be sanitized to lowercase
            username="  TestUser123  ",    # Should be sanitized to lowercase
            password="validPassword123"
        )
        
        # Check that sanitization occurred
        if result['email'] == 'test@example.com' and result['username'] == 'testuser123':
            print("✓ Decorator sanitization working correctly")
            print(f"  Email sanitized: 'TEST@EXAMPLE.COM' -> '{result['email']}'")
            print(f"  Username sanitized: 'TestUser123' -> '{result['username']}'")
        else:
            print("✗ Sanitization not working correctly")
            print(f"  Expected: test@example.com, testuser123")
            print(f"  Got: {result['email']}, {result['username']}")
            
    except Exception as e:
        print(f"✗ Unexpected error with valid inputs: {e}")


def test_decorator_validation_failure():
    """Test that the decorator properly rejects invalid inputs."""
    print("\nTesting decorator with invalid inputs...")
    
    # Test with invalid email
    try:
        mock_create_user(
            email="invalid-email",
            username="validuser",
            password="validPassword123"
        )
        print("✗ Should have failed with invalid email")
    except ValueError as e:
        if "email" in str(e).lower():
            print("✓ Correctly rejected invalid email")
        else:
            print(f"✗ Wrong error message for email: {e}")
    
    # Test with invalid username (too short)
    try:
        mock_create_user(
            email="test@example.com",
            username="ab",  # Too short
            password="validPassword123"
        )
        print("✗ Should have failed with invalid username")
    except ValueError as e:
        if "username" in str(e).lower():
            print("✓ Correctly rejected invalid username")
        else:
            print(f"✗ Wrong error message for username: {e}")
    
    # Test with invalid password (too short)
    try:
        mock_create_user(
            email="test@example.com",
            username="validuser",
            password="short"  # Too short
        )
        print("✗ Should have failed with invalid password")
    except ValueError as e:
        if "password" in str(e).lower():
            print("✓ Correctly rejected invalid password")
        else:
            print(f"✗ Wrong error message for password: {e}")


def test_missing_parameters():
    """Test that the decorator handles missing required parameters."""
    print("\nTesting decorator with missing parameters...")
    
    # Mock function with missing parameter validation
    @sanitize_and_validate(
        validators={'required_param': validate_username},
        sanitizers={}
    )
    def mock_function_with_required(required_param, optional_param=None):
        return {'required_param': required_param}
    
    # Test with missing required parameter
    try:
        mock_function_with_required(optional_param="value")
        print("✗ Should have failed with missing required parameter")
    except ValueError as e:
        if "missing" in str(e).lower():
            print("✓ Correctly detected missing required parameter")
        else:
            print(f"✗ Wrong error message for missing parameter: {e}")


if __name__ == "__main__":
    print("Running decorator integration tests...\n")
    
    test_decorator_success()
    test_decorator_validation_failure()
    test_missing_parameters()
    
    print("\nDecorator integration tests completed!")