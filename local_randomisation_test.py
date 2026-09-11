"""Local-only randomisation smoke test.

Creates instance/randomisation_test.db, inserts 500 distinct questions, and
stores one 50-question randomized attempt snapshot. This does not import or
modify the Flask application.
"""

import json
import secrets
import sqlite3
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "instance" / "randomisation_test.db"
QUESTION_COUNT = 50
BANK_SIZE = 500


def main():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH) as connection:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.executescript(
            """
            DROP TABLE IF EXISTS assessment_attempt;
            DROP TABLE IF EXISTS question_bank;

            CREATE TABLE question_bank (
                id INTEGER PRIMARY KEY,
                assessment_key TEXT NOT NULL,
                question_json TEXT NOT NULL
            );

            CREATE TABLE assessment_attempt (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                assessment_key TEXT NOT NULL,
                questions_json TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            """
        )

        questions = [
            {
                "id": question_id,
                "type": "mcq",
                "question": f"ASAT General test question {question_id}",
                "options": {
                    "A": f"Option A for question {question_id}",
                    "B": f"Option B for question {question_id}",
                    "C": f"Option C for question {question_id}",
                    "D": f"Option D for question {question_id}",
                },
                "correct": "A",
                "points": 1,
            }
            for question_id in range(1, BANK_SIZE + 1)
        ]

        connection.executemany(
            "INSERT INTO question_bank (id, assessment_key, question_json) VALUES (?, ?, ?)",
            [
                (question["id"], "asat_gen", json.dumps(question))
                for question in questions
            ],
        )

        bank_rows = connection.execute(
            "SELECT question_json FROM question_bank "
            "WHERE assessment_key = ? ORDER BY id",
            ("asat_gen",),
        ).fetchall()
        question_bank = [json.loads(row[0]) for row in bank_rows]

        if QUESTION_COUNT <= 0 or QUESTION_COUNT > len(question_bank):
            raise ValueError(
                f"question_count={QUESTION_COUNT} is invalid for bank size {len(question_bank)}"
            )

        rng = secrets.SystemRandom()
        selected_questions = rng.sample(question_bank, QUESTION_COUNT)
        rng.shuffle(selected_questions)

        connection.execute(
            "INSERT INTO assessment_attempt (assessment_key, questions_json) VALUES (?, ?)",
            ("asat_gen", json.dumps(selected_questions, ensure_ascii=False)),
        )
        connection.commit()

        attempt_id = connection.execute(
            "SELECT last_insert_rowid()"
        ).fetchone()[0]

        stored_questions = json.loads(
            connection.execute(
                "SELECT questions_json FROM assessment_attempt WHERE id = ?",
                (attempt_id,),
            ).fetchone()[0]
        )

        selected_ids = [question["id"] for question in stored_questions]
        assert len(question_bank) == BANK_SIZE
        assert len(stored_questions) == QUESTION_COUNT
        assert len(set(selected_ids)) == QUESTION_COUNT
        assert stored_questions == selected_questions

        print(f"Database: {DB_PATH}")
        print(f"Question bank size: {len(question_bank)}")
        print(f"Attempt ID: {attempt_id}")
        print(f"Selected question count: {len(stored_questions)}")
        print(f"Selected IDs in stored order: {selected_ids}")
        print("Unique selection: PASS")
        print("Snapshot persistence: PASS")


if __name__ == "__main__":
    main()
