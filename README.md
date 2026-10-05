# Campus Customs — MGT 409 Homework 4

A Yale apparel storefront with an AI shopping assistant. React + Vite on the
front, FastAPI on the back, a PydanticAI agent on `gpt-6-luna` reaching a SQLite
catalogue of 102 products through four read-only tools.

The assistant answers from the database, never from memory: ask it how many XL
are left in a hoodie and it reads the inventory table and tells you the number.

---

## Before you start: place the data pack

**This repository deliberately contains no data.** The database and the product
photographs are the course-supplied `data.zip` for Homework 4; `.gitignore` keeps
them out of git, as the assignment requires. Unpack that zip into the project
root so it looks like this:

```
hw4/
├── data/
│   ├── campus_customs.db        <- the catalogue, inventory, users, chat history
│   └── products/                <- 102 product photographs (.jpg)
├── backend/
├── frontend/
└── output/
```

Nothing works without it: the backend reads `data/campus_customs.db` on every
request and serves `data/products/` as the product images.

**Keep `data.zip` itself in the project root too.** Step 3 below reads from it,
and it is the only copy of the untouched originals.

## Setup

### 1. Secrets

```bash
cp .env.example .env
```

Then open `.env` and fill in `PORTKEY_API_KEY`. The shop runs without it — the
catalogue, search, filters, accounts and every page work straight from the
database — but the chat assistant returns 503 and `/api/health` reports
`"agent_configured": false`.

### 2. Backend dependencies

Python 3.11 or newer (built on 3.14).

```bash
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

On macOS or Linux use `.venv/bin/python` in place of `.venv\Scripts\python.exe`
throughout.

### 3. Prepare the photographs

**Not optional if you want to see the shop as designed.** The zip holds the
photographs as they arrived: 75 of the 102 on a black backdrop, between 450 and
900 pixels, several not square. Against white product cards a black backdrop
reads as a mistake, so Problem 10 repaints it white, squares every frame and
smooths the cut-out edges. A script does that, and its output is a build
artefact rather than source, so it is not committed:

```bash
.venv\Scripts\python.exe backend\whiten_images.py
```

About a minute. It reads only from `data.zip` and overwrites `data/products/`
with 102 white-backed 1200px images, so it is safe to re-run. Skip it and the
shop still works — but every product will carry the black background that the
design problem was about.

### 4. Frontend dependencies

**Node 20.19 or newer** (or 22.12+). Built on 24. Vite 8, the React plugin and
react-router all require that version, so on Node 18 the install fails — check
with `node --version` first.

```bash
cd frontend
npm install
```

## Running it

Two processes, two terminals. **Start the backend from inside `backend/`** — it
reads its prompt from a path relative to that folder.

**Terminal 1 — backend, on port 8000:**

```bash
cd backend
../.venv/Scripts/python.exe -m uvicorn main:app --reload --port 8000
```

**Terminal 2 — frontend, on port 5173:**

```bash
cd frontend
npm run dev
```

Then open **http://localhost:5173**.

Only 5173 needs to be open in a browser: Vite proxies `/api` and `/static`
through to port 8000, so the image paths stored in the database work unchanged.

### Check it came up

```bash
curl http://localhost:8000/api/health
```

```json
{"status":"ok","database":"campus_customs.db","products":102,
 "agent_configured":true,"model":"gpt-6-luna"}
```

`"products":102` means the data pack is in the right place.
`"agent_configured":true` means the key was found.

### If `--reload` does not reload

On the machine this was built on, `uvicorn --reload` logs `Reloading...` and
then never restarts. `backend/dev.ps1` wraps the server in `watchfiles`, which
does work:

```powershell
cd backend
powershell -ExecutionPolicy Bypass -File dev.ps1
```

## Try these

| | |
| --- | --- |
| Honest stock | Ask the chat *"How many XS are left in the Basic Hoodie Big Yale, and what does it cost?"* — compare its answer with the size buttons on the product page behind it |
| Dynamic results | Ask *"What hoodies do you have?"* — product cards appear on the page itself, with a true count and a "See all" link |
| Sold out | Ask *"Is the Yale Dad Crewneck in stock in L?"* — it says no, then offers crewnecks that are in stock in L |
| Size filter | On Products, pick a size under **In stock in** — the filter lives in the URL and can be shared |
| Search anywhere | Press **Ctrl K** (or Cmd K) on any page |
| Dark mode | The half-moon in the nav bar |

## What is where

```
hw4/
├── AI_prompts.md            every prompt used to build this, problem by problem
├── requirements.txt         backend dependencies, pinned
├── .env.example             copy to .env and fill in
├── .gitignore               keeps the data pack and real secrets out of git
├── README.md                this file
│
├── backend/                 the server needs all seven .py files below
│   ├── main.py              FastAPI app: routes, auth endpoints, chat endpoint
│   ├── agent.py             the PydanticAI agent, its model and its loop limits
│   ├── tools.py             the four tools, plus catalogue and inventory access
│   ├── models.py            every Pydantic model, for tools and for the API
│   ├── prompts/
│   │   └── prompt.md        the system prompt and 25 safety rules
│   ├── audit.py             append-only log of agent activity
│   ├── auth.py              password hashing and session tokens
│   ├── env_file.py          finds the .env wherever the project is cloned
│   │
│   ├── dev.ps1              optional: a reloader that works
│   ├── whiten_images.py     the image pipeline — how the product photos were
│   ├── derive_colors.py     prepared. Not imported by the server, and they read
│   └── remove_person.py     the originals from data.zip, so they are a record of
│                            method rather than something to run from a clone.
│
├── frontend/src/
│   ├── pages/               Home, Products, ProductDetail, About, auth pages
│   ├── components/          chat widget, product cards, palette, nav, ticker
│   └── index.css            the whole design system
│
└── output/
    ├── harness.md           how the system works, and every test behind it
    ├── design.md            the design decisions and why they should sell
    ├── usability.md         the four usability improvements
    ├── app_check.html       three live checks with screenshots — open in a browser
    ├── app_check_images/
    └── audit_trail.json     what the agent actually did, one JSON object per line
```

**The agent itself is four files:** `backend/prompts/prompt.md`,
`backend/agent.py`, `backend/tools.py`, `backend/models.py`.

The three beside them are there because the assignment asks for what they do:
`auth.py` holds the password hashing and session tokens from Problem 4,
`audit.py` writes the append-only trail from Problem 12, and `env_file.py`
locates the `.env` so a clone is self-contained. The server imports all three,
so it will not start without them.

**Start with `output/harness.md`.** Its last section, *How the system works*, is
a single description of the finished build: how to run it, the model, every
field in `models.py` and why, the tools and what they can reach, the safety
rules, and every cap and limit.

## Worth knowing

- **There is no checkout.** No cart, no payment, no shipping, no order lookup.
  The assistant is told to say so rather than pretend otherwise.
- **The agent cannot read the `users` table or saved conversations.** No tool
  touches them. The only customer facts it sees are the first name and email of
  whoever is signed in, passed in by the server.
- **The agent cannot write to the database.** Every connection it uses is opened
  read-only.
- **Passwords** are stored as salted PBKDF2-HMAC-SHA256 digests, never in
  plaintext, and verified in constant time.
- **A few product photos** keep a faint dark wedge where a sleeve meets the
  body. Four ways of removing it were tried and every one damaged garments, so
  it stays. `output/harness.md` records what was tried.
