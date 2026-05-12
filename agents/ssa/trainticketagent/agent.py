"""
Train ticket agent — 车票与行程助手
===================================

使用全局 MODEL（OpenAI 或 DeepSeek 等，见 app.settings），并挂载计算器与联网搜索工具。
"""

from agno.agent import Agent
from agno.tools.calculator import CalculatorTools
from agno.tools.duckduckgo import DuckDuckGoTools

from .instructions import INSTRUCTIONS
from app.settings import MODEL, agent_db

# ---------------------------------------------------------------------------
# Create Agent
# ---------------------------------------------------------------------------
trainticketagent = Agent(
    id="train-ticket-agent",
    name="车票助手",
    model=MODEL,
    db=agent_db,
    tools=[CalculatorTools(), DuckDuckGoTools()],
    instructions=INSTRUCTIONS,
    enable_agentic_memory=True,
    add_datetime_to_context=True,
    add_history_to_context=True,
    read_chat_history=True,
    num_history_runs=5,
    markdown=True,
)
