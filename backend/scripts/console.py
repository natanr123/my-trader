#!/usr/bin/env python
"""
Host-side FastAPI/SQLModel console using ptpython.
No .env loading here — relies on process env / Settings defaults.

Run on host:
  cd backend
  uv run python scripts/console.py
"""

from __future__ import annotations
import sys
from pathlib import Path

# Ensure backend/ on sys.path so `import app...` works
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# App context
from sqlmodel import Session, select  # noqa: E402
from app.core.db import engine        # noqa: E402

# (Optional) import models so SQLModel metadata is populated
def _import_models() -> None:
    import importlib, pkgutil
    try:
        pkg = importlib.import_module("app.models")
    except ModuleNotFoundError:
        return
    for m in pkgutil.iter_modules(pkg.__path__):
        importlib.import_module(f"app.models.{m.name}")

_import_models()

# Open a session (close when done if you open many)
session = Session(engine)

BANNER = """
🚀 FastAPI/SQLModel console (ptpython, host)

Preloaded:
  - engine  -> app.core.db.engine
  - session -> sqlmodel.Session(engine)
  - select  -> sqlmodel.select
  - app.models.* imported (if present)

Use Tab/Ctrl-Space for completions. F6 shows docstrings.
"""

def main() -> None:
    # Pretty printing if available
    try:
        from rich import pretty
        pretty.install()
    except Exception:
        pass

    from ptpython.repl import embed
    history_file = str(ROOT / ".ptpython_history")
    try:
        embed(
            globals(), locals(),
            title="FastAPI Console",
            history_filename=history_file,
        )
    except Exception:
        print(BANNER)
        import code
        code.interact(local=globals())

if __name__ == "__main__":
    main()
