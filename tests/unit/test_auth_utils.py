"""Test authentication utilities."""

from datetime import datetime, timedelta

import pytest

from src.shared.auth.utils import (
    create_access_token,
    get_password_hash,
    validate_password_strength,
    verify_password,
    verify_token,
)


def test_password_hashing():
    """Test password hashing and verification."""
    password = "test_password_123"
    hashed = get_password_hash(password)
    
    assert hashed != password
    assert verify_password(password, hashed) is True
    assert verify_password("wrong_password", hashed) is False


def test_password_strength_validation():
    """Test password strength validation."""
    # Valid passwords
    assert validate_password_strength("Password123") is True
    assert validate_password_strength("MySecure1Pass") is True
    
    # Invalid passwords
    assert validate_password_strength("short") is False  # Too short
    assert validate_password_strength("alllowercase123") is False  # No uppercase
    assert validate_password_strength("ALLUPPERCASE123") is False  # No lowercase
    assert validate_password_strength("NoNumbers") is False  # No digits


def test_jwt_token_creation_and_verification():
    """Test JWT token creation and verification."""
    data = {"sub": "test_user", "email": "test@example.com"}
    token = create_access_token(data)
    
    assert token is not None
    assert isinstance(token, str)
    
    # Verify token
    payload = verify_token(token)
    assert payload is not None
    assert payload["sub"] == "test_user"
    assert payload["email"] == "test@example.com"
    assert "exp" in payload


def test_jwt_token_with_custom_expiration():
    """Test JWT token with custom expiration."""
    data = {"sub": "test_user"}
    expires_delta = timedelta(minutes=30)
    token = create_access_token(data, expires_delta)
    
    payload = verify_token(token)
    assert payload is not None
    
    # Check expiration is approximately 30 minutes from now
    exp_timestamp = payload["exp"]
    exp_datetime = datetime.fromtimestamp(exp_timestamp)
    expected_exp = datetime.utcnow() + expires_delta
    
    # Allow 1 minute tolerance
    assert abs((exp_datetime - expected_exp).total_seconds()) < 60


def test_invalid_jwt_token():
    """Test verification of invalid JWT token."""
    invalid_token = "invalid.jwt.token"
    payload = verify_token(invalid_token)
    assert payload is None