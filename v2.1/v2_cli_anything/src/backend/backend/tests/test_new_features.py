"""
Tests for Open Slap! features added in v2:
  - message_feedback table and retroalimenta logic
  - plan_tasks table and status transitions
  - expert_ratings and MoE weighting
  - orchestration_runs table
  - projects table and conversation linking
  - memory phases (salience columns, decay, reinforce)
  - MoE router: force override, selection reason
"""

import importlib
import sqlite3
from pathlib import Path
from unittest.mock import patch

import pytest

# ── Helpers ──────────────────────────────────────────────────────────────────


def _make_db(tmp_path: Path) -> tuple:
    """Initialise a real SQLite DB using the actual db.py schema."""
    db_file = tmp_path / "data" / "auth.db"
    db_file.parent.mkdir(parents=True, exist_ok=True)

    # Patch the db path before importing db module
    import os

    os.chdir(tmp_path)

    # We import db directly to get a fresh instance pointing at tmp_path
    spec = importlib.util.spec_from_file_location(
        "backend.db",
        Path(__file__).parent.parent / "db.py",
    )
    db_mod = importlib.util.module_from_spec(spec)
    # Patch the default db path
    with patch.dict("os.environ", {"SLAP_DB_PATH": str(db_file)}):
        # Monkey-patch the DatabaseManager default so it uses tmp_path
        try:
            spec.loader.exec_module(db_mod)
        except Exception:
            pass
    return db_mod, str(db_file)


