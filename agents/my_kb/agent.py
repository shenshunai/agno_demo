"""
我的知识库 Agent
================

基于 PgVector 的 RAG：先把资料用 scripts/load_knowledge.py 写入向量库，再对话检索。
"""

from agno.agent import Agent

from agents.my_kb.instructions import INSTRUCTIONS
from agents.my_kb.settings import my_kb
from app.settings import MODEL, agent_db

# ---------------------------------------------------------------------------
# Create Agent
# ---------------------------------------------------------------------------
my_kb_agent = Agent(
    id="my-kb-agent",
    name="我的知识库",
    model=MODEL,
    db=agent_db,
    knowledge=my_kb,
    search_knowledge=True,
    instructions=INSTRUCTIONS,
    enable_agentic_memory=True,
    add_datetime_to_context=True,
    add_history_to_context=True,
    read_chat_history=True,
    num_history_runs=5,
    markdown=True,
)
