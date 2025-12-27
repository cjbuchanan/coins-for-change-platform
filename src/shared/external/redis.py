"""
Redis client connection management with connection pooling and resilience features.
"""
import asyncio
import logging
import time
from typing import Any, Dict, Optional
from urllib.parse import urlparse

import redis.asyncio as aioredis
from redis.exceptions import ConnectionError, RedisError

from ..config import get_settings
from .circuit_breaker import circuit_breaker
from .retry import with_retry

logger = logging.getLogger(__name__)


class RedisManager:
    """
    Redis connection manager with connection pooling and resilience features.
    """
    
    def __init__(self):
        self._client: Optional[aioredis.Redis] = None
        self._pool: Optional[aioredis.ConnectionPool] = None
        self._settings = get_settings()
        
    def _create_connection_pool(self) -> aioredis.ConnectionPool:
        """
        Create Redis connection pool with proper configuration.
        """
        # Parse Redis URL
        parsed_url = urlparse(self._settings.redis_url)
        
        # Connection pool configuration
        pool_config = {
            "host": parsed_url.hostname or "localhost",
            "port": parsed_url.port or 6379,
            "db": int(parsed_url.path.lstrip('/')) if parsed_url.path else 0,
            "max_connections": self._settings.redis_max_connections,
            "socket_timeout": self._settings.redis_socket_timeout,
            "socket_connect_timeout": self._settings.redis_socket_timeout,
            "socket_keepalive": True,
            "socket_keepalive_options": {},
            "health_check_interval": 30,  # Health check every 30 seconds
            "retry_on_timeout": True,
            "decode_responses": True,
            "encoding": "utf-8",
        }
        
        # Authentication if provided in URL
        if parsed_url.password:
            pool_config["password"] = parsed_url.password
        if parsed_url.username:
            pool_config["username"] = parsed_url.username
            
        return aioredis.ConnectionPool(**pool_config)
    
    @property
    def pool(self) -> aioredis.ConnectionPool:
        """Get or create the Redis connection pool."""
        if self._pool is None:
            self._pool = self._create_connection_pool()
        return self._pool
    
    @property
    def client(self) -> aioredis.Redis:
        """Get or create the Redis client."""
        if self._client is None:
            self._client = aioredis.Redis(connection_pool=self.pool)
        return self._client
    
    @circuit_breaker("redis", fail_max=5, reset_timeout=60)
    @with_retry(max_retries=3, base_delay=1.0)
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform Redis health check with circuit breaker and retry logic.
        
        Returns:
            dict: Health check results with status and metrics
        """
        health_status = {
            "status": "healthy",
            "service": "redis",
            "connection_pool": {},
            "performance": {},
            "server_info": {},
            "errors": []
        }
        
        try:
            # Test basic connectivity
            start_time = time.time()
            pong_result = await self.client.ping()
            ping_time = (time.time() - start_time) * 1000
            
            if pong_result != True:
                raise Exception("Ping command returned unexpected result")
            
            health_status["performance"]["ping_time_ms"] = round(ping_time, 2)
            
            # Get server information
            start_time = time.time()
            server_info = await self.client.info()
            info_time = (time.time() - start_time) * 1000
            
            health_status["server_info"] = {
                "redis_version": server_info.get("redis_version", "unknown"),
                "connected_clients": server_info.get("connected_clients", 0),
                "used_memory_human": server_info.get("used_memory_human", "unknown"),
                "uptime_in_seconds": server_info.get("uptime_in_seconds", 0)
            }
            health_status["performance"]["info_query_time_ms"] = round(info_time, 2)
            
            # Connection pool information
            health_status["connection_pool"] = {
                "max_connections": self._settings.redis_max_connections,
                "created_connections": self.pool.created_connections,
                "available_connections": len(self.pool._available_connections),
                "in_use_connections": len(self.pool._in_use_connections)
            }
            
            # Performance thresholds
            if ping_time > 100:  # 100ms threshold
                health_status["errors"].append("Ping response time degraded")
            if info_time > 500:  # 500ms threshold
                health_status["errors"].append("Info query performance degraded")
                
            # Check memory usage (warn if over 80% of max memory)
            max_memory = server_info.get("maxmemory", 0)
            used_memory = server_info.get("used_memory", 0)
            if max_memory > 0 and used_memory / max_memory > 0.8:
                health_status["errors"].append("High memory usage detected")
                
        except ConnectionError as e:
            health_status["status"] = "unhealthy"
            health_status["errors"].append(f"Connection failed: {str(e)}")
            logger.error(f"Redis connection failed: {e}")
        except RedisError as e:
            health_status["status"] = "unhealthy"
            health_status["errors"].append(f"Redis error: {str(e)}")
            logger.error(f"Redis error: {e}")
        except Exception as e:
            health_status["status"] = "unhealthy"
            health_status["errors"].append(f"Unexpected error: {str(e)}")
            logger.error(f"Redis health check failed: {e}")
        
        return health_status
    
    @circuit_breaker("redis", fail_max=5, reset_timeout=60)
    @with_retry(max_retries=3, base_delay=1.0)
    async def test_operations(self) -> bool:
        """
        Test basic Redis operations to verify functionality.
        
        Returns:
            bool: True if operations succeed
        """
        try:
            # Test basic set/get operations
            test_key = "health_check_test"
            test_value = f"test_value_{int(time.time())}"
            
            await self.client.set(test_key, test_value, ex=60)  # Expire in 60 seconds
            retrieved_value = await self.client.get(test_key)
            
            if retrieved_value != test_value:
                raise Exception("Set/Get operation returned unexpected result")
            
            # Clean up test key
            await self.client.delete(test_key)
            return True
            
        except Exception as e:
            logger.warning(f"Redis operation test failed: {e}")
            return False
    
    async def graceful_degradation_fallback(self) -> Dict[str, Any]:
        """
        Provide fallback response when Redis is unavailable.
        
        Returns:
            dict: Fallback response indicating service unavailable
        """
        return {
            "status": "degraded",
            "message": "Redis service temporarily unavailable",
            "fallback_active": True,
            "timestamp": time.time()
        }
    
    async def close(self) -> None:
        """Close Redis client and connection pool."""
        if self._client:
            await self._client.aclose()
            self._client = None
        if self._pool:
            await self._pool.aclose()
            self._pool = None
        logger.info("Redis client and pool closed")


# Global Redis manager instance
_redis_manager = RedisManager()


def get_redis_client() -> aioredis.Redis:
    """Get the async Redis client."""
    return _redis_manager.client


async def get_redis_health() -> Dict[str, Any]:
    """Get Redis health check results."""
    return await _redis_manager.health_check()


async def close_redis() -> None:
    """Close Redis connections (for application shutdown)."""
    await _redis_manager.close()