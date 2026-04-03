"""
Tests for the CORS middleware configuration in main_auth.py.

Covers:
  - CORSMiddleware is registered on the app
  - allow_methods is an explicit list, not ["*"]
  - allow_headers is an explicit list, not ["*"]
  - The explicit lists include the methods/headers the frontend actually needs
"""

import sys
from pathlib import Path

import pytest
from fastapi.middleware.cors import CORSMiddleware

src_dir = Path(__file__).resolve().parents[2]
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))


@pytest.fixture(scope="module")
def cors_kwargs():
    """Extract the kwargs passed to CORSMiddleware from the app's middleware stack."""
    from backend.main_auth import app

    for middleware in app.user_middleware:
        if middleware.cls is CORSMiddleware:
            return middleware.options
    pytest.fail("CORSMiddleware not found in app.user_middleware")


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_cors_middleware_is_registered(cors_kwargs):
    assert cors_kwargs is not None


def test_allow_methods_is_not_wildcard(cors_kwargs):
    """
    Regression: allow_methods=["*"] combined with allow_credentials=True is
    insecure. The fix enumerates only the methods the app actually needs.
    """
    methods = cors_kwargs.get("allow_methods", [])
    assert methods != ["*"], (
        'allow_methods=["*"] with allow_credentials=True is insecure. '
        "Enumerate the required methods explicitly."
    )


def test_allow_headers_is_not_wildcard(cors_kwargs):
    """
    Regression: allow_headers=["*"] combined with allow_credentials=True is
    insecure. The fix enumerates only the headers the app actually needs.
    """
    headers = cors_kwargs.get("allow_headers", [])
    assert headers != ["*"], (
        'allow_headers=["*"] with allow_credentials=True is insecure. '
        "Enumerate the required headers explicitly."
    )


def test_required_methods_are_allowed(cors_kwargs):
    """The explicit list must still cover the methods the frontend uses."""
    methods = [m.upper() for m in cors_kwargs.get("allow_methods", [])]
    for required in ("GET", "POST", "OPTIONS"):
        assert required in methods, f"Required method {required} is missing from allow_methods"


def test_required_headers_are_allowed(cors_kwargs):
    """The explicit list must still cover Authorization and Content-Type."""
    headers = [h.lower() for h in cors_kwargs.get("allow_headers", [])]
    for required in ("authorization", "content-type"):
        assert required in headers, f"Required header {required} is missing from allow_headers"
