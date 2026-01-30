#!/usr/bin/env python3
"""
Error Handling Migration Script

This script helps migrate API routes from basic HTTPException handling
to the standardized ErrorService for consistent error responses.
"""

import os
import re
from pathlib import Path
from typing import List, Dict, Any


class ErrorHandlingMigrator:
    """Migrates API routes to use standardized error handling."""

    def __init__(self, base_path: str = "python/src/server/api_routes"):
        self.base_path = Path(base_path)
        self.migration_stats = {
            "files_processed": 0,
            "files_modified": 0,
            "routes_updated": 0,
            "errors": []
        }

    def migrate_all_files(self) -> Dict[str, Any]:
        """Migrate all API route files to use standardized error handling."""
        if not self.base_path.exists():
            raise FileNotFoundError(f"API routes directory not found: {self.base_path}")

        # Find all Python files in the api_routes directory
        api_files = list(self.base_path.glob("*.py"))
        api_files = [f for f in api_files if f.name != "__init__.py"]

        print(f"Found {len(api_files)} API route files to process")

        for api_file in api_files:
            try:
                self._migrate_file(api_file)
                self.migration_stats["files_processed"] += 1
            except Exception as e:
                error_msg = f"Failed to migrate {api_file.name}: {str(e)}"
                print(f"ERROR: {error_msg}")
                self.migration_stats["errors"].append(error_msg)

        return self.migration_stats

    def _migrate_file(self, file_path: Path):
        """Migrate a single API route file."""
        print(f"Processing {file_path.name}...")

        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        original_content = content

        # Apply migrations
        content = self._add_error_service_import(content)
        content = self._add_request_dependency(content)
        content = self._replace_httpexception_usage(content)

        # Check if file was modified
        if content != original_content:
            # Create backup
            backup_path = file_path.with_suffix('.py.backup')
            with open(backup_path, 'w', encoding='utf-8') as f:
                f.write(original_content)

            # Write migrated content
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)

            self.migration_stats["files_modified"] += 1
            print(f"Migrated {file_path.name} (backup created)")

    def _add_error_service_import(self, content: str) -> str:
        """Add error service import if not present."""
        import_line = "from ..services.error_service import error_service"

        # Check if already imported
        if "from ..services.error_service import" in content:
            return content

        # Find the import section
        lines = content.split('\n')
        import_end_index = 0

        for i, line in enumerate(lines):
            if line.startswith('from ') or line.startswith('import '):
                import_end_index = i + 1
            elif line.strip() and not line.startswith('#'):
                break

        # Insert import after other imports
        if import_end_index > 0:
            lines.insert(import_end_index, import_line)
            return '\n'.join(lines)

        return content

    def _add_request_dependency(self, content: str) -> str:
        """Add Request import from FastAPI if not present."""
        # Check if Request is already imported
        if "Request" in content and "from fastapi import" in content:
            return content

        # Find FastAPI import line
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if line.startswith('from fastapi import'):
                # Add Request to the import
                if 'Request' not in line:
                    line = line.rstrip() + ', Request'
                    lines[i] = line
                return '\n'.join(lines)

        return content

    def _replace_httpexception_usage(self, content: str) -> str:
        """Replace HTTPException raises with error_service calls."""
        # Pattern to match raise HTTPException calls
        httpexception_pattern = r'raise HTTPException\(status_code=(\d+),\s*detail=([^\)]+)\)'

        def replace_httpexception(match):
            status_code = match.group(1)
            detail = match.group(2)

            # Map status codes to error codes
            error_code_mapping = {
                '400': 'VALIDATION_ERROR',
                '401': 'AUTHENTICATION_ERROR',
                '403': 'AUTHORIZATION_ERROR',
                '404': 'NOT_FOUND',
                '409': 'CONFLICT',
                '422': 'VALIDATION_ERROR',
                '429': 'RATE_LIMIT_ERROR',
                '500': 'INTERNAL_ERROR'
            }

            error_code = error_code_mapping.get(status_code, 'INTERNAL_ERROR')

            return f'''return error_service.create_error_response(
            request=request,
            error_code="{error_code}",
            message={detail},
            status_code={status_code}
        )'''

        # Replace all HTTPException raises
        new_content = re.sub(httpexception_pattern, replace_httpexception, content)

        # Count replacements
        replacements = len(re.findall(httpexception_pattern, content))
        self.migration_stats["routes_updated"] += replacements

        return new_content


def main():
    """Main migration function."""
    print("Starting Error Handling Migration")
    print("=" * 50)

    migrator = ErrorHandlingMigrator()

    try:
        stats = migrator.migrate_all_files()

        print("\n" + "=" * 50)
        print("Migration Summary:")
        print(f"Files processed: {stats['files_processed']}")
        print(f"Files modified: {stats['files_modified']}")
        print(f"Routes updated: {stats['routes_updated']}")

        if stats['errors']:
            print(f"Errors encountered: {len(stats['errors'])}")
            for error in stats['errors']:
                print(f"  - {error}")

        if stats['files_modified'] > 0:
            print("\nMigration completed successfully!")
            print("Backup files created with .backup extension")
            print("Please review changes and test thoroughly before deployment")
        else:
            print("\nNo files needed migration")

    except Exception as e:
        print(f"Migration failed: {str(e)}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
