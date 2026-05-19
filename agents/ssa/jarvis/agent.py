"""
贾维斯（Jarvis）— SSA 知识库导向助理（向量库见 ``jarvis_kb``）。
=====================================

可选：入库脚本 ``scripts/load_knowledge.py`` 支持环境变量 ``JARVIS_REMOTE_SOURCE_URL``
与 ``--with-remote-source-url``，追加抓取单个在线文档并入向量库（无法访问时会失败）。

运行时使用 ``jarvis_kb`` 做检索增强（RAG）；上述远程内容由入库脚本注入，不是 Agent 运行期字段。
"""

from agno.agent import Agent
from agno.tools.llms_txt import LLMsTxtTools

from .instructions import INSTRUCTIONS
from .settings import jarvis_kb
from app.settings import MODEL, agent_db

# ---------------------------------------------------------------------------
# 创建 Agent
# ---------------------------------------------------------------------------
# 基于 ``jarvis_kb`` 的 RAG；向量内容由 ``scripts/load_knowledge.py`` 写入（目录文件 + 可选远程单页地址）。
jarvis = Agent(
    # 在 AgentOS / API 中使用的稳定标识
    id="jarvis",
    # 界面展示名称
    name="贾维斯",
    # 对话模型（见 app.settings，可为 OpenAI、DeepSeek 等）
    model=MODEL,
    # 会话、记忆等持久化到 PostgreSQL
    db=agent_db,
    # 绑定向量知识库（贾维斯专用表前缀 jarvis_kb）
    knowledge=jarvis_kb,
    # 允许在回答前检索上述知识库（RAG）
    search_knowledge=True,
    # 按需拉取 llms.txt 文档（白名单域名，避免任意 URL 的 SSRF）
    tools=[LLMsTxtTools(allowed_hosts=["docs.agno.com"])],
    # 系统提示：人设、知识库与边界
    instructions=INSTRUCTIONS,
    # 启用代理侧记忆与学习相关能力
    enable_agentic_memory=True,
    # 把当前日期时间写入上下文，便于回答「今天」等相对时间
    add_datetime_to_context=True,
    # 把历史运行摘要写入上下文
    add_history_to_context=True,
    # 读取近期聊天记录以保持多轮连贯
    read_chat_history=True,
    # 纳入上下文的最近对话轮数
    num_history_runs=5,
    # 回复使用 Markdown 排版
    markdown=True,
)
