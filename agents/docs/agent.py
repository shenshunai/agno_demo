"""
Docs - Agno Documentation Agent (via LLMs.txt)
===========================

Answers developer questions about the Agno framework by dynamically
fetching documentation pages via the llms.txt protocol. No pre-loading
required -- the agent reads the index and fetches relevant pages on demand.

通过使用 llms.txt 协议动态获取文档页面的方式，为开发人员解答关于 Agno 框架的问题。无需预先加载——代理会读取索引并按需获取相关页面。
"""

from agno.agent import Agent
from agno.tools.llms_txt import LLMsTxtTools

from agents.docs.instructions import INSTRUCTIONS
from app.settings import MODEL, agent_db

# ---------------------------------------------------------------------------
# 创建 Agent
# ---------------------------------------------------------------------------
docs_agent = Agent(
    # API / 界面里用的稳定标识
    id="docs",
    # 在 AgentOS 界面显示的名称
    name="Docs",
    # 全局默认模型（见 app.settings，可为 OpenAI、DeepSeek 等）
    model=MODEL,
    # PostgreSQL：会话与记忆持久化
    db=agent_db,
    # 通过 llms.txt 按需拉取 Agno 官方文档（白名单域名，避免任意站）
    tools=[LLMsTxtTools(allowed_hosts=["docs.agno.com"])],
    # 系统提示：如何用工具、如何回答文档类问题
    instructions=INSTRUCTIONS,
    # 跨轮次记忆与学习能力
    enable_agentic_memory=True,
    # 把当前日期时间写入上下文
    add_datetime_to_context=True,
    # 把历史运行摘要写入上下文
    add_history_to_context=True,
    # 读取近期聊天记录以保持连贯
    read_chat_history=True,
    # 纳入上下文的最近运行轮数
    num_history_runs=5,
    # 回复使用 Markdown 排版
    markdown=True,
)
