from __future__ import annotations


def fallback_markdown(title: str, body: str) -> str:
    return f"# {title}\n\n{body}\n"
