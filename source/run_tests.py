#!/usr/bin/env python
# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
"""
Test runner for FirmwareDroid tests
"""
import os
import sys
import django
from django.conf import settings
from django.test.utils import get_runner


def setup_django():
    """Setup Django for testing"""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tests.test_settings')
    django.setup()


def run_tests():
    """Run all tests"""
    setup_django()
    
    # Get Django test runner
    TestRunner = get_runner(settings)
    test_runner = TestRunner()
    
    # Run specific test modules
    test_modules = [
        'file_upload.tests',
        'file_download.tests', 
        # 'setup.tests',  # Skip setup tests due to external dependencies
    ]
    
    failures = 0
    for test_module in test_modules:
        print(f"\n{'='*60}")
        print(f"Running tests for: {test_module}")
        print(f"{'='*60}")
        
        try:
            result = test_runner.run_tests([test_module])
            failures += result
        except Exception as e:
            print(f"Error running {test_module}: {e}")
            failures += 1
    
    return failures


if __name__ == '__main__':
    failures = run_tests()
    sys.exit(failures)