"""Pydantic and PydanticAI structured types for Campus Customs.

Shared by the REST routes in main.py, the agent tools in tools.py, and the agent
itself in agent.py, so the shape of a product is defined in exactly one place.
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field

# --------------------------------------------------------------------------
# Catalogue
# --------------------------------------------------------------------------


class SizeStock(BaseModel):
    size: str
    quantity: int
    in_stock: bool


class ProductSummary(BaseModel):
    """A product card: enough to render a tile or a chat suggestion."""

    product_id: str
    name: str
    garment_type: str
    category: str
    short_description: str
    colors: list[str]
    price: float
    image_url: str
    total_stock: int


class ProductDetail(ProductSummary):
    """Everything on the single-item page."""

    description: str
    search_tags: list[str]
    sizes: list[SizeStock]


# --------------------------------------------------------------------------
# Agent tool results
#
# These are what the model actually sees. They stay small and plain so the
# agent is not handed fields it has no use for.
# --------------------------------------------------------------------------


class CatalogueMatch(BaseModel):
    """One search hit, as returned to the agent.

    Carries price and the list of sizes currently in stock so the agent can
    answer "what do you have" without a second lookup per product. Exact
    quantities are deliberately left out - those come from SizeAvailability,
    which is scoped to the one size a shopper actually asked about.
    """

    product_id: str
    name: str
    garment_type: str
    colors: list[str]
    price: float
    description: str
    sizes_in_stock: list[str]


class SearchResults(BaseModel):
    """A page of search hits, plus how many there really were.

    Search is capped so a broad query cannot flood the model's context. Without
    `total_matches` the agent cannot tell a complete answer from a truncated
    one, and will describe 8 hoodies as if they were the only 8 in the shop.
    """

    query: str
    total_matches: int
    returned: int
    truncated: bool
    matches: list[CatalogueMatch]


class AlternativeMatch(BaseModel):
    """One suggested substitute, trimmed to what the agent needs to pitch it."""

    product_id: str
    name: str
    price: float
    colors: list[str]
    sizes_in_stock: list[str]


class Alternatives(BaseModel):
    """What to offer when the thing a shopper wants is not available."""

    product_id: str
    product_name: Optional[str] = None
    size: Optional[str] = None
    reason: str = Field(description="Plain sentence explaining what these are.")
    alternatives: list[AlternativeMatch] = Field(default_factory=list)


class LookupFailure(BaseModel):
    """Returned when a product id does not exist.

    An explicit failure object rather than null: it gives the agent a sentence
    it can relay, and makes "I have no data for this" impossible to mistake for
    "the data was empty".
    """

    found: bool = False
    product_id: str
    message: str


class SizeAvailability(BaseModel):
    """Answer to 'do you have this in medium?'

    Includes `quantity` straight from the inventory row and a ready-made
    `message`, so the agent restates a fact rather than composing one. Also
    lists the other sizes that are in stock, which is the natural follow-up
    when the requested size is gone.
    """

    found: bool = True
    product_id: str
    product_name: str
    size: str
    size_exists: bool = Field(description="False when the product is not made in this size.")
    in_stock: bool
    quantity: int
    other_sizes_in_stock: list[str]
    message: str = Field(description="Plain sentence the agent can relay to the shopper.")


# --------------------------------------------------------------------------
# Chat
# --------------------------------------------------------------------------


class ChatTurn(BaseModel):
    """One prior message, replayed so follow-ups like 'in pink?' resolve."""

    role: str
    content: str


class PageContext(BaseModel):
    """Where the shopper is on the site when they send a message.

    This is what lets "do you have this in pink?" resolve: on a product page
    the website reports which product is open, so "this" has a referent even
    though the shopper never named it.
    """

    path: Optional[str] = Field(default=None, description="Route, e.g. /products/branford-1-4-zip")
    product_id: Optional[str] = Field(
        default=None, description="Set when the shopper is viewing one product."
    )


class ChatRequest(BaseModel):
    message: str
    history: list[ChatTurn] = Field(
        default_factory=list,
        description="Earlier turns from this conversation, oldest first.",
    )
    page: Optional[PageContext] = None


class StoredMessage(BaseModel):
    """One saved turn, as replayed to a returning shopper."""

    id: int
    role: str
    content: str
    products: list[ProductSummary] = Field(default_factory=list)
    created_at: str


class ChatHistoryResponse(BaseModel):
    messages: list[StoredMessage] = Field(default_factory=list)


class AgentReply(BaseModel):
    """Structured output the agent is asked to produce.

    This is the agent's half of the contract with the website: prose for the
    chat bubble, plus the ids of the products the page should display as cards.
    """

    reply: str = Field(description="What to say to the shopper, in the Campus Customs voice.")
    product_ids: list[str] = Field(
        default_factory=list,
        description="product_id values to show as cards. Only ids returned by a tool.",
    )
    search_query: Optional[str] = Field(
        default=None,
        description=(
            "Short label for what these products are, e.g. 'hoodies' or "
            "'navy baseball gear'. Shown as the heading above the cards. "
            "Leave null when returning no products."
        ),
    )
    search_terms: Optional[str] = Field(
        default=None,
        description=(
            "The exact query string you passed to search_products. Not a "
            "description - the literal words you searched, e.g. 'hoodie'. The "
            "page re-runs this search to offer a link to the rest of the "
            "matches. Leave null if you did not search."
        ),
    )


class ChatResponse(BaseModel):
    """What the website receives.

    `products` are full product cards resolved from the agent's `product_ids`
    against the catalogue, so the page never has to look anything up itself and
    a card can only exist for a real product.
    """

    reply: str
    products: list[ProductSummary] = Field(default_factory=list)
    search_query: Optional[str] = None
    # Both server-computed. search_terms is only passed through once it has
    # been shown to actually return more products than are already on screen,
    # so a "See all" link can never promise results the page will not show.
    search_terms: Optional[str] = None
    total_matches: Optional[int] = None


# --------------------------------------------------------------------------
# Auth
# --------------------------------------------------------------------------


class RegisterRequest(BaseModel):
    first_name: str
    last_name: str
    email: str
    password: str
    confirm_password: Optional[str] = None


class LoginRequest(BaseModel):
    email: str
    password: str


class PublicUser(BaseModel):
    """Everything the API is willing to say about a user. Never the hash."""

    id: int
    first_name: Optional[str]
    last_name: Optional[str]
    name: str
    email: str
    created_at: str


class AuthResponse(BaseModel):
    token: str
    user: PublicUser
