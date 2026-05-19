"""
Chatrobot（银月）— 中文闲聊 Agent
=================================

使用 DeepSeek 作为对话模型；与全局 `DEEPSEEK_MODEL_ID` 环境变量对齐。
"""

from os import getenv

from agno.agent import Agent
from agno.models.deepseek import DeepSeek

from .instructions import INSTRUCTIONS
from app.settings import agent_db

# ---------------------------------------------------------------------------
# Create Agent
# ---------------------------------------------------------------------------
# Single chat agent instance: stable `id` for routing / AgentOS registry; `name` is UI label.
yinyue = Agent(
    id="yinyue",
    name="银月",
    # Model id from env (falls back to deepseek-chat) to match deployment config.
    model=DeepSeek(id=getenv("DEEPSEEK_MODEL_ID", "deepseek-chat")),
    db=agent_db,
    instructions=INSTRUCTIONS,
    # Persistent agentic memory across runs (backed by `agent_db`).
    enable_agentic_memory=True,
    # Inject current datetime into each run for time-aware replies.
    add_datetime_to_context=True,
    # Attach recent conversation turns to the model context.
    add_history_to_context=True,
    # Allow the agent to read prior chat history from storage.
    read_chat_history=True,
    # Number of past runs to include when building history context.
    num_history_runs=5,
    markdown=True,
)
