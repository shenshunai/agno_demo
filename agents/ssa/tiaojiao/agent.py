"""
调教系统 — SSA 提示词与行为迭代顾问
=====================================

使用全局 MODEL（见 app.settings），与 trainticketagent / jarvis 等一致。
"""

from agno.agent import Agent

from .instructions import INSTRUCTIONS
from app.settings import MODEL, agent_db

# ---------------------------------------------------------------------------
# 创建 Agent
# ---------------------------------------------------------------------------
ziling = Agent(
    id="ziling",
    name="紫灵",
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