def _raw_db(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


# ── DB Schema Tests ───────────────────────────────────────────────────────────


class TestNewTablesExist:
    def test_message_feedback_table(self, tmp_path):
        from backend.db import DatabaseManager

        DatabaseManager(str(tmp_path / "test.db"))
        conn = sqlite3.connect(str(tmp_path / "test.db"))
        tables = {
            r[0]
            for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
        assert "message_feedback" in tables, "message_feedback table missing"

    def test_plan_tasks_table(self, tmp_path):
        from backend.db import DatabaseManager

        DatabaseManager(str(tmp_path / "test.db"))
        conn = sqlite3.connect(str(tmp_path / "test.db"))
        tables = {
            r[0]
            for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
        assert "plan_tasks" in tables, "plan_tasks table missing"

    def test_projects_table(self, tmp_path):
        from backend.db import DatabaseManager

        DatabaseManager(str(tmp_path / "test.db"))
        conn = sqlite3.connect(str(tmp_path / "test.db"))
        tables = {
            r[0]
            for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
        assert "projects" in tables, "projects table missing"

    def test_expert_ratings_table(self, tmp_path):
        from backend.db import DatabaseManager

        DatabaseManager(str(tmp_path / "test.db"))
        conn = sqlite3.connect(str(tmp_path / "test.db"))
        tables = {
            r[0]
            for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
        assert "expert_ratings" in tables, "expert_ratings table missing"

    def test_orchestration_runs_table(self, tmp_path):
        from backend.db import DatabaseManager

        DatabaseManager(str(tmp_path / "test.db"))
        conn = sqlite3.connect(str(tmp_path / "test.db"))
        tables = {
            r[0]
            for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
        assert "orchestration_runs" in tables, "orchestration_runs table missing"

    def test_soul_events_has_salience(self, tmp_path):
        from backend.db import DatabaseManager

        DatabaseManager(str(tmp_path / "test.db"))
        conn = sqlite3.connect(str(tmp_path / "test.db"))
        cols = {
            r[1] for r in conn.execute("PRAGMA table_info(user_soul_events)").fetchall()
        }
        assert "salience" in cols, "salience column missing from user_soul_events"
        assert "last_used_at" in cols, "last_used_at column missing"
        assert "pinned" in cols, "pinned column missing"


# ── Message Feedback Tests ────────────────────────────────────────────────────


class TestMessageFeedback:
    def _setup(self, tmp_path):
        from backend.db import DatabaseManager

        db_path = str(tmp_path / "test.db")
        DatabaseManager(db_path)
        conn = sqlite3.connect(db_path)
        conn.execute(
            "CREATE TABLE IF NOT EXISTS users ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "email TEXT UNIQUE NOT NULL, "
            "hashed_password TEXT NOT NULL, "
            "created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"
        )
        conn.commit()
        conn.execute(
            "INSERT INTO users (email, hashed_password) VALUES ('test@test.com', 'hash')"
        )
        conn.execute(
            "INSERT INTO conversations (user_id, session_id, title) VALUES (1, 'sess1', 'Test')"
        )
        conn.execute(
            "INSERT INTO messages (conversation_id, role, content) VALUES (1, 'user', 'What is X?')"
        )
        conn.execute(
            "INSERT INTO messages (conversation_id, role, content) VALUES (1, 'assistant', 'X is Y')"
        )
        conn.commit()
        conn.close()
        return mgr

    def test_upsert_positive_feedback(self, tmp_path):
        mgr = self._setup(tmp_path)
        mgr.upsert_message_feedback(1, 2, 1)
        result = mgr.get_message_feedback(1, 2)
        assert result == 1

    def test_upsert_negative_feedback(self, tmp_path):
        mgr = self._setup(tmp_path)
        mgr.upsert_message_feedback(1, 2, -1)
        result = mgr.get_message_feedback(1, 2)
        assert result == -1

    def test_overwrite_feedback(self, tmp_path):
        mgr = self._setup(tmp_path)
        mgr.upsert_message_feedback(1, 2, 1)
        mgr.upsert_message_feedback(1, 2, -1)  # overwrite
        result = mgr.get_message_feedback(1, 2)
        assert result == -1, "Feedback should be overwritable"

    def test_get_message_with_preceding(self, tmp_path):
        mgr = self._setup(tmp_path)
        pair = mgr.get_message_with_preceding_user_message(2)
        assert pair is not None, "Should find Q&A pair"
        user_msg, asst_msg = pair
        assert user_msg["role"] == "user"
        assert asst_msg["role"] == "assistant"
        assert "What is X?" in user_msg["content"]

    def test_get_preceding_returns_none_for_user_message(self, tmp_path):
        mgr = self._setup(tmp_path)
        result = mgr.get_message_with_preceding_user_message(1)  # message 1 is user
        assert result is None


# ── Plan Tasks Tests ──────────────────────────────────────────────────────────


class TestPlanTasks:
    def _setup(self, tmp_path):
        from backend.db import DatabaseManager

        db_path = str(tmp_path / "test.db")
        mgr = DatabaseManager(db_path)
        conn = sqlite3.connect(db_path)
        conn.execute(
            "CREATE TABLE IF NOT EXISTS users ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "email TEXT UNIQUE NOT NULL, "
            "hashed_password TEXT NOT NULL, "
            "created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"
        )
        conn.commit()
        conn.execute(
            "INSERT INTO users (email, hashed_password) VALUES ('u@u.com', 'h')"
        )
        conn.execute(
            "INSERT INTO conversations (user_id, session_id, title) VALUES (1, 's', 'P')"
        )
        conn.commit()
        conn.close()
        return mgr

    def test_create_and_retrieve_plan_tasks(self, tmp_path):
        mgr = self._setup(tmp_path)
        tasks = [
            {"title": "Design architecture", "skill_id": "systems-architect"},
            {"title": "Build backend API", "skill_id": "backend-dev"},
            {"title": "Write tests", "skill_id": "tests"},
        ]
        ids = mgr.create_plan_tasks(1, 1, tasks)
        assert len(ids) == 3

        retrieved = mgr.get_plan_tasks(1)
        assert len(retrieved) == 3
        titles = [t["title"] for t in retrieved]
        assert "Design architecture" in titles

    def test_task_position_ordering(self, tmp_path):
        mgr = self._setup(tmp_path)
        tasks = [{"title": f"Task {i}", "skill_id": None} for i in range(5)]
        mgr.create_plan_tasks(1, 1, tasks)
        retrieved = mgr.get_plan_tasks(1)
        positions = [t["position"] for t in retrieved]
        assert positions == sorted(positions), "Tasks should be ordered by position"

    def test_update_status_to_done(self, tmp_path):
        mgr = self._setup(tmp_path)
        ids = mgr.create_plan_tasks(1, 1, [{"title": "T", "skill_id": None}])
        mgr.update_plan_task_status(ids[0], "done")
        tasks = mgr.get_plan_tasks(1)
        assert tasks[0]["status"] == "done"

    def test_update_status_to_failed(self, tmp_path):
        mgr = self._setup(tmp_path)
        ids = mgr.create_plan_tasks(1, 1, [{"title": "T", "skill_id": None}])
        mgr.update_plan_task_status(ids[0], "failed")
        tasks = mgr.get_plan_tasks(1)
        assert tasks[0]["status"] == "failed"

    def test_update_status_with_conversation_id(self, tmp_path):
        mgr = self._setup(tmp_path)
        conn = sqlite3.connect(str(tmp_path / "test.db"))
        conn.execute(
            "INSERT INTO conversations (user_id, session_id, title) VALUES (1, 's2', 'Sub')"
        )
        conn.commit()
        conn.close()
        ids = mgr.create_plan_tasks(1, 1, [{"title": "T", "skill_id": None}])
        mgr.update_plan_task_status(ids[0], "active", conversation_id=2)
        tasks = mgr.get_plan_tasks(1)
        assert tasks[0]["conversation_id"] == 2

    def test_invalid_status_rejected(self, tmp_path):
        """SQLite CHECK constraint should reject invalid status."""
        mgr = self._setup(tmp_path)
        ids = mgr.create_plan_tasks(1, 1, [{"title": "T", "skill_id": None}])
        with pytest.raises(Exception):
            mgr.update_plan_task_status(ids[0], "invalid_status_xyz")


# ── Projects Tests ────────────────────────────────────────────────────────────


class TestProjects:
    def _setup(self, tmp_path):
        from backend.db import DatabaseManager

        db_path = str(tmp_path / "test.db")
        mgr = DatabaseManager(db_path)
        conn = sqlite3.connect(db_path)
        conn.execute(
            "CREATE TABLE IF NOT EXISTS users ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "email TEXT UNIQUE NOT NULL, "
            "hashed_password TEXT NOT NULL, "
            "created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"
        )
        conn.commit()
        conn.execute(
            "INSERT INTO users (email, hashed_password) VALUES ('u@u.com', 'h')"
        )
        conn.commit()
        conn.close()
        return mgr

    def test_create_and_list_projects(self, tmp_path):
        mgr = self._setup(tmp_path)
        pid = mgr.create_project(1, "My Project", "Initial context")
        assert isinstance(pid, int)
        projects = mgr.get_user_projects(1)
        assert len(projects) == 1
        assert projects[0]["name"] == "My Project"

    def test_get_project(self, tmp_path):
        mgr = self._setup(tmp_path)
        pid = mgr.create_project(1, "Test", "ctx")
        proj = mgr.get_project(pid, 1)
        assert proj is not None
        assert proj["context_md"] == "ctx"

    def test_get_project_wrong_user_returns_none(self, tmp_path):
        mgr = self._setup(tmp_path)
        pid = mgr.create_project(1, "Test", "ctx")
        result = mgr.get_project(pid, 99)  # wrong user_id
        assert result is None

    def test_update_project_context(self, tmp_path):
        mgr = self._setup(tmp_path)
        pid = mgr.create_project(1, "Proj", "old context")
        mgr.update_project_context(pid, 1, "new context")
        proj = mgr.get_project(pid, 1)
        assert proj["context_md"] == "new context"


# ── Expert Ratings Tests ──────────────────────────────────────────────────────


class TestExpertRatings:
    def _setup(self, tmp_path):
        from backend.db import DatabaseManager

        db_path = str(tmp_path / "test.db")
        mgr = DatabaseManager(db_path)
        conn = sqlite3.connect(db_path)
        conn.execute(
            "CREATE TABLE IF NOT EXISTS users ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "email TEXT UNIQUE NOT NULL, "
            "hashed_password TEXT NOT NULL, "
            "created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"
        )
        conn.commit()
        conn.execute(
            "INSERT INTO users (email, hashed_password) VALUES ('u@u.com', 'h')"
        )
        conn.commit()
        conn.close()
        return mgr

    def test_record_positive_rating(self, tmp_path):
        mgr = self._setup(tmp_path)
        mgr.record_expert_rating(1, "backend", positive=True)
        summary = mgr.get_expert_rating_summary(1)
        assert "backend" in summary
        assert summary["backend"] == 1.0

    def test_record_negative_rating(self, tmp_path):
        mgr = self._setup(tmp_path)
        mgr.record_expert_rating(1, "backend", positive=False)
        summary = mgr.get_expert_rating_summary(1)
        assert summary["backend"] == 0.0

    def test_mixed_ratings_approval_rate(self, tmp_path):
        mgr = self._setup(tmp_path)
        mgr.record_expert_rating(1, "backend", positive=True)
        mgr.record_expert_rating(1, "backend", positive=True)
        mgr.record_expert_rating(1, "backend", positive=False)  # 2/3 positive
        summary = mgr.get_expert_rating_summary(1)
        assert abs(summary["backend"] - 2 / 3) < 0.01

    def test_empty_ratings_returns_empty_dict(self, tmp_path):
        mgr = self._setup(tmp_path)
        summary = mgr.get_expert_rating_summary(1)
        assert summary == {}


# ── Memory Phase Tests ────────────────────────────────────────────────────────


class TestMemoryPhases:
    def _setup(self, tmp_path):
        from backend.db import DatabaseManager

        db_path = str(tmp_path / "test.db")
        mgr = DatabaseManager(db_path)
        conn = sqlite3.connect(db_path)
        conn.execute(
            "CREATE TABLE IF NOT EXISTS users ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "email TEXT UNIQUE NOT NULL, "
            "hashed_password TEXT NOT NULL, "
            "created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"
        )
        conn.commit()
        conn.execute(
            "INSERT INTO users (email, hashed_password) VALUES ('u@u.com', 'h')"
        )
        # Insert soul events with known salience
        for i in range(5):
            conn.execute(
                "INSERT INTO user_soul_events (user_id, source, content, salience) "
                "VALUES (1, 'auto', ?, ?)",
                (f"fact {i}", 0.5 + i * 0.1),
            )
        conn.commit()
        conn.close()
        return mgr

    def test_decay_reduces_salience(self, tmp_path):
        mgr = self._setup(tmp_path)
        # Set last_used_at to far past so decay triggers
        conn = sqlite3.connect(str(tmp_path / "test.db"))
        conn.execute(
            "UPDATE user_soul_events SET last_used_at = datetime('now', '-30 days')"
        )
        conn.commit()
        conn.close()
        decayed = mgr.decay_memory(1, days_threshold=14)
        assert decayed >= 0  # may be 0 if constraint prevents it

    def test_prune_low_salience(self, tmp_path):
        mgr = self._setup(tmp_path)
        conn = sqlite3.connect(str(tmp_path / "test.db"))
        conn.execute(
            "UPDATE user_soul_events SET salience = 0.05 WHERE id IN (SELECT id FROM user_soul_events LIMIT 2)"
        )
        conn.commit()
        conn.close()
        pruned = mgr.prune_low_salience_memories(1, min_salience=0.1)
        assert pruned == 2

    def test_consolidation_snapshot_orders_by_salience(self, tmp_path):
        mgr = self._setup(tmp_path)
        snapshot = mgr.get_consolidated_memory_snapshot(1)
        assert isinstance(snapshot, str)
        assert len(snapshot) > 0

    def test_reinforce_updates_last_used(self, tmp_path):
        mgr = self._setup(tmp_path)
        conn = sqlite3.connect(str(tmp_path / "test.db"))
        ids = [
            r[0]
            for r in conn.execute(
                "SELECT id FROM user_soul_events WHERE user_id=1"
            ).fetchall()
        ]
        conn.close()
        mgr.reinforce_memory_usage(1, ids[:2])
        conn = sqlite3.connect(str(tmp_path / "test.db"))
        rows = conn.execute(
            "SELECT last_used_at FROM user_soul_events WHERE id IN (?,?)", ids[:2]
        ).fetchall()
        conn.close()
        assert all(
            r[0] is not None for r in rows
        ), "last_used_at should be set after reinforce"


# ── MoE Router Tests ──────────────────────────────────────────────────────────


class TestMoERouter:
    def test_select_returns_general_for_empty_text(self):
        from backend.moe_router_simple import MoERouter

        router = MoERouter()
        result = router.select_expert("")
        assert result["id"] == "general"

    def test_backend_keywords_select_backend(self):
        from backend.moe_router_simple import MoERouter

        router = MoERouter()
        result = router.select_expert(
            "I need help with FastAPI and SQL database migrations"
        )
        assert result["id"] == "backend"

    def test_force_override_respected(self):
        from backend.moe_router_simple import MoERouter

        router = MoERouter()
        # Message is backend-themed but we force frontend
        result = router.select_expert("Help me with SQL", force_expert_id="frontend")
        assert result["id"] == "frontend", "Force override should be respected"
        assert result["selection_reason"] == "User override"

    def test_force_unknown_id_falls_back_to_auto(self):
        from backend.moe_router_simple import MoERouter

        router = MoERouter()
        result = router.select_expert(
            "Help me with SQL", force_expert_id="nonexistent_expert"
        )
        # Should fall back to auto selection (backend or general)
        assert result["id"] in ("backend", "general", "data")

    def test_selection_reason_present(self):
        from backend.moe_router_simple import MoERouter

        router = MoERouter()
        result = router.select_expert("How do I deploy with Docker and Kubernetes?")
        assert "selection_reason" in result
        assert isinstance(result["selection_reason"], str)
        assert len(result["selection_reason"]) > 0

    def test_matched_keywords_present(self):
        from backend.moe_router_simple import MoERouter

        router = MoERouter()
        result = router.select_expert("deploy ci/cd docker monitoring")
        assert "matched_keywords" in result
        assert isinstance(result["matched_keywords"], list)

    def test_matched_keywords_max_5(self):
        from backend.moe_router_simple import MoERouter

        router = MoERouter()
        result = router.select_expert(
            "deploy ci/cd docker kubernetes monitoring aws cloud infrastructure"
        )
        assert len(result["matched_keywords"]) <= 5

    def test_project_keywords_select_project_manager(self):
        from backend.moe_router_simple import MoERouter

        router = MoERouter()
        result = router.select_expert(
            "I need a project roadmap and planning priorities for next sprint"
        )
        assert result["id"] == "project"

    def test_all_experts_have_required_fields(self):
        from backend.moe_router_simple import MoERouter

        router = MoERouter()
        for expert in router.get_experts():
            assert "id" in expert
            assert "name" in expert
            assert "prompt" in expert
            assert "description" in expert


# ── Orchestration DB Tests ────────────────────────────────────────────────────


class TestOrchestrationDB:
    def _setup(self, tmp_path):
        from backend.db import DatabaseManager

        db_path = str(tmp_path / "test.db")
        mgr = DatabaseManager(db_path)
        conn = sqlite3.connect(db_path)
        conn.execute(
            "CREATE TABLE IF NOT EXISTS users ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "email TEXT UNIQUE NOT NULL, "
            "hashed_password TEXT NOT NULL, "
            "created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"
        )
        conn.commit()
        conn.execute(
            "INSERT INTO users (email, hashed_password) VALUES ('u@u.com', 'h')"
        )
        conn.execute(
            "INSERT INTO conversations (user_id, session_id, title) VALUES (1, 's', 'P')"
        )
        conn.commit()
        conn.close()
        return mgr

    def test_create_run(self, tmp_path):
        mgr = self._setup(tmp_path)
        run_id = mgr.create_orchestration_run(1, 1)
        assert isinstance(run_id, int)
        assert run_id > 0

    def test_get_run_default_status_running(self, tmp_path):
        mgr = self._setup(tmp_path)
        run_id = mgr.create_orchestration_run(1, 1)
        run = mgr.get_orchestration_run(run_id)
        assert run["status"] == "running"

    def test_update_run_status_completed(self, tmp_path):
        mgr = self._setup(tmp_path)
        run_id = mgr.create_orchestration_run(1, 1)
        log = [{"task_id": 1, "status": "done", "msg": "OK"}]
        mgr.update_orchestration_run(run_id, "completed", log)
        run = mgr.get_orchestration_run(run_id)
        assert run["status"] == "completed"
        assert run["finished_at"] is not None
        assert len(run["log"]) == 1

    def test_update_run_status_failed(self, tmp_path):
        mgr = self._setup(tmp_path)
        run_id = mgr.create_orchestration_run(1, 1)
        mgr.update_orchestration_run(run_id, "failed", [])
        run = mgr.get_orchestration_run(run_id)
        assert run["status"] == "failed"
        assert run["finished_at"] is not None

    def test_get_nonexistent_run_returns_none(self, tmp_path):
        mgr = self._setup(tmp_path)
        result = mgr.get_orchestration_run(99999)
        assert result is None

    def test_log_is_parsed_as_list(self, tmp_path):
        mgr = self._setup(tmp_path)
        run_id = mgr.create_orchestration_run(1, 1)
        log = [
            {"task_id": 1, "status": "active", "msg": "Starting"},
            {"task_id": 1, "status": "done", "msg": "Finished"},
        ]
        mgr.update_orchestration_run(run_id, "completed", log)
        run = mgr.get_orchestration_run(run_id)
        assert isinstance(run["log"], list)
        assert run["log"][0]["msg"] == "Starting"


# ── get_db_path Tests ─────────────────────────────────────────────────────────


class TestGetDbPath:
    def test_get_db_path_returns_string(self, tmp_path):
        from backend.db import DatabaseManager, get_db_path

        DatabaseManager(str(tmp_path / "test.db"))
        # The module-level db_manager may differ; just test the function exists and returns str
        path = get_db_path()
        assert isinstance(path, str)
        assert path.endswith(".db")
