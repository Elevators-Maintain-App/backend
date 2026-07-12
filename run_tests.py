#!/usr/bin/env python3
"""
Test runner script for the maintenance backend application.
Provides convenient ways to run different types of tests.
"""

import sys
import subprocess
from pathlib import Path

from app.core.database_safety import UnsafeTestDatabaseError, validate_safe_test_database_from_env


def run_command(cmd: list, description: str) -> int:
    """Run a command and return the exit code."""
    print(f"\n🔍 {description}")
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=Path(__file__).parent)
    return result.returncode


def main():
    """Main test runner function."""
    try:
        validate_safe_test_database_from_env()
    except UnsafeTestDatabaseError as exc:
        print(f"Refusing to run tests outside the isolated test database: {exc}")
        print("Use: docker compose -f docker-compose.test.yml exec -T api-test python run_tests.py <command>")
        return 1

    if len(sys.argv) < 2:
        print("Usage: python run_tests.py [command]")
        print("\nAvailable commands:")
        print("  unit        - Run unit tests only")
        print("  integration - Run integration tests only")
        print("  all         - Run all tests")
        print("  coverage    - Run tests with coverage report")
        print("  fast        - Run tests excluding slow tests")
        print("  specific    - Run specific test file (requires file path)")
        print("  bootstrap-db - Create test schema with create_all and stamp Alembic")
        return 1

    command = sys.argv[1].lower()

    if command == "bootstrap-db":
        for cmd, description in (
            (["python", "scripts/bootstrap_test_database.py"], "Creating isolated test schema"),
            (["alembic", "stamp", "7b8d4f2c1a90"], "Stamping Alembic at current test baseline"),
            (["alembic", "current"], "Showing Alembic current revision"),
        ):
            exit_code = run_command(cmd, description)
            if exit_code != 0:
                return exit_code
        return 0

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
