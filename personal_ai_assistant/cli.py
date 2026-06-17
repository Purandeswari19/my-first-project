"""CLI helper that orchestrates morning and end-of-day flows."""

from __future__ import annotations

from datetime import date

MORNING_PROMPT = """
Good morning! Let's set your day up for success.
Please share:
1) Your top 1-3 priorities today.
2) Any meetings/constraints.
3) Health intent (water, meals, sleep target).
""".strip()

EOD_PROMPT = """
End-of-day reflection:
1) Which tasks are completed and which are pending?
2) How was your mood and energy today (1-10)?
3) How many glasses of water did you drink?
4) What did you eat today?
5) What should we improve tomorrow?
""".strip()


def show_checkin_prompts() -> None:
    print(f"Date: {date.today().isoformat()}")
    print("\n=== MORNING CHECK-IN ===")
    print(MORNING_PROMPT)
    print("\n=== END OF DAY CHECK-IN ===")
    print(EOD_PROMPT)


if __name__ == "__main__":
    show_checkin_prompts()
