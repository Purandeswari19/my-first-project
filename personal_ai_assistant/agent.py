"""ADK entrypoint expected by `adk web` loader.

ADK looks for `personal_ai_assistant.agent.root_agent` by default.
This file re-exports the root agent defined in assistant_agent.py.
"""

from personal_ai_assistant.assistant_agent import root_agent

__all__ = ["root_agent"]
