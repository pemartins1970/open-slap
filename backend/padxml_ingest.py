import argparse
import json
import os
import sqlite3
from datetime import datetime

from padxml import (
    load_ndjson,
    validate_padxml_v1,
    compute_record_id,
    normalize_padxml,
)


def ensure_parent_dir(path: str):
    d = os.path.dirname(os.path.abspath(path))
    if d and not os.path.exists(d):
        os.makedirs(d, exist_ok=True)


def open_db(db_path: str) -> sqlite3.Connection:
    ensure_parent_dir(db_path)
    conn = sqlite3.connect(db_path)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS padxml_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            record_id TEXT NOT NULL UNIQUE,
            record_type TEXT NOT NULL,
            provider TEXT NOT NULL,
            source_url TEXT NOT NULL,
            collected_at TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_padxml_by_type ON padxml_records(record_type)"
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_padxml_by_provider ON padxml_records(provider)"
    )
    conn.commit()
    return conn


def ingest_file(input_path: str, db_path: str) -> dict:
    items = []
    if input_path.lower().endswith(".ndjson"):
        items = load_ndjson(input_path)
    else:
        with open(input_path, "r", encoding="utf-8") as f:
            obj = json.load(f)
            if isinstance(obj, list):
                items = obj
            else:
                items = [obj]

    conn = open_db(db_path)
    cur = conn.cursor()

    stats = {"total": 0, "valid": 0, "inserted": 0, "skipped": 0, "failed": 0}

    for it in items:
        stats["total"] += 1
        normalize_padxml(it)
        ok, errs = validate_padxml_v1(it)
        if not ok:
            stats["failed"] += 1
            print(json.dumps({"ok": False, "errors": errs}, ensure_ascii=False))
            continue

        stats["valid"] += 1

        payload_json = json.dumps(it, ensure_ascii=False, separators=(",", ":"))
        record_id = it["record_id"]
        record_type = str(it.get("record_type") or "")
        provider = str((it.get("source") or {}).get("provider") or "")
        source_url = str((it.get("source") or {}).get("url") or "")
        collected_at = str((it.get("source") or {}).get("collected_at") or "")
        if not collected_at:
            collected_at = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

        try:
            cur.execute(
                """
                INSERT OR IGNORE INTO padxml_records
                (record_id, record_type, provider, source_url, collected_at, payload_json)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (record_id, record_type, provider, source_url, collected_at, payload_json),
            )
            if cur.rowcount > 0:
                stats["inserted"] += 1
                print(json.dumps({"ok": True, "record_id": record_id, "action": "inserted"}, ensure_ascii=False))
            else:
                stats["skipped"] += 1
                print(json.dumps({"ok": True, "record_id": record_id, "action": "skipped"}, ensure_ascii=False))
        except Exception as e:
            stats["failed"] += 1
            print(json.dumps({"ok": False, "record_id": record_id, "error": str(e)}, ensure_ascii=False))

    conn.commit()
    conn.close()
    return stats


def main():
    ap = argparse.ArgumentParser(description="PADXML v1 NDJSON/JSON validator and SQLite ingestor")
    ap.add_argument("input", help="Path to .ndjson or .json file with PADXML items")
    ap.add_argument(
        "--db",
        default=os.path.join("src", "backend", "data", "padxml.db"),
        help="Path to SQLite DB (default: src/backend/data/padxml.db)",
    )
    args = ap.parse_args()

    stats = ingest_file(args.input, args.db)
    print(json.dumps({"summary": stats}, ensure_ascii=False))
    if stats["failed"] > 0:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
