"""Catalogue and inventory access for Campus Customs.

Holds the database helpers used by the REST routes in main.py and the three
tools the agent is allowed to call. Keeping both here means the agent and the
website read the catalogue through exactly the same code.

Nothing in this module writes to the catalogue or inventory tables.
"""

from __future__ import annotations

import json
import re
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator, Optional

from models import (
    AlternativeMatch,
    Alternatives,
    CatalogueMatch,
    LookupFailure,
    ProductDetail,
    ProductSummary,
    SearchResults,
    SizeAvailability,
)

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "campus_customs.db"
DATA_DIR = BASE_DIR / "data"

SIZE_ORDER = ["XS", "S", "M", "L", "XL", "XXL"]

# How many hits a single catalogue search may hand the agent. Bounded so a
# broad query cannot flood the model's context with the whole catalogue.
MAX_SEARCH_RESULTS = 8

# Search results carry a trimmed description. The agent is picking which
# products to show, not writing copy, and the full text is one lookup away.
SEARCH_DESCRIPTION_CHARS = 90

# Words that carry no signal in a catalogue search. "yale" is here because it
# appears in nearly every product, so scoring it would flatten the ranking.
SEARCH_STOPWORDS = {
    "a", "an", "the", "and", "or", "of", "for", "in", "on", "at", "to", "with",
    "do", "does", "did", "is", "are", "was", "be", "have", "has", "had", "get",
    "i", "me", "my", "we", "us", "our", "you", "your", "it", "this", "that",
    "any", "anything", "some", "something", "show", "find", "looking", "look",
    "want", "need", "like", "please", "can", "could", "would", "there", "what",
    "whats", "yale", "team", "gear", "campus", "customs", "shop", "store",
}

# garment_type in the catalogue is free text with 22 variants and inconsistent
# casing ("short-sleeve t-shirt" vs "short-sleeve T-shirt"), so shopper-facing
# categories are derived rather than taken from the column directly.
CATEGORY_RULES = [
    ("Quarter-Zips", ("quarter-zip", "mockneck")),
    ("Jackets", ("jacket",)),
    ("Hoodies", ("hoodie", "hooded")),
    ("Crewnecks", ("crewneck", "crew-neck", "crew neck")),
    ("T-Shirts", ("t-shirt", "tshirt", "tee")),
    ("Performance", ("performance", "long-sleeve")),
]


# --------------------------------------------------------------------------
# Database access
# --------------------------------------------------------------------------


@contextmanager
def get_db() -> Iterator[sqlite3.Connection]:
    """Open a read-only connection. Catalogue reads never write."""
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


