"""Local setup diagnostics for the personal AI assistant project."""

from __future__ import annotations

import importlib.util
import os
import sys
from dataclasses import dataclass
from typing import Callable


def load_local_env(path: str = ".env") -> None:
    """Load simple KEY=VALUE lines without requiring python-dotenv."""
    if not os.path.exists(path):
        return

    with open(path, encoding="utf-8") as env_file:
        for raw_line in env_file:
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


load_local_env()

@dataclass
class CheckResult:
    name: str
    passed: bool
    detail: str


def has_module(module_name: str) -> bool:
    try:
        return importlib.util.find_spec(module_name) is not None
    except ModuleNotFoundError:
        return False


def check_python_version() -> CheckResult:
    version = sys.version_info
    passed = version >= (3, 10)
    return CheckResult(
        "Python version",
        passed,
        f"Detected {version.major}.{version.minor}.{version.micro}; Python 3.10+ is recommended.",
    )


def check_required_modules() -> CheckResult:
    required = ["google.adk", "mcp", "psycopg", "dotenv", "apscheduler"]
    missing = [name for name in required if not has_module(name)]
    if missing:
        return CheckResult(
            "Required packages",
            False,
            "Missing: " + ", ".join(missing) + ". Run: pip install -r requirements.txt",
        )
    return CheckResult("Required packages", True, "All required packages are importable.")


def check_environment() -> CheckResult:
    missing = [name for name in ["GOOGLE_API_KEY", "DATABASE_URL"] if not os.getenv(name)]
    if missing:
        return CheckResult(
            "Environment variables",
            False,
            "Missing: " + ", ".join(missing) + ". Copy .env.example to .env and fill values.",
        )
    return CheckResult("Environment variables", True, "GOOGLE_API_KEY and DATABASE_URL are set.")


def check_postgres_connection() -> CheckResult:
    if not has_module("psycopg"):
        return CheckResult(
            "PostgreSQL connection",
            False,
            "Cannot test DB because psycopg is not installed.",
        )

    import psycopg

    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        return CheckResult(
            "PostgreSQL connection",
            False,
            "DATABASE_URL is not set.",
        )

    with psycopg.connect(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT 1")
            value = cur.fetchone()[0]

    return CheckResult("PostgreSQL connection", value == 1, "Successfully ran SELECT 1.")


def main() -> int:
    checks: list[Callable[[], CheckResult]] = [
        check_python_version,
        check_required_modules,
        check_environment,
        check_postgres_connection,
    ]

    failed = False
    for check in checks:
        result = check()
        icon = "✅" if result.passed else "❌"
        print(f"{icon} {result.name}: {result.detail}")
        failed = failed or not result.passed

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
