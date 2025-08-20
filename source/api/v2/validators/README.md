# GraphQL API Parameter Validation and Sanitization

This directory contains the validation and sanitization framework for the FirmwareDroid GraphQL API. This system ensures that all user inputs are properly validated and sanitized before being processed, improving security and stability.

## Overview

The validation system is built around a decorator `@sanitize_and_validate` that can be applied to GraphQL mutation methods. The decorator:

1. **Sanitizes** input parameters (e.g., trimming whitespace, converting to lowercase)
2. **Validates** input parameters against specified rules
3. **Provides consistent error messages** for validation failures

## Usage

### Basic Example

```python
from api.v2.validators.validation import (
    sanitize_and_validate, validate_email, validate_username,
    sanitize_email, sanitize_username
)

@sanitize_and_validate(
    validators={
        'email': validate_email,
        'username': validate_username
    },
    sanitizers={
        'email': sanitize_email,
        'username': sanitize_username
    }
)
def mutate(cls, root, info, email, username, **kwargs):
    # email and username are now validated and sanitized
    # Implementation here...
```

### Available Validators

- `validate_email(email)` - Validates email format using regex
- `validate_username(username)` - Validates username (3-30 chars, alphanumeric + . _ -)
- `validate_password(password)` - Validates password (minimum 8 characters)
- `validate_api_key(api_key)` - Validates API key format (minimum 10 chars, alphanumeric + . _ -)
- `validate_object_id(object_id)` - Validates single MongoDB ObjectId
- `validate_object_id_list(object_id_list)` - Validates list of MongoDB ObjectIds
- `validate_queue_name(queue_name)` - Validates RQ queue name against configured queues
- `validate_module_name(module_name)` - Validates scanner module name
- `validate_regex_pattern(pattern)` - Validates regex patterns and prevents ReDoS attacks
- `validate_format_name(format_name)` - Validates AOSP build format names (mk, bp)
- `validate_kwargs(kwargs)` - Validates JSON string format

### Available Sanitizers

- `sanitize_email(email)` - Converts email to lowercase and trims whitespace
- `sanitize_username(username)` - Converts username to lowercase and trims whitespace
- `sanitize_api_key(api_key)` - Trims whitespace from API keys
- `sanitize_string(value)` - Removes special characters, keeps alphanumeric + [] , - _
- `sanitize_json(value)` - Validates and reformats JSON strings

## Security Features

### ReDoS Prevention

The `validate_regex_pattern` function specifically addresses the TODO comment in `FirmwareFileSchema.py` about preventing Regular Expression Denial of Service (ReDoS) attacks. It:

- Limits pattern length to 500 characters
- Detects potentially dangerous regex constructs
- Validates that the pattern compiles correctly

### Input Sanitization

All user inputs are sanitized to:
- Remove or escape potentially dangerous characters
- Normalize formatting (lowercase, trimmed)
- Ensure consistent data format

### Parameter Validation

All parameters are validated for:
- Correct data types
- Appropriate lengths and formats
- Valid values (e.g., queue names must exist in configuration)
- Security constraints (e.g., ObjectId format validation)

## Applied To

The validation system has been applied to the following GraphQL schemas:

- **UserAccountSchema.py** - User creation/deletion with email, username, and password validation
- **VirustotalSchema.py** - API key and ObjectId validation for external service integration
- **FirmwareFileSchema.py** - Regex pattern validation to prevent ReDoS attacks
- **AecsJobSchema.py** - Format name and ObjectId validation for AOSP build jobs
- **AndroidFirmwareSchema.py** - Queue name and ObjectId validation for firmware operations
- **AndroidAppSchema.py** - Queue name validation for import jobs
- **FirmwareImporterSettingSchema.py** - Queue name validation for importer settings

## Error Handling

When validation fails, the decorator raises `ValueError` exceptions with descriptive messages:

```
ValueError: Validation failed for email: Invalid email format: invalid-email
ValueError: Validation failed for username: Username must be between 3 and 30 characters
ValueError: Missing validations for: ['required_param']
```

## Adding New Validators

To add a new validator:

1. Create the validator function in `validation.py`:
```python
def validate_my_field(value):
    if not meets_criteria(value):
        raise ValueError(f"Invalid my_field: {value}")
    return value
```

2. Optionally create a sanitizer:
```python
def sanitize_my_field(value):
    return value.strip().lower()
```

3. Apply to your mutation:
```python
@sanitize_and_validate(
    validators={'my_field': validate_my_field},
    sanitizers={'my_field': sanitize_my_field}
)
def mutate(cls, root, info, my_field, **kwargs):
    # Implementation
```

## Testing

The validation system includes comprehensive tests demonstrating:
- Individual validator function behavior
- Sanitizer function behavior  
- Decorator integration and error handling
- End-to-end validation workflows

Run tests with:
```bash
python api/v2/validators/test_validation.py
python api/v2/validators/test_decorator_integration.py
```

## Benefits

This validation system provides:

1. **Security** - Prevents injection attacks, ReDoS, and invalid data processing
2. **Stability** - Ensures consistent data formats and catches errors early
3. **Maintainability** - Centralized validation logic that's easy to update
4. **User Experience** - Clear, consistent error messages for API consumers
5. **Compliance** - Helps meet security requirements for API parameter handling