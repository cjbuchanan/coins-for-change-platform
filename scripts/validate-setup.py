#!/usr/bin/env python3
"""Validate the project setup without external dependencies."""

import os
import sys
from pathlib import Path


def check_file_exists(file_path: str, description: str) -> bool:
    """Check if a file exists."""
    if Path(file_path).exists():
        print(f"✅ {description}: {file_path}")
        return True
    else:
        print(f"❌ {description}: {file_path} (missing)")
        return False


def check_directory_exists(dir_path: str, description: str) -> bool:
    """Check if a directory exists."""
    if Path(dir_path).is_dir():
        print(f"✅ {description}: {dir_path}")
        return True
    else:
        print(f"❌ {description}: {dir_path} (missing)")
        return False


def validate_project_structure():
    """Validate the project structure."""
    print("🔍 Validating project structure...")
    
    checks = []
    
    # Core configuration files
    checks.append(check_file_exists("pyproject.toml", "Poetry configuration"))
    checks.append(check_file_exists(".env.example", "Environment template"))
    checks.append(check_file_exists("docker-compose.yml", "Docker Compose configuration"))
    checks.append(check_file_exists("Dockerfile", "Docker configuration"))
    checks.append(check_file_exists("Makefile", "Make configuration"))
    checks.append(check_file_exists("README.md", "README documentation"))
    checks.append(check_file_exists(".gitignore", "Git ignore file"))
    checks.append(check_file_exists(".pre-commit-config.yaml", "Pre-commit configuration"))
    
    # Source code structure
    checks.append(check_directory_exists("src", "Source code directory"))
    checks.append(check_directory_exists("src/shared", "Shared utilities"))
    checks.append(check_directory_exists("src/services", "Services directory"))
    
    # Individual services
    services = ["auth", "campaigns", "ideas", "coins", "search", "notifications", "analytics"]
    for service in services:
        checks.append(check_directory_exists(f"src/services/{service}", f"{service.title()} service"))
        checks.append(check_file_exists(f"src/services/{service}/main.py", f"{service.title()} service main"))
    
    # Shared modules
    shared_modules = ["database", "auth", "logging", "validation"]
    for module in shared_modules:
        checks.append(check_directory_exists(f"src/shared/{module}", f"Shared {module} module"))
    
    # Test structure
    checks.append(check_directory_exists("tests", "Tests directory"))
    checks.append(check_directory_exists("tests/unit", "Unit tests"))
    checks.append(check_directory_exists("tests/integration", "Integration tests"))
    checks.append(check_directory_exists("tests/e2e", "End-to-end tests"))
    checks.append(check_file_exists("tests/conftest.py", "Test configuration"))
    
    # Scripts
    checks.append(check_directory_exists("scripts", "Scripts directory"))
    checks.append(check_file_exists("scripts/dev-setup.sh", "Development setup script"))
    checks.append(check_file_exists("scripts/run-services.sh", "Service runner script"))
    
    # Configuration
    checks.append(check_directory_exists("config", "Configuration directory"))
    checks.append(check_file_exists("config/prometheus.yml", "Prometheus configuration"))
    
    # Summary
    passed = sum(checks)
    total = len(checks)
    
    print(f"\n📊 Validation Summary: {passed}/{total} checks passed")
    
    if passed == total:
        print("🎉 Project structure validation successful!")
        return True
    else:
        print("⚠️  Some files or directories are missing. Please review the setup.")
        return False


def check_python_version():
    """Check Python version."""
    print("🐍 Checking Python version...")
    
    version = sys.version_info
    if version.major == 3 and version.minor >= 11:
        print(f"✅ Python {version.major}.{version.minor}.{version.micro} (compatible)")
        return True
    else:
        print(f"❌ Python {version.major}.{version.minor}.{version.micro} (requires Python 3.11+)")
        return False


def check_import_structure():
    """Check if the import structure is correct."""
    print("📦 Checking import structure...")
    
    # Add current directory to Python path
    current_dir = Path.cwd()
    sys.path.insert(0, str(current_dir))
    
    try:
        # Try to import the main modules (without external dependencies)
        import src
        print("✅ Main src package importable")
        
        import src.shared
        print("✅ Shared package importable")
        
        import src.services
        print("✅ Services package importable")
        
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False


def main():
    """Main validation function."""
    print("🚀 Coins for Change Platform - Setup Validation")
    print("=" * 50)
    
    checks = [
        check_python_version(),
        validate_project_structure(),
        check_import_structure(),
    ]
    
    print("\n" + "=" * 50)
    
    if all(checks):
        print("🎉 All validation checks passed!")
        print("\n📋 Next steps:")
        print("   1. Install dependencies: poetry install")
        print("   2. Start infrastructure: make docker-up")
        print("   3. Run services: make dev")
        print("   4. Run tests: make test")
        return 0
    else:
        print("❌ Some validation checks failed. Please review the issues above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())