import json
import re
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

            # Validate arguments
            missing_validations = []
            for arg, validator in validators.items():
                if arg in kwargs:
                    try:
                        validator(kwargs[arg])
                    except ValueError as e:
                        raise ValueError(f"Validation failed for {arg}: {e}")
                else:
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


def validate_object_id_list(object_id_list):
    for document_id in object_id_list:
        try:
            ObjectId(document_id)
        except Exception:
            raise ValueError(f"Invalid ObjectId: {document_id}")


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




