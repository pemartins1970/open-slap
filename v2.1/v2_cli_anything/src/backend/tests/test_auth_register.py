"""
Tests for the /auth/register endpoint handler and the auth.create_user function.

Covers:
  - Successful registration
  - Duplicate email returns HTTP 400
  - Unexpected internal errors return HTTP 500 with a generic message
    (no internal exception details leaked to the client)
"""

import sys
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi import HTTPException

src_dir = Path(__file__).resolve().parents[2]
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))


# ---------------------------------------------------------------------------
# Unit tests for auth.create_user (no HTTP layer)
# ---------------------------------------------------------------------------


def test_create_user_success(tmp_path):
    """create_user returns user dict with id and email on success."""
    import importlib
    import os

    db_file = str(tmp_path / "auth.db")
    with patch.dict(os.environ, {"SLAP_DB_PATH": db_file}):
        import backend.auth as auth_mod
        importlib.reload(auth_mod)
        user = auth_mod.create_user("success@example.com", "password123")

    assert user["email"] == "success@example.com"
    assert "id" in user


def test_create_user_duplicate_raises_400(tmp_path):
    """create_user raises HTTP 400 for duplicate emails, not 500."""
    import importlib
    import os

    db_file = str(tmp_path / "auth.db")
    with patch.dict(os.environ, {"SLAP_DB_PATH": db_file}):
        import backend.auth as auth_mod
        importlib.reload(auth_mod)
        auth_mod.create_user("dup@example.com", "password123")
        with pytest.raises(HTTPException) as exc_info:
            auth_mod.create_user("dup@example.com", "password123")

    assert exc_info.value.status_code == 400


# ---------------------------------------------------------------------------
# Unit test for the register endpoint handler (no HTTP layer)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_register_unexpected_error_does_not_leak_details():
    """
    When create_user raises an unexpected exception, the register endpoint
    must return HTTP 500 with a generic message — internal details must not
    appear in the response.
    """
    from backend.main_auth import register

    # Simulate a class of unexpected errors that contains sensitive info
    secret_detail = "db path: /home/user/.private/auth.db"

    class _FakeUserRegister:
        email = "error_test@example.com"
        password = "password123"

    with patch(
        "backend.main_auth.create_user",
        side_effect=RuntimeError(secret_detail),
    ):
        with pytest.raises(HTTPException) as exc_info:
            await register(_FakeUserRegister())

    assert exc_info.value.status_code == 500
    detail = exc_info.value.detail

    # Internal exception message must NOT be exposed to the caller
    assert secret_detail not in detail
    assert "RuntimeError" not in detail
