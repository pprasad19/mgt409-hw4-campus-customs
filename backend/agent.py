"""Campus Customs shop agent.

Wires the model, the system prompt, and the catalogue tools into a single
PydanticAI agent, and exposes one `answer()` call for the chat route.

Model:  gpt-6-luna, reached through Portkey with the OpenAI-compatible API.
Key:    PORTKEY_API_KEY, read from the class-folder .env one level above
        Homework 4 (the same .env the other assignments use).
Prompt: prompts/prompt.md, read fresh on each agent build so edits to the
        prompt do not require a code change.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Optional

from openai import AsyncOpenAI
from pydantic_ai import Agent, RunContext
from pydantic_ai.exceptions import UsageLimitExceeded
from pydantic_ai.usage import UsageLimits
from pydantic_ai.models.openai import OpenAIChatModel, OpenAIChatModelSettings
from pydantic_ai.providers.openai import OpenAIProvider

import audit
from env_file import load_env
from models import (
    AgentReply,
    Alternatives,
    ChatTurn,
    LookupFailure,
    ProductDetail,
    SearchResults,
    SizeAvailability,
)
from tools import (
    check_size_availability,
    find_alternatives as tools_find_alternatives,
    get_product_details,
    search_catalogue,
)

BACKEND_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BACKEND_DIR.parent
PROMPT_PATH = BACKEND_DIR / "prompts" / "prompt.md"

# Loaded through env_file so that auth.py can rely on it too, rather than on
# being imported after this module. See env_file.py.
load_env()

DEFAULT_MODEL = "gpt-6-luna"
PORTKEY_BASE_URL = "https://api.portkey.ai/v1"

# How many earlier turns to replay. Enough for "do you have this in pink?" to
# resolve, bounded so a long conversation cannot grow the request without limit.
MAX_HISTORY_TURNS = 10

# A stuck agent would otherwise call tools forever. Four model requests is
# comfortably above what a real turn needs - a search, a size check and the
# structured reply is three - and well under anything that could run away.
MAX_MODEL_REQUESTS = 4


class AgentUnavailable(RuntimeError):
    """Raised when the agent cannot be built, usually a missing API key."""


@dataclass
class ShopContext:
    """Everything the agent is told about *who* and *where*, per request.

    Passed as PydanticAI deps, so it is scoped to a single run and never
    leaks between shoppers. Deliberately narrow: the agent sees a name and an
    email so it can address someone properly, and nothing else about the
    account. No id, no password hash, no signup date, no order history.
    """

    # Who. Both None for a guest.
    name: Optional[str] = None
    email: Optional[str] = None

    # Where on the site the message was sent from.
    #
    # page_label is chosen by the server from a fixed set of phrases - the raw
    # URL is never passed through. A path arrives from the browser, so a
    # crafted link can put anything in it; interpolating that into the
    # instructions let a URL inject its own orders to the agent.
    page_label: Optional[str] = None
    viewing_product_id: Optional[str] = None
    viewing_product_name: Optional[str] = None

    @property
    def is_signed_in(self) -> bool:
        return self.email is not None


def load_prompt() -> str:
    if not PROMPT_PATH.is_file():
        raise AgentUnavailable(f"System prompt not found at {PROMPT_PATH}")
    return PROMPT_PATH.read_text(encoding="utf-8")


@lru_cache(maxsize=1)
def build_agent() -> Agent:
    """Build the agent once and reuse it across requests."""
    api_key = os.getenv("PORTKEY_API_KEY")
    if not api_key:
        raise AgentUnavailable("PORTKEY_API_KEY is missing from the class-folder .env")

    client = AsyncOpenAI(
        api_key=api_key,
        base_url=PORTKEY_BASE_URL,
        default_headers={"x-portkey-api-key": api_key, "x-portkey-provider": "openai"},
    )
    model = OpenAIChatModel(
        os.getenv("OPENAI_MODEL", DEFAULT_MODEL),
        provider=OpenAIProvider(openai_client=client),
    )

    agent = Agent(
        model,
        output_type=AgentReply,
        deps_type=ShopContext,
        # gpt-6-luna refuses function tools on /v1/chat/completions unless
        # reasoning effort is off:
        #   "Function tools with reasoning_effort are not supported for
        #    gpt-6-luna-global in /v1/chat/completions."
        # The shop agent needs its catalogue tools far more than it needs
        # reasoning tokens, so effort is disabled rather than dropping tools.
        model_settings=OpenAIChatModelSettings(openai_reasoning_effort="none"),
    )

    @agent.instructions
    def system_prompt() -> str:
        """Read prompts/prompt.md on every run.

        `uvicorn --reload` only watches .py files, so a static prompt would go
        stale the moment the file is edited. Reading it per run means prompt
        changes take effect on the next message with no restart.
        """
        return load_prompt()

    @agent.instructions
    def shopper_and_page(ctx: RunContext[ShopContext]) -> str:
        """Tell the agent who it is talking to and what they are looking at.

        Injected as instructions rather than exposed as a tool: the agent
        needs this on every single turn, and a tool it has to remember to call
        is a tool it will sometimes forget. "Do you have this in pink?" has to
        work on the first try.
        """
        deps = ctx.deps
        lines = ["## Who you are talking to"]

        if deps.is_signed_in:
            lines.append(
                f"A signed-in shopper: {deps.name} ({deps.email}). You may greet them by "
                f"their first name. Their conversation with you is saved to their account."
            )
        else:
            lines.append(
                "A guest who is not signed in. Do not guess their name. If it would help "
                "them, mention that signing in saves their conversation - but only once, "
                "and never as a condition of helping."
            )

        lines.append("")
        lines.append("## Where they are on the site")

        if deps.viewing_product_id:
            lines.append(
                f"They are on the product page for **{deps.viewing_product_name}** "
                f"(product_id `{deps.viewing_product_id}`).\n\n"
                "Treat vague references - \"this\", \"it\", \"this one\", \"this hoodie\" - as "
                f"meaning that product, unless they clearly mean something else. A question "
                f"like \"do you have this in pink?\" is about `{deps.viewing_product_id}`, so "
                "look that product up rather than asking which item they mean."
            )
        elif deps.page_label:
            lines.append(
                f"They are on {deps.page_label}, which is not a single product page. If they "
                "say \"this\" without a product in view, ask which item they mean."
            )
        else:
            lines.append("Their location on the site is unknown.")

        return "\n".join(lines)

    @agent.tool_plain
    def search_products(query: str) -> SearchResults:
        """Search the Campus Customs catalogue. Reads the live product database.

        Use this for any question about what the shop sells. The query can be a
        color, a team, a residential college, a garment type, or a phrase from
        the shopper.

        Returns at most eight products, each with its real price and the sizes
        currently in stock. Check `total_matches` and `truncated`: when
        `truncated` is true there are more products than the ones listed, so say
        so rather than presenting the list as everything the shop has.
        """
        return search_catalogue(query)

    @agent.tool_plain
    def product_details(product_id: str) -> ProductDetail | LookupFailure:
        """Full detail for one product: description, price, colors, every size and its stock.

        Reads the live product database. Use a product_id returned by
        search_products. If the id does not exist you get a LookupFailure with
        found=false, which means you have no information about it - say so
        instead of describing or pricing it.
        """
        return get_product_details(product_id)

    @agent.tool_plain
    def find_alternatives(product_id: str, size: str | None = None) -> Alternatives:
        """Find similar products that ARE available, when one is not.

        Call this whenever a shopper cannot have what they asked for: their
        size is sold out, the colour does not exist, or the product is not in
        the catalogue. Pass the size when they named one, and every suggestion
        will be in stock in that size.

        Returns up to four products from the same category, closest in price,
        each with the sizes it is actually in stock in. Offer these instead of
        ending on "no".
        """
        return tools_find_alternatives(product_id, size)

    @agent.tool_plain
    def size_availability(product_id: str, size: str) -> SizeAvailability | LookupFailure:
        """Check whether one size of one product is in stock, and how many are left.

        Reads the live inventory table. Use this whenever a shopper asks about a
        specific size. Sizes are XS, S, M, L, XL, XXL.

        `quantity` is the real number on hand and `in_stock` is false when it is
        zero. `size_exists` is false if the product is not made in that size at
        all. The `message` field is a sentence you can relay as-is.
        """
        return check_size_availability(product_id, size)

    return agent


def model_name() -> str:
    return os.getenv("OPENAI_MODEL", DEFAULT_MODEL)


def is_configured() -> bool:
    """True when the agent has what it needs to run."""
    return bool(os.getenv("PORTKEY_API_KEY")) and PROMPT_PATH.is_file()


def _as_conversation(message: str, history: list[ChatTurn]) -> str:
    """Flatten prior turns into the prompt so follow-ups resolve.

    Kept as plain text rather than replayed message objects because the chat
    widget stores its own history and the backend holds no session state.
    """
    recent = history[-MAX_HISTORY_TURNS:]
    if not recent:
        return message

    lines = ["Earlier in this conversation:"]
    for turn in recent:
        speaker = "Shopper" if turn.role == "user" else "You"
        lines.append(f"{speaker}: {turn.content}")
    lines.append("")
    lines.append(f"The shopper now says: {message}")
    return "\n".join(lines)


async def answer(
    message: str,
    history: list[ChatTurn] | None = None,
    context: ShopContext | None = None,
) -> AgentReply:
    """Run one turn, record what the loop did, and return the structured reply."""
    agent = build_agent()
    deps = context or ShopContext()
    try:
        result = await agent.run(
            _as_conversation(message, history or []),
            deps=deps,
            usage_limits=UsageLimits(request_limit=MAX_MODEL_REQUESTS),
        )
    except UsageLimitExceeded as exceeded:
        # The loop hit its ceiling instead of finishing. That is exactly the
        # case the audit trail exists for, so it gets a line of its own rather
        # than vanishing into a 500.
        audit.append(
            {
                "event": "run_end",
                "run_id": "",
                "question": message[:300],
                "steps": MAX_MODEL_REQUESTS,
                "tools_used": [],
                "stop_reason": "request_limit_exceeded",
                "signed_in": deps.is_signed_in,
                "page": deps.page_label or "",
                "tokens": None,
                "detail": str(exceeded)[:300],
            }
        )
        return _give_up()
    except Exception as error:
        # Anything else that ended the turn: the provider refusing the input,
        # the API being down, a tool raising. These were invisible to the audit
        # trail at first, because only the usage limit was caught - which meant
        # the log went quiet in exactly the cases worth reviewing. A blocked
        # jailbreak attempt left no trace at all.
        #
        # The record is written and the error re-raised unchanged, so the
        # endpoint's own handling of each case still decides what the shopper
        # sees.
        detail = str(error)
        reason = "content_filter" if "content_filter" in detail else f"error:{type(error).__name__}"
        audit.append(
            {
                "event": "run_end",
                "run_id": "",
                "question": message[:300],
                "steps": 0,
                "tools_used": [],
                "stop_reason": reason,
                "signed_in": deps.is_signed_in,
                "page": deps.page_label or "",
                "tokens": None,
                "detail": detail[:300],
            }
        )
        raise

    return _finish(result, message, deps)


def _give_up() -> AgentReply:
    """What the shopper hears when the loop ran out of room."""
    return AgentReply(
        reply=(
            "Sorry - I could not work that one out. Could you ask it a "
            "different way, or name the product you have in mind?"
        )
    )


def _finish(result: Any, message: str, deps: ShopContext) -> AgentReply:
    """Record a completed run and hand back its reply.

    Audited after the fact rather than from inside the tools: the finished run
    holds the tool calls, their results and the finish reason together, so one
    pass over it records the whole loop without threading state through tools.
    """
    messages = result.all_messages()
    # The last finish_reason is always "tool_call", because the structured
    # reply itself arrives as a call to final_result. That says nothing about
    # whether the turn went well, so a run that produced its output is recorded
    # as "completed" and the raw reason is kept only when it did not.
    raw_reason = ""
    for message_obj in reversed(messages):
        reason = getattr(message_obj, "finish_reason", None)
        if reason:
            raw_reason = str(reason)
            break
    stop_reason = "completed" if result.output is not None else (raw_reason or "unknown")

    tokens = None
    try:
        tokens = result.usage.total_tokens
    except Exception:
        pass

    audit.record_run(
        run_id=str(getattr(result, "run_id", "")),
        question=message,
        messages=messages,
        stop_reason=stop_reason,
        signed_in=deps.is_signed_in,
        page_label=deps.page_label,
        tokens=tokens,
    )
    return result.output
