#!/usr/bin/env python3
"""
Comprehensive test runner for Zippy Archon platform
Runs frontend, backend, and integration tests with coverage reporting
"""

import os
import sys
import subprocess
import json
import time
from pathlib import Path
from datetime import datetime

class TestRunner:
    """Comprehensive test runner for all test suites."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.scripts_dir = self.project_root / "Scripts"
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "frontend": {},
            "backend": {},
            "integration": {},
            "summary": {}
        }
        
    def run_frontend_tests(self):
        """Run frontend test suite."""
        print("🧪 Running Frontend Tests...")
        frontend_dir = self.scripts_dir / "frontend-tests"
        
        if not frontend_dir.exists():
            print("❌ Frontend tests directory not found")
            self.results["frontend"]["status"] = "skipped"
            self.results["frontend"]["error"] = "Directory not found"
            return False
        
        try:
            # Install dependencies
            print("📦 Installing frontend dependencies...")
            subprocess.run(["npm", "install"], cwd=frontend_dir, check=True, capture_output=True)
            
            # Run tests with coverage
            print("🚀 Executing frontend tests...")
            result = subprocess.run(
                ["npm", "run", "test:coverage"],
                cwd=frontend_dir,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                print("✅ Frontend tests passed")
                self.results["frontend"]["status"] = "passed"
                self.results["frontend"]["output"] = result.stdout
                return True
            else:
                print("❌ Frontend tests failed")
                self.results["frontend"]["status"] = "failed"
                self.results["frontend"]["error"] = result.stderr
                return False
                
        except subprocess.CalledProcessError as e:
            print(f"❌ Frontend test execution failed: {e}")
            self.results["frontend"]["status"] = "error"
            self.results["frontend"]["error"] = str(e)
            return False
        except Exception as e:
            print(f"❌ Unexpected error in frontend tests: {e}")
            self.results["frontend"]["status"] = "error"
            self.results["frontend"]["error"] = str(e)
            return False
    
    def run_backend_tests(self):
        """Run backend test suite."""
        print("🐍 Running Backend Tests...")
        backend_dir = self.scripts_dir / "backend-tests"
        
        if not backend_dir.exists():
            print("❌ Backend tests directory not found")
            self.results["backend"]["status"] = "skipped"
            self.results["backend"]["error"] = "Directory not found"
            return False
        
        try:
            # Install dependencies
            print("📦 Installing backend dependencies...")
            subprocess.run(
                ["pip", "install", "-r", "requirements.txt"],
                cwd=backend_dir,
                check=True,
                capture_output=True
            )
            
            # Run tests with coverage
            print("🚀 Executing backend tests...")
            result = subprocess.run(
                ["python", "-m", "pytest", "--cov=../agentic-workflow", "--cov-report=html", "--cov-report=term"],
                cwd=backend_dir,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                print("✅ Backend tests passed")
                self.results["backend"]["status"] = "passed"
                self.results["backend"]["output"] = result.stdout
                return True
            else:
                print("❌ Backend tests failed")
                self.results["backend"]["status"] = "failed"
                self.results["backend"]["error"] = result.stderr
                return False
                
        except subprocess.CalledProcessError as e:
            print(f"❌ Backend test execution failed: {e}")
            self.results["backend"]["status"] = "error"
            self.results["backend"]["error"] = str(e)
            return False
        except Exception as e:
            print(f"❌ Unexpected error in backend tests: {e}")
            self.results["backend"]["status"] = "error"
            self.results["backend"]["error"] = str(e)
            return False
    
    def run_integration_tests(self):
        """Run integration test suite."""
        print("🔗 Running Integration Tests...")
        integration_dir = self.scripts_dir / "integration-tests"
        
        if not integration_dir.exists():
            print("❌ Integration tests directory not found")
            self.results["integration"]["status"] = "skipped"
            self.results["integration"]["error"] = "Directory not found"
            return False
        
        try:
            # Run integration tests
            print("🚀 Executing integration tests...")
            result = subprocess.run(
                ["python", "-m", "pytest", "-v"],
                cwd=integration_dir,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                print("✅ Integration tests passed")
                self.results["integration"]["status"] = "passed"
                self.results["integration"]["output"] = result.stdout
                return True
            else:
                print("❌ Integration tests failed")
                self.results["integration"]["status"] = "failed"
                self.results["integration"]["error"] = result.stderr
                return False
                
        except subprocess.CalledProcessError as e:
            print(f"❌ Integration test execution failed: {e}")
            self.results["integration"]["status"] = "error"
            self.results["integration"]["error"] = str(e)
            return False
        except Exception as e:
            print(f"❌ Unexpected error in integration tests: {e}")
            self.results["integration"]["status"] = "error"
            self.results["integration"]["error"] = str(e)
            return False
    
    def generate_summary(self):
        """Generate test execution summary."""
        total_tests = 3
        passed_tests = sum(1 for suite in ["frontend", "backend", "integration"] 
                          if self.results[suite].get("status") == "passed")
        failed_tests = sum(1 for suite in ["frontend", "backend", "integration"] 
                          if self.results[suite].get("status") == "failed")
        error_tests = sum(1 for suite in ["frontend", "backend", "integration"] 
                         if self.results[suite].get("status") == "error")
        skipped_tests = sum(1 for suite in ["frontend", "backend", "integration"] 
                           if self.results[suite].get("status") == "skipped")
        
        self.results["summary"] = {
            "total_suites": total_tests,
            "passed": passed_tests,
            "failed": failed_tests,
            "errors": error_tests,
            "skipped": skipped_tests,
            "success_rate": (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        }
        
        print(f"\n📊 Test Summary:")
        print(f"   Total Test Suites: {total_tests}")
        print(f"   ✅ Passed: {passed_tests}")
        print(f"   ❌ Failed: {failed_tests}")
        print(f"   ⚠️  Errors: {error_tests}")
        print(f"   ⏭️  Skipped: {skipped_tests}")
        print(f"   📈 Success Rate: {self.results['summary']['success_rate']:.1f}%")
    
    def save_results(self):
        """Save test results to file."""
        results_file = self.scripts_dir / "test_results.json"
        
        try:
            with open(results_file, 'w') as f:
                json.dump(self.results, f, indent=2)
            print(f"\n💾 Test results saved to: {results_file}")
        except Exception as e:
            print(f"❌ Failed to save test results: {e}")
    
    def run_all_tests(self):
        """Run all test suites."""
        print("🚀 Starting Comprehensive Test Suite Execution")
        print("=" * 60)
        
        start_time = time.time()
        
        # Run test suites
        frontend_success = self.run_frontend_tests()
        print()
        
        backend_success = self.run_backend_tests()
        print()
        
        integration_success = self.run_integration_tests()
        print()
        
        # Generate summary
        self.generate_summary()
        
        # Calculate execution time
        execution_time = time.time() - start_time
        print(f"\n⏱️  Total execution time: {execution_time:.2f} seconds")
        
        # Save results
        self.save_results()
        
        # Return overall success
        return all([frontend_success, backend_success, integration_success])

def main():
    """Main entry point."""
    runner = TestRunner()
    
    try:
        success = runner.run_all_tests()
        
        if success:
            print("\n🎉 All test suites completed successfully!")
            sys.exit(0)
        else:
            print("\n💥 Some test suites failed. Check results for details.")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⏹️  Test execution interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n💥 Unexpected error during test execution: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
