#!/usr/bin/env python3
"""
Comprehensive Test Runner for Zippy Archon Platform

This script runs all frontend and backend tests, collects results,
and generates detailed reports for analysis.
"""

import os
import sys
import json
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import argparse

class TestRunner:
    """Comprehensive test runner for the Zippy Archon platform."""

    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.results_dir = self.project_root / "test_results"
        self.results_dir.mkdir(exist_ok=True)

        # Test configuration
        self.test_suites = {
            "frontend": {
                "path": self.project_root / "Scripts" / "frontend-tests",
                "command": ["npm", "test", "--", "--coverage", "--watchAll=false"],
                "timeout": 300,
            },
            "backend": {
                "path": self.project_root / "Scripts" / "backend-tests",
                "command": ["python", "-m", "pytest", "-v", "--tb=short", "--cov=python/src", "--cov-report=html"],
                "timeout": 600,
            },
            "integration": {
                "path": self.project_root / "Scripts" / "integration-tests",
                "command": ["python", "-m", "pytest", "-v", "--tb=short"],
                "timeout": 300,
            },
            "e2e": {
                "path": self.project_root / "e2e-tests",
                "command": ["python", "-m", "pytest", "-v", "--tb=short"],
                "timeout": 300,
            }
        }

        self.results = {
            "timestamp": datetime.now().isoformat(),
            "test_suites": {},
            "summary": {},
            "issues": [],
            "recommendations": []
        }

    def run_test_suite(self, suite_name: str) -> Dict[str, Any]:
        """Run a specific test suite and collect results."""
        if suite_name not in self.test_suites:
            raise ValueError(f"Unknown test suite: {suite_name}")

        suite_config = self.test_suites[suite_name]
        suite_path = suite_config["path"]
        command = suite_config["command"]
        timeout = suite_config["timeout"]

        print(f"🚀 Running {suite_name} tests...")
        print(f"   Path: {suite_path}")
        print(f"   Command: {' '.join(command)}")

        # Change to test directory if needed
        original_cwd = os.getcwd()
        if suite_path.exists():
            os.chdir(suite_path)

        result = {
            "suite_name": suite_name,
            "start_time": datetime.now().isoformat(),
            "status": "running",
            "output": "",
            "error": "",
            "duration": 0,
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "coverage": {}
        }

        try:
            start_time = time.time()

            # Run the test command
            process = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=suite_path if suite_path.exists() else None
            )

            end_time = time.time()
            result["duration"] = round(end_time - start_time, 2)
            result["output"] = process.stdout
            result["error"] = process.stderr

            if process.returncode == 0:
                result["status"] = "passed"
                print(f"✅ {suite_name} tests completed successfully")
            else:
                result["status"] = "failed"
                print(f"❌ {suite_name} tests failed")

            # Parse test results
            self._parse_test_output(result, suite_name)

        except subprocess.TimeoutExpired:
            result["status"] = "timeout"
            result["error"] = f"Test suite timed out after {timeout} seconds"
            print(f"⏰ {suite_name} tests timed out")

        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)
            print(f"💥 {suite_name} tests encountered an error: {e}")

        finally:
            # Restore original working directory
            os.chdir(original_cwd)

        result["end_time"] = datetime.now().isoformat()
        return result

    def _parse_test_output(self, result: Dict[str, Any], suite_name: str):
        """Parse test output to extract metrics."""
        output = result["output"]

        if suite_name == "frontend":
            self._parse_frontend_output(result, output)
        elif suite_name in ["backend", "integration", "e2e"]:
            self._parse_backend_output(result, output)

    def _parse_frontend_output(self, result: Dict[str, Any], output: str):
        """Parse frontend (Vitest) test output."""
        lines = output.split('\n')

        for line in lines:
            line = line.strip()
            if "Tests:" in line and "passed" in line:
                # "Tests: 15 passed, 2 failed, 1 skipped"
                parts = line.split(',')
                for part in parts:
                    part = part.strip()
                    if "passed" in part:
                        result["passed"] = int(part.split()[0])
                    elif "failed" in part:
                        result["failed"] = int(part.split()[0])
                    elif "skipped" in part:
                        result["skipped"] = int(part.split()[0])

            elif "Coverage" in line and "Statements" in line:
                # Parse coverage information
                try:
                    coverage_parts = line.split('|')
                    if len(coverage_parts) >= 4:
                        result["coverage"] = {
                            "statements": coverage_parts[1].strip(),
                            "branches": coverage_parts[2].strip(),
                            "functions": coverage_parts[3].strip(),
                            "lines": coverage_parts[4].strip() if len(coverage_parts) > 4 else ""
                        }
                except:
                    pass

    def _parse_backend_output(self, result: Dict[str, Any], output: str):
        """Parse backend (pytest) test output."""
        lines = output.split('\n')

        for line in lines:
            line = line.strip()

            # Look for pytest summary
            if line.startswith("=====") and "passed" in line:
                # "===== 15 passed, 2 failed, 1 skipped in 12.34s ====="
                parts = line.split()
                for i, part in enumerate(parts):
                    if part.isdigit():
                        count = int(part)
                        if i + 1 < len(parts):
                            next_word = parts[i + 1].lower()
                            if "passed" in next_word:
                                result["passed"] = count
                            elif "failed" in next_word:
                                result["failed"] = count
                            elif "skipped" in next_word:
                                result["skipped"] = count

            # Parse coverage if available
            elif "TOTAL" in line and any(char.isdigit() for char in line):
                try:
                    parts = line.split()
                    if len(parts) >= 4:
                        result["coverage"] = {
                            "statements": parts[1],
                            "missing": parts[2],
                            "coverage": parts[3]
                        }
                except:
                    pass

    def run_all_tests(self) -> Dict[str, Any]:
        """Run all test suites and collect comprehensive results."""
        print("🎯 Starting comprehensive test execution...")
        print("=" * 60)

        all_results = {}

        for suite_name in self.test_suites.keys():
            result = self.run_test_suite(suite_name)
            all_results[suite_name] = result

            # Add spacing between test suites
            print()

        self.results["test_suites"] = all_results
        self._generate_summary()
        self._analyze_issues()
        self._generate_recommendations()

        return self.results

    def _generate_summary(self):
        """Generate overall test summary."""
        total_passed = 0
        total_failed = 0
        total_skipped = 0
        total_duration = 0
        suite_statuses = {}

        for suite_name, result in self.results["test_suites"].items():
            total_passed += result.get("passed", 0)
            total_failed += result.get("failed", 0)
            total_skipped += result.get("skipped", 0)
            total_duration += result.get("duration", 0)
            suite_statuses[suite_name] = result.get("status", "unknown")

        total_tests = total_passed + total_failed + total_skipped
        success_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0

        self.results["summary"] = {
            "total_tests": total_tests,
            "passed": total_passed,
            "failed": total_failed,
            "skipped": total_skipped,
            "success_rate": round(success_rate, 2),
            "total_duration": round(total_duration, 2),
            "suite_statuses": suite_statuses
        }

    def _analyze_issues(self):
        """Analyze test results for issues and patterns."""
        issues = []

        for suite_name, result in self.results["test_suites"].items():
            status = result.get("status")

            if status == "failed":
                issues.append({
                    "type": "test_failure",
                    "suite": suite_name,
                    "severity": "high",
                    "description": f"{suite_name} test suite failed",
                    "details": result.get("error", "")
                })

            elif status == "timeout":
                issues.append({
                    "type": "timeout",
                    "suite": suite_name,
                    "severity": "medium",
                    "description": f"{suite_name} test suite timed out",
                    "details": f"Timeout after {self.test_suites[suite_name]['timeout']} seconds"
                })

            elif status == "error":
                issues.append({
                    "type": "execution_error",
                    "suite": suite_name,
                    "severity": "high",
                    "description": f"{suite_name} test suite encountered execution error",
                    "details": result.get("error", "")
                })

            # Check for low test coverage
            coverage = result.get("coverage", {})
            if coverage and "statements" in coverage:
                try:
                    coverage_pct = float(coverage["statements"].rstrip('%'))
                    if coverage_pct < 80:
                        issues.append({
                            "type": "low_coverage",
                            "suite": suite_name,
                            "severity": "medium",
                            "description": f"Low test coverage in {suite_name}",
                            "details": f"Coverage: {coverage_pct}% (target: 80%)"
                        })
                except:
                    pass

        self.results["issues"] = issues

    def _generate_recommendations(self):
        """Generate recommendations based on test results."""
        recommendations = []

        summary = self.results.get("summary", {})
        success_rate = summary.get("success_rate", 0)

        if success_rate < 90:
            recommendations.append({
                "priority": "high",
                "category": "test_quality",
                "description": "Improve test success rate",
                "action": f"Address failing tests to achieve >90% success rate (current: {success_rate}%)"
            })

        if summary.get("failed", 0) > 0:
            recommendations.append({
                "priority": "high",
                "category": "bug_fixes",
                "description": "Fix failing tests",
                "action": "Review and fix all failing test cases"
            })

        # Check for missing test suites
        for suite_name in self.test_suites:
            if self.results["test_suites"].get(suite_name, {}).get("status") == "error":
                recommendations.append({
                    "priority": "medium",
                    "category": "test_setup",
                    "description": f"Fix {suite_name} test setup",
                    "action": f"Resolve setup issues in {suite_name} test suite"
                })

        self.results["recommendations"] = recommendations

    def save_results(self, output_file: Optional[str] = None):
        """Save test results to file."""
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"test_results_{timestamp}.json"

        output_path = self.results_dir / output_file

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)

        print(f"📊 Test results saved to: {output_path}")
        return output_path

    def generate_report(self, output_file: Optional[str] = None):
        """Generate a human-readable test report."""
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"test_report_{timestamp}.md"

        output_path = self.results_dir / output_file

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("# Zippy Archon Test Report\n\n")
            f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

            # Summary
            summary = self.results.get("summary", {})
            f.write("## Summary\n\n")
            f.write(f"- **Total Tests:** {summary.get('total_tests', 0)}\n")
            f.write(f"- **Passed:** {summary.get('passed', 0)}\n")
            f.write(f"- **Failed:** {summary.get('failed', 0)}\n")
            f.write(f"- **Skipped:** {summary.get('skipped', 0)}\n")
            f.write(f"- **Success Rate:** {summary.get('success_rate', 0)}%\n")
            f.write(f"- **Total Duration:** {summary.get('total_duration', 0)}s\n\n")

            # Suite Status
            f.write("## Test Suite Status\n\n")
            for suite_name, status in summary.get("suite_statuses", {}).items():
                status_emoji = {
                    "passed": "✅",
                    "failed": "❌",
                    "timeout": "⏰",
                    "error": "💥",
                    "running": "🔄"
                }.get(status, "❓")
                f.write(f"- **{suite_name}:** {status_emoji} {status}\n")
            f.write("\n")

            # Detailed Results
            f.write("## Detailed Results\n\n")
            for suite_name, result in self.results.get("test_suites", {}).items():
                f.write(f"### {suite_name.title()} Tests\n\n")
                f.write(f"- **Status:** {result.get('status', 'unknown')}\n")
                f.write(f"- **Duration:** {result.get('duration', 0)}s\n")

                if result.get("passed", 0) > 0:
                    f.write(f"- **Passed:** {result['passed']}\n")
                if result.get("failed", 0) > 0:
                    f.write(f"- **Failed:** {result['failed']}\n")
                if result.get("skipped", 0) > 0:
                    f.write(f"- **Skipped:** {result['skipped']}\n")

                coverage = result.get("coverage", {})
                if coverage:
                    f.write("- **Coverage:**\n")
                    for key, value in coverage.items():
                        f.write(f"  - {key}: {value}\n")

                if result.get("error"):
                    f.write(f"- **Error:** {result['error']}\n")

                f.write("\n")

            # Issues
            issues = self.results.get("issues", [])
            if issues:
                f.write("## Issues\n\n")
                for issue in issues:
                    severity_emoji = {
                        "high": "🔴",
                        "medium": "🟡",
                        "low": "🟢"
                    }.get(issue.get("severity", "medium"), "🟡")

                    f.write(f"### {severity_emoji} {issue['description']}\n\n")
                    f.write(f"**Suite:** {issue['suite']}\n\n")
                    f.write(f"**Type:** {issue['type']}\n\n")
                    if issue.get("details"):
                        f.write(f"**Details:** {issue['details']}\n\n")

            # Recommendations
            recommendations = self.results.get("recommendations", [])
            if recommendations:
                f.write("## Recommendations\n\n")
                for rec in recommendations:
                    priority_emoji = {
                        "high": "🔴",
                        "medium": "🟡",
                        "low": "🟢"
                    }.get(rec.get("priority", "medium"), "🟡")

                    f.write(f"### {priority_emoji} {rec['description']}\n\n")
                    f.write(f"**Category:** {rec['category']}\n\n")
                    f.write(f"**Action:** {rec['action']}\n\n")

        print(f"📋 Test report generated: {output_path}")
        return output_path

    def print_summary(self):
        """Print a concise summary to console."""
        summary = self.results.get("summary", {})

        print("\n" + "=" * 60)
        print("🎯 TEST EXECUTION SUMMARY")
        print("=" * 60)
        print(f"Total Tests:     {summary.get('total_tests', 0)}")
        print(f"Passed:          {summary.get('passed', 0)}")
        print(f"Failed:          {summary.get('failed', 0)}")
        print(f"Skipped:         {summary.get('skipped', 0)}")
        print(f"- **Success Rate:** {summary.get('success_rate', 0):.2f}%")
        print(f"- **Total Duration:** {summary.get('total_duration', 0):.2f}s")
        print()

        # Suite status
        print("Test Suite Status:")
        for suite_name, status in summary.get("suite_statuses", {}).items():
            status_emoji = {
                "passed": "✅",
                "failed": "❌",
                "timeout": "⏰",
                "error": "💥"
            }.get(status, "❓")
            print(f"  {status_emoji} {suite_name}: {status}")

        # Issues
        issues = self.results.get("issues", [])
        if issues:
            print(f"\n⚠️  Issues Found: {len(issues)}")
            for issue in issues:
                severity_emoji = {
                    "high": "🔴",
                    "medium": "🟡",
                    "low": "🟢"
                }.get(issue.get("severity", "medium"), "🟡")
                print(f"  {severity_emoji} {issue['description']} ({issue['suite']})")