@contextmanager
def get_db_write() -> Iterator[sqlite3.Connection]:
    """Open a writable connection. Only the auth endpoints use this."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# --------------------------------------------------------------------------
# Row helpers
# --------------------------------------------------------------------------


def categorize(garment_type: str) -> str:
    g = garment_type.lower()
    for label, needles in CATEGORY_RULES:
        if any(n in g for n in needles):
            return label
    return "Other"


def load_json_list(raw: str) -> list[str]:
    """colors and search_tags are JSON arrays stored as TEXT."""
    try:
        value = json.loads(raw)
        return [str(v) for v in value] if isinstance(value, list) else []
    except (json.JSONDecodeError, TypeError):
        return []


def short_description(description: str, limit: int = 120) -> str:
    if len(description) <= limit:
        return description
    return description[:limit].rsplit(" ", 1)[0].rstrip(",.;") + "..."


def image_url(image_file_path: str) -> str:
    """Build the image URL with a version stamp from the file's timestamp.

    Browsers hold onto product photos aggressively. Stamping the URL means an
    edited photo gets a new address, so a stale copy cannot be shown - which
    is exactly what happened when every backdrop was repainted white and the
    pages kept displaying the old black ones.

    The timestamp is read per call rather than cached. An earlier version
    cached it against the database's timestamp, which was wrong: images change
    independently of the database, so repainting every photo left the stamps
    frozen and the stale images on screen. A stat() is measured in
    microseconds; being right matters more here.
    """
    try:
        version = int((DATA_DIR / image_file_path).stat().st_mtime)
    except OSError:
        version = 0
    return f"/static/{image_file_path}?v={version}"


def row_to_summary(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "product_id": row["product_id"],
        "name": row["name"],
        "garment_type": row["garment_type"],
        "category": categorize(row["garment_type"]),
        "short_description": short_description(row["description"]),
        "colors": load_json_list(row["colors"]),
        "price": row["price"],
        "image_url": image_url(row["image_file_path"]),
        "total_stock": row["total_stock"] or 0,
    }


def sort_sizes(rows: list[sqlite3.Row]) -> list[dict[str, Any]]:
    """Order XS..XXL and mark each size in or out of stock.

    145 of 612 inventory rows sit at quantity 0, so availability is always
    reported per size rather than per product.
    """
    return sorted(
        (
            {"size": r["size"], "quantity": r["quantity"], "in_stock": r["quantity"] > 0}
            for r in rows
        ),
        key=lambda s: SIZE_ORDER.index(s["size"]) if s["size"] in SIZE_ORDER else len(SIZE_ORDER),
    )


CATALOGUE_SQL = """
    SELECT c.*, COALESCE(SUM(i.quantity), 0) AS total_stock
    FROM catalogue c
    LEFT JOIN inventory i ON i.product_id = c.product_id
    {where}
    GROUP BY c.product_id
    ORDER BY c.name
