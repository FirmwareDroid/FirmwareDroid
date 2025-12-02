# FirmwareDroid Testing Guide

This document provides comprehensive information about testing in the FirmwareDroid project.

## Test Structure Overview

The FirmwareDroid testing framework provides comprehensive coverage for:
- **Unit Tests**: Individual component testing
- **Integration Tests**: API workflow testing  
- **GraphQL Tests**: Schema and query testing
- **Security Tests**: Validation and security feature testing
- **Performance Tests**: Response time and resource usage testing

## Test Files Organization

```
source/
├── tests/                          # Core testing framework
│   ├── __init__.py                # Testing utilities
│   ├── base.py                    # Base test classes and factories
│   ├── test_settings.py           # Test-specific Django settings
│   ├── test_graphql_schemas.py    # GraphQL API tests
│   ├── test_static_analysis.py    # Static analysis module tests
│   └── test_integration.py        # Integration and workflow tests
├── file_upload/
│   └── tests.py                   # File upload API tests
├── file_download/
│   └── tests.py                   # File download API tests
├── setup/
│   └── tests.py                   # Setup and configuration tests
└── run_tests.py                   # Test runner script
```

## Running Tests

### Quick Test Run
```bash
cd source/
python run_tests.py
```

### Running Specific Test Modules
```bash
# Unit tests only
DJANGO_SETTINGS_MODULE=tests.test_settings python -m unittest file_upload.tests -v

# Integration tests
DJANGO_SETTINGS_MODULE=tests.test_settings python -m unittest tests.test_integration -v

# GraphQL tests
DJANGO_SETTINGS_MODULE=tests.test_integration -v
```

### Running Individual Test Cases
```bash
# Specific test class
DJANGO_SETTINGS_MODULE=tests.test_settings python -c "
import django; django.setup()
import unittest
from file_upload.tests import FirmwareUploadTestCase
unittest.main(module=None, argv=[''], testLoader=unittest.TestLoader().loadTestsFromTestCase(FirmwareUploadTestCase), verbosity=2, exit=False)
"
```

## Test Categories

### 1. Unit Tests

**File Upload Tests** (`file_upload/tests.py`)
- File extension validation
- File size limits
- Filename sanitization  
- Authentication requirements
- Storage configuration
- Error handling

**File Download Tests** (`file_download/tests.py`)
- File streaming
- Content type detection
- Error handling for missing files
- Response header validation
- Authentication checks

**Setup Tests** (`setup/tests.py`)
- Configuration validation
- Database setup
- Middleware configuration
- URL routing
- Authentication system

### 2. API Tests

**REST API Testing**
- All endpoint validation
- Request/response format testing
- Authentication and authorization
- Error response validation
- Input validation and sanitization

**GraphQL API Testing** (`tests/test_graphql_schemas.py`)
- Schema validation for all analysis tools:
  - AndroGuard reports
  - APKScan reports
  - Statistics aggregation
  - RQ job monitoring
  - User management
- Query filtering and pagination
- Authentication requirements
- Error handling

### 3. Static Analysis Tests (`tests/test_static_analysis.py`)

**AndroGuard Analysis**
- APK parsing validation
- Permission analysis
- Component detection (activities, services, receivers)
- Error handling for invalid APKs

**Quark Engine Vulnerability Detection**
- CWE vulnerability checking
- Method analysis
- Security pattern detection
- Report generation

**Analysis Pipeline**
- Multi-tool coordination
- Result aggregation
- Performance monitoring
- Resource management

### 4. Integration Tests (`tests/test_integration.py`)

**File Workflow Testing**
- Complete upload → process → download workflows
- Multiple file handling
- Cross-API error propagation

**Security Integration**
- File validation across pipeline
- Authentication flow testing
- Authorization consistency
- Input sanitization validation

**Performance Testing**
- API response time monitoring
- Concurrent request handling
- Memory usage patterns
- Database query efficiency

## Test Utilities and Fixtures

### Base Test Classes

**BaseTestCase**: Basic Django test setup
```python
from tests.base import BaseTestCase

class MyTestCase(BaseTestCase):
    def test_something(self):
        # Automatic user creation, temp directories, cleanup
        pass
```

**BaseAPITestCase**: REST API testing with authentication
```python
from tests.base import BaseAPITestCase

class MyAPITestCase(BaseAPITestCase):
    def test_api_endpoint(self):
        # Automatic authentication, API client setup
        response = self.client.get('/api/endpoint/')
        self.assertEqual(response.status_code, 200)
```

**GraphQLTestCase**: GraphQL API testing
```python
from tests.base import GraphQLTestCase

class MyGraphQLTestCase(GraphQLTestCase):
    def test_query(self):
        response = self.query('{ field }')
        data = self.assertGraphQLSuccess(response)
```

### Test Data Factories

