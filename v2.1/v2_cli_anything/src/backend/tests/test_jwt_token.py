"""
Tests for JWT token creation and verification in auth.AuthManager.

Covers:
  - create_access_token returns a non-empty string
  - verify_token decodes a valid token and returns the correct payload
  - verify_token returns None for a tampered token
  - verify_token returns None for an expired token
  - Token expiry is at most 2 hours from now (regression: was 7 days)
"""

import importlib
import os
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch

import pytest

src_dir = Path(__file__).resolve().parents[2]
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))


@pytest.fixture()
def auth(tmp_path):
    db_file = str(tmp_path / "auth.db")
    with patch.dict(os.environ, {
        "SLAP_DB_PATH": db_file,
        "JWT_SECRET": "test-secret-for-jwt-tests",
    }):
        import backend.auth as auth_mod
        importlib.reload(auth_mod)
        yield auth_mod.AuthManager(db_path=db_file)


# ---------------------------------------------------------------------------
# Basic token behaviour
# ---------------------------------------------------------------------------


def test_create_access_token_returns_string(auth):
    token = auth.create_access_token({"sub": "42"})
    assert isinstance(token, str)
    assert len(token) > 0


def test_verify_token_returns_correct_payload(auth):
    token = auth.create_access_token({"sub": "99"})
    payload = auth.verify_token(token)
    assert payload is not None
    assert payload.get("sub") == "99"


def test_verify_token_rejects_tampered_token(auth):
    token = auth.create_access_token({"sub": "1"})
    tampered = token[:-4] + "xxxx"
    assert auth.verify_token(tampered) is None


def test_verify_token_rejects_expired_token(auth):
    import backend.auth as auth_mod
    expired_delta = timedelta(seconds=-1)
    token = auth.create_access_token({"sub": "1"}, expires_delta=expired_delta)
    assert auth.verify_token(token) is None


# ---------------------------------------------------------------------------
# Expiry regression test
# ---------------------------------------------------------------------------


def test_token_expires_within_two_hours(auth):
    """
    Regression: the old value was 60 * 24 * 7 minutes (7 days).
    A compromised token should be valid for at most 2 hours.
    """
    before = datetime.utcnow()
    token = auth.create_access_token({"sub": "1"})
    payload = auth.verify_token(token)
    assert payload is not None

    exp_timestamp = payload.get("exp")
    assert exp_timestamp is not None

    expiry = datetime.utcfromtimestamp(exp_timestamp)
    max_allowed_expiry = before + timedelta(hours=2, minutes=1)  # 1 min grace

    assert expiry <= max_allowed_expiry, (
        f"Token expires at {expiry}, which is more than 2 hours from now ({before}). "
        f"Expected expiry ≤ {max_allowed_expiry}."
    )