def main():
    """Main entry point for the test runner."""
    parser = argparse.ArgumentParser(description="Run comprehensive tests for Zippy Archon")
    parser.add_argument(
        "--suites",
        nargs="+",
        choices=["frontend", "backend", "integration", "e2e"],
        help="Specific test suites to run (default: all)"
    )
    parser.add_argument(
        "--output-dir",
        default="test_results",
        help="Output directory for test results"
    )
    parser.add_argument(
        "--no-report",
        action="store_true",
        help="Skip generating detailed report"
    )

    args = parser.parse_args()

    # Get project root
    project_root = Path(__file__).parent.parent

    # Initialize test runner
    runner = TestRunner(project_root)

    try:
        # Run tests
        if args.suites:
            print(f"Running specific test suites: {', '.join(args.suites)}")
            for suite in args.suites:
                result = runner.run_test_suite(suite)
                runner.results["test_suites"][suite] = result
            runner._generate_summary()
            runner._analyze_issues()
            runner._generate_recommendations()
        else:
            runner.run_all_tests()

        # Save results
        json_file = runner.save_results()

        # Generate report
        if not args.no_report:
            report_file = runner.generate_report()

        # Print summary
        runner.print_summary()

        # Return appropriate exit code
        summary = runner.results.get("summary", {})
        failed = summary.get("failed", 0)
        errors = len([s for s in summary.get("suite_statuses", {}).values() if s in ["failed", "error", "timeout"]])

        if failed > 0 or errors > 0:
            print("\n❌ Test execution completed with failures")
            sys.exit(1)
        else:
            print("\n✅ All tests passed successfully!")
            sys.exit(0)

    except Exception as e:
        print(f"💥 Fatal error during test execution: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
