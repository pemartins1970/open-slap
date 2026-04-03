"""
Tests for the password-reset flow in auth.AuthManager.

Covers:
  - create_password_reset returns a code for a known email
  - create_password_reset returns None for an unknown email
  - correct code + email lets confirm_password_reset succeed
  - wrong code is rejected
  - code cannot be reused (consumed on first use)
  - reset code has sufficient entropy (not a 6-digit number)
"""

import importlib
import os
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

src_dir = Path(__file__).resolve().parents[2]
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))


@pytest.fixture()
def auth(tmp_path):
    db_file = str(tmp_path / "auth.db")
    with patch.dict(os.environ, {"SLAP_DB_PATH": db_file}):
        import backend.auth as auth_mod
        importlib.reload(auth_mod)
        manager = auth_mod.AuthManager(db_path=db_file)
        manager.create_user("user@example.com", "password123")
        yield manager


# ---------------------------------------------------------------------------
# Basic flow
# ---------------------------------------------------------------------------


def test_create_reset_returns_code_for_known_email(auth):
    code = auth.create_password_reset("user@example.com")
    assert code is not None
    assert len(code) > 0


def test_create_reset_returns_none_for_unknown_email(auth):
    code = auth.create_password_reset("nobody@example.com")
    assert code is None


def test_correct_code_allows_password_change(auth):
    code = auth.create_password_reset("user@example.com")
    consumed = auth.consume_password_reset("user@example.com", code)
    assert consumed is True
    auth.set_password_by_email("user@example.com", "newpassword")
    assert auth.authenticate_user("user@example.com", "newpassword") is not None


def test_wrong_code_is_rejected(auth):
    auth.create_password_reset("user@example.com")
    result = auth.consume_password_reset("user@example.com", "wrongcode")
    assert result is False


def test_code_cannot_be_reused(auth):
    code = auth.create_password_reset("user@example.com")
    auth.consume_password_reset("user@example.com", code)
    # Second use of the same code must fail
    result = auth.consume_password_reset("user@example.com", code)
    assert result is False


# ---------------------------------------------------------------------------
# Entropy regression test
# ---------------------------------------------------------------------------


def test_reset_code_is_not_six_digit_number(auth):
    """
    Regression: the old implementation used a 6-digit numeric code
    (secrets.randbelow(1_000_000)) which has only 1 million possible values.
    The fix replaces it with secrets.token_urlsafe(16) — at least 16 bytes
    of entropy, alphanumeric, and never purely numeric.
    """
    codes = {auth.create_password_reset("user@example.com") for _ in range(10)}
    for code in codes:
        # Must not be a plain 6-digit number
        assert not (code.isdigit() and len(code) == 6), (
            f"Code '{code}' looks like the old low-entropy 6-digit format"
        )
        # Must have meaningful length (token_urlsafe(16) produces ~22 chars)
        assert len(code) >= 16, f"Code '{code}' is too short to have adequate entropy"
