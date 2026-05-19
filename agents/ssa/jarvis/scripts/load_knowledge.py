"""
将 ``agents/ssa/jarvis/knowledge/`` 下的文件载入 ``jarvis_kb``（PgVector）。

可选：在 ``.env`` 中配置 ``JARVIS_REMOTE_SOURCE_URL``，并传入 ``--with-remote-source-url``，
会额外对该地址执行一次 ``insert(url=...)``（需登录或鉴权的页面常会抓取失败）。

用法（在项目根目录执行）::
    python -m agents.ssa.jarvis.scripts.load_knowledge
    python -m agents.ssa.jarvis.scripts.load_knowledge --recreate
    python -m agents.ssa.jarvis.scripts.load_knowledge --with-remote-source-url
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path


def _repo_root() -> Path:
    # 本文件在 agents/ssa/jarvis/scripts/；向上 4 层为仓库根 demo-os/
    return Path(__file__).resolve().parents[4]


def main() -> None:
    # 载入本地环境变量（.env）；若无 python-dotenv 则跳过，便于无该依赖的环境跑脚本
    try:
        from dotenv import load_dotenv

        load_dotenv(_repo_root() / ".env", override=True)
    except ImportError:
        pass

    parser = argparse.ArgumentParser(description="将贾维斯知识库写入 PgVector")
    parser.add_argument(
        "--recreate",
        action="store_true",
        help="写入前先删除并重建 jarvis_kb 向量存储",
    )
    parser.add_argument(
        "--with-remote-source-url",
        action="store_true",
        dest="with_remote_source_url",
        help="额外插入环境变量 JARVIS_REMOTE_SOURCE_URL 指向的单页文档（须已配置；受站点访问限制可能影响入库）",
    )
    args = parser.parse_args()

    # 校验 embedding 等配置，与项目中其他 knowledge 载入脚本共用同一辅助函数
    from agents.my_kb.scripts.load_knowledge import _check_embedding_config

    _check_embedding_config()

    from agents.ssa.jarvis.settings import jarvis_kb

    pkg_dir = Path(__file__).resolve().parent.parent
    knowledge_dir = pkg_dir / "knowledge"

    if args.recreate and jarvis_kb.vector_db:
        print("Recreating jarvis_kb vector store...\n")
        jarvis_kb.vector_db.drop()
        jarvis_kb.vector_db.create()

    # 排除占位与垃圾文件；.gitkeep 不是文档正文
    exclude = ["*.url", "*.URL", "*.lnk", "Thumbs.db", ".DS_Store", ".gitkeep", "*.gitkeep"]

    if knowledge_dir.is_dir():
        print(f"Loading knowledge from: {knowledge_dir}\n")
        jarvis_kb.insert(name="jarvis-batch", path=str(knowledge_dir), exclude=exclude)
    else:
        print(f"No knowledge directory at {knowledge_dir} (skip file batch).\n")

    # 单页远程地址按需入库；仅存于环境变量，仓库内不写死链接
    if args.with_remote_source_url:
        remote_source_url = (os.getenv("JARVIS_REMOTE_SOURCE_URL") or "").strip()
        if not remote_source_url:
            print("Skipping remote-source insert: JARVIS_REMOTE_SOURCE_URL is not set in environment.\n")
        else:
            print(f"Inserting remote source URL: {remote_source_url}\n")
            jarvis_kb.insert(name="jarvis-remote-source", url=remote_source_url)

    print("Done.")


if __name__ == "__main__":
    main()