"""


# --------------------------------------------------------------------------
# Catalogue cache
#
# Every search previously re-read all 102 catalogue rows and all 612 inventory
# rows from SQLite, and a single agent turn can search several times. The
# catalogue is static between edits, so it is read once and kept in memory.
#
# The cache is keyed on the database file's modification time, so any write -
# a signup, a saved chat turn, a manual edit - invalidates it automatically.
# There is no stale-data window to reason about.
# --------------------------------------------------------------------------

_cache_key: Optional[float] = None
_cached_rows: list[sqlite3.Row] = []
_cached_stock: dict[str, dict[str, int]] = {}


def _db_mtime() -> float:
    try:
        return DB_PATH.stat().st_mtime
    except OSError:
        return 0.0


def catalogue_rows() -> tuple[list[sqlite3.Row], dict[str, dict[str, int]]]:
    """All catalogue rows plus a {product_id: {size: quantity}} stock map."""
    global _cache_key, _cached_rows, _cached_stock

    mtime = _db_mtime()
    if _cache_key == mtime and _cached_rows:
        return _cached_rows, _cached_stock

    with get_db() as conn:
        rows = conn.execute(CATALOGUE_SQL.format(where="")).fetchall()
        stock_rows = conn.execute("SELECT product_id, size, quantity FROM inventory").fetchall()

    stock: dict[str, dict[str, int]] = {}
    for r in stock_rows:
        stock.setdefault(r["product_id"], {})[r["size"]] = r["quantity"]

    _cache_key, _cached_rows, _cached_stock = mtime, rows, stock
    return rows, stock


def sizes_in_stock(product_id: str, stock: dict[str, dict[str, int]]) -> list[str]:
    sizes = [s for s, q in stock.get(product_id, {}).items() if q > 0]
    return sorted(sizes, key=lambda s: SIZE_ORDER.index(s) if s in SIZE_ORDER else len(SIZE_ORDER))


# --------------------------------------------------------------------------
# Shared catalogue queries (used by the REST routes and the agent tools)
# --------------------------------------------------------------------------


def list_products(
    search: Optional[str] = None,
    category: Optional[str] = None,
    size: Optional[str] = None,
    color: Optional[str] = None,
) -> list[ProductSummary]:
    """Catalogue listing for the website's Products page.

    Uses the same word scoring as the agent's `search_catalogue`, so the two
    never disagree. That matters because the chat results band links here with
    the agent's own query: a plain substring match would make "hoodies" find
    nothing (the products say "hoodie"), and "See all 27" would land on an
    empty page.
    """
    rows, stock = catalogue_rows()

    if category and category.lower() != "all":
        rows = [r for r in rows if categorize(r["garment_type"]).lower() == category.lower()]

    # Only products actually buyable in that size - quantity greater than zero,
    # not merely listed. 145 of 612 size rows sit at zero.
    #
    # "any" and "all" both mean no filter. The Products page uses "Any" as its
    # sentinel and strips it from the URL, but a hand-typed or shared link can
    # still carry it, and treating it as a real size emptied the catalogue.
    if size and size.strip().lower() not in ("all", "any", ""):
        wanted = size.strip().upper()
        rows = [r for r in rows if stock.get(r["product_id"], {}).get(wanted, 0) > 0]

    # Exact colour match against the product's own colour list, not a text
    # search: "navy" should mean the garment comes in navy, not that the word
    # appears somewhere in its description.
    if color:
        wanted = color.strip().lower()
        rows = [r for r in rows if wanted in [c.lower() for c in load_json_list(r["colors"])]]

    if not search:
        return [ProductSummary(**row_to_summary(r)) for r in rows]

    tokens = [t for t in re.findall(r"[a-z0-9]+", search.lower()) if t not in SEARCH_STOPWORDS]
    if not tokens:
        return [ProductSummary(**row_to_summary(r)) for r in rows]

    scored = []
    for row in rows:
        haystack = " ".join(
            [row["name"], row["description"], row["colors"], row["search_tags"], row["garment_type"]]
        ).lower()
        score = _match_score(tokens, haystack)
        if score:
            scored.append((score, row["name"], row))

    # Same rule as the agent's search, so the catalogue page and the chat agree
    # on what a query means. They have to: the "See all N" button sends the
    # shopper from one to the other.
    scored = _drop_partial_matches(scored, len(tokens))
    scored.sort(key=lambda item: (-item[0], item[1]))
    return [ProductSummary(**row_to_summary(row)) for _, _, row in scored]


def get_product(product_id: str) -> ProductDetail | None:
    with get_db() as conn:
        row = conn.execute(
            CATALOGUE_SQL.format(where="WHERE c.product_id = ?"), (product_id,)
        ).fetchone()
        if row is None:
            return None
        size_rows = conn.execute(
            "SELECT size, quantity FROM inventory WHERE product_id = ?", (product_id,)
        ).fetchall()

    detail = row_to_summary(row)
    detail.update(
        description=row["description"],
        search_tags=load_json_list(row["search_tags"]),
        sizes=sort_sizes(size_rows),
    )
    return ProductDetail(**detail)


def get_products_by_ids(product_ids: list[str]) -> list[ProductSummary]:
    """Resolve the ids the agent chose into cards, preserving its order.

    Ids that do not exist are dropped, so a card can only ever be built from a
    real catalogue row. Repeats are dropped too: the model occasionally lists
    the same product twice, which would render the same card twice and give
    React two children with the same key.
    """
    if not product_ids:
        return []

    unique_ids = list(dict.fromkeys(product_ids))

    placeholders = ",".join("?" for _ in unique_ids)
    with get_db() as conn:
        rows = conn.execute(
            CATALOGUE_SQL.format(where=f"WHERE c.product_id IN ({placeholders})"),
            unique_ids,
        ).fetchall()

    found = {r["product_id"]: ProductSummary(**row_to_summary(r)) for r in rows}
    return [found[pid] for pid in unique_ids if pid in found]


# --------------------------------------------------------------------------
# Chat history (logged-in shoppers only)
#
# Stored in the chat_messages table that shipped with the database, in the
# shape it already used: one row per turn, with the assistant's product cards
# snapshotted into products_json so a reloaded conversation still shows them.
# --------------------------------------------------------------------------

# Cap on how much of a conversation is replayed to a returning shopper.
MAX_STORED_HISTORY = 50


def save_chat_turn(
    user_id: int,
    user_message: str,
    assistant_reply: str,
    products: list[ProductSummary],
) -> None:
    """Persist one exchange. Both rows are written in a single transaction."""
    products_json = json.dumps([p.model_dump() for p in products]) if products else None

    with get_db_write() as conn:
        conn.execute(
            "INSERT INTO chat_messages (user_id, role, content, products_json) VALUES (?, ?, ?, ?)",
            (user_id, "user", user_message, None),
        )
        conn.execute(
            "INSERT INTO chat_messages (user_id, role, content, products_json) VALUES (?, ?, ?, ?)",
            (user_id, "assistant", assistant_reply, products_json),
        )


def load_chat_history(user_id: int) -> list[dict[str, Any]]:
    """Return a shopper's saved conversation, oldest first."""
    with get_db() as conn:
        rows = conn.execute(
            """
            SELECT id, role, content, products_json, created_at
            FROM chat_messages
            WHERE user_id = ?
            ORDER BY id DESC
            LIMIT ?
            """,
            (user_id, MAX_STORED_HISTORY),
        ).fetchall()

    messages = []
    for row in reversed(rows):  # DESC + LIMIT keeps the newest; flip back to reading order
        # products_json records *which* products were shown. The cards are then
        # rebuilt from the live catalogue rather than from the stored copy, for
        # two reasons: a returning shopper sees today's prices and stock rather
        # than a stale snapshot, and old rows keep working after the card shape
        # changes. The seeded rows predate two fields on ProductSummary, so
        # trusting the stored JSON made the whole history fail to load.
        product_ids = _stored_product_ids(row["products_json"])
        products = [p.model_dump() for p in get_products_by_ids(product_ids)]

        messages.append(
            {
                "id": row["id"],
                "role": row["role"],
                "content": row["content"],
                "products": products,
                "created_at": row["created_at"],
            }
        )
    return messages


