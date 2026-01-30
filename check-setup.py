#!/usr/bin/env python3
"""
Quick setup checker for Zippy-Archon
This script validates your environment and provides guidance for getting started.
"""

import os
import sys
import subprocess
import json
from pathlib import Path


def check_docker():
    """Check if Docker is installed and running."""
    print("🔍 Checking Docker...")

    try:
        result = subprocess.run(['docker', '--version'],
                              capture_output=True, text=True, check=True)
        print(f"   ✅ Docker installed: {result.stdout.strip()}")

        # Check if Docker daemon is running
        result = subprocess.run(['docker', 'info'],
                              capture_output=True, check=True)
        print("   ✅ Docker daemon is running")

        return True
    except subprocess.CalledProcessError:
        print("   ❌ Docker is not installed or not running")
        print("   💡 Install Docker Desktop: https://www.docker.com/products/docker-desktop/")
        return False
    except FileNotFoundError:
        print("   ❌ Docker command not found")
        print("   💡 Install Docker Desktop: https://www.docker.com/products/docker-desktop/")
        return False


def check_python():
    """Check if Python 3.8+ is installed."""
    print("🔍 Checking Python...")

    try:
        result = subprocess.run([sys.executable, '--version'],
                              capture_output=True, text=True, check=True)
        version = result.stdout.strip()

        # Parse version
        version_num = version.split()[1]
        major, minor = map(int, version_num.split('.')[:2])

        if major >= 3 and minor >= 8:
            print(f"   ✅ Python {version_num} (compatible)")
            return True
        else:
            print(f"   ❌ Python {version_num} (need Python 3.8+)")
            return False
    except (subprocess.CalledProcessError, IndexError, ValueError):
        print("   ❌ Could not determine Python version")
        return False


def check_environment_file():
    """Check if .env.production file exists and has required variables."""
    print("🔍 Checking environment configuration...")

    env_file = Path('.env.production')

    if not env_file.exists():
        print("   ❌ .env.production file not found")
        print("   💡 Copy env.production.example to .env.production and configure it")
        return False

    print("   ✅ .env.production file exists")

    # Check for required variables
    required_vars = ['SUPABASE_URL', 'SUPABASE_SERVICE_KEY', 'JWT_SECRET_KEY']
    missing_vars = []

    try:
        with open(env_file, 'r') as f:
            content = f.read()

        for var in required_vars:
            if f'{var}=' not in content:
                missing_vars.append(var)

        if missing_vars:
            print(f"   ❌ Missing required environment variables: {', '.join(missing_vars)}")
            print("   💡 Please set these in your .env.production file")
            return False
        else:
            print("   ✅ All required environment variables are set")
            return True

    except Exception as e:
        print(f"   ❌ Could not read .env.production file: {e}")
        return False


def check_ports():
    """Check for port conflicts and run port scanner."""
    print("🔍 Checking port conflicts...")

    try:
        # Import and run port manager
        sys.path.insert(0, 'python/src')
        from utils.port_manager import port_manager

        allocations = port_manager.check_and_resolve_conflicts(auto_resolve=False)

        conflicts = [a for a in allocations.values() if a.is_conflict]

        if conflicts:
            print(f"   ⚠️  {len(conflicts)} port conflicts detected:")
            for conflict in conflicts:
                print(f"      - {conflict.service_name}: Port {conflict.original_port} -> {conflict.allocated_port}")
            print("   💡 Run the launch script to automatically resolve conflicts")
            return False
        else:
            print("   ✅ No port conflicts detected")
            return True

    except Exception as e:
        print(f"   ❌ Could not run port scanner: {e}")
        print("   💡 Continue with launch script - it will handle port conflicts automatically")
        return True


def show_next_steps():
    """Show what to do next."""
    print("\n🚀 Next Steps:")
    print("   1. Configure your .env.production file with API keys")
    print("   2. Run: ./launch-with-port-check.sh")
    print("   3. Visit: http://localhost:3737")
    print("   4. Complete the onboarding wizard")
    print("\n📚 For detailed instructions, see: GETTING_STARTED.md")


def main():
    """Main setup checker."""
    print("🎯 Zippy-Archon Setup Checker")
    print("=" * 40)

    checks = [
        ("Docker", check_docker),
        ("Python", check_python),
        ("Environment File", check_environment_file),
        ("Port Conflicts", check_ports),
    ]

    results = []
    for name, check_func in checks:
        print(f"\n{name}:")
        results.append((name, check_func()))

    print("\n" + "=" * 40)
    print("📊 Setup Summary:")

    all_passed = all(result[1] for result in results)

    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"   {name"20"} | {status}")

    if all_passed:
        print("\n🎉 All checks passed! You're ready to launch.")
        show_next_steps()
    else:
        print("\n⚠️  Some checks failed. Please fix the issues above before launching.")
        show_next_steps()


if __name__ == "__main__":
    main()
