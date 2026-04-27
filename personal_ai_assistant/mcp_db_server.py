"""MCP server exposing PostgreSQL-backed memory tools for the personal assistant."""

from __future__ import annotations

import os
from contextlib import contextmanager
from datetime import date, datetime
from typing import Any, Iterator

import psycopg
from mcp.server.fastmcp import FastMCP

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/personal_assistant",
)

mcp = FastMCP("personal-assistant-db")


@contextmanager
def db_cursor() -> Iterator[psycopg.Cursor]:
    with psycopg.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            yield cur
        conn.commit()


def init_db() -> None:
    with db_cursor() as cur:
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS goals (
                id BIGSERIAL PRIMARY KEY,
                goal_text TEXT NOT NULL,
                priority TEXT NOT NULL DEFAULT 'medium',
                target_date DATE,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS todo_items (
                id BIGSERIAL PRIMARY KEY,
                item_text TEXT NOT NULL,
                due_date DATE NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                completed_at TIMESTAMPTZ
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS meals (
                id BIGSERIAL PRIMARY KEY,
                meal_type TEXT NOT NULL,
                description TEXT NOT NULL,
                calories INTEGER,
                eaten_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS health_logs (
                id BIGSERIAL PRIMARY KEY,
                energy_level INTEGER,
                mood TEXT,
                water_glasses INTEGER,
                notes TEXT,
                log_date DATE NOT NULL,
                logged_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS reminders (
                id BIGSERIAL PRIMARY KEY,
                reminder_type TEXT NOT NULL,
                message TEXT NOT NULL,
                reminder_time TIME NOT NULL,
                active BOOLEAN NOT NULL DEFAULT TRUE,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
            """
        )


@mcp.tool()
def add_goal(goal_text: str, priority: str = "medium", target_date: str = "") -> dict[str, Any]:
    """Store a user goal that the mentor assistant should optimize for."""
    parsed_target = target_date or None
    with db_cursor() as cur:
        cur.execute(
            """
            INSERT INTO goals(goal_text, priority, target_date, created_at)
            VALUES (%s, %s, %s, %s)
            RETURNING id
            """,
            (goal_text, priority, parsed_target, datetime.utcnow()),
        )
        goal_id = cur.fetchone()[0]
    return {"goal_id": goal_id, "status": "stored"}


@mcp.tool()
def create_todo(item_text: str, due_date: str = "") -> dict[str, Any]:
    """Create a to-do item for a given date (YYYY-MM-DD)."""
    due = due_date or date.today().isoformat()
    with db_cursor() as cur:
        cur.execute(
            """
            INSERT INTO todo_items(item_text, due_date, created_at)
            VALUES (%s, %s, %s)
            RETURNING id
            """,
            (item_text, due, datetime.utcnow()),
        )
        todo_id = cur.fetchone()[0]
    return {"todo_id": todo_id, "status": "created", "due_date": due}


@mcp.tool()
def complete_todo(todo_id: int) -> dict[str, Any]:
    """Mark a to-do item as completed."""
    with db_cursor() as cur:
        cur.execute(
            "UPDATE todo_items SET status='completed', completed_at=%s WHERE id=%s",
            (datetime.utcnow(), todo_id),
        )
        rows = cur.rowcount
    return {"status": "updated", "rows": rows}


@mcp.tool()
def list_todos(for_date: str = "") -> list[dict[str, Any]]:
    """List to-do items for a date (default today)."""
    target = for_date or date.today().isoformat()
    with db_cursor() as cur:
        cur.execute(
            """
            SELECT id, item_text, due_date::text, status, created_at::text, completed_at::text
            FROM todo_items WHERE due_date=%s ORDER BY id DESC
            """,
            (target,),
        )
        rows = cur.fetchall()
    return [
        {
            "id": r[0],
            "item_text": r[1],
            "due_date": r[2],
            "status": r[3],
            "created_at": r[4],
            "completed_at": r[5],
        }
        for r in rows
    ]


@mcp.tool()
def log_meal(meal_type: str, description: str, calories: int = 0) -> dict[str, Any]:
    """Log a meal eaten by the user."""
    with db_cursor() as cur:
        cur.execute(
            """
            INSERT INTO meals(meal_type, description, calories, eaten_at)
            VALUES (%s, %s, %s, %s)
            RETURNING id
            """,
            (meal_type, description, calories or None, datetime.utcnow()),
        )
        meal_id = cur.fetchone()[0]
    return {"meal_id": meal_id, "status": "logged"}


@mcp.tool()
def log_health(energy_level: int, mood: str, water_glasses: int, notes: str = "") -> dict[str, Any]:
    """Store end-of-day health and wellness check-in."""
    with db_cursor() as cur:
        cur.execute(
            """
            INSERT INTO health_logs(energy_level, mood, water_glasses, notes, log_date, logged_at)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
            """,
            (
                energy_level,
                mood,
                water_glasses,
                notes,
                date.today().isoformat(),
                datetime.utcnow(),
            ),
        )
        health_log_id = cur.fetchone()[0]
    return {"health_log_id": health_log_id, "status": "logged"}


@mcp.tool()
def nutrition_summary(for_date: str = "") -> dict[str, Any]:
    """Return all meals and total calories for a specific date."""
    target = for_date or date.today().isoformat()
    with db_cursor() as cur:
        cur.execute(
            """
            SELECT meal_type, description, COALESCE(calories, 0), eaten_at::text
            FROM meals
            WHERE eaten_at::date=%s
            ORDER BY eaten_at ASC
            """,
            (target,),
        )
        rows = cur.fetchall()

    meals = [
        {
            "meal_type": row[0],
            "description": row[1],
            "calories": row[2],
            "eaten_at": row[3],
        }
        for row in rows
    ]

    return {
        "date": target,
        "total_meals": len(meals),
        "total_calories": sum(row["calories"] for row in meals),
        "meals": meals,
    }


@mcp.tool()
def save_reminder(reminder_type: str, message: str, reminder_time: str) -> dict[str, Any]:
    """Save a recurring reminder in HH:MM 24-hour format."""
    with db_cursor() as cur:
        cur.execute(
            """
            INSERT INTO reminders(reminder_type, message, reminder_time, created_at)
            VALUES (%s, %s, %s, %s)
            RETURNING id
            """,
            (reminder_type, message, reminder_time, datetime.utcnow()),
        )
        reminder_id = cur.fetchone()[0]
    return {"reminder_id": reminder_id, "status": "saved"}


@mcp.tool()
def get_active_reminders() -> list[dict[str, Any]]:
    """Fetch active reminders for scheduler."""
    with db_cursor() as cur:
        cur.execute(
            """
            SELECT id, reminder_type, message, reminder_time::text, active, created_at::text
            FROM reminders WHERE active=TRUE
            ORDER BY reminder_time ASC
            """
        )
        rows = cur.fetchall()
    return [
        {
            "id": r[0],
            "reminder_type": r[1],
            "message": r[2],
            "reminder_time": r[3],
            "active": r[4],
            "created_at": r[5],
        }
        for r in rows
    ]


if __name__ == "__main__":
    init_db()
    mcp.run()
