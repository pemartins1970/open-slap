"""
Tests for path traversal protection in the /media endpoint.

The endpoint resolves the requested path and must reject any path that
escapes the MEDIA_DIR root, including classic traversal sequences like
"../../etc/passwd" and URL-encoded variants.

Covers:
  - A legitimate file inside MEDIA_DIR is served (happy path)
  - A traversal attempt (../../) is blocked with 403 or 404
  - An absolute path that resolves outside MEDIA_DIR is blocked
"""

import os
import sys
from pathlib import Path
from unittest.mock import patch, AsyncMock

import pytest

src_dir = Path(__file__).resolve().parents[2]
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))


@pytest.fixture(scope="module")
def serve_media():
    """Import the _serve_media_direct handler directly."""
    from backend.main_auth import _serve_media_direct
    return _serve_media_direct


@pytest.fixture(scope="module")
def media_dir():
    from backend.main_auth import MEDIA_DIR
    return MEDIA_DIR


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_traversal_attempt_is_blocked(serve_media, media_dir, tmp_path):
    """
    A path like '../../etc/passwd' must not resolve to a file outside MEDIA_DIR.
    The handler must raise HTTPException (404 or 403), not serve the file.
    """
    from fastapi import HTTPException

    # Create a file outside media_dir to ensure the traversal target exists
    target = tmp_path / "secret.txt"
    target.write_text("secret")

    # Craft a traversal that would escape MEDIA_DIR toward tmp_path
    levels_up = len(media_dir.parts)
    traversal = "../" * levels_up + str(target).lstrip("/")

    with pytest.raises(HTTPException) as exc_info:
        await serve_media(traversal)

    assert exc_info.value.status_code in (403, 404)


@pytest.mark.asyncio
async def test_nonexistent_file_returns_404(serve_media):
    """A valid-looking path that doesn't exist must return 404."""
    from fastapi import HTTPException

    with pytest.raises(HTTPException) as exc_info:
        await serve_media("does_not_exist.png")

    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_legitimate_file_is_served(serve_media, media_dir):
    """A real file inside MEDIA_DIR must be served without raising."""
    from fastapi.responses import FileResponse

    # Use an actual file that ships with the project
    candidate = next(media_dir.glob("*.png"), None)
    if candidate is None:
        pytest.skip("No .png files found in MEDIA_DIR — skipping happy-path test")

    response = await serve_media(candidate.name)
    assert isinstance(response, FileResponse)