def _stored_product_ids(products_json: Optional[str]) -> list[str]:
    """Pull product ids out of a stored snapshot, whatever shape it is in."""
    if not products_json:
        return []
    try:
        parsed = json.loads(products_json)
    except json.JSONDecodeError:
        # One malformed row should not break a whole conversation.
        return []
    if not isinstance(parsed, list):
        return []
    return [
        entry["product_id"]
        for entry in parsed
        if isinstance(entry, dict) and isinstance(entry.get("product_id"), str)
    ]


def clear_chat_history(user_id: int) -> int:
    """Delete a shopper's saved conversation. Returns rows removed."""
    with get_db_write() as conn:
        cursor = conn.execute("DELETE FROM chat_messages WHERE user_id = ?", (user_id,))
        return cursor.rowcount


def related_products(product_id: str, limit: int = 4) -> list[ProductSummary]:
    """Other products a shopper looking at this one would plausibly want.

    Same derived category, in stock, closest in price. Price proximity keeps a
    $32 tee from being shown next to a $98 jacket, which is the usual failure
    of naive "related items" lists.
    """
    rows, stock = catalogue_rows()
    by_id = {r["product_id"]: r for r in rows}
    target = by_id.get(product_id)
    if target is None:
        return []

    category = categorize(target["garment_type"])
    candidates = [
        r
        for r in rows
        if r["product_id"] != product_id
        and categorize(r["garment_type"]) == category
        and sizes_in_stock(r["product_id"], stock)
    ]
    candidates.sort(key=lambda r: (abs(r["price"] - target["price"]), r["name"]))
    return [ProductSummary(**row_to_summary(r)) for r in candidates[:limit]]


