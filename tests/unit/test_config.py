"""Test configuration management."""

import os
import pytest

from src.shared.config import get_settings, DevelopmentSettings, ProductionSettings, TestingSettings


def test_get_settings_development():
    """Test getting development settings."""
    os.environ["ENVIRONMENT"] = "development"
    settings = get_settings()
    assert isinstance(settings, DevelopmentSettings)
    assert settings.debug is True
    assert settings.log_level == "DEBUG"


def test_get_settings_production():
    """Test getting production settings."""
    os.environ["ENVIRONMENT"] = "production"
    settings = get_settings()
    assert isinstance(settings, ProductionSettings)
    assert settings.debug is False
    assert settings.log_level == "INFO"


def test_get_settings_testing():
    """Test getting testing settings."""
    os.environ["ENVIRONMENT"] = "testing"
    settings = get_settings()
    assert isinstance(settings, TestingSettings)
    assert settings.debug is True
    assert settings.log_level == "DEBUG"
    assert "test" in settings.database_url


def test_cors_origins_parsing():
    """Test CORS origins parsing from string."""
    os.environ["CORS_ORIGINS"] = "http://localhost:3000,http://localhost:8080"
    settings = get_settings()
    assert len(settings.cors_origins) == 2
    assert "http://localhost:3000" in settings.cors_origins
    assert "http://localhost:8080" in settings.cors_origins


def test_log_level_validation():
    """Test log level validation."""
    with pytest.raises(ValueError):
        settings = get_settings()
        settings.log_level = "INVALID"
        settings.__post_init__()