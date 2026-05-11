"""
Demo AgentOS
============

Demo AgentOS 主入口文件。

运行方式：
    python -m app.main
"""

from contextlib import asynccontextmanager
from pathlib import Path

# 在任何模块读取环境变量之前，先从项目根目录（或当前工作目录）加载 .env。
# 这样在导入 app.settings 和各个 agent 时，OPENAI_API_KEY、DEEPSEEK_API_KEY、
# DB_* 等变量已经可用。
from dotenv import load_dotenv
import yaml

# 解析仓库根目录（`app/` 的上级目录），避免 IDE 工作目录不正确时无法加载 .env。
_REPO_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(_REPO_ROOT / ".env")
with (_REPO_ROOT / "app" / "config.yaml").open(encoding="utf-8") as _f:
    _APP_CONFIG = yaml.safe_load(_f)

from agno.os import AgentOS
from agno.os.config import AgentOSConfig

# 独立 Agent（每个都位于 agents/<name>/ 目录）。
from agents.approvals import approvals
from agents.compressor import compressor
from agents.contacts import contacts
from agents.craftsman import craftsman
from agents.dash import dash, dash_knowledge, dash_learnings
from agents.docs import docs_agent
from agents.feedback import feedback
from agents.helpdesk import helpdesk
from agents.injector import injector
from agents.mcp import mcp_agent
from agents.reasoner import reasoner
from agents.reporter import reporter
from agents.scheduler import scheduler
from agents.studio import studio
from agents.taskboard import taskboard
from agents.chatrobot import shenshunai

from app.registry import registry
from app.settings import RUNTIME_ENV, SCHEDULER_BASE_URL, SLACK_SIGNING_SECRET, SLACK_TOKEN, agent_db

# 多框架 Agent（LangGraph、DSPy、Claude SDK 封装）。
from frameworks.claude_repo import claude_repo
from frameworks.dspy_math import dspy_math
from frameworks.langgraph_debate import langgraph_debate

from teams.investment import (
    investment_broadcast,
    investment_coordinate,
    investment_knowledge,
    investment_learnings,
    investment_route,
    investment_tasks,
)
from teams.research import research_broadcast, research_coordinate, research_route, research_tasks

from workflows.ai_research import ai_research
from workflows.content_pipeline import content_pipeline
from workflows.morning_brief import morning_brief
from workflows.repo_walkthrough import repo_walkthrough
from workflows.support_triage import support_triage

# ---------------------------------------------------------------------------
# 接口层
# ---------------------------------------------------------------------------
# 可选外部接口（例如 Slack）。未配置 SLACK_* 环境变量时保持为空。
interfaces: list = []
if SLACK_TOKEN and SLACK_SIGNING_SECRET:
    from agno.os.interfaces.slack import Slack

    interfaces.append(
        Slack(
            agent=docs_agent,
            streaming=True,
            token=SLACK_TOKEN,
            signing_secret=SLACK_SIGNING_SECRET,
            resolve_user_identity=True,
        )
    )


# ---------------------------------------------------------------------------
# 生命周期
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app):  # type: ignore[no-untyped-def]
    """FastAPI 生命周期钩子：在启动时注册一次定时任务。"""
    _register_schedules()
    yield


# ---------------------------------------------------------------------------
# 创建 AgentOS
# ---------------------------------------------------------------------------
agent_os = AgentOS(
    name="Demo OS",
    tracing=True,
    scheduler=True,
    # 定时任务触发时用于回调的 HTTP 基础地址（见 SCHEDULER_BASE_URL / AGENTOS_URL）。
    scheduler_base_url=SCHEDULER_BASE_URL,
    # 当 RUNTIME_ENV=prd（生产）时启用 JWT RBAC；本地 dev 模式默认关闭。
    authorization=RUNTIME_ENV == "prd",
    lifespan=lifespan,
    db=agent_db,
    agents=[
        docs_agent,
        mcp_agent,
        helpdesk,
        feedback,
        approvals,
        reasoner,
        reporter,
        contacts,
        studio,
        scheduler,
        taskboard,
        compressor,
        injector,
        craftsman,
        shenshunai,
        claude_repo,  # type: ignore[list-item]
        langgraph_debate,  # type: ignore[list-item]
        dspy_math,  # type: ignore[list-item]
    ],
    teams=[
        dash,
        research_coordinate,
        research_route,
        research_broadcast,
        research_tasks,
        investment_coordinate,
        investment_route,
        investment_broadcast,
        investment_tasks,
    ],
    workflows=[
        morning_brief,
        ai_research,
        content_pipeline,
        repo_walkthrough,
        support_triage,
    ],
    knowledge=[
        dash_knowledge,
        dash_learnings,
        investment_knowledge,
        investment_learnings,
    ],
    interfaces=interfaces,
    # 共享工具集 / 可选模型（当对应 Key 存在时会展示到 AgentOS UI）。
    registry=registry,
    # Web UI 使用的快捷提示配置（按 agent/workflow id）。
    # 显式使用 UTF-8 加载，避免 Windows 区域设置导致解码问题。
    config=AgentOSConfig.model_validate(_APP_CONFIG),
)

# ASGI 应用对象，供 uvicorn 启动（Docker CMD 或 python -m app.main）。
app = agent_os.get_app()


# ---------------------------------------------------------------------------
# 定时任务
# ---------------------------------------------------------------------------
def _register_schedules() -> None:
    """注册全部定时任务（幂等，可在每次启动时安全调用）。"""
    from agno.scheduler import ScheduleManager

    mgr = ScheduleManager(agent_db)
    # 纽约时区工作日 8:00：触发 morning-brief 工作流运行端点。
    mgr.create(
        name="morning-brief",
        cron="0 8 * * 1-5",
        endpoint="/workflows/morning-brief/runs",
        payload={"message": "Generate my morning briefing."},
        timezone="America/New_York",
        description="Weekday morning briefing",
        if_exists="update",
    )
    # UTC 每天 07:00：触发 ai-research 工作流运行端点。
    mgr.create(
        name="ai-research",
        cron="0 7 * * *",
        endpoint="/workflows/ai-research/runs",
        payload={"message": "Run the daily AI research brief."},
        timezone="UTC",
        description="Daily parallel AI research",
        if_exists="update",
    )


if __name__ == "__main__":
    # RUNTIME_ENV=dev 时启用自动重载（见 compose / env）。
    agent_os.serve(
        app="app.main:app",
        reload=RUNTIME_ENV == "dev",
    )
