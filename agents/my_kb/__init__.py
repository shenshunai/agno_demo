"""My KB package: lazy-load `my_kb` and `my_kb_agent` so `.env` is applied before
`create_knowledge` runs (e.g. `python -m agents.my_kb.scripts.load_knowledge`).
"""

__all__ = ["my_kb", "my_kb_agent"]


def __getattr__(name: str):
    if name == "my_kb":
        from agents.my_kb.settings import my_kb as _kb

        return _kb
    if name == "my_kb_agent":
        from agents.my_kb.agent import my_kb_agent as _agent

        return _agent
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