**TestDataFactory**: Consistent test data generation
```python
from tests.base import TestDataFactory

# Create sample data
firmware_data = TestDataFactory.create_firmware_file_data()
apk_data = TestDataFactory.create_apk_file_data()
analysis_data = TestDataFactory.create_analysis_report_data()
```

### Mock Utilities

**Storage Mocking**
```python
from tests.base import mock_storage_setting

@mock_storage_setting('/tmp/firmware', '/tmp/uploads')
def test_with_storage(self):
    # Test with mocked storage paths
    pass
```

**Database Mocking**
```python
from tests.base import mock_mongo_connection

@mock_mongo_connection()
def test_with_db(self):
    # Test with mocked MongoDB
    pass
```

## Test Configuration

### Test Settings (`tests/test_settings.py`)

The test settings provide:
- SQLite in-memory database for fast testing
- Minimal installed apps to avoid external dependencies
- Disabled external services (Redis, MongoDB)
- Test-optimized middleware stack
- Proper authentication configuration

### Environment Setup

Tests run in isolated environment with:
- Temporary file system locations
- Mocked external service dependencies
- Clean database state for each test
- Automatic cleanup after tests

## Writing New Tests

### 1. Unit Test Example

```python
from tests.base import BaseTestCase
from unittest.mock import patch, Mock

class NewFeatureTestCase(BaseTestCase):
    
    def setUp(self):
        super().setUp()
        # Additional setup
    
    @patch('module.external_dependency')
    def test_feature_functionality(self, mock_external):
        # Setup mocks
        mock_external.return_value = 'expected_result'
        
        # Test the feature
        result = feature_function()
        
        # Assertions
        self.assertEqual(result, 'expected_result')
        mock_external.assert_called_once()
```

### 2. API Test Example

```python
from tests.base import BaseAPITestCase
from rest_framework import status

class NewAPITestCase(BaseAPITestCase):
    
    def test_api_endpoint(self):
        data = {'key': 'value'}
        response = self.client.post('/api/endpoint/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('result', response.data)
```

### 3. GraphQL Test Example

```python
from tests.base import GraphQLTestCase

class NewGraphQLTestCase(GraphQLTestCase):
    
    def test_graphql_query(self):
        query = '''
        query {
            newField {
                id
                name
            }
        }
        '''
        
        response = self.query(query)
        data = self.assertGraphQLSuccess(response)
        self.assertIn('newField', data)
```

## Test Best Practices

### 1. Test Isolation
- Each test should be independent
- Use `setUp()` and `tearDown()` for test-specific setup
- Mock external dependencies
- Clean up resources after tests

### 2. Comprehensive Coverage
- Test success cases and error cases
- Test edge cases and boundary conditions
- Test authentication and authorization
- Test input validation

### 3. Performance Considerations
- Use in-memory database for speed
- Mock expensive operations
- Keep tests focused and fast
- Group related tests logically

### 4. Maintainability
- Use descriptive test names
- Include docstrings explaining test purpose
- Use test utilities to reduce duplication
- Keep tests simple and readable

## Continuous Integration

### Running Tests in CI

```yaml
# Example CI configuration
- name: Run Tests
  run: |
    cd source/
    python run_tests.py
    
- name: Run Coverage
  run: |
    cd source/
    coverage run --source='.' run_tests.py
    coverage report --show-missing
```

### Test Requirements

Required packages for testing:
- Django testing framework (included)
- unittest.mock (Python standard library)
- tempfile (Python standard library)
- Additional test dependencies as needed

## Troubleshooting

### Common Issues

**Django Settings Not Configured**
```bash
# Solution: Set DJANGO_SETTINGS_MODULE
export DJANGO_SETTINGS_MODULE=tests.test_settings
```

**External Service Dependencies**
```python
# Solution: Mock external services
@patch('module.external_service')
def test_feature(self, mock_service):
    # Test with mocked service
```

**Database Errors**
```python
# Solution: Use test database settings
@override_settings(DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}})
```

### Performance Issues

**Slow Tests**
- Use mocking for expensive operations
- Optimize database queries
- Use in-memory databases
- Run tests in parallel when possible

**Memory Issues**
- Clean up resources in tearDown()
- Use context managers for file operations
- Mock large data structures

## Future Improvements

### Planned Enhancements
- [ ] Add automated test discovery
- [ ] Implement test coverage reporting
- [ ] Add performance benchmarking
- [ ] Create test data generators
- [ ] Add mutation testing
- [ ] Implement property-based testing

### Tool Integration
- [ ] pytest compatibility
- [ ] tox for multi-environment testing
- [ ] Continuous integration hooks
- [ ] Test result reporting
- [ ] Automated test generation

## Contributing to Tests

When adding new features:
1. Write tests for new functionality
2. Update existing tests if behavior changes
3. Ensure all tests pass before submitting
4. Add documentation for new test utilities
5. Follow existing test patterns and conventions

For questions about testing, refer to this documentation or the existing test examples.