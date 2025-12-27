"""
Service discovery integration for dynamic service endpoints.
"""
import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse

from ..config import get_settings

logger = logging.getLogger(__name__)


class ServiceEndpoint:
    """Represents a service endpoint with health status."""
    
    def __init__(self, host: str, port: int, scheme: str = "http", weight: int = 1):
        self.host = host
        self.port = port
        self.scheme = scheme
        self.weight = weight
        self.healthy = True
        self.last_check = None
        
    @property
    def url(self) -> str:
        """Get the full URL for this endpoint."""
        return f"{self.scheme}://{self.host}:{self.port}"
    
    def __str__(self) -> str:
        return f"{self.url} (weight={self.weight}, healthy={self.healthy})"
    
    def __repr__(self) -> str:
        return f"ServiceEndpoint(host='{self.host}', port={self.port}, scheme='{self.scheme}', weight={self.weight})"


class ServiceDiscovery(ABC):
    """Abstract base class for service discovery implementations."""
    
    @abstractmethod
    async def discover_endpoints(self, service_name: str) -> List[ServiceEndpoint]:
        """Discover endpoints for a given service."""
        pass
    
    @abstractmethod
    async def health_check_endpoint(self, endpoint: ServiceEndpoint) -> bool:
        """Check if an endpoint is healthy."""
        pass


class StaticServiceDiscovery(ServiceDiscovery):
    """
    Static service discovery using configuration.
    Suitable for development and simple deployments.
    """
    
    def __init__(self):
        self._settings = get_settings()
        self._static_endpoints = self._load_static_endpoints()
    
    def _load_static_endpoints(self) -> Dict[str, List[ServiceEndpoint]]:
        """Load static endpoints from configuration."""
        endpoints = {}
        
        # Database endpoints
        db_url = urlparse(self._settings.database_url)
        if db_url.hostname:
            endpoints["database"] = [
                ServiceEndpoint(
                    host=db_url.hostname,
                    port=db_url.port or 5432,
                    scheme=db_url.scheme.split('+')[0]  # Remove +asyncpg
                )
            ]
        
        # Redis endpoints
        redis_url = urlparse(self._settings.redis_url)
        if redis_url.hostname:
            endpoints["redis"] = [
                ServiceEndpoint(
                    host=redis_url.hostname,
                    port=redis_url.port or 6379,
                    scheme=redis_url.scheme
                )
            ]
        
        # OpenSearch endpoints
        opensearch_url = urlparse(self._settings.opensearch_url)
        if opensearch_url.hostname:
            endpoints["opensearch"] = [
                ServiceEndpoint(
                    host=opensearch_url.hostname,
                    port=opensearch_url.port or 9200,
                    scheme=opensearch_url.scheme
                )
            ]
        
        return endpoints
    
    async def discover_endpoints(self, service_name: str) -> List[ServiceEndpoint]:
        """Discover endpoints for a given service from static configuration."""
        return self._static_endpoints.get(service_name, [])
    
    async def health_check_endpoint(self, endpoint: ServiceEndpoint) -> bool:
        """Basic health check for static endpoints."""
        import socket
        
        try:
            # Simple TCP connection test
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)  # 5 second timeout
            result = sock.connect_ex((endpoint.host, endpoint.port))
            sock.close()
            return result == 0
        except Exception as e:
            logger.warning(f"Health check failed for {endpoint}: {e}")
            return False


class KubernetesServiceDiscovery(ServiceDiscovery):
    """
    Kubernetes service discovery using service names and DNS.
    Suitable for Kubernetes deployments.
    """
    
    def __init__(self, namespace: str = "default"):
        self.namespace = namespace
        self._service_cache = {}
        self._cache_ttl = 300  # 5 minutes
    
    async def discover_endpoints(self, service_name: str) -> List[ServiceEndpoint]:
        """
        Discover endpoints using Kubernetes service DNS.
        
        In Kubernetes, services are accessible via DNS:
        - <service-name>.<namespace>.svc.cluster.local
        - <service-name> (within same namespace)
        """
        # For MVP, we'll use simple DNS resolution
        # In production, you might use the Kubernetes API
        
        endpoints = []
        
        # Try service name within namespace
        service_dns = f"{service_name}.{self.namespace}.svc.cluster.local"
        
        try:
            import socket
            
            # Resolve DNS to get IP addresses
            addr_info = socket.getaddrinfo(service_dns, None)
            unique_ips = set(info[4][0] for info in addr_info)
            
            # Default ports for common services
            default_ports = {
                "database": 5432,
                "postgres": 5432,
                "redis": 6379,
                "opensearch": 9200,
                "elasticsearch": 9200
            }
            
            port = default_ports.get(service_name, 80)
            
            for ip in unique_ips:
                endpoints.append(ServiceEndpoint(
                    host=ip,
                    port=port,
                    scheme="http"  # Default to HTTP, override as needed
                ))
                
        except Exception as e:
            logger.warning(f"Failed to discover endpoints for {service_name}: {e}")
            
            # Fallback to simple service name (works within same namespace)
            endpoints.append(ServiceEndpoint(
                host=service_name,
                port=default_ports.get(service_name, 80),
                scheme="http"
            ))
        
        return endpoints
    
    async def health_check_endpoint(self, endpoint: ServiceEndpoint) -> bool:
        """Health check using HTTP request to /health endpoint."""
        import aiohttp
        
        try:
            timeout = aiohttp.ClientTimeout(total=5)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                health_url = f"{endpoint.url}/health"
                async with session.get(health_url) as response:
                    return response.status == 200
        except Exception as e:
            logger.debug(f"Health check failed for {endpoint}: {e}")
            return False


