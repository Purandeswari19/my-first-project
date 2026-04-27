"""ADK agent definition that consumes MCP DB tools."""

from __future__ import annotations

import os

from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
from mcp import StdioServerParameters

from personal_ai_assistant.prompts import MENTOR_DIARY_INSTRUCTIONS

load_dotenv()

DB_SERVER_CMD = os.getenv("DB_MCP_COMMAND", "python")
DB_SERVER_ARGS = os.getenv(
    "DB_MCP_ARGS", "-m personal_ai_assistant.mcp_db_server"
).split()

root_agent = Agent(
    name="astra_personal_mentor",
    model="gemini-2.5-flash",
    instruction=MENTOR_DIARY_INSTRUCTIONS,
    tools=[
        McpToolset(
            connection_params=StdioConnectionParams(
                server_params=StdioServerParameters(
                    command=DB_SERVER_CMD,
                    args=DB_SERVER_ARGS,
                )
            )
        )
    ],
)
