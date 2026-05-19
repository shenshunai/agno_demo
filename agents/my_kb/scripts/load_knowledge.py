"""
将 agents/my_kb/knowledge/ 下的文件批量写入向量知识库。

支持多种常见格式（由 Agno 按扩展名解析），例如 .md、.txt、.pdf、.csv、
.xlsx/.xls、.docx/.doc、.pptx、.json 等；不仅限于 Markdown。

另支持网页：将 `seed_urls.example` 复制为 `agents/my_kb/seed_urls.txt`，每行一个
http(s) URL，运行本脚本时会调用 `Knowledge.insert(url=...)` 拉取并入库。

用法（在项目根目录）：
    python -m agents.my_kb.scripts.load_knowledge
    python -m agents.my_kb.scripts.load_knowledge --recreate
"""

from __future__ import annotations

import argparse
from pathlib import Path


def _repo_root() -> Path:
    # agents/my_kb/scripts/load_knowledge.py -> parents[3] = repo root
    return Path(__file__).resolve().parents[3]


def _existing_pgvector_embedding_dim(vdb) -> int | None:
    """If vector table exists, return embedding column vector(N) dimension N; else None."""
    import re

    from sqlalchemy import text

    if not getattr(vdb, "db_engine", None) or not vdb.exists():
        return None
    schema = getattr(vdb, "schema", None) or "public"
    table = vdb.table_name
    try:
        with vdb.db_engine.connect() as conn:
            row = conn.execute(
                text(
                    """
                    SELECT format_type(a.atttypid, a.atttypmod) AS ft
                    FROM pg_attribute a
                    JOIN pg_class c ON a.attrelid = c.oid
                    JOIN pg_namespace n ON c.relnamespace = n.oid
                    WHERE n.nspname = :schema
                      AND c.relname = :tbl
                      AND a.attname = 'embedding'
                      AND NOT a.attisdropped
                    """
                ),
                {"schema": schema, "tbl": table},
            ).one_or_none()
        if not row or not row[0]:
            return None
        m = re.search(r"vector\((\d+)\)", str(row[0]))
        return int(m.group(1)) if m else None
    except Exception:
        return None


def _check_embedding_config() -> None:
    """Fail fast with a clear message if embedding API cannot authenticate."""
    from db.session import resolve_embedding_provider

    provider = resolve_embedding_provider()
    if provider not in ("deepseek", "openai"):
        raise SystemExit(
            f"不支持的 EMBEDDING_PROVIDER={provider!r}，请设为 openai 或 deepseek（本机向量模式已移除）。"
        )
    if provider == "deepseek":
        from os import getenv

        if not getenv("DEEPSEEK_API_KEY", "").strip():
            raise SystemExit(
                "嵌入失败：已选择 DeepSeek 向量路径，但 .env 中缺少有效的 DEEPSEEK_API_KEY。\n"
                "请在项目根 .env 填写 DeepSeek Key。"
            )
        return
    else:
        from os import getenv

        if not getenv("OPENAI_API_KEY", "").strip():
            raise SystemExit(
                "嵌入失败：当前为 OpenAI 向量路径，但 .env 中缺少 OPENAI_API_KEY。\n"
                "请任选其一：\n"
                "  1) 填写 OPENAI_API_KEY=sk-...\n"
                "  2) 仅 DeepSeek：设 USE_DEEPSEEK=1、DEEPSEEK_API_KEY，且不要填 OPENAI_API_KEY；"
                "或显式 EMBEDDING_PROVIDER=deepseek（会用 DeepSeek 对话模型生成向量，较慢、较贵）。\n"
                "改完后重新运行本脚本。"
            )


def _load_urls_from_file(my_kb, urls_file: Path) -> None:
    if not urls_file.is_file():
        return
    lines = urls_file.read_text(encoding="utf-8").splitlines()
    urls = [ln.strip() for ln in lines if ln.strip() and not ln.strip().startswith("#")]
    if not urls:
        print(f"No URLs in {urls_file.name} (skip).\n")
        return
    print(f"Loading {len(urls)} URL(s) from {urls_file}...\n")
    for i, url in enumerate(urls, start=1):
        name = f"my-kb-url-{i}"
        print(f"  [{i}/{len(urls)}] {url}")
        my_kb.insert(name=name, url=url)
    print()


def main() -> None:
    # Load .env before DB / embedder read getenv (same as app.main).
    try:
        from dotenv import load_dotenv

        # Use override=True so project .env wins over empty shell vars (e.g. EMBEDDING_PROVIDER="").
        load_dotenv(_repo_root() / ".env", override=True)
    except ImportError:
        pass

    parser = argparse.ArgumentParser(description="Load my_kb knowledge into PgVector")
    parser.add_argument(
        "--recreate",
        action="store_true",
        help="Drop existing vector table and reload from scratch",
    )
    args = parser.parse_args()

    _check_embedding_config()

    from agents.my_kb.settings import my_kb

    pkg_dir = Path(__file__).resolve().parent.parent
    knowledge_dir = pkg_dir / "knowledge"
    if not knowledge_dir.is_dir():
        print(f"Knowledge directory not found: {knowledge_dir}")
        return

    embed_dims = int(getattr(my_kb.vector_db.embedder, "dimensions", 0) or 0)
    existing_dim = _existing_pgvector_embedding_dim(my_kb.vector_db)
    if (
        existing_dim is not None
        and embed_dims > 0
        and existing_dim != embed_dims
        and not args.recreate
    ):
        raise SystemExit(
            f"数据库向量列为 {existing_dim} 维，当前嵌入器为 {embed_dims} 维，无法直接写入。\n"
            "请先清空并按新维度重建表，再重新入库：\n"
            "  python -m agents.my_kb.scripts.load_knowledge --recreate\n"
            "（会删除 ai.my_kb 向量表并重建；重要数据请先自行备份。）"
        )

    if args.recreate:
        print("Recreating my_kb vector store...\n")
        if my_kb.vector_db:
            my_kb.vector_db.drop()
            my_kb.vector_db.create()

    # Exclude desktop shortcut / URL stub files (e.g. Lark .larkdocx.url) — not real document bodies.
    exclude = ["*.url", "*.URL", "*.lnk", "Thumbs.db", ".DS_Store"]

    print(f"Loading knowledge from: {knowledge_dir}\n")
    my_kb.insert(name="my-kb-batch", path=str(knowledge_dir), exclude=exclude)

    seed_urls = pkg_dir / "seed_urls.txt"
    _load_urls_from_file(my_kb, seed_urls)

    print("Done.")


if __name__ == "__main__":
    main()
