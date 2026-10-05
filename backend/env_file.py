"""Find and load the .env, wherever this copy of the project is sitting.

Two places are tried, in order:

1. the project root - a clone of this repository has its own .env there, made
   from .env.example, which is what the README asks a grader to do;
2. one level above it - where the key lives on the machine this was written
   on, in a single .env shared with the other homeworks.

Why this is a module rather than two lines in `agent.py`
-------------------------------------------------------
It used to be two lines in `agent.py`, and `auth.py` read
CAMPUS_CUSTOMS_SECRET straight from the environment at import time. That worked
only because `main.py` happens to import `agent` one line before `auth`, so the
file had been loaded by the time the secret was read. Import `auth` on its own -
as a test does - and the secret silently fell back to a freshly generated key,
which quietly means every session token stops working on restart even though
the variable was set correctly.

Anything that needs a value from the file now calls `load_env()` first, so it no
longer depends on which module imported which.

`load_dotenv` does not overwrite variables that are already set, so a real
environment variable still beats either file, and calling this more than once is
harmless.
"""

from __future__ import annotations

from pathlib import Path

from dotenv import load_dotenv

PROJECT_DIR = Path(__file__).resolve().parent.parent


def load_env() -> None:
    """Load the first .env that exists, nearest first."""
    for path in (PROJECT_DIR / ".env", PROJECT_DIR.parent / ".env"):
        if path.is_file():
            load_dotenv(path)
