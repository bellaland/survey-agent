import sqlite3
from pathlib import Path
from playwright.sync_api import Page

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
                started_at TEXT,
                finished_at TEXT,
                status TEXT,
                pages_completed INTEGER
            )
            """
        )

        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS pages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id TEXT,
                page_index INTEGER,
                url TEXT,
                screenshot_path TEXT,
                html_path TEXT
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

    def save_run_start(
        self,
        run_id: str,
        survey_url: str,
        started_at: str,
    ) -> None:
        self.conn.execute(
            """
            INSERT INTO runs (
                run_id,
                survey_url,
                started_at,
                status,
                pages_completed
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (run_id, survey_url, started_at, "running", 0),
        )
        self.conn.commit()

    def save_run_end(
        self,
        run_id: str,
        finished_at: str,
        status: str,
        pages_completed: int,
    ) -> None:
        self.conn.execute(
            """
            UPDATE runs
            SET finished_at = ?,
                status = ?,
                pages_completed = ?
            WHERE run_id = ?
            """,
            (finished_at, status, pages_completed, run_id),
        )
        self.conn.commit()

    def save_page(
        self,
        run_id: str,
        page_index: int,
        url: str,
        screenshot_path: str,
        html_path: str,
    ):
        self.conn.execute(
            """
            INSERT INTO pages (
                run_id,
                page_index,
                url,
                screenshot_path,
                html_path
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                run_id,
                page_index,
                url,
                screenshot_path,
                html_path,
            ),
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

    def save_screenshot(self, run_id: str, page_index: int, page: Page) -> str:
        screenshot_dir = Path("logs/screenshots")
        screenshot_dir.mkdir(parents=True, exist_ok=True)
        path = screenshot_dir / f"{run_id}_page_{page_index}.png"
        page.screenshot(path=str(path), full_page=True)
        return str(path)

    def save_html_snapshot(self, run_id: str, page_index: int, page: Page) -> str:
        html_dir = Path("logs/html")
        html_dir.mkdir(parents=True, exist_ok=True)
        path = html_dir / f"{run_id}_page_{page_index}.html"
        path.write_text(page.content(), encoding="utf-8")
        return str(path)

    def close(self) -> None:
        self.conn.close()
