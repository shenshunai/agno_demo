"""
潜伏（Qianfu）— SSA 潜伏特工 Agent
=====================================

使用全局 MODEL（见 app.settings）。
"""

from agno.agent import Agent

from .instructions import INSTRUCTIONS
from app.settings import MODEL, agent_db

# ---------------------------------------------------------------------------
# Create Agent
# ---------------------------------------------------------------------------
qianfu = Agent(
    id="qianfu",
    name="潜伏",
    model=MODEL,
    db=agent_db,
    instructions=INSTRUCTIONS,
    enable_agentic_memory=True,
    add_datetime_to_context=True,
    add_history_to_context=True,
    read_chat_history=True,
    num_history_runs=5,
    markdown=True,
)
