#!/usr/bin/env python3
"""
Simple validation script to check database setup without external dependencies.
"""
import sys
import os
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

def validate_imports():
    """Validate that all database modules can be imported."""
    print("Validating database module imports...")
    
    try:
        # Test basic imports
        from shared.config import get_settings
        print("✓ Config module imported successfully")
        
        from shared.database.base import BaseModel, Base
        print("✓ Database base models imported successfully")
        
        from shared.database.connection import DatabaseManager
        print("✓ Database connection manager imported successfully")
        
        from shared.database.transactions import database_transaction, TransactionError
        print("✓ Database transaction utilities imported successfully")
        
        from shared.database.repository import BaseRepository
        print("✓ Database repository base class imported successfully")
        
        from shared.health import router
        print("✓ Health check router imported successfully")
        
        return True
        
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return False


def validate_configuration():
    """Validate configuration settings."""
    print("\nValidating configuration...")
    
    try:
        from shared.config import get_settings
        settings = get_settings()
        
        # Check required settings exist
        required_attrs = [
            'database_url', 'database_pool_size', 'database_max_overflow',
            'database_pool_timeout', 'debug', 'environment'
        ]
        
        for attr in required_attrs:
            if not hasattr(settings, attr):
                print(f"✗ Missing required setting: {attr}")
                return False
            print(f"✓ Setting '{attr}' is configured")
        
        # Validate database URL format
        if not settings.database_url.startswith(('postgresql://', 'postgresql+asyncpg://')):
            print(f"✗ Invalid database URL format: {settings.database_url}")
            return False
        
        print("✓ Database URL format is valid")
        
        # Validate pool settings
        if settings.database_pool_size <= 0:
            print(f"✗ Invalid pool size: {settings.database_pool_size}")
            return False
        
        print(f"✓ Database pool size is valid: {settings.database_pool_size}")
        
        return True
        
    except Exception as e:
        print(f"✗ Configuration validation error: {e}")
        return False


def validate_alembic_setup():
    """Validate Alembic configuration."""
    print("\nValidating Alembic setup...")
    
    # Check if alembic.ini exists
    alembic_ini = Path("alembic.ini")
    if not alembic_ini.exists():
        print("✗ alembic.ini not found")
        return False
    print("✓ alembic.ini exists")
    
    # Check if alembic directory exists
    alembic_dir = Path("alembic")
    if not alembic_dir.exists():
        print("✗ alembic directory not found")
        return False
    print("✓ alembic directory exists")
    
    # Check if env.py exists
    env_py = alembic_dir / "env.py"
    if not env_py.exists():
        print("✗ alembic/env.py not found")
        return False
    print("✓ alembic/env.py exists")
    
    # Check if versions directory exists
    versions_dir = alembic_dir / "versions"
    if not versions_dir.exists():
        print("✗ alembic/versions directory not found")
        return False
    print("✓ alembic/versions directory exists")
    
    return True


def validate_file_structure():
    """Validate expected file structure."""
    print("\nValidating file structure...")
    
    expected_files = [
        "src/shared/database/__init__.py",
        "src/shared/database/base.py",
        "src/shared/database/connection.py",
        "src/shared/database/transactions.py",
        "src/shared/database/repository.py",
        "src/shared/config.py",
        "src/shared/health.py",
        "scripts/seed_database.py",
        "tests/unit/test_database_connection.py",
        "tests/integration/test_database_integration.py",
    ]
    
    all_exist = True
    for file_path in expected_files:
        path = Path(file_path)
        if path.exists():
            print(f"✓ {file_path}")
        else:
            print(f"✗ {file_path} not found")
            all_exist = False
    
    return all_exist


def main():
    """Run all validation checks."""
    print("=== Database Infrastructure Validation ===\n")
    
    checks = [
        ("File Structure", validate_file_structure),
        ("Module Imports", validate_imports),
        ("Configuration", validate_configuration),
        ("Alembic Setup", validate_alembic_setup),
    ]
    
    all_passed = True
    
    for check_name, check_func in checks:
        try:
            if not check_func():
                all_passed = False
        except Exception as e:
            print(f"✗ {check_name} validation failed with error: {e}")
            all_passed = False
    
    print("\n=== Validation Summary ===")
    if all_passed:
        print("✓ All validation checks passed!")
        print("\nDatabase infrastructure setup is complete and ready for use.")
        print("\nNext steps:")
        print("1. Install dependencies: poetry install")
        print("2. Set up environment variables in .env file")
        print("3. Run database migrations: alembic upgrade head")
        print("4. Start the application: python src/main.py")
        return 0
    else:
        print("✗ Some validation checks failed.")
        print("Please review the errors above and fix any issues.")
        return 1


if __name__ == "__main__":
    sys.exit(main())