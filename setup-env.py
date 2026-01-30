#!/usr/bin/env python3
"""
Environment setup helper for Zippy-Archon
This script helps you create a .env.production file with the correct structure.
"""

import os
import sys
from pathlib import Path


def create_env_file():
    """Create a .env.production file with template values."""

    env_example = Path('env.production.example')
    env_production = Path('.env.production')

    if not env_example.exists():
        print("❌ env.production.example not found!")
        print("💡 Make sure you're running this from the Zippy-Archon root directory")
        return False

    if env_production.exists():
        print("⚠️  .env.production already exists!")
        response = input("   Do you want to overwrite it? (y/N): ").strip().lower()
        if response != 'y':
            print("   Keeping existing .env.production file")
            return True

    # Copy the example file
    import shutil
    shutil.copy(env_example, env_production)

    print("✅ Created .env.production from template")
    print("\n📝 Next steps:")
    print("   1. Edit .env.production with your actual API keys and database credentials")
    print("   2. Required fields to update:")
    print("      - SUPABASE_URL and SUPABASE_SERVICE_KEY")
    print("      - At least one AI provider API key (OPENAI_API_KEY, ANTHROPIC_API_KEY, or XAI_API_KEY)")
    print("      - JWT_SECRET_KEY (generate a secure random string)")
    print("   3. Run: python check-setup.py")
    print("   4. Launch: ./launch-with-port-check.sh")

    return True


def show_env_requirements():
    """Show what needs to be configured in the environment file."""

    print("📋 Environment Configuration Requirements:")
    print("=" * 50)
    print()
    print("🔑 Required Settings:")
    print("   • SUPABASE_URL - Your Supabase project URL")
    print("   • SUPABASE_SERVICE_KEY - Your Supabase service key")
    print("   • JWT_SECRET_KEY - Secure random string (min 32 chars)")
    print()
    print("🤖 AI Provider (at least one):")
    print("   • OPENAI_API_KEY - Your OpenAI API key")
    print("   • ANTHROPIC_API_KEY - Your Anthropic API key")
    print("   • XAI_API_KEY - Your XAI API key")
    print()
    print("📊 Optional but Recommended:")
    print("   • SENTRY_DSN - Error tracking")
    print("   • GRAFANA_ADMIN_PASSWORD - Monitoring dashboard access")
    print()
    print("💡 Tip: You can start with just the required settings and add optional ones later.")


def main():
    """Main environment setup helper."""
    print("🎯 Zippy-Archon Environment Setup")
    print("=" * 40)

    if len(sys.argv) > 1 and sys.argv[1] == '--help':
        show_env_requirements()
        return

    print("This script will help you set up your .env.production file.")
    print()

    # Show requirements first
    show_env_requirements()

    print("\n" + "=" * 40)

    response = input("Do you want to create .env.production from the template? (Y/n): ").strip().lower()

    if response in ['', 'y', 'yes']:
        if create_env_file():
            print("\n🎉 Setup complete! Edit .env.production and then run:")
            print("   python check-setup.py")
            print("   ./launch-with-port-check.sh")
    else:
        print("Setup cancelled. You can manually copy and edit env.production.example")


if __name__ == "__main__":
    main()
