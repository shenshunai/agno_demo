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
from agno.knowledge.embedder.openai_like import OpenAILikeEmbedder
from agno.vectordb.pgvector import PgVector, SearchType

from db.url import db_url

DB_ID = "demo-os-db"


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

    规则很简单：
    - 默认使用 OpenAI 嵌入（兼容旧配置）
    - 当 EMBEDDING_PROVIDER=deepseek 时，改用 DeepSeek 兼容的嵌入接口
    """
    provider = getenv("EMBEDDING_PROVIDER", "openai").strip().lower()

    if provider == "deepseek":
        return OpenAILikeEmbedder(
            id=getenv("DEEPSEEK_EMBEDDING_MODEL", "deepseek-embedding"),
            api_key=getenv("DEEPSEEK_API_KEY", "").strip() or None,
            base_url=getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1"),
            dimensions=int(getenv("DEEPSEEK_EMBEDDING_DIMENSIONS", "1536")),
        )

    return OpenAIEmbedder(
        id=getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small"),
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
