"""Fill in colours for catalogue rows that shipped without any.

Three products - benjamin-franklin-t-shirt, berkeley-sweater-fleece-jacket and
timothy-dwight-college-crewneck - arrived as stubs: an empty colours array and
a placeholder description reading "Vision blocked; filename-based stub". On the
site that showed as a product card with no colour dots at all.

The photograph is the ground truth, so the colour is read from it: every pixel
inside the garment is matched to the nearest of the colour names the catalogue
already uses, near-identical greys are collapsed to the most common one, and
white is added only when there is a real printed area rather than a few stray
light pixels.

    python backend/derive_colors.py           # show what it would write
    python backend/derive_colors.py --apply   # write it to the database
"""

from __future__ import annotations

import collections
import json
import pathlib
import sqlite3
import sys

from PIL import Image

BASE_DIR = pathlib.Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "campus_customs.db"
PRODUCTS = BASE_DIR / "data" / "products"

# The colour names already used by the catalogue, with the hex the site shows.
PALETTE = {
    "navy blue": (27, 42, 74), "royal blue": (43, 79, 162), "blue": (47, 95, 168),
    "light blue": (168, 198, 232), "ivory": (246, 242, 231), "cream": (242, 233, 213),
    "heather gray": (185, 188, 192), "light gray": (214, 216, 219), "gray": (154, 160, 166),
    "dark heather gray": (123, 128, 133), "charcoal gray": (74, 79, 85), "black": (26, 26, 26),
    "red": (179, 40, 45), "dusty coral": (217, 136, 120), "yellow": (232, 197, 71),
    "gold": (201, 162, 39), "green": (47, 107, 79),
}

# Shades too close to call apart by eye on a small swatch.
GREYS = {"heather gray", "light gray", "gray", "dark heather gray", "charcoal gray"}

BACKDROP = 236   # at or above this on every channel, the pixel is the white backdrop
PRINT_MIN = 0.02  # white must cover this much of the garment to count as a print


def nearest(rgb: tuple[int, int, int]) -> str:
    return min(PALETTE, key=lambda k: sum((a - b) ** 2 for a, b in zip(rgb, PALETTE[k])))


def derive(path: pathlib.Path) -> list[str]:
    im = Image.open(path).convert("RGB")
    im.thumbnail((220, 220))

    counts: collections.Counter[str] = collections.Counter()
    white_in_garment = 0
    garment = 0
    for px in im.getdata():
        if min(px) >= BACKDROP:
            continue                      # backdrop, not the garment
        garment += 1
        if min(px) >= 200:
            white_in_garment += 1         # a light print on the fabric
            continue
        counts[nearest(px)] += 1

    if not counts:
        return []

    # Collapse the grey family to whichever shade dominates.
    grey_total = sum(n for c, n in counts.items() if c in GREYS)
    if grey_total:
        best_grey = max((c for c in counts if c in GREYS), key=lambda c: counts[c])
        for c in list(counts):
            if c in GREYS:
                del counts[c]
        counts[best_grey] = grey_total

    total = sum(counts.values())
    colours = [c for c, n in counts.most_common() if n / total >= 0.12][:2]

    if garment and white_in_garment / garment >= PRINT_MIN:
        colours.append("white")
    return colours


def main() -> int:
    apply = "--apply" in sys.argv
    db = sqlite3.connect(DB_PATH)
    rows = db.execute(
        "SELECT product_id, image_file_path FROM catalogue WHERE colors = '[]' OR colors IS NULL"
    ).fetchall()

    if not rows:
        print("Every product already lists at least one colour.")
        return 0

    for product_id, image_path in rows:
        colours = derive(BASE_DIR / "data" / image_path)
        print(f"  {product_id:40} -> {colours}")
        if apply:
            db.execute(
                "UPDATE catalogue SET colors = ? WHERE product_id = ?",
                (json.dumps(colours), product_id),
            )
    if apply:
        db.commit()
        print(f"\nwrote colours for {len(rows)} products")
    else:
        print(f"\n{len(rows)} products would be updated; re-run with --apply")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
