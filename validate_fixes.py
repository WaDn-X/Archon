#!/usr/bin/env python3
"""
Validate Core Fixes for Zippy-Archon

Tests the critical fixes we made to ensure they work properly.
"""

import sys
import os
from pathlib import Path

def test_plugin_system_fixes():
    """Test that plugin system fixes work."""
    print("🧩 Testing Plugin System Fixes...")

    try:
        # Change to agentic-workflow directory
        os.chdir('agentic-workflow')

        # Test import
        from plugins.plugin_manager import load_plugins, TOOLS_REGISTRY
        print("  ✅ Plugin manager imports successfully")

        # Test load_plugins function
        # This should work without the 'plugins_directory' error
        try:
            load_plugins('plugins')
            print("  ✅ load_plugins works with correct parameters")
        except Exception as e:
            print(f"  ❌ load_plugins failed: {e}")
            return False

        return True

    except Exception as e:
        print(f"  ❌ Plugin system test failed: {e}")
        return False
    finally:
        # Go back to main directory
        os.chdir('..')

def test_trust_manager_integration():
    """Test that trust manager integration works."""
    print("\n🔐 Testing Trust Manager Integration...")

    try:
        # Change to agentic-workflow directory
        os.chdir('agentic-workflow')

        # Test import
        from plugins.trust_manager import ZippyTrustManager, TrustScore, PluginMetadata
        print("  ✅ Trust manager imports successfully")

        # Test trust score creation
        trust_manager = ZippyTrustManager()
        print("  ✅ Trust manager instance created")

        # Test calculate_trust_score method exists
        if hasattr(trust_manager, 'calculate_trust_score'):
            print("  ✅ calculate_trust_score method exists")
        else:
            print("  ❌ calculate_trust_score method missing")
            return False

        return True

    except Exception as e:
        print(f"  ❌ Trust manager test failed: {e}")
        return False
    finally:
        # Go back to main directory
        os.chdir('..')

def test_marketplace_integration():
    """Test that marketplace integration works."""
    print("\n🛒 Testing Marketplace Integration...")

    try:
        # Change to agentic-workflow directory
        os.chdir('agentic-workflow')

        # Test import
        from plugins.marketplace import ZippyCoinMarketplace
        print("  ✅ Marketplace imports successfully")

        # Test marketplace creation
        marketplace = ZippyCoinMarketplace()
        print("  ✅ Marketplace instance created")

        return True

    except Exception as e:
        print(f"  ❌ Marketplace test failed: {e}")
        return False
    finally:
        # Go back to main directory
        os.chdir('..')

def test_voidspec_integration():
    """Test that VoidSpec integration works."""
    print("\n📋 Testing VoidSpec Integration...")

    try:
        # Change to agentic-workflow directory
        os.chdir('agentic-workflow')

        # Test imports
        from specs.voidspec_requirements_manager import VoidSpecRequirementsManager
        from specs.voidspec_design_manager import VoidSpecDesignManager
        print("  ✅ VoidSpec managers import successfully")

        # Test instance creation
        req_manager = VoidSpecRequirementsManager()
        design_manager = VoidSpecDesignManager()
        print("  ✅ VoidSpec manager instances created")

        return True

    except Exception as e:
        print(f"  ❌ VoidSpec integration test failed: {e}")
        return False
    finally:
        # Go back to main directory
        os.chdir('..')

def test_fastapi_server():
    """Test that FastAPI server fixes work."""
    print("\n🚀 Testing FastAPI Server...")

    try:
        # Change to agentic-workflow directory
        os.chdir('agentic-workflow')

        # Test import (this was the main issue)
        from api.fastapi_server import app
        print("  ✅ FastAPI server imports successfully")

        # Test that app is a FastAPI instance
        from fastapi import FastAPI
        if isinstance(app, FastAPI):
            print("  ✅ FastAPI app instance created correctly")
        else:
            print("  ❌ FastAPI app is not a valid instance")
            return False

        return True

    except Exception as e:
        print(f"  ❌ FastAPI server test failed: {e}")
        return False
    finally:
        # Go back to main directory
        os.chdir('..')

def main():
    """Run all validation tests."""
    print("🔬 Zippy-Archon Core Fixes Validation")
    print("=" * 50)

    # Change to project root
    project_root = Path(__file__).parent
    os.chdir(project_root)

    tests = [
        test_plugin_system_fixes,
        test_trust_manager_integration,
        test_marketplace_integration,
        test_voidspec_integration,
        test_fastapi_server
    ]

    results = {'passed': 0, 'failed': 0}

    for test in tests:
        if test():
            results['passed'] += 1
        else:
            results['failed'] += 1

    # Print summary
    print("\n" + "=" * 50)
    print("📊 VALIDATION RESULTS SUMMARY")
    print("=" * 50)

    total_tests = results['passed'] + results['failed']
    print(f"Total Tests: {total_tests}")
    print(f"✅ Passed: {results['passed']}")
    print(f"❌ Failed: {results['failed']}")

    success_rate = (results['passed'] / total_tests * 100) if total_tests > 0 else 0
    print(".1f"
    if success_rate >= 80:
        print("🎉 Core fixes are working well!")
        print("✅ Ready to proceed with VS Code extension implementation")
    elif success_rate >= 60:
        print("⚠️  Core fixes are mostly working")
        print("🔧 Minor issues may need attention")
    else:
        print("❌ Core fixes need more work")
        print("🔧 Critical issues should be addressed")

    return results

if __name__ == "__main__":
    main()
