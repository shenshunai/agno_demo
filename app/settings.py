"""
全局共享配置
============

这个文件集中管理：
- 数据库连接
- 默认大模型选择
- 运行环境相关变量
"""

from os import getenv

from db import get_postgres_db

# ---------------------------------------------------------------------------
# 数据库
# ---------------------------------------------------------------------------
agent_db = get_postgres_db()

# ---------------------------------------------------------------------------
# 模型选择
# ---------------------------------------------------------------------------
_openai_key = getenv("OPENAI_API_KEY", "").strip()
_deepseek_key = getenv("DEEPSEEK_API_KEY", "").strip()
_use_deepseek = getenv("USE_DEEPSEEK", "").lower() in ("1", "true", "yes")

if _use_deepseek and _deepseek_key:
    from agno.models.deepseek import DeepSeek

    MODEL = DeepSeek(id=getenv("DEEPSEEK_MODEL_ID", "deepseek-chat"))
elif _openai_key:
    from agno.models.openai import OpenAIResponses

    MODEL = OpenAIResponses(id="gpt-5.4")
elif _deepseek_key:
    from agno.models.deepseek import DeepSeek

    MODEL = DeepSeek(id=getenv("DEEPSEEK_MODEL_ID", "deepseek-chat"))
else:
    raise RuntimeError(
        "未检测到可用的 LLM Key。请在 .env 中配置 OPENAI_API_KEY 或 DEEPSEEK_API_KEY。"
        "如果两个都配置了，且希望默认使用 DeepSeek，请增加 USE_DEEPSEEK=1。"
    )


def get_compression_model():
    """返回压缩场景使用的模型。

    - 有 OpenAI Key 时：使用更便宜的 gpt-5.4-mini
    - 没有 OpenAI Key 时：复用当前默认 MODEL（例如 DeepSeek）
    """
    if _openai_key:
        from agno.models.openai import OpenAIResponses

        return OpenAIResponses(id="gpt-5.4-mini")
    return MODEL


# ---------------------------------------------------------------------------
# 运行环境
# ---------------------------------------------------------------------------
# 默认使用 dev：本地/IDE 启动时不走 JWT 鉴权。
# 生产环境请显式设置 RUNTIME_ENV=prd，并配置 JWT_VERIFICATION_KEY。
RUNTIME_ENV = getenv("RUNTIME_ENV", "dev")
SCHEDULER_BASE_URL = getenv("AGENTOS_URL", "http://127.0.0.1:8000")
SLACK_TOKEN = getenv("SLACK_TOKEN", "")
SLACK_SIGNING_SECRET = getenv("SLACK_SIGNING_SECRET", "")

# ---------------------------------------------------------------------------
# 可选工具
# ---------------------------------------------------------------------------
PARALLEL_API_KEY = getenv("PARALLEL_API_KEY", "")


def get_parallel_tools(**kwargs) -> list:
    """按需返回 ParallelTools。

    配置了 PARALLEL_API_KEY 才启用，否则返回空列表。
    """
    if PARALLEL_API_KEY:
        from agno.tools.parallel import ParallelTools

        return [ParallelTools(**kwargs)]
    return []
