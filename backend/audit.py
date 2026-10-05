"""Append-only record of what the agent loop did.

Every turn the agent takes is written to output/audit_trail.json: which tools it
called, with what arguments, what came back, and why the loop stopped. The file
is only ever appended to, so a run never erases what earlier runs recorded.

Why one JSON object per line
---------------------------
A single JSON array cannot be appended to. Adding an element means rewriting the
whole file, which is the opposite of append-only and loses the entire history if
the process dies mid-write. So the file holds one complete JSON object per line
- the JSON Lines convention - which appends in a single write and keeps every
earlier line untouched. Read it back with:

    records = [json.loads(line) for line in open(path, encoding="utf-8")]

Why the fields are the ones they are
------------------------------------
The point of the log is to answer "did the agent make that up?" after the fact.
That needs the tool name and its arguments (what was asked), a slice of the
result (what came back), and the stop reason (whether the loop finished on its
own or was cut off). Timestamps are UTC and ISO-8601 so lines sort correctly no
matter where the machine is.

Arguments and results are truncated to MAX_FIELD characters. A full tool result
is a whole product record; logging all of it would make the file enormous and
bury the one number worth auditing.

Auditing never breaks a reply. Every write is wrapped, because a shopper losing
their answer to a logging error would be a far worse bug than a missing line.
"""

from __future__ import annotations

import json
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

BACKEND_DIR = Path(__file__).resolve().parent
AUDIT_PATH = BACKEND_DIR.parent / "output" / "audit_trail.json"

MAX_FIELD = 300        # characters kept from any one argument or result

# Appends are serialised. Open-write-close is not atomic, so two turns landing
# together interleaved and truncated each other: a test firing 300 records from
# 12 threads kept only 272 of them and left 5 blank lines behind. FastAPI runs
# handlers on a thread pool, so two shoppers asking at once is the ordinary
# case rather than an edge case. One lock per process fixes it; run under
# several worker processes this would need file locking instead.
_WRITE_LOCK = threading.Lock()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _short(value: Any) -> str:
    """One-line, length-capped rendering of a tool argument or result."""
    if value is None:
        return ""
    if isinstance(value, (dict, list)):
        try:
            text = json.dumps(value, default=str, separators=(",", ":"))
        except (TypeError, ValueError):
            text = str(value)
    else:
        text = str(value)
    text = " ".join(text.split())          # collapse newlines, so one line stays one line
    if len(text) > MAX_FIELD:
        return text[:MAX_FIELD] + f"...[+{len(text) - MAX_FIELD} chars]"
    return text


def append(record: dict[str, Any]) -> None:
    """Write one record. Never raises."""
    try:
        AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
        line = json.dumps({"time": _now(), **record}, default=str)
        with _WRITE_LOCK:
            with AUDIT_PATH.open("a", encoding="utf-8") as handle:
                handle.write(line + "\n")
                handle.flush()
    except Exception:
        # A failed audit write must not cost the shopper their answer.
        pass


def record_run(
    *,
    run_id: str,
    question: str,
    messages: list[Any],
    stop_reason: str,
    signed_in: bool,
    page_label: str | None,
    tokens: int | None = None,
) -> None:
    """Unpack one agent run into one line per tool call plus a closing line.

    `messages` is what PydanticAI returns from result.all_messages(): an
    alternating list of requests and responses, where a response carries the
    tool calls the model decided on and the following request carries what those
    tools returned. Pairing them by tool name gives each call its own result.
    """
    returns: dict[str, list[str]] = {}
    for message in messages:
        for part in getattr(message, "parts", []):
            if type(part).__name__ == "ToolReturnPart":
                returns.setdefault(part.tool_name, []).append(_short(part.content))

    taken: dict[str, int] = {}
    step = 0
    tools_used: list[str] = []

    for message in messages:
        finish = getattr(message, "finish_reason", None)
        for part in getattr(message, "parts", []):
            if type(part).__name__ != "ToolCallPart":
                continue
            step += 1
            name = part.tool_name
            tools_used.append(name)
            index = taken.get(name, 0)
            taken[name] = index + 1
            results = returns.get(name, [])
            append(
                {
                    "event": "tool_call",
                    "run_id": run_id,
                    "step": step,
                    "tool": name,
                    "args": _short(part.args),
                    "result": _short(results[index]) if index < len(results) else "",
                    "stop_reason": finish or "",
                }
            )

    append(
        {
            "event": "run_end",
            "run_id": run_id,
            "question": _short(question),
            "steps": step,
            "tools_used": tools_used,
            "stop_reason": stop_reason,
            "signed_in": signed_in,
            "page": page_label or "",
            "tokens": tokens,
        }
    )