class ServiceRegistry:
    """
    Service registry that manages service discovery and endpoint health.
    """
    
    def __init__(self, discovery: ServiceDiscovery):
        self.discovery = discovery
        self._endpoints_cache: Dict[str, List[ServiceEndpoint]] = {}
        self._health_check_interval = 30  # seconds
        self._health_check_tasks: Dict[str, asyncio.Task] = {}
    
    async def get_healthy_endpoints(self, service_name: str) -> List[ServiceEndpoint]:
        """
        Get healthy endpoints for a service.
        
        Args:
            service_name: Name of the service
            
        Returns:
            List of healthy endpoints
        """
        if service_name not in self._endpoints_cache:
            await self._refresh_endpoints(service_name)
        
        # Start health checking if not already running
        if service_name not in self._health_check_tasks:
            self._health_check_tasks[service_name] = asyncio.create_task(
                self._health_check_loop(service_name)
            )
        
        # Return only healthy endpoints
        return [ep for ep in self._endpoints_cache.get(service_name, []) if ep.healthy]
    
    async def get_best_endpoint(self, service_name: str) -> Optional[ServiceEndpoint]:
        """
        Get the best available endpoint for a service based on health and weight.
        
        Args:
            service_name: Name of the service
            
        Returns:
            Best available endpoint or None if no healthy endpoints
        """
        healthy_endpoints = await self.get_healthy_endpoints(service_name)
        
        if not healthy_endpoints:
            return None
        
        # Simple weighted selection (higher weight = higher probability)
        total_weight = sum(ep.weight for ep in healthy_endpoints)
        if total_weight == 0:
            return healthy_endpoints[0]  # Return first if all weights are 0
        
        # For now, just return the highest weight endpoint
        # In production, you might implement proper weighted round-robin
        return max(healthy_endpoints, key=lambda ep: ep.weight)
    
    async def _refresh_endpoints(self, service_name: str) -> None:
        """Refresh endpoints for a service."""
        try:
            endpoints = await self.discovery.discover_endpoints(service_name)
            self._endpoints_cache[service_name] = endpoints
            logger.info(f"Discovered {len(endpoints)} endpoints for service '{service_name}'")
        except Exception as e:
            logger.error(f"Failed to refresh endpoints for service '{service_name}': {e}")
    
    async def _health_check_loop(self, service_name: str) -> None:
        """Continuous health checking loop for a service."""
        while True:
            try:
                endpoints = self._endpoints_cache.get(service_name, [])
                
                # Check health of all endpoints
                health_tasks = [
                    self.discovery.health_check_endpoint(ep) for ep in endpoints
                ]
                
                if health_tasks:
                    health_results = await asyncio.gather(*health_tasks, return_exceptions=True)
                    
                    for endpoint, is_healthy in zip(endpoints, health_results):
                        if isinstance(is_healthy, Exception):
                            endpoint.healthy = False
                            logger.warning(f"Health check error for {endpoint}: {is_healthy}")
                        else:
                            endpoint.healthy = is_healthy
                            endpoint.last_check = asyncio.get_event_loop().time()
                
                await asyncio.sleep(self._health_check_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in health check loop for '{service_name}': {e}")
                await asyncio.sleep(self._health_check_interval)
    
    async def close(self) -> None:
        """Close the service registry and cleanup resources."""
        # Cancel all health check tasks
        for task in self._health_check_tasks.values():
            task.cancel()
        
        # Wait for tasks to complete
        if self._health_check_tasks:
            await asyncio.gather(*self._health_check_tasks.values(), return_exceptions=True)
        
        self._health_check_tasks.clear()
        self._endpoints_cache.clear()
        logger.info("Service registry closed")


# Global service registry instance
_service_registry: Optional[ServiceRegistry] = None


def get_service_registry() -> ServiceRegistry:
    """Get or create the global service registry."""
    global _service_registry
    
    if _service_registry is None:
        # Choose discovery method based on environment
        settings = get_settings()
        
        if settings.environment == "production":
            # In production, try Kubernetes service discovery
            discovery = KubernetesServiceDiscovery()
        else:
            # In development, use static configuration
            discovery = StaticServiceDiscovery()
        
        _service_registry = ServiceRegistry(discovery)
    
    return _service_registry


async def close_service_registry() -> None:
    """Close the global service registry."""
    global _service_registry
    if _service_registry:
        await _service_registry.close()
        _service_registry = None