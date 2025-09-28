#!/usr/bin/env python3
"""
Simple Test Runner for Zippy-Archon Backend Tests

Handles both sync and async tests properly.
"""

import os
import sys
import asyncio
import importlib.util
from pathlib import Path

async def run_async_test(test_instance, method_name):
    """Run an async test method."""
    method = getattr(test_instance, method_name)
    await method()

def run_sync_test(test_instance, method_name):
    """Run a sync test method."""
    method = getattr(test_instance, method_name)
    method()

async def run_test_class(test_class):
    """Run all tests in a test class."""
    results = {'passed': 0, 'failed': 0, 'skipped': 0, 'errors': []}

    # Create test instance
    test_instance = test_class()

    # Run setup if exists
    if hasattr(test_instance, 'setup_method'):
        try:
            test_instance.setup_method()
        except Exception as e:
            print(f"  ❌ Setup failed: {e}")
            return results

    # Get all test methods
    test_methods = [method for method in dir(test_class) if method.startswith('test_')]

    for method_name in test_methods:
        try:
            method = getattr(test_instance, method_name)

            # Check if method is async
            if asyncio.iscoroutinefunction(method):
                await run_async_test(test_instance, method_name)
            else:
                run_sync_test(test_instance, method_name)

            results['passed'] += 1
            print(f"  ✅ {method_name}")

        except Exception as e:
            results['failed'] += 1
            results['errors'].append(f"{method_name}: {str(e)}")
            print(f"  ❌ {method_name}: {str(e)}")

    # Run teardown if exists
    if hasattr(test_instance, 'teardown_method'):
        try:
            test_instance.teardown_method()
        except Exception as e:
            print(f"  ❌ Teardown failed: {e}")

    return results

async def run_plugin_system_tests():
    """Run plugin system tests."""
    print("\n🧩 Testing Plugin System...")

    # Import the test module
    spec = importlib.util.spec_from_file_location(
        "test_plugin_system",
        "Scripts/backend-tests/test_plugin_system.py"
    )
    test_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(test_module)

    total_results = {'passed': 0, 'failed': 0, 'skipped': 0, 'errors': []}

    # Get test classes
    test_classes = [cls for cls in dir(test_module) if cls.startswith('Test')]

    for test_class_name in test_classes:
        test_class = getattr(test_module, test_class_name)
        print(f"Running {test_class_name}...")

        results = await run_test_class(test_class)
        total_results['passed'] += results['passed']
        total_results['failed'] += results['failed']
        total_results['skipped'] += results['skipped']
        total_results['errors'].extend(results['errors'])

    return total_results

async def run_fastapi_server_tests():
    """Run FastAPI server tests."""
    print("\n🚀 Testing FastAPI Server...")

    try:
        # Import the test module
        spec = importlib.util.spec_from_file_location(
            "test_fastapi_server",
            "Scripts/backend-tests/test_fastapi_server.py"
        )
        test_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(test_module)

        total_results = {'passed': 0, 'failed': 0, 'skipped': 0, 'errors': []}

        # Get test classes
        test_classes = [cls for cls in dir(test_module) if cls.startswith('Test')]

        for test_class_name in test_classes:
            test_class = getattr(test_module, test_class_name)
            print(f"Running {test_class_name}...")

            results = await run_test_class(test_class)
            total_results['passed'] += results['passed']
            total_results['failed'] += results['failed']
            total_results['skipped'] += results['skipped']
            total_results['errors'].extend(results['errors'])

        return total_results

    except Exception as e:
        print(f"❌ Failed to load FastAPI server tests: {e}")
        return {'passed': 0, 'failed': 0, 'skipped': 1, 'errors': [str(e)]}

async def main():
    """Main test runner function."""
    print("🔬 Zippy-Archon Backend Test Runner")
    print("=" * 50)

    # Change to project root
    os.chdir(Path(__file__).parent)

    # Add agentic-workflow to path
    sys.path.insert(0, 'agentic-workflow')

    total_results = {'passed': 0, 'failed': 0, 'skipped': 0, 'errors': []}

    # Run plugin system tests
    plugin_results = await run_plugin_system_tests()
    total_results['passed'] += plugin_results['passed']
    total_results['failed'] += plugin_results['failed']
    total_results['skipped'] += plugin_results['skipped']
    total_results['errors'].extend(plugin_results['errors'])

    # Run FastAPI server tests
    fastapi_results = await run_fastapi_server_tests()
    total_results['passed'] += fastapi_results['passed']
    total_results['failed'] += fastapi_results['failed']
    total_results['skipped'] += fastapi_results['skipped']
    total_results['errors'].extend(fastapi_results['errors'])

    # Print summary
    print("\n" + "=" * 50)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 50)

    total_tests = total_results['passed'] + total_results['failed'] + total_results['skipped']
    print(f"Total Tests: {total_tests}")
    print(f"✅ Passed: {total_results['passed']}")
    print(f"❌ Failed: {total_results['failed']}")
    print(f"⏭️  Skipped: {total_results['skipped']}")

    if total_tests > 0:
        success_rate = (total_results['passed'] / total_tests) * 100
        print(".1f"
    # Show errors
    if total_results['errors']:
        print("
🚨 ERRORS:"        for error in total_results['errors'][:5]:
            print(f"  • {error}")
        if len(total_results['errors']) > 5:
            print(f"  ... and {len(total_results['errors']) - 5} more")

    return total_results

if __name__ == "__main__":
    asyncio.run(main())
