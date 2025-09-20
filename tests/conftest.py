"""Pytest configuration and shared fixtures."""

import asyncio
import os
from typing import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

# Set test environment
os.environ["ENVIRONMENT"] = "testing"

from src.shared.config import get_settings
from src.shared.database.connection import get_db_session


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def settings():
    """Get test settings."""
    return get_settings()


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Get a database session for testing."""
    async with get_db_session() as session:
        yield session


@pytest.fixture
def auth_client():
    """Get a test client for the auth service."""
    from src.services.auth.main import app
    return TestClient(app)


@pytest.fixture
def campaigns_client():
    """Get a test client for the campaigns service."""
    from src.services.campaigns.main import app
    return TestClient(app)


@pytest.fixture
def ideas_client():
    """Get a test client for the ideas service."""
    from src.services.ideas.main import app
    return TestClient(app)


@pytest.fixture
def coins_client():
    """Get a test client for the coins service."""
    from src.services.coins.main import app
    return TestClient(app)


@pytest.fixture
def search_client():
    """Get a test client for the search service."""
    from src.services.search.main import app
    return TestClient(app)


@pytest.fixture
def notifications_client():
    """Get a test client for the notifications service."""
    from src.services.notifications.main import app
    return TestClient(app)


@pytest.fixture
def analytics_client():
    """Get a test client for the analytics service."""
    from src.services.analytics.main import app
    return TestClient(app)