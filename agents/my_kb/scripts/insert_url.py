"""
Insert a single web page into my_kb via Knowledge.insert(url=...).

Usage (from repo root):
    python -m agents.my_kb.scripts.insert_url --name "My doc" --url https://example.com/doc
"""

from __future__ import annotations

import argparse
from pathlib import Path


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def main() -> None:
    try:
        from dotenv import load_dotenv

        load_dotenv(_repo_root() / ".env", override=True)
    except ImportError:
        pass

    parser = argparse.ArgumentParser(description="Insert one URL into my_kb (PgVector)")
    parser.add_argument("--name", required=True, help="Stable display name for this document")
    parser.add_argument("--url", required=True, help="https://... page to fetch and embed")
    args = parser.parse_args()

    from agents.my_kb.scripts.load_knowledge import _check_embedding_config

    _check_embedding_config()

    from agents.my_kb.settings import my_kb

    my_kb.insert(name=args.name, url=args.url.strip())
    print(f"Done: inserted name={args.name!r} url={args.url!r}")


if __name__ == "__main__":
    main()
