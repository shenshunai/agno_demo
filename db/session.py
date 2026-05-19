"""
数据库会话与知识库构造
=====================

这个文件负责两件事：
1) 创建 Postgres 数据库连接
2) 创建带向量检索能力（PgVector）的 Knowledge 对象
"""

from os import getenv

from agno.db.postgres import PostgresDb
from agno.knowledge import Knowledge
from agno.knowledge.embedder.base import Embedder
from agno.knowledge.embedder.openai import OpenAIEmbedder
from agno.vectordb.pgvector import PgVector, SearchType

from db.url import db_url

DB_ID = "demo-os-db"


def resolve_embedding_provider() -> str:
    """Resolve which embedding backend to use (shared by create_knowledge and load_knowledge)."""
    raw_key = getenv("EMBEDDING_PROVIDER")
    raw = (raw_key or "").strip().lower()
    if raw:
        return raw
    use_ds = getenv("USE_DEEPSEEK", "").strip().lower() in ("1", "true", "yes")
    if use_ds and getenv("DEEPSEEK_API_KEY", "").strip() and not getenv("OPENAI_API_KEY", "").strip():
        return "deepseek"
    return "openai"


def get_postgres_db(knowledge_table: str | None = None) -> PostgresDb:
    """创建 PostgresDb 实例。

    参数：
        knowledge_table: 可选。用于保存知识正文内容的表名。

    返回：
        配置好的 PostgresDb 实例。
    """
    if knowledge_table is not None:
        return PostgresDb(id=DB_ID, db_url=db_url, knowledge_table=knowledge_table)
    return PostgresDb(id=DB_ID, db_url=db_url)


def _build_embedder() -> Embedder:
    """根据环境变量创建向量嵌入器（Embedder）。

    - openai：OpenAIEmbedder（默认）。
    - deepseek：官方无可用 /v1/embeddings，改用 DeepSeek **对话模型**通过 chat 生成向量
      （仅 DEEPSEEK_API_KEY；见 ``DeepSeekChatEmbedder``，成本与延迟高于专用嵌入）。
    """
    provider = resolve_embedding_provider()
    if provider == "deepseek":
        from db.deepseek_chat_embedder import DeepSeekChatEmbedder

        base = getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1").strip().rstrip("/")
        if base == "https://api.deepseek.com":
            base = "https://api.deepseek.com/v1"
        chat_model = getenv(
            "DEEPSEEK_EMBEDDING_MODEL",
            getenv("DEEPSEEK_MODEL_ID", "deepseek-v4-flash"),
        ).strip()
        if not chat_model:
            chat_model = "deepseek-v4-flash"
        dimensions = int(getenv("DEEPSEEK_EMBEDDING_DIMENSIONS", "256"))
        return DeepSeekChatEmbedder(
            dimensions=dimensions,
            chat_model=chat_model,
            api_key=getenv("DEEPSEEK_API_KEY", "").strip() or None,
            base_url=base,
        )

    if provider != "openai":
        raise ValueError(
            f"Unsupported EMBEDDING_PROVIDER={provider!r}. Use 'openai' or 'deepseek' (see db/session.py)."
        )

    return OpenAIEmbedder(
        id=getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small"),
        api_key=getenv("OPENAI_API_KEY", "").strip() or None,
    )


def create_knowledge(name: str, table_name: str) -> Knowledge:
    """创建带 PgVector 混合检索的 Knowledge 实例。

    参数：
        name: 知识库显示名称。
        table_name: 用于存放向量数据的 PostgreSQL 表名。

    返回：
        配置好的 Knowledge 实例。
    """
    return Knowledge(
        name=name,
        vector_db=PgVector(
            db_url=db_url,
            table_name=table_name,
            search_type=SearchType.hybrid,
            embedder=_build_embedder(),
        ),
        contents_db=get_postgres_db(knowledge_table=f"{table_name}_contents"),
    )
