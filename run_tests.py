#!/usr/bin/env python3
"""
Test Runner Script for Zippy-Archon

This script runs all tests and provides detailed reporting.
"""

import os
import sys
import subprocess
import json
from pathlib import Path

def run_tests():
    """Run all test suites and provide comprehensive reporting."""

    # Add project paths to Python path
    project_root = Path(__file__).parent
    agentic_workflow = project_root / "agentic-workflow"
    scripts_dir = project_root / "Scripts"
    backend_tests = scripts_dir / "backend-tests"

    sys.path.insert(0, str(project_root))
    sys.path.insert(0, str(agentic_workflow))
    sys.path.insert(0, str(backend_tests))

    print("🔬 Zippy-Archon Test Suite Runner")
    print("=" * 50)

    # Test results tracking
    results = {
        'total_tests': 0,
        'passed': 0,
        'failed': 0,
        'skipped': 0,
        'errors': []
    }

    # Test 1: Plugin System Tests
    print("\n🧩 Testing Plugin System...")
    try:
        # Change to backend-tests directory
        os.chdir(backend_tests)

        # Import and run plugin tests
        import test_plugin_system

        # Get test classes
        test_classes = [cls for cls in dir(test_plugin_system) if cls.startswith('Test')]

        for test_class_name in test_classes:
            test_class = getattr(test_plugin_system, test_class_name)
            print(f"Running {test_class_name}...")

            # Get test methods
            test_methods = [method for method in dir(test_class) if method.startswith('test_')]

            for method_name in test_methods:
                results['total_tests'] += 1
                try:
                    # Create test instance and run method
                    test_instance = test_class()

                    # Check if method is async
                    import inspect
                    method = getattr(test_instance, method_name)
                    if inspect.iscoroutinefunction(method):
                        # Skip async tests for now
                        results['skipped'] += 1
                        print(f"  ⏭️  {method_name} (async - skipped)")
                    else:
                        method()
                        results['passed'] += 1
                        print(f"  ✅ {method_name}")

                except Exception as e:
                    results['failed'] += 1
                    results['errors'].append(f"{test_class_name}.{method_name}: {str(e)}")
                    print(f"  ❌ {method_name}: {str(e)}")

    except Exception as e:
        results['errors'].append(f"Plugin System Tests: {str(e)}")
        print(f"❌ Plugin System Tests failed: {str(e)}")

    # Test 2: FastAPI Server Tests
    print("\n🚀 Testing FastAPI Server...")
    try:
        import test_fastapi_server

        # Get test classes
        test_classes = [cls for cls in dir(test_fastapi_server) if cls.startswith('Test')]

        for test_class_name in test_classes:
            test_class = getattr(test_fastapi_server, test_class_name)
            print(f"Running {test_class_name}...")

            # Get test methods
            test_methods = [method for method in dir(test_class) if method.startswith('test_')]

            for method_name in test_methods:
                results['total_tests'] += 1
                try:
                    # Create test instance and run method
                    test_instance = test_class()

                    # Check if method is async
                    import inspect
                    method = getattr(test_instance, method_name)
                    if inspect.iscoroutinefunction(method):
                        # Skip async tests for now
                        results['skipped'] += 1
                        print(f"  ⏭️  {method_name} (async - skipped)")
                    else:
                        method()
                        results['passed'] += 1
                        print(f"  ✅ {method_name}")

                except Exception as e:
                    results['failed'] += 1
                    results['errors'].append(f"{test_class_name}.{method_name}: {str(e)}")
                    print(f"  ❌ {method_name}: {str(e)}")

    except Exception as e:
        results['errors'].append(f"FastAPI Server Tests: {str(e)}")
        print(f"❌ FastAPI Server Tests failed: {str(e)}")

    # Print Results Summary
    print("\n" + "=" * 50)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 50)

    print(f"Total Tests: {results['total_tests']}")
    print(f"✅ Passed: {results['passed']}")
    print(f"❌ Failed: {results['failed']}")
    print(f"⏭️  Skipped: {results['skipped']}")

    success_rate = (results['passed'] / results['total_tests'] * 100) if results['total_tests'] > 0 else 0
    print(".1f"
    if results['errors']:
        print("
🚨 ERRORS:"        for error in results['errors'][:5]:  # Show first 5 errors
            print(f"  • {error}")
        if len(results['errors']) > 5:
            print(f"  ... and {len(results['errors']) - 5} more errors")

    # Generate recommendations
    print("
💡 RECOMMENDATIONS:"    if success_rate < 60:
        print("  • Fix critical import and setup issues")
        print("  • Implement missing async test handling")
        print("  • Resolve module path dependencies")
    elif success_rate < 80:
        print("  • Address remaining test failures")
        print("  • Improve async test coverage")
        print("  • Add integration tests")
    else:
        print("  • Expand test coverage")
        print("  • Add performance tests")
        print("  • Implement CI/CD integration")

    return results

if __name__ == "__main__":
    run_tests()
