"""Simple reminder scheduler for hydration and meal alerts (PostgreSQL-backed)."""

from __future__ import annotations

import os
from datetime import datetime

import psycopg
from apscheduler.schedulers.blocking import BlockingScheduler

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/personal_assistant",
)
TZ = os.getenv("REMINDER_TIMEZONE", "UTC")


def send_alert(message: str) -> None:
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    print(f"[{now}] 🔔 Reminder: {message}")


def load_reminders() -> list[dict]:
    with psycopg.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT reminder_type, message, reminder_time::text
                FROM reminders
                WHERE active=TRUE
                ORDER BY reminder_time ASC
                """
            )
            rows = cur.fetchall()

    return [
        {"reminder_type": row[0], "message": row[1], "reminder_time": row[2]}
        for row in rows
    ]


def run_scheduler() -> None:
    scheduler = BlockingScheduler(timezone=TZ)

    # Default reminders to make onboarding easy.
    default_reminders = [
        ("water", "Drink a glass of water.", "09:30"),
        ("breakfast", "Time for breakfast.", "08:00"),
        ("lunch", "Lunch time. Have a balanced meal.", "13:00"),
        ("dinner", "Dinner time. Keep it light if possible.", "20:00"),
    ]

    reminders = load_reminders() or [
        {"reminder_type": t, "message": m, "reminder_time": tm}
        for t, m, tm in default_reminders
    ]

    for reminder in reminders:
        hhmm = reminder["reminder_time"][:5]
        hour, minute = hhmm.split(":")
        scheduler.add_job(
            send_alert,
            trigger="cron",
            hour=int(hour),
            minute=int(minute),
            args=[reminder["message"]],
            id=f"{reminder['reminder_type']}-{hour}-{minute}",
            replace_existing=True,
        )

    print(f"Loaded {len(reminders)} reminders in timezone={TZ}")
    scheduler.start()


if __name__ == "__main__":
    run_scheduler()
