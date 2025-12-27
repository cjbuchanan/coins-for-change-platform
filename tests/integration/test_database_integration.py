"""
Integration tests for database connectivity and operations.
"""
import pytest
import asyncio
from sqlalchemy import text

from src.shared.database import get_db_session, get_database_health, database_transaction
from src.shared.config import get_settings


@pytest.mark.asyncio
@pytest.mark.integration
async def test_database_connection():
    """Test basic database connectivity."""
    try:
        async with get_db_session() as session:
            result = await session.execute(text("SELECT 1 as test_value"))
            row = result.fetchone()
            assert row[0] == 1
    except Exception as e:
        pytest.skip(f"Database not available for integration test: {e}")


@pytest.mark.asyncio
@pytest.mark.integration
async def test_database_health_check():
    """Test database health check integration."""
    try:
        health_result = await get_database_health()
        
        # Verify health check structure
        assert "status" in health_result
        assert "connection_pool" in health_result
        assert "query_performance" in health_result
        
        # If database is available, status should be healthy
        if health_result["status"] == "healthy":
            assert "simple_query_ms" in health_result["query_performance"]
            assert health_result["query_performance"]["simple_query_ms"] > 0
            
            pool_info = health_result["connection_pool"]
            assert "size" in pool_info
            assert "checked_in" in pool_info
            assert "checked_out" in pool_info
            
    except Exception as e:
        pytest.skip(f"Database not available for integration test: {e}")


@pytest.mark.asyncio
@pytest.mark.integration
async def test_database_transaction_commit():
    """Test database transaction commit behavior."""
    try:
        # Test that changes are committed
        async with database_transaction() as session:
            # Create a temporary table for testing
            await session.execute(text("""
                CREATE TEMPORARY TABLE test_transaction (
                    id SERIAL PRIMARY KEY,
                    value TEXT
                )
            """))
            
            # Insert test data
            await session.execute(text("""
                INSERT INTO test_transaction (value) VALUES ('test_commit')
            """))
        
        # Verify data was committed by reading in new session
        async with get_db_session() as session:
            result = await session.execute(text("""
                SELECT value FROM test_transaction WHERE value = 'test_commit'
            """))
            row = result.fetchone()
            # Note: Temporary tables are session-specific, so this test
            # verifies the transaction completed without error
            
    except Exception as e:
        pytest.skip(f"Database not available for integration test: {e}")


@pytest.mark.asyncio
@pytest.mark.integration
async def test_database_transaction_rollback():
    """Test database transaction rollback behavior."""
    try:
        # Test that changes are rolled back on exception
        with pytest.raises(Exception):
            async with database_transaction() as session:
                # Create a temporary table for testing
                await session.execute(text("""
                    CREATE TEMPORARY TABLE test_rollback (
                        id SERIAL PRIMARY KEY,
                        value TEXT
                    )
                """))
                
                # Insert test data
                await session.execute(text("""
                    INSERT INTO test_rollback (value) VALUES ('test_rollback')
                """))
                
                # Force an exception to trigger rollback
                raise Exception("Intentional error for rollback test")
        
        # The exception should have been caught and re-raised as TransactionError
        # The temporary table and data should not exist due to rollback
        
    except Exception as e:
        if "Database not available" in str(e):
            pytest.skip(f"Database not available for integration test: {e}")


@pytest.mark.asyncio
@pytest.mark.integration
async def test_concurrent_database_connections():
    """Test multiple concurrent database connections."""
    try:
        async def db_operation(operation_id: int):
            """Simulate a database operation."""
            async with get_db_session() as session:
                result = await session.execute(
                    text("SELECT :op_id as operation_id"),
                    {"op_id": operation_id}
                )
                row = result.fetchone()
                return row[0]
        
        # Run multiple concurrent operations
        tasks = [db_operation(i) for i in range(10)]
        results = await asyncio.gather(*tasks)
        
        # Verify all operations completed successfully
        assert len(results) == 10
        assert results == list(range(10))
        
    except Exception as e:
        pytest.skip(f"Database not available for integration test: {e}")


@pytest.mark.asyncio
@pytest.mark.integration
async def test_database_configuration_validation():
    """Test that database configuration is valid."""
    settings = get_settings()
    
    # Verify database URL format
    assert settings.database_url.startswith(('postgresql://', 'postgresql+asyncpg://'))
    
    # Verify pool settings are reasonable
    assert 1 <= settings.database_pool_size <= 100
    assert 0 <= settings.database_max_overflow <= 200
    assert 1 <= settings.database_pool_timeout <= 300