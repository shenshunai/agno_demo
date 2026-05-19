"""
Meimo（魅魔）— SSA 中文闲聊 Agent
==============================

对话模型 DeepSeek；与全局 ``DEEPSEEK_MODEL_ID`` 环境变量一致。
"""

from os import getenv

from agno.agent import Agent
from agno.models.deepseek import DeepSeek

from .instructions import INSTRUCTIONS
from app.settings import agent_db

# ---------------------------------------------------------------------------
# 创建 Agent
# ---------------------------------------------------------------------------
# 稳定 ``id`` 供 AgentOS 路由；``name`` 为界面展示标签。
meimo = Agent(
    id="meimo",
    name="魅魔",
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