def find_alternatives(product_id: str, size: Optional[str] = None, limit: int = 4) -> Alternatives:
    """Similar products that are actually available, for when one is not.

    Answers the question a shopper really has when their size is gone: not
    "is it sold out" but "what else works". When a size is given, every
    suggestion is in stock in that size.
    """
    rows, stock = catalogue_rows()
    by_id = {r["product_id"]: r for r in rows}
    target = by_id.get(product_id)
    if target is None:
        return Alternatives(
            product_id=product_id,
            size=size,
            reason=f"There is no product with id '{product_id}'.",
            alternatives=[],
        )

    wanted = size.strip().upper() if size else None
    category = categorize(target["garment_type"])

    def available(row: sqlite3.Row) -> bool:
        sizes = stock.get(row["product_id"], {})
        return sizes.get(wanted, 0) > 0 if wanted else any(q > 0 for q in sizes.values())

    pool = [
        r
        for r in rows
        if r["product_id"] != product_id and available(r) and categorize(r["garment_type"]) == category
    ]
    # Nothing in the same category? Widen to the whole catalogue rather than
    # telling the shopper there is nothing at all.
    widened = False
    if not pool:
        pool = [r for r in rows if r["product_id"] != product_id and available(r)]
        widened = True

    pool.sort(key=lambda r: (abs(r["price"] - target["price"]), r["name"]))
    picks = pool[:limit]

    if not picks:
        reason = "Nothing else in the catalogue is available in that size either."
    elif widened:
        reason = (
            f"No other {category.lower()} are available"
            + (f" in {wanted}" if wanted else "")
            + ", so these are the closest alternatives from the rest of the shop."
        )
    else:
        reason = (
            f"Other {category.lower()} available"
            + (f" in {wanted}" if wanted else "")
            + ", closest in price to {}.".format(target["name"])
        )

    return Alternatives(
        product_id=product_id,
        product_name=target["name"],
        size=wanted,
        reason=reason,
        alternatives=[
            AlternativeMatch(
                product_id=r["product_id"],
                name=r["name"],
                price=r["price"],
                colors=load_json_list(r["colors"]),
                sizes_in_stock=sizes_in_stock(r["product_id"], stock),
            )
            for r in picks
        ],
    )


def list_colors() -> list[str]:
    """Every colour the catalogue uses, most common first."""
    rows, _ = catalogue_rows()
    counts: dict[str, int] = {}
    for row in rows:
        for color in load_json_list(row["colors"]):
            counts[color] = counts.get(color, 0) + 1
    return [c for c, _ in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))]


def list_categories() -> list[str]:
    with get_db() as conn:
        rows = conn.execute("SELECT DISTINCT garment_type FROM catalogue").fetchall()
    return sorted({categorize(r["garment_type"]) for r in rows})


# --------------------------------------------------------------------------
# Agent tools
#
# These are what the model is allowed to call. They are deliberately narrow:
# the agent can read the catalogue and nothing else.
# --------------------------------------------------------------------------


def _match_score(tokens: list[str], haystack: str) -> int:
    """How many of the query's words appear in a product's text.

    Shoppers type phrases ("navy hoodie for the baseball team"), so matching
    the whole string as one substring would find nothing. Scoring word by word
    ranks the products that hit the most of what they asked for.
    """
    score = 0
    for token in tokens:
        singular = token[:-1] if len(token) > 3 and token.endswith("s") else token
        if token in haystack or singular in haystack:
            score += 1
    return score


def _drop_partial_matches(
    scored: list[tuple[int, str, sqlite3.Row]], token_count: int
) -> list[tuple[int, str, sqlite3.Row]]:
    """Keep only whole-query matches, when the query has any.

    Scoring word by word ranks well but counts like OR: a product scoring one
    word out of two is still a match. So `navy hoodie` returned 82 products of
    which only 27 were hoodies - everything navy scored its point - and the
    agent then truthfully relayed "82 navy hoodie matches", which is a worse
    answer than a smaller honest one. `white t-shirt` was the whole catalogue.

    So when at least one product matches every word, the partial matches are
    not what was asked for and go.

    The fallback matters as much as the rule. When nothing matches every word,
    the full list is kept. That is what a conversational ask looks like -
    "something warm for a game" has no product with "warm" in it - and
    narrowing there would answer a reasonable question with nothing. It also
    means a one-word query is untouched, since every match is already a whole
    one.
    """
    if token_count < 2 or not scored:
        return scored
    whole = [item for item in scored if item[0] == token_count]
    return whole or scored


