"""
Chatrobot（申顺爱）— 中文闲聊 Agent
=================================

使用 DeepSeek 作为对话模型；与全局 `DEEPSEEK_MODEL_ID` 环境变量对齐。
"""

from os import getenv

from agno.agent import Agent
from agno.models.deepseek import DeepSeek

from agents.chatrobot.instructions import INSTRUCTIONS
from app.settings import agent_db

# ---------------------------------------------------------------------------
# Create Agent
# ---------------------------------------------------------------------------
shenshunai = Agent(
    id="shenshunai",
    name="申顺爱robot",
    model=DeepSeek(id=getenv("DEEPSEEK_MODEL_ID", "deepseek-chat")),
    db=agent_db,
    instructions=INSTRUCTIONS,
    enable_agentic_memory=True,
    add_datetime_to_context=True,
    add_history_to_context=True,
    read_chat_history=True,
    num_history_runs=5,
    markdown=True,
)
