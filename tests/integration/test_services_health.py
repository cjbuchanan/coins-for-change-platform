"""Test service health endpoints."""

import pytest


@pytest.mark.integration
def test_auth_service_health(auth_client):
    """Test auth service health endpoint."""
    response = auth_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "auth"


@pytest.mark.integration
def test_campaigns_service_health(campaigns_client):
    """Test campaigns service health endpoint."""
    response = campaigns_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "campaigns"


@pytest.mark.integration
def test_ideas_service_health(ideas_client):
    """Test ideas service health endpoint."""
    response = ideas_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "ideas"


@pytest.mark.integration
def test_coins_service_health(coins_client):
    """Test coins service health endpoint."""
    response = coins_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "coins"


@pytest.mark.integration
def test_search_service_health(search_client):
    """Test search service health endpoint."""
    response = search_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "search"


@pytest.mark.integration
def test_notifications_service_health(notifications_client):
    """Test notifications service health endpoint."""
    response = notifications_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "notifications"


@pytest.mark.integration
def test_analytics_service_health(analytics_client):
    """Test analytics service health endpoint."""
    response = analytics_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "analytics"