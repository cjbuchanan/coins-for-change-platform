"""
OpenSearch client connection management with authentication, SSL, and connection pooling.
"""
import asyncio
import logging
import time
from contextlib import asynccontextmanager
from typing import Any, Dict, Optional
from urllib.parse import urlparse

from opensearchpy import AsyncOpenSearch, OpenSearch
from opensearchpy.exceptions import ConnectionError, RequestError

from ..config import get_settings
from .circuit_breaker import circuit_breaker
from .retry import with_retry

logger = logging.getLogger(__name__)


class OpenSearchManager:
    """
    OpenSearch connection manager with SSL, authentication, and resilience features.
    """
    
    def __init__(self):
        self._client: Optional[AsyncOpenSearch] = None
        self._sync_client: Optional[OpenSearch] = None
        self._settings = get_settings()
        
    def _create_client_config(self) -> Dict[str, Any]:
        """
        Create OpenSearch client configuration with SSL and authentication.
        """
        # Parse URL to extract components
        parsed_url = urlparse(self._settings.opensearch_url)
        
        # Base configuration
        config = {
            "hosts": [{"host": parsed_url.hostname, "port": parsed_url.port or 9200}],
            "timeout": self._settings.opensearch_timeout,
            "max_retries": self._settings.opensearch_max_retries,
            "retry_on_timeout": True,
            "http_compress": True,  # Enable gzip compression
        }
        
        # SSL configuration
        if parsed_url.scheme == "https":
            config.update({
                "use_ssl": True,
                "verify_certs": True,
                "ssl_show_warn": False,
            })
            
            # In production, you would configure proper CA certificates
            if self._settings.environment == "development":
                config["verify_certs"] = False
        
        # Authentication configuration
        if self._settings.opensearch_username and self._settings.opensearch_password:
            config["http_auth"] = (
                self._settings.opensearch_username,
                self._settings.opensearch_password
            )
        
        return config
    
    @property
    def client(self) -> AsyncOpenSearch:
        """Get or create the async OpenSearch client."""
        if self._client is None:
            config = self._create_client_config()
            self._client = AsyncOpenSearch(**config)
        return self._client
    
    @property
    def sync_client(self) -> OpenSearch:
        """Get or create the sync OpenSearch client for health checks."""
        if self._sync_client is None:
            config = self._create_client_config()
            self._sync_client = OpenSearch(**config)
        return self._sync_client
    
    @circuit_breaker("opensearch", fail_max=5, reset_timeout=60)
    @with_retry(max_retries=3, base_delay=1.0)
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform OpenSearch health check with circuit breaker and retry logic.
        
        Returns:
            dict: Health check results with status and metrics
        """
        health_status = {
            "status": "healthy",
            "service": "opensearch",
            "cluster_info": {},
            "performance": {},
            "errors": []
        }
        
        try:
            # Test basic connectivity
            start_time = time.time()
            cluster_info = await self.client.info()
            connection_time = (time.time() - start_time) * 1000
            
            health_status["cluster_info"] = {
                "name": cluster_info.get("cluster_name", "unknown"),
                "version": cluster_info.get("version", {}).get("number", "unknown"),
                "status": "connected"
            }
            health_status["performance"]["connection_time_ms"] = round(connection_time, 2)
            
            # Test cluster health
            start_time = time.time()
            cluster_health = await self.client.cluster.health()
            health_time = (time.time() - start_time) * 1000
            
            health_status["cluster_info"]["cluster_status"] = cluster_health.get("status", "unknown")
            health_status["cluster_info"]["number_of_nodes"] = cluster_health.get("number_of_nodes", 0)
            health_status["performance"]["health_query_time_ms"] = round(health_time, 2)
            
            # Performance thresholds
            if connection_time > 1000:  # 1 second threshold
                health_status["errors"].append("Connection time degraded")
            if health_time > 2000:  # 2 second threshold
                health_status["errors"].append("Health query performance degraded")
            
            # Check cluster status
            cluster_status = cluster_health.get("status", "red")
            if cluster_status == "red":
                health_status["status"] = "unhealthy"
                health_status["errors"].append("Cluster status is red")
            elif cluster_status == "yellow":
                health_status["errors"].append("Cluster status is yellow")
                
        except ConnectionError as e:
            health_status["status"] = "unhealthy"
            health_status["errors"].append(f"Connection failed: {str(e)}")
            logger.error(f"OpenSearch connection failed: {e}")
        except RequestError as e:
            health_status["status"] = "unhealthy"
            health_status["errors"].append(f"Request failed: {str(e)}")
            logger.error(f"OpenSearch request failed: {e}")
        except Exception as e:
            health_status["status"] = "unhealthy"
            health_status["errors"].append(f"Unexpected error: {str(e)}")
            logger.error(f"OpenSearch health check failed: {e}")
        
        return health_status
    
    @circuit_breaker("opensearch", fail_max=5, reset_timeout=60)
    @with_retry(max_retries=3, base_delay=1.0)
    async def test_search_operation(self) -> bool:
        """
        Test basic search operation to verify functionality.
        
        Returns:
            bool: True if search operation succeeds
        """
        try:
            # Perform a simple search that should work on any cluster
            await self.client.search(
                index="_all",
                body={"query": {"match_all": {}}, "size": 1}
            )
            return True
        except Exception as e:
            logger.warning(f"OpenSearch search test failed: {e}")
            return False
    
    async def graceful_degradation_fallback(self) -> Dict[str, Any]:
        """
        Provide fallback response when OpenSearch is unavailable.
        
        Returns:
            dict: Fallback response indicating service unavailable
        """
        return {
            "status": "degraded",
            "message": "OpenSearch service temporarily unavailable",
            "fallback_active": True,
            "timestamp": time.time()
        }
    
    async def close(self) -> None:
        """Close OpenSearch clients and cleanup resources."""
        if self._client:
            await self._client.close()
            self._client = None
        if self._sync_client:
            self._sync_client.close()
            self._sync_client = None
        logger.info("OpenSearch clients closed")


# Global OpenSearch manager instance
_opensearch_manager = OpenSearchManager()


def get_opensearch_client() -> AsyncOpenSearch:
    """Get the async OpenSearch client."""
    return _opensearch_manager.client


async def get_opensearch_health() -> Dict[str, Any]:
    """Get OpenSearch health check results."""
    return await _opensearch_manager.health_check()


async def close_opensearch() -> None:
    """Close OpenSearch connections (for application shutdown)."""
    await _opensearch_manager.close()