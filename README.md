# Personal AI Assistant (ADK + MCP + Agentic Workflow)

This project implements an **agentic personal AI assistant** that acts as:
- your diary + memory,
- hydration/meal reminder coach,
- nutrition and health tracker,
- technical mentor aligned to your long-term goals.

It uses:
- **Google ADK** for the LLM agent,
- an **MCP server** for database tools,
- **PostgreSQL** for persistent memory (works with pgAdmin-managed DBs),
- **APScheduler** for timed reminders.

## Features

- Store and retrieve long-term goals.
- Generate morning to-do items aligned with goals.
- End-of-day reflection and health logging.
- Meal tracking with daily nutrition summaries.
- Timely reminders for water and meals.
- Database access exposed through MCP tools.

## Project structure

```text
personal_ai_assistant/
  __init__.py
  assistant_agent.py      # ADK root agent wired with MCP tools
  mcp_db_server.py        # MCP server exposing PostgreSQL operations
  prompts.py              # behavior and mentoring prompt
  scheduler.py            # scheduled reminders (water/meals)
  cli.py                  # morning/eod prompt templates
requirements.txt
.env.example
```

## Setup

1. Create and activate virtual env:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Configure env:
   ```bash
   cp .env.example .env
   # set GOOGLE_API_KEY and DATABASE_URL
   ```
4. In pgAdmin, create a database named `personal_assistant` (or update `DATABASE_URL` accordingly).

## Run components

### 1) Start DB MCP server (auto-creates required tables)
```bash
python -m personal_ai_assistant.mcp_db_server
```

### 2) Run ADK web UI with the agent
```bash
adk web
```
Then choose app `personal_ai_assistant` in the UI (or CLI picker).
ADK will load `personal_ai_assistant.agent.root_agent` (provided by `personal_ai_assistant/agent.py`).
The root agent lives in `personal_ai_assistant/assistant_agent.py` as `root_agent`.

### 3) Run reminder scheduler (timely alerts)
```bash
python -m personal_ai_assistant.scheduler
```

### 4) Show morning/end-of-day check-in scripts
```bash
python -m personal_ai_assistant.cli
```

## Core MCP tools exposed

- `add_goal`
- `create_todo`
- `complete_todo`
- `list_todos`
- `log_meal`
- `nutrition_summary`
- `log_health`
- `save_reminder`
- `get_active_reminders`

## PostgreSQL + pgAdmin quick notes

- pgAdmin is your GUI; the Python app connects via `DATABASE_URL`.
- Tables are created automatically when `mcp_db_server` starts.
- Recommended local URL format:
  `postgresql://<username>:<password>@localhost:5432/<database_name>`

## Next upgrades

- Add authentication per user profile.
- Add push notifications (Telegram/Slack/WhatsApp/email).
- Add embeddings + semantic memory retrieval.
- Add weekly/monthly progress analytics dashboards.
