"""
Unit tests for database connection and transaction management.
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock

from src.shared.database.connection import DatabaseManager, get_database_health
from src.shared.database.transactions import database_transaction, TransactionError
from src.shared.config import get_settings


class TestDatabaseManager:
    """Test database manager functionality."""
    
    @pytest.fixture
    def db_manager(self):
        """Create database manager instance for testing."""
        return DatabaseManager()
    
    def test_database_manager_initialization(self, db_manager):
        """Test database manager initializes correctly."""
        assert db_manager._engine is None
        assert db_manager._session_factory is None
        assert db_manager._settings is not None
    
    @patch('src.shared.database.connection.create_async_engine')
    def test_create_engine_configuration(self, mock_create_engine, db_manager):
        """Test engine creation with proper configuration."""
        mock_engine = AsyncMock()
        mock_create_engine.return_value = mock_engine
        
        # Access engine property to trigger creation
        engine = db_manager.engine
        
        # Verify create_async_engine was called with correct parameters
        mock_create_engine.assert_called_once()
        call_args = mock_create_engine.call_args
        
        # Check that important configuration options are present
        assert 'pool_size' in call_args.kwargs
        assert 'max_overflow' in call_args.kwargs
        assert 'pool_timeout' in call_args.kwargs
        assert 'pool_pre_ping' in call_args.kwargs
        assert call_args.kwargs['pool_pre_ping'] is True
    
    def test_invalid_database_url_raises_error(self, db_manager):
        """Test that invalid database URL raises ValueError."""
        with patch.object(db_manager._settings, 'database_url', 'mysql://invalid'):
            with pytest.raises(ValueError, match="Only PostgreSQL databases are supported"):
                db_manager._create_engine()
    
    @pytest.mark.asyncio
    async def test_health_check_success(self, db_manager):
        """Test successful database health check."""
        # Mock the session and query execution
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.fetchone.return_value = [1]
        mock_session.execute.return_value = mock_result
        
        # Mock the pool
        mock_pool = MagicMock()
        mock_pool.size.return_value = 20
        mock_pool.checkedin.return_value = 15
        mock_pool.checkedout.return_value = 5
        mock_pool.overflow.return_value = 0
        mock_pool.invalid.return_value = 0
        
        with patch.object(db_manager, 'get_session') as mock_get_session:
            mock_get_session.return_value.__aenter__.return_value = mock_session
            mock_get_session.return_value.__aexit__.return_value = None
            
            with patch.object(db_manager, 'engine') as mock_engine:
                mock_engine.pool = mock_pool
                
                health_result = await db_manager.health_check()
        
        assert health_result["status"] == "healthy"
        assert "connection_pool" in health_result
        assert "query_performance" in health_result
        assert health_result["connection_pool"]["size"] == 20
    
    @pytest.mark.asyncio
    async def test_health_check_failure(self, db_manager):
        """Test database health check failure."""
        with patch.object(db_manager, 'get_session') as mock_get_session:
            mock_get_session.side_effect = Exception("Connection failed")
            
            health_result = await db_manager.health_check()
        
        assert health_result["status"] == "unhealthy"
        assert len(health_result["errors"]) > 0
        assert "Connection failed" in health_result["errors"][0]
    
    @pytest.mark.asyncio
    async def test_retry_connection_success(self, db_manager):
        """Test successful connection retry."""
        mock_session = AsyncMock()
        
        with patch.object(db_manager, 'get_session') as mock_get_session:
            mock_get_session.return_value.__aenter__.return_value = mock_session
            mock_get_session.return_value.__aexit__.return_value = None
            
            result = await db_manager.retry_connection(max_retries=1)
        
        assert result is True
    
    @pytest.mark.asyncio
    async def test_retry_connection_failure(self, db_manager):
        """Test connection retry failure after max attempts."""
        with patch.object(db_manager, 'get_session') as mock_get_session:
            mock_get_session.side_effect = Exception("Connection failed")
            
            with patch('asyncio.sleep'):  # Speed up test by mocking sleep
                result = await db_manager.retry_connection(max_retries=2, base_delay=0.01)
        
        assert result is False


class TestDatabaseTransactions:
    """Test database transaction management."""
    
    @pytest.mark.asyncio
    async def test_database_transaction_success(self):
        """Test successful database transaction."""
        mock_session = AsyncMock()
        
        with patch('src.shared.database.transactions.get_db_session') as mock_get_session:
            mock_get_session.return_value.__aenter__.return_value = mock_session
            mock_get_session.return_value.__aexit__.return_value = None
            
            async with database_transaction() as session:
                assert session == mock_session
                # Simulate some database operation
                await session.execute("SELECT 1")
    
    @pytest.mark.asyncio
    async def test_database_transaction_rollback(self):
        """Test database transaction rollback on exception."""
        mock_session = AsyncMock()
        
        with patch('src.shared.database.transactions.get_db_session') as mock_get_session:
            mock_get_session.return_value.__aenter__.return_value = mock_session
            mock_get_session.return_value.__aexit__.return_value = None
            
            with pytest.raises(TransactionError):
                async with database_transaction() as session:
                    # Simulate an error that should trigger rollback
                    raise Exception("Database error")
    
    @pytest.mark.asyncio
    async def test_nested_transaction(self):
        """Test nested transaction with savepoint."""
        mock_session = AsyncMock()
        mock_savepoint = AsyncMock()
        mock_session.begin_nested.return_value.__aenter__.return_value = mock_savepoint
        mock_session.begin_nested.return_value.__aexit__.return_value = None
        
        async with database_transaction(session=mock_session) as session:
            assert session == mock_session
            mock_session.begin_nested.assert_called_once()


class TestHealthEndpoints:
    """Test health check endpoints."""
    
    @pytest.mark.asyncio
    async def test_get_database_health_success(self):
        """Test successful database health check."""
        mock_health_result = {
            "status": "healthy",
            "connection_pool": {"size": 20},
            "query_performance": {"simple_query_ms": 5.0}
        }
        
        with patch('src.shared.database.connection._db_manager') as mock_manager:
            mock_manager.health_check.return_value = mock_health_result
            
            result = await get_database_health()
        
        assert result == mock_health_result
        mock_manager.health_check.assert_called_once()


@pytest.mark.asyncio
async def test_database_configuration():
    """Test database configuration from settings."""
    settings = get_settings()
    
    # Verify required database settings exist
    assert hasattr(settings, 'database_url')
    assert hasattr(settings, 'database_pool_size')
    assert hasattr(settings, 'database_max_overflow')
    assert hasattr(settings, 'database_pool_timeout')
    
    # Verify default values are reasonable
    assert settings.database_pool_size > 0
    assert settings.database_max_overflow >= 0
    assert settings.database_pool_timeout > 0