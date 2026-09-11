#!/usr/bin/env python3
"""
Standalone migration script for updating the violation_log table structure.
Adds any missing columns (timestamp, student_id, course_key, reason, detail_json, ip, user_agent)
and backfills timestamps for existing rows.
"""

from datetime import datetime
from app import app, db


def migrate_violation_log():
    print("🔧 Starting migrate_violation_log ...")

    with app.app_context():
        insp = db.inspect(db.engine)
        cols = {c['name'] for c in insp.get_columns("violation_log")}
        add_cols = []

        if "timestamp"   not in cols: add_cols.append("ADD COLUMN timestamp   TIMESTAMP")
        if "student_id"  not in cols: add_cols.append("ADD COLUMN student_id  VARCHAR(64)")
        if "course_key"  not in cols: add_cols.append("ADD COLUMN course_key  VARCHAR(128)")
        if "reason"      not in cols: add_cols.append("ADD COLUMN reason      VARCHAR(128)")
        if "detail_json" not in cols: add_cols.append("ADD COLUMN detail_json TEXT")
        if "ip"          not in cols: add_cols.append("ADD COLUMN ip          VARCHAR(64)")
        if "user_agent"  not in cols: add_cols.append("ADD COLUMN user_agent  TEXT")

        if add_cols:
            conn = db.engine.connect()
            try:
                for stmt in add_cols:
                    print(f"➡ Executing: ALTER TABLE violation_log {stmt}")
                    conn.execute(db.text(f'ALTER TABLE violation_log {stmt}'))
            finally:
                conn.close()
            print("✅ Added missing columns.")
        else:
            print("ℹ️ No columns needed; already up-to-date.")

        # Backfill missing timestamps
        db.session.execute(
            db.text("UPDATE violation_log SET timestamp = :now WHERE timestamp IS NULL"),
            {"now": datetime.utcnow()}
        )
        db.session.commit()

        print("✅ Migration complete.")

        # Show final structure
        print("📋 Final columns:")
        cols = [c['name'] for c in insp.get_columns("violation_log")]
        print(cols)


if __name__ == "__main__":
    migrate_violation_log()