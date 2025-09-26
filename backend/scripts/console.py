#!/usr/bin/env python
"""
Minimal FastAPI/SQLModel console (container-friendly).
Run from inside the backend container:

  docker compose exec backend uv run python scripts/console.py
"""

from __future__ import annotations
import sys
from pathlib import Path

# Ensure project root (backend/) is importable so `import app...` works
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Import DB bits and (optionally) preload models
from sqlmodel import Session, select  # noqa: E402
from app.core.db import engine        # noqa: E402

def _import_models() -> None:
    """Eager-import app.models.* so SQLModel metadata is populated (optional)."""
    import importlib, pkgutil
    try:
        pkg = importlib.import_module("app.models")
    except ModuleNotFoundError:
        return
    for m in pkgutil.iter_modules(pkg.__path__):
        importlib.import_module(f"app.models.{m.name}")

_import_models()

# Open a session (close it manually if you open many)
session = Session(engine)

BANNER = """
🚀 FastAPI/SQLModel console

Preloaded:
  - engine  -> app.core.db.engine
  - session -> sqlmodel.Session(engine)
  - select  -> sqlmodel.select
  - app.models.* imported (if present)

Tips:
  %load_ext autoreload ; %autoreload 2
"""

def _start():
    try:
        from IPython import embed
        # nice quality-of-life extras (safe if they fail)
        try:
            from IPython import get_ipython
            ip = get_ipython()
            if ip:
                ip.run_line_magic("load_ext", "autoreload")
                ip.run_line_magic("autoreload", "2")
                ip.run_line_magic("autoawait", "asyncio")
        except Exception:
            pass
        embed(header=BANNER, colors="neutral")
    except Exception:
        print(BANNER)
        import code
        code.interact(local=globals())

if __name__ == "__main__":
    _start()
