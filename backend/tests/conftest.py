import sys
from pathlib import Path

src_dir = Path(__file__).resolve().parents[2]
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

import pytest

@pytest.fixture
def tmp_db(tmp_path):
    """Banco SQLite temporário e isolado para testes de banco."""
    db_path = str(tmp_path / "test.db")
    from backend.db import DatabaseManager
    DatabaseManager(db_path)
    return db_path

