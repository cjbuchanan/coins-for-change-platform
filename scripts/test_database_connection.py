#!/usr/bin/env python3
"""
Test database connection in Kubernetes environment.
"""
import asyncio
import sys
import os
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

async def test_database_connection():
    """Test database connection and health checks."""
    print("🔍 Testing database connection...")
    
    try:
        from shared.database.connection import DatabaseManager
        from shared.database import get_database_health
        from sqlalchemy import text
        
        # Create database manager instance
        db_manager = DatabaseManager()
        
        # Test basic connection
        print("📡 Testing basic database connectivity...")
        async with db_manager.get_session() as session:
            result = await session.execute(text("SELECT version()"))
            version = result.scalar()
            print(f"✅ Connected to PostgreSQL: {version}")
        
        # Test health check
        print("🏥 Testing database health check...")
        health_result = await get_database_health()
        print(f"✅ Health check status: {health_result['status']}")
        
        if health_result['status'] == 'healthy':
            print(f"📊 Connection pool info:")
            pool_info = health_result['connection_pool']
            print(f"   - Pool size: {pool_info['size']}")
            print(f"   - Checked in: {pool_info['checked_in']}")
            print(f"   - Checked out: {pool_info['checked_out']}")
            
            print(f"⚡ Query performance:")
            perf_info = health_result['query_performance']
            print(f"   - Simple query: {perf_info['simple_query_ms']}ms")
            print(f"   - Complex query: {perf_info['complex_query_ms']}ms")
        else:
            print(f"❌ Health check failed: {health_result.get('errors', [])}")
            return False
        
        # Test transaction
        print("🔄 Testing transaction management...")
        from shared.database.transactions import database_transaction
        
        async with database_transaction() as session:
            # Create a test table
            await session.execute(text("""
                CREATE TEMPORARY TABLE test_connection (
                    id SERIAL PRIMARY KEY,
                    message TEXT
                )
            """))
            
            # Insert test data
            await session.execute(text("""
                INSERT INTO test_connection (message) VALUES ('Hello from Kubernetes!')
            """))
            
            # Query test data
            result = await session.execute(text("""
                SELECT message FROM test_connection
            """))
            message = result.scalar()
            print(f"✅ Transaction test successful: {message}")
        
        print("🎉 All database tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_configuration():
    """Test configuration loading."""
    print("⚙️ Testing configuration...")
    
    try:
        from shared.config import get_settings
        
        settings = get_settings()
        print(f"✅ Environment: {settings.environment}")
        print(f"✅ Debug mode: {settings.debug}")
        print(f"✅ Database pool size: {settings.database_pool_size}")
        
        # Don't print the full database URL for security
        db_url = settings.database_url
        if db_url.startswith('postgresql'):
            print("✅ Database URL format is valid (PostgreSQL)")
        else:
            print(f"❌ Invalid database URL format: {db_url}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False

async def main():
    """Run all tests."""
    print("🧪 Testing Coins for Change Database Infrastructure in Kubernetes")
    print("=" * 60)
    
    # Test configuration first
    config_ok = await test_configuration()
    if not config_ok:
        print("❌ Configuration tests failed")
        return 1
    
    print()
    
    # Test database connection
    db_ok = await test_database_connection()
    if not db_ok:
        print("❌ Database tests failed")
        return 1
    
    print()
    print("🎉 All tests passed! Database infrastructure is working correctly in Kubernetes.")
    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)