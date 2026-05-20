"""
若曦学姐（轻小说风 / 全年龄校园喜剧）
=====================================

使用全局 MODEL（见 app.settings）。
人设与叙事约束见 ``instructions``；不含成人、催眠控制或性剥削题材。
"""

from agno.agent import Agent

from .instructions import INSTRUCTIONS
from app.settings import MODEL, agent_db

# ---------------------------------------------------------------------------
# 创建 Agent
# ---------------------------------------------------------------------------
ruoxi = Agent(
    id="ruoxi",
    name="若曦学姐",
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