def search_catalogue(query: str) -> SearchResults:
    """Find products matching a shopper's description.

    Matches against name, description, colors, search tags, and garment type,
    so a query can be a color, a team, a residential college, a garment type,
    or a whole sentence. Returns the best matches first, along with the true
    number of matches so a truncated list is never mistaken for a complete one.
    """
    rows, stock = catalogue_rows()
    tokens = [t for t in re.findall(r"[a-z0-9]+", query.lower()) if t not in SEARCH_STOPWORDS]

    scored: list[tuple[int, str, sqlite3.Row]] = []
    for row in rows:
        haystack = " ".join(
            [row["name"], row["description"], row["colors"], row["search_tags"], row["garment_type"]]
        ).lower()

        # An empty or all-stopword query means "show me anything".
        score = _match_score(tokens, haystack) if tokens else 1
        if score:
            scored.append((score, row["name"], row))

    # Before counting, not after: total_matches is what the agent reports and
    # what the "See all N" link promises, so it has to be the narrowed number.
    scored = _drop_partial_matches(scored, len(tokens))
    scored.sort(key=lambda item: (-item[0], item[1]))

    matches: list[CatalogueMatch] = []
    for _, _, row in scored[:MAX_SEARCH_RESULTS]:
        matches.append(
            CatalogueMatch(
                product_id=row["product_id"],
                name=row["name"],
                garment_type=row["garment_type"],
                colors=load_json_list(row["colors"]),
                price=row["price"],
                # Trimmed, not the full description. Eight full descriptions
                # per search is a lot of text for the model to carry when the
                # shopper is only choosing which product to look at next; the
                # full text is one product_details call away.
                description=short_description(row["description"], SEARCH_DESCRIPTION_CHARS),
                sizes_in_stock=sizes_in_stock(row["product_id"], stock),
            )
        )

    return SearchResults(
        query=query,
        total_matches=len(scored),
        returned=len(matches),
        truncated=len(scored) > len(matches),
        matches=matches,
    )


def _not_found(product_id: str) -> LookupFailure:
    return LookupFailure(
        product_id=product_id,
        message=(
            f"There is no product with id '{product_id}' in the catalogue. "
            "Do not describe, price, or quote stock for it."
        ),
    )


def get_product_details(product_id: str) -> ProductDetail | LookupFailure:
    """Full detail for one product, including stock for every size."""
    product = get_product(product_id)
    return product if product is not None else _not_found(product_id)


def check_size_availability(product_id: str, size: str) -> SizeAvailability | LookupFailure:
    """Whether one specific size of one specific product is in stock."""
    product = get_product(product_id)
    if product is None:
        return _not_found(product_id)

    wanted = size.strip().upper()
    match = next((s for s in product.sizes if s.size.upper() == wanted), None)
    others = [s.size for s in product.sizes if s.in_stock and s.size.upper() != wanted]

    if match is None:
        # Every product in this catalogue carries all six sizes, so this only
        # fires on a size that does not exist at all (for example "XXXL").
        message = (
            f"{product.name} is not made in size {wanted}. "
            f"It comes in {', '.join(SIZE_ORDER)}."
        )
        return SizeAvailability(
            product_id=product.product_id,
            product_name=product.name,
            size=wanted,
            size_exists=False,
            in_stock=False,
            quantity=0,
            other_sizes_in_stock=others,
            message=message,
        )

    if match.in_stock:
        message = (
            f"{product.name} is in stock in {match.size}: "
            f"{match.quantity} available at {product.price:.2f} dollars."
        )
    else:
        message = f"{product.name} is sold out in {match.size}."
        if others:
            message += f" Still in stock in {', '.join(others)}."

    return SizeAvailability(
        product_id=product.product_id,
        product_name=product.name,
        size=match.size,
        size_exists=True,
        in_stock=match.in_stock,
        quantity=match.quantity,
        other_sizes_in_stock=others,
        message=message,
    )
