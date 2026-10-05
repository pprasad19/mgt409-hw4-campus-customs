# Campus Customs — Usability Improvements

Four improvements made in Problem 9, after the core shop was working: two on the website
and two in the agent and backend. Each one is live in the running app, and the section
for each says where to find it.

---

## Front-end 1 — Filter the catalogue by the size you actually wear

**Where to see it:** Products page → the **"In stock in"** row beneath the category
filters. Pick XS, S, M, L, XL, or XXL.

### What it does

The catalogue has 102 products, and every product is listed in all six sizes. But **145
of the 612 size rows are at zero**. Before this change, browsing told you nothing about
whether your size existed — you picked something you liked, opened it, and only then
found out it was sold out in your size.

The filter removes that. Choosing a size shows only the products that have **at least one
unit in stock in that size**, and it combines with the category filter and the search box.
The result line spells out what you are looking at: *"21 products in Hoodies in stock in XS"*.

The filter lives in the URL (`/products?size=XS&category=Hoodies`), so it survives a
refresh, works with the browser's back button, and can be shared or bookmarked.

### Why it helps

**For the shopper:** no more opening six products to find one that comes in your size.
At XS the catalogue drops from 102 products to 75 — a quarter of the shop was never going
to work for that shopper, and now they never see it.

**For the business:** shoppers spend their time on products they can actually buy. Every
click that ends in "sold out in your size" is a chance to leave the site, and this removes
most of them.

---

## Front-end 2 — "More hoodies" suggestions on every product page

**Where to see it:** open any product, for example
`/products/basic-hoodie-big-yale`, and scroll to the bottom.

### What it does

Each product page now ends with up to four other products from the same category, each one
**in stock** and chosen as the **closest in price** to the item being viewed. The heading
names the category ("More hoodies") and links through to the full filtered list.

Price proximity is deliberate. Naive "you might also like" strips put a $98 jacket next to
a $32 t-shirt; sorting by price distance keeps the suggestions in the range the shopper has
already shown they are willing to spend.

Sold-out products are excluded, so the strip never sends anyone to a dead end.

### Why it helps

**For the shopper:** the product page used to be a cul-de-sac. If the item was not right,
the only way onward was the back button. Now the alternatives are already on screen, and
they are comparable things at a comparable price.

**For the business:** this is the standard mechanism for keeping someone browsing instead
of leaving, and it uses live stock data, so it never advertises something unbuyable.

---

## Agent 1 — A `find_alternatives` tool, so the assistant never ends on "no"

**Where to see it:** open the chat and ask
*"I want the Baseball Left Chest Crewneck in XL"* — it is sold out in XL.

### What it does

The assistant previously answered that kind of question honestly and then stopped:
"sold out in XL." True, and useless.

A fourth tool, `find_alternatives(product_id, size)`, returns up to four products that are
**actually available** — same category, closest in price, and when a size is given, every
suggestion is confirmed in stock in that exact size. The prompt now says: give the honest
no first, then the alternatives, and put them on the page as cards.

Live response:

> The Baseball Left Chest Crewneck is sold out in XL. Other crewnecks available in XL are
> Champion Mens Triumph Raglan Crew ($58), Champion Reverse Weave Crewneck ($58),
> Davenport College Crewneck ($58), and District Vit Crewneck Vintage Bulldog ($58).

All four appear as clickable product cards on the page.

It also covers products we do not carry at all. Asked for a pink hoodie — there are none —
the assistant says so and shows the hoodies that do exist.

If nothing in the same category is available, the search widens to the whole catalogue
rather than giving up.

### Why it helps

**For the shopper:** the question behind "is this in XL?" is not really about that product.
It is "can I buy a crewneck in XL from you today?" The assistant now answers the real
question in one turn instead of making them start over.

**For the business:** a sold-out item used to end the conversation. It now becomes four
alternatives at the same price point, every one of them in stock. The honesty is
unchanged — the "no" still comes first and is never softened.

---

## Agent 2 — Cheaper and faster: a catalogue cache and smaller tool payloads

**Where to see it:** any chat message. This one is invisible by design — it is the same
answers, arriving sooner and costing less.

### What it does

**A catalogue cache.** Every catalogue search used to re-read all 102 product rows and all
612 inventory rows from SQLite, and a single reply can search two or three times. The
catalogue barely changes, so it is now read once and held in memory.

| | Time |
|---|---|
| Reading the catalogue from SQLite | 2.62 ms |
| Reading it from the cache | 0.017 ms |
| | **~157× faster** |

The cache is keyed on the database file's modification time, so **any** write — a signup,
a saved chat message, a manual edit — invalidates it automatically. There is no window
where the shop can serve stale prices or stock, and nothing to remember to clear.

**Smaller tool payloads.** Search results used to hand the model the full product
description for all eight matches. The agent is choosing *which* products to show, not
writing copy, and the full text is one `product_details` call away when it actually needs
it. Descriptions in search results are now trimmed to about 90 characters.

| | Per search |
|---|---|
| Before | 3,252 characters (~813 tokens) |
| After | 2,686 characters (~671 tokens) |
| | **17% smaller** |

### Why it helps

**For the shopper:** replies come back sooner. The database work inside a turn is now
effectively free, so the only real wait is the model itself.

**For the business:** tokens are the running cost of the assistant, and this cuts roughly
a sixth off every search — on every turn, for every shopper, forever. The cache also means
traffic spikes do not multiply into database load: a hundred shoppers searching at once
read from memory, not from disk.

Neither change affects what the assistant says. Prices, stock, and product facts still come
from the same tools reading the same database.

---

## Where each improvement lives in the code

| Improvement | Files |
|---|---|
| Size filter | `backend/tools.py` (`list_products`), `backend/main.py` (`/api/products?size=`), `frontend/src/pages/Products.tsx` |
| Related products | `backend/tools.py` (`related_products`), `backend/main.py` (`/api/products/{id}/related`), `frontend/src/pages/ProductDetail.tsx` |
| `find_alternatives` | `backend/tools.py`, `backend/models.py` (`Alternatives`), `backend/agent.py`, `backend/prompts/prompt.md` |
| Cache + smaller payloads | `backend/tools.py` (`catalogue_rows`, `SEARCH_DESCRIPTION_CHARS`) |

## Verified in the running app

| Check | Result |
|---|---|
| Size filter present on Products | "In stock in" row with Any/XS/S/M/L/XL/XXL |
| Filtering by XS | 102 → 75 products, URL `?size=XS` |
| XS combined with Hoodies | 21 products, *"21 products in Hoodies in stock in XS"* |
| Related strip on a product page | "More hoodies", 4 cards, images loaded, excludes the product itself |
| Related strip links | each card opens its own product page; "See all hoodies" filters the catalogue |
| Sold-out question in chat | honest no, then 4 in-stock alternatives, shown as cards |
| Product we do not carry | says so, then shows what we do have |
| Cache | 2.62 ms → 0.017 ms, invalidates on any database write |
| Payload | 3,252 → 2,686 characters per search |
