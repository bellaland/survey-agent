import sqlite3
from pathlib import Path

from src.models.answer_result import AnswerResult
from src.models.answer_plan import AnswerPlan
from src.models.question import Question


class Storage:
    def __init__(self, db_path: str = "logs/survey.db"):
        Path(db_path).parent.mkdir(
            parents=True,
            exist_ok=True,
        )
        self.conn = sqlite3.connect(db_path)
        self._create_tables()

    def _create_tables(self) -> None:
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS runs (
                run_id TEXT PRIMARY KEY,
                survey_url TEXT,
                started_at TEXT
            )
            """
        )
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS answers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id TEXT,
                page_index INTEGER,
                qid TEXT,
                question_type TEXT,
                category TEXT,
                answer TEXT,
                policy TEXT,
                verified INTEGER
            )
            """
        )
        self.conn.commit()

    def save_answer_result(
        self,
        run_id: str,
        page_index: int,
        question: Question,
        plan: AnswerPlan,
        result: AnswerResult,
    ) -> None:
        self.conn.execute(
            """
            INSERT INTO answers (
                run_id,
                page_index,
                qid,
                question_type,
                category,
                answer,
                policy,
                verified
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                page_index,
                question.qid,
                question.type,
                question.category,
                str(result.answer),
                plan.policy,
                int(result.verified),
            ),
        )
        self.conn.commit()
