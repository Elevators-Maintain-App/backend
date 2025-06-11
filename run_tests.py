#!/usr/bin/env python3
"""
Test runner script for the maintenance backend application.
Provides convenient ways to run different types of tests.
"""

import sys
import subprocess
from pathlib import Path


def run_command(cmd: list, description: str) -> int:
    """Run a command and return the exit code."""
    print(f"\n🔍 {description}")
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=Path(__file__).parent)
    return result.returncode


def main():
    """Main test runner function."""
    if len(sys.argv) < 2:
        print("Usage: python run_tests.py [command]")
        print("\nAvailable commands:")
        print("  unit        - Run unit tests only")
        print("  integration - Run integration tests only")
        print("  all         - Run all tests")
        print("  coverage    - Run tests with coverage report")
        print("  fast        - Run tests excluding slow tests")
        print("  specific    - Run specific test file (requires file path)")
        return 1

    command = sys.argv[1].lower()
    
    if command == "unit":
        return run_command(
            ["python", "-m", "pytest", "tests/", "-m", "unit"],
            "Running unit tests only"
        )
    
    elif command == "integration":
        return run_command(
            ["python", "-m", "pytest", "tests/", "-m", "integration"],
            "Running integration tests only"
        )
    
    elif command == "all":
        return run_command(
            ["python", "-m", "pytest", "tests/"],
            "Running all tests"
        )
    
    elif command == "coverage":
        return run_command(
            ["python", "-m", "pytest", "tests/", "--cov=app", "--cov-report=html", "--cov-report=term"],
            "Running tests with coverage analysis"
        )
    
    elif command == "fast":
        return run_command(
            ["python", "-m", "pytest", "tests/", "-m", "not slow"],
            "Running fast tests only"
        )
    
    elif command == "specific":
        if len(sys.argv) < 3:
            print("Error: Please provide the test file path")
            print("Example: python run_tests.py specific tests/test_repositories/test_base_repository.py")
            return 1
        
        test_file = sys.argv[2]
        return run_command(
            ["python", "-m", "pytest", test_file, "-v"],
            f"Running specific test file: {test_file}"
        )
    
    else:
        print(f"Unknown command: {command}")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code) 