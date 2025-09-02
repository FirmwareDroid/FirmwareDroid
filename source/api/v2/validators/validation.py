import json
import re
import inspect
from bson import ObjectId
from functools import wraps


def sanitize_and_validate(validators, sanitizers):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Sanitize arguments
            for arg, sanitizer in sanitizers.items():
                if arg in kwargs:
                    kwargs[arg] = sanitizer(kwargs[arg])

            # Get function signature for default values
            sig = inspect.signature(func)
            missing_validations = []
            for arg, validator in validators.items():
                if arg in kwargs:
                    try:
                        validator(kwargs[arg])
                    except ValueError as e:
                        raise ValueError(f"Validation failed for {arg}: {e}")
                else:
                    # Only require validation if no default or default is not None
                    param = sig.parameters.get(arg)
                    if param is None or param.default is inspect.Parameter.empty or param.default is not None:
                        missing_validations.append(arg)
            if missing_validations:
                raise ValueError(f"Missing validations for: {', '.join(missing_validations)}")
            return func(*args, **kwargs)
        return wrapper
    return decorator


def sanitize_string(value):
    if isinstance(value, str):
        # Allow only numbers, characters, and special symbols like []
        sanitized_value = re.sub(r'[^a-zA-Z0-9\[\],\-_]', '', value)
        return sanitized_value.strip()
    return value


def sanitize_json(value):
    try:
        return json.dumps(json.loads(value))
    except json.JSONDecodeError:
        raise ValueError("Invalid JSON string for kwargs.")


def validate_module_name(module_name):
    from api.v2.schema.AndroidAppSchema import ScannerModules
    valid_modules = list(ScannerModules.__members__.keys())
    if module_name not in valid_modules:
        raise ValueError(f"Invalid module name: {module_name}. Must be one of {valid_modules}")


def validate_object_id(object_id):
    """Validate a single ObjectId."""
    try:
        ObjectId(object_id)
    except Exception:
        raise ValueError(f"Invalid ObjectId: {object_id}")
    return object_id


def validate_object_id_list(object_id_list):
    """Validate a list of ObjectIds."""
    for document_id in object_id_list:
        try:
            ObjectId(document_id)
        except Exception:
            raise ValueError(f"Invalid ObjectId: {document_id}")
    return object_id_list


def validate_kwargs(kwargs):
    try:
        json.loads(kwargs)
    except json.JSONDecodeError:
        raise ValueError("Invalid JSON string for kwargs.")


def validate_queue_name(queue_name):
    from webserver.settings import RQ_QUEUES
    if queue_name not in RQ_QUEUES.keys():
        raise ValueError(f"Invalid queue name: {queue_name}. Must be one of {list(RQ_QUEUES.keys())}")
    return queue_name


def validate_email(email):
    """Validate email format using regex pattern."""
    import re
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not isinstance(email, str) or not re.match(email_pattern, email):
        raise ValueError(f"Invalid email format: {email}")
    return email


def validate_username(username):
    """Validate username format - allow alphanumeric and common special characters."""
    if not isinstance(username, str):
        raise ValueError("Username must be a string")
    if len(username) < 3 or len(username) > 30:
        raise ValueError("Username must be between 3 and 30 characters")
    if not re.match(r'^[a-zA-Z0-9._-]+$', username):
        raise ValueError("Username can only contain letters, numbers, dots, underscores, and hyphens")
    return username


def validate_password(password):
    """Validate password strength - minimum 8 characters."""
    if not isinstance(password, str):
        raise ValueError("Password must be a string")
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters long")
    return password


def validate_api_key(api_key):
    """Validate API key format - allow alphanumeric and common special characters."""
    if not isinstance(api_key, str):
        raise ValueError("API key must be a string")
    if len(api_key) < 10:
        raise ValueError("API key must be at least 10 characters long")
    # Allow alphanumeric and common API key characters
    if not re.match(r'^[a-zA-Z0-9._-]+$', api_key):
        raise ValueError("API key contains invalid characters")
    return api_key


def validate_regex_pattern(pattern):
    """Validate regex pattern to prevent ReDoS attacks."""
    if not isinstance(pattern, str):
        raise ValueError("Regex pattern must be a string")
    
    # Basic length check to prevent overly complex patterns
    if len(pattern) > 500:
        raise ValueError("Regex pattern too long - maximum 500 characters")
    
    # Check for potentially dangerous patterns that could cause ReDoS
    dangerous_patterns = [
        r'\(\?\=.*\)\+',  # Positive lookahead with quantifier - escaped backslashes
        r'\(\?\!.*\)\+',  # Negative lookahead with quantifier - escaped backslashes
        r'\(.*\)\+.*\\1',  # Nested quantifiers with backreferences - double backslash for literal backslash
    ]
    
    for dangerous in dangerous_patterns:
        try:
            if re.search(dangerous, pattern):
                raise ValueError("Regex pattern contains potentially dangerous constructs")
        except re.error:
            # If our dangerous pattern detection regex is malformed, skip this check
            continue
    
    # Try to compile the pattern to ensure it's valid
    try:
        re.compile(pattern)
    except re.error as e:
        raise ValueError(f"Invalid regex pattern: {e}")
    
    return pattern


def sanitize_email(email):
    """Sanitize email by converting to lowercase and stripping whitespace."""
    if isinstance(email, str):
        return email.strip().lower()
    return email


def sanitize_username(username):
    """Sanitize username by stripping whitespace and converting to lowercase."""
    if isinstance(username, str):
        return username.strip().lower()
    return username


def validate_format_name(format_name):
    """Validate format name for AOSP build files."""
    if not isinstance(format_name, str):
        raise ValueError("Format name must be a string")
    
    # Only allow specific known format types
    valid_formats = ['mk', 'bp']
    if format_name.lower() not in valid_formats:
        raise ValueError(f"Invalid format name: {format_name}. Must be one of {valid_formats}")
    
    return format_name.lower()


def sanitize_api_key(api_key):
    """Sanitize API key by stripping whitespace."""
    if isinstance(api_key, str):
        return api_key.strip()
    return api_key


