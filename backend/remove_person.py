"""Turn the one worn product photo into a flat garment shot.

NOT CURRENTLY IN USE. The shop decided the photograph is better with the model
in it, so this script's output was switched off rather than deleted: it now sits
in data/products_edited/disabled/, where whiten_images.py does not look. Moving
that file back up one level turns the flat version on again. Nothing else in the
project imports this module, and the site runs without it.

It is kept because the catalogue still contains the worn photograph and this
records how the alternative was produced, which output/design.md and
output/harness.md both refer to.

Every photograph in the catalogue shows the garment on its own except
the-forest-school-hoodie, which shows someone wearing it: face and neck inside
the hood opening, a white t-shirt at the collar, and jeans below the hem. On a
grid of flat product shots it is the one card that looks like it came from a
different shop.

There is no way to synthesise a flat-lay from a worn photo, so the person is
removed instead:

* inside the hood opening, skin and the white t-shirt are replaced with the
  hood's own interior tone, sampled from the fabric just inside its edge and
  lightly dithered so it does not read as a flat patch;
* the jeans below the hem are cropped off;
* the result is re-squared on white to match the other photographs.

The replacement is written to data/products_edited/, which whiten_images.py
prefers over the original in data.zip. The original is never modified.

    python backend/remove_person.py
"""

from __future__ import annotations

import io
import pathlib
import random
import zipfile

from PIL import Image, ImageFilter

BASE_DIR = pathlib.Path(__file__).resolve().parent.parent
ZIP_PATH = BASE_DIR / "data.zip"
DEST = BASE_DIR / "data" / "products_edited"

NAME = "the-forest-school-hoodie"
OPENING = (295, 0, 505, 150)   # the hood opening, where the face and collar are
HEM_Y = 778                    # the jeans start below this
TONE_PATCH = (250, 120, 300, 200)  # hood fabric to sample the interior tone from


def looks_like_person(pixel: tuple[int, int, int]) -> bool:
    r, g, b = pixel
    skin = r > 85 and r > g + 8 and g >= b - 14
    tee = min(pixel) > 140
    return skin or tee


def main() -> int:
    with zipfile.ZipFile(ZIP_PATH) as archive:
        im = Image.open(io.BytesIO(archive.read(f"data/products/{NAME}.jpg"))).convert("RGB")

    w, h = im.size
    px = im.load()

    x0, y0, x1, y1 = TONE_PATCH
    patch = [px[x, y] for y in range(y0, y1) for x in range(x0, x1)]
    tone = tuple(sum(c[i] for c in patch) // len(patch) for i in range(3))

    mask = Image.new("L", (w, h), 0)
    mp = mask.load()
    for y in range(OPENING[1], OPENING[3]):
        for x in range(OPENING[0], OPENING[2]):
            if looks_like_person(px[x, y]):
                mp[x, y] = 255
    mask = mask.filter(ImageFilter.MaxFilter(9)).filter(ImageFilter.GaussianBlur(3))

    rnd = random.Random(7)
    fill = Image.new("RGB", (w, h))
    fp = fill.load()
    for y in range(h):
        for x in range(w):
            jitter = rnd.randint(-5, 5)
            fp[x, y] = tuple(max(0, min(255, tone[i] + jitter)) for i in range(3))

    out = im.copy()
    out.paste(fill, (0, 0), mask)
    out = out.crop((0, 0, w, HEM_Y))

    side = max(out.size)
    canvas = Image.new("RGB", (side, side), (255, 255, 255))
    canvas.paste(out, ((side - out.width) // 2, (side - out.height) // 2))

    DEST.mkdir(parents=True, exist_ok=True)
    canvas.save(DEST / f"{NAME}.jpg", "JPEG", quality=96)
    print(f"wrote {DEST / (NAME + '.jpg')}  (hood tone {tone})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
