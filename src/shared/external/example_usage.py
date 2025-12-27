"""
Example usage of external service connections and resilience features.
This demonstrates how to integrate all the components together.
"""
import asyncio
import logging
from typing import Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def example_service_integration():
    """
    Example showing how to integrate all external service components.
    """
    print("=== External Service Integration Example ===\n")
    
    # This example shows how the components would be used in a real application
    # Note: This requires the actual dependencies to be installed
    
    try:
        # 1. Import the managers (would normally be done at module level)
        from .opensearch import get_opensearch_client, get_opensearch_health
        from .redis import get_redis_client, get_redis_health
        from .circuit_breaker import circuit_breaker, get_circuit_breaker_metrics
        from .retry import with_retry
        from .monitoring import setup_default_monitoring, get_monitoring_manager
        from .service_discovery import get_service_registry
        
        print("1. Setting up service monitoring...")
        await setup_default_monitoring()
        
        print("2. Getting service clients...")
        opensearch_client = get_opensearch_client()
        redis_client = get_redis_client()
        
        print("3. Testing service health...")
        opensearch_health = await get_opensearch_health()
        redis_health = await get_redis_health()
        
        print(f"   OpenSearch: {opensearch_health['status']}")
        print(f"   Redis: {redis_health['status']}")
        
        print("4. Circuit breaker metrics:")
        cb_metrics = get_circuit_breaker_metrics()
        for name, metrics in cb_metrics.items():
            print(f"   {name}: {metrics['state']} (failures: {metrics['fail_counter']})")
        
        print("5. Service discovery example...")
        service_registry = get_service_registry()
        redis_endpoints = await service_registry.get_healthy_endpoints("redis")
        print(f"   Found {len(redis_endpoints)} Redis endpoints")
        
        print("6. Monitoring summary:")
        monitoring_manager = get_monitoring_manager()
        health_summary = monitoring_manager.get_health_summary()
        print(f"   Overall health: {health_summary['overall_health']}")
        print(f"   Healthy services: {health_summary['healthy_services']}/{health_summary['total_services']}")
        
    except ImportError as e:
        print(f"Skipping integration test due to missing dependencies: {e}")
        print("To run this example, install: pip install opensearch-py redis")


@circuit_breaker("example_service", fail_max=3, reset_timeout=30)
@with_retry(max_retries=2, base_delay=1.0)
async def example_external_api_call(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Example function showing how to use circuit breaker and retry decorators together.
    
    This function simulates an external API call with resilience patterns applied.
    """
    # Simulate external API call
    import random
    
    if random.random() < 0.3:  # 30% chance of failure
        raise Exception("Simulated API failure")
    
    return {"status": "success", "data": data, "processed": True}


async def example_resilient_operations():
    """
    Example showing resilient operations with circuit breaker and retry.
    """
    print("\n=== Resilient Operations Example ===\n")
    
    success_count = 0
    failure_count = 0
    
    # Make multiple calls to demonstrate resilience patterns
    for i in range(10):
        try:
            result = await example_external_api_call({"request_id": i})
            success_count += 1
            print(f"Call {i+1}: ✓ Success")
        except Exception as e:
            failure_count += 1
            print(f"Call {i+1}: ✗ Failed - {e}")
        
        # Small delay between calls
        await asyncio.sleep(0.1)
    
    print(f"\nResults: {success_count} successes, {failure_count} failures")
    
    # Show circuit breaker metrics
    from .circuit_breaker import get_circuit_breaker_metrics
    cb_metrics = get_circuit_breaker_metrics()
    if "example_service" in cb_metrics:
        metrics = cb_metrics["example_service"]
        print(f"Circuit breaker state: {metrics['state']}")
        print(f"Total requests: {metrics['total_requests']}")
        print(f"Failure rate: {metrics['failure_rate']:.2%}")


async def example_graceful_degradation():
    """
    Example showing graceful degradation when services are unavailable.
    """
    print("\n=== Graceful Degradation Example ===\n")
    
    try:
        from .opensearch import _opensearch_manager
        from .redis import _redis_manager
        
        # Simulate service unavailability by getting fallback responses
        opensearch_fallback = await _opensearch_manager.graceful_degradation_fallback()
        redis_fallback = await _redis_manager.graceful_degradation_fallback()
        
        print("OpenSearch fallback response:")
        print(f"  Status: {opensearch_fallback['status']}")
        print(f"  Message: {opensearch_fallback['message']}")
        
        print("Redis fallback response:")
        print(f"  Status: {redis_fallback['status']}")
        print(f"  Message: {redis_fallback['message']}")
        
    except ImportError:
        print("Skipping graceful degradation example due to missing dependencies")


async def main():
    """Run all examples."""
    try:
        await example_service_integration()
        await example_resilient_operations()
        await example_graceful_degradation()
        
        print("\n🎉 All examples completed successfully!")
        
    except Exception as e:
        print(f"❌ Example failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())