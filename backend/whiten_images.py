"""Repaint product photo backdrops white.

75 of the 102 catalogue photographs arrived on a black backdrop. Against the
site's white cards that read as a mistake, so the backdrop is replaced.

The method matters, because two obvious approaches both fail:

* A flat brightness cut eats the garment. Navy fabric in shadow falls to the
  same values as the backdrop, so any threshold low enough to spare it leaves
  a dark fringe, and any threshold high enough to remove the fringe bites
  notches out of the sleeves.
* A flood fill from the border leaves the gaps between a sleeve and the body
  untouched, because they are enclosed by garment and the fill cannot reach
  them.

So the backdrop is built up in steps, each handling what the last could not:

1. Flood from the border, which takes the open backdrop.
2. Claim the grit JPEG scatters around the edge - islands of nearly-black that
   the fill stops at because they sit just above the threshold. See below.
3. Claim whatever pure black is enclosed and left over. On a typical image
   that is two sizeable regions, the gaps between a sleeve and the body, plus
   a few dozen specks of noise inside the garment itself: regions above
   MIN_REGION are backdrop and painted, the specks are left alone.
4. Creep into the narrow crevices, but only where doing so stays small.
5. Smooth, grow and feather, so an outline that arrived stepped is rounded,
   the dark halo along the edge is swallowed, and the cut is anti-aliased.

Originals are never read from disk - always from data.zip - so this can be
re-run without compounding JPEG loss.

    python backend/whiten_images.py

Why the specks have to go
-------------------------
JPEG puts ringing noise around a high-contrast edge, so the black backdrop of
these photographs is not actually black near the garment - it is littered with
flecks sitting at 17-31. The border fill stops at every one of them, and on the
most compressed photograph that leaves 436 of them, a crust of dark grit
tracing the whole silhouette. Growing the mask does not reach them and
lowering the threshold does not either, because they are above it by design.

They are removed by what they are: islands. The garment is one connected mass
of 775,103 pixels; the grit is hundreds of islands of 1-12 pixels stranded in
the backdrop, touching nothing. So any island that touches no border and stays
under SPECK is painted. Measured across the catalogue the largest island this
ever claims is 269 pixels, well under the cap, and a drawstring - which joins
the hood - is part of the garment and never a candidate.

Why the silhouette is smoothed
------------------------------
Several photographs were cut out once before, at their original size and with
a hard binary edge, so the outline arrives already stepped. Enlarging to the
master size multiplies each step. A median across the mask rounds steps off
without moving the outline; at radius 9 it claims at most 337 pixels more than
the despeckle alone on any photograph in the catalogue, which is far too
little to be a real feature and about right for a sawtooth.

Why some crevices keep a dark line
----------------------------------
A few photographs keep a thin dark line where a sleeve meets the body. Those
pixels sit at 17-40, the same range as fabric in deep shadow, and every rule
tried to claim them also claimed real garment:

* growing the backdrop through dim pixels without a limit tunnels along a
  hoodie's shadows and carves it open;
* capping that growth to a few pixels still gashes, just less;
* filling enclosed pure-black regions fills the shadow inside a hood - and
  size does not separate the two cases, because on this catalogue a hood's
  shadow measures 0.77% of the image while a genuine sleeve gap measures
  0.61%;
* requiring those regions to be narrow does not help either, since the shadow
  inside a hood is also narrow.

Nothing separates "dark backdrop in a crevice" from "dark fabric in shadow" by
colour or by shape, because on these photographs they are the same pixels.
What is kept is the bounded creep below, attempted per image and accepted only
when it removes a crevice-sized area; anything that would open up a garment
removes far more and is discarded. So some crevices are cleaned and some keep
a faint line, and no garment is ever damaged - which is the right way round.
"""

from __future__ import annotations

import io
import pathlib
import sys
import zipfile

from collections import deque

from PIL import Image, ImageChops, ImageDraw, ImageFilter

BASE_DIR = pathlib.Path(__file__).resolve().parent.parent
ZIP_PATH = BASE_DIR / "data.zip"
# Hand-corrected sources, used in place of the original where one exists.
# the-forest-school-hoodie ships as a photograph of someone wearing it, the
# only such shot in a catalogue of flat garment photography, and was edited to
# match the rest. That edit is switched off at the shop's request: the photo
# is better worn, so the original is used. The edited source is kept in
# products_edited/disabled/ and backend/remove_person.py still regenerates it,
# so moving that file back up one level restores the flat version.
EDITED = BASE_DIR / "data" / "products_edited"
DEST = BASE_DIR / "data" / "products"

BLACK = 16        # at or below this, a pixel is backdrop rather than fabric
GROW = 3          # pixels of mask dilation at master size, to swallow the halo
FEATHER = 1.6     # gaussian radius at master size; enough to anti-alias the cut
TARGET = 1200     # master width; browsers downsample crisply but upsample softly
SHARPEN = 1.12    # gentle unsharp, to recover edge definition JPEG softened

# Crevice removal is attempted per image and only kept when it stays small.
# A crevice is a few hundred pixels; a gash through a hoodie is tens of
# thousands, so the size of what a setting removes is the safety check.
CREVICE_TRIES = ((22, 3), (26, 4), (30, 5))   # (dim threshold, max creep px)
MAX_EXTRA = 0.009                              # of the image, per attempt
MIN_REGION = 400  # enclosed black at least this big is backdrop, not noise
SPECK = 1200      # an island of non-backdrop smaller than this is JPEG grit
SMOOTH = 7        # blur radius used to round a stepped outline off
WHITE = 235       # at or above this, a pixel is white backdrop rather than garment
BAND = 0.015      # how far in from an edge the margin reaches
FRAME_LEVEL = 40  # how dark a ruled border round a photograph is
FRAME_MAX = 5     # and the most of it worth cropping away

# Enclosed black is normally the gap between a sleeve and the body, and
# filling it is what clears the last dark wedges. On a few photographs it is
# instead the shadow inside a hood, and filling that cuts the garment open.
# Nothing in the pixels tells the two apart - the sizes overlap (0.77% versus
# 0.61%), both are narrow, both are pure black, and the hood shadow is
# actually *closer* to the backdrop than the real gaps are. So all 49
# affected photographs were rendered and looked at, and the ones where the
# fill does damage are listed here. Re-run the review if the catalogue changes.
NO_ENCLOSED_FILL = {
    "basic-hoodie-big-yale",
    "brooks-brothers-double-knit-full-zip-hoodie-yale",
}
SENTINEL = (255, 0, 255)
QUALITY = 96


def backdrop_mask(im: Image.Image, name: str = "") -> Image.Image | None:
    """Mask of everything that is backdrop. None if the photo is already clean."""
    w, h = im.size
    r, g, b = im.split()
    maxc = ImageChops.lighter(ImageChops.lighter(r, g), b)
    black = maxc.point(lambda v: 255 if v <= BLACK else 0)

    # 1. The outer backdrop, via a flood fill from the border.
    work = im.copy()
    px = work.load()
    step = max(1, min(w, h) // 200)
    seeds = [(x, y) for x in range(0, w, step) for y in (0, h - 1)]
    seeds += [(x, y) for y in range(0, h, step) for x in (0, w - 1)]

    filled = False
    for sx, sy in seeds:
        pr, pg, pb = px[sx, sy]
        if max(pr, pg, pb) <= BLACK:
            ImageDraw.floodfill(work, (sx, sy), SENTINEL, thresh=BLACK)
            filled = True
    if not filled:
        return None

    wr, wg, wb = work.split()
    mask: Image.Image = ImageChops.multiply(
        ImageChops.multiply(wr.point(lambda v: 255 if v == 255 else 0),
                            wg.point(lambda v: 255 if v == 0 else 0)),
        wb.point(lambda v: 255 if v == 255 else 0),
    )

    # 2. The grit JPEG leaves around the edge, which the fill stops at because
    #    it sits just above the threshold rather than at it.
    mask = _despeckle(mask)

    # 3. Enclosed pure black: the gaps between a sleeve and the body, which
    #    the border fill cannot reach.
    if name not in NO_ENCLOSED_FILL:
        mp = maxc.load()
        kp = mask.load()
        seen = bytearray(w * h)
        for start_y in range(h):
            for start_x in range(w):
                index = start_y * w + start_x
                if seen[index]:
                    continue
                if mp[start_x, start_y] > BLACK or kp[start_x, start_y]:
                    seen[index] = 1
                    continue
                queue = deque([(start_x, start_y)])
                seen[index] = 1
                region = []
                while queue:
                    x, y = queue.popleft()
                    region.append((x, y))
                    for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
                        if 0 <= nx < w and 0 <= ny < h and not seen[ny * w + nx]:
                            if mp[nx, ny] <= BLACK and not kp[nx, ny]:
                                seen[ny * w + nx] = 1
                                queue.append((nx, ny))
                if len(region) >= MIN_REGION:
                    for x, y in region:
                        kp[x, y] = 255

    # 4. Try to also claim the narrow crevices between a sleeve and the body.
    #    Those pixels sit at 17-40, the same range as fabric in deep shadow,
    #    so no fixed rule separates them. Instead each setting is tried and
    #    kept only if it removes a crevice-sized area: a setting that tunnels
    #    into a hoodie removes far more than that and is discarded.
    base_count = _count(mask)
    budget = MAX_EXTRA * w * h
    for dim_level, creep in CREVICE_TRIES:
        dim = maxc.point(lambda v, d=dim_level: 255 if v <= d else 0)
        candidate = mask
        for _ in range(creep):
            grown = ImageChops.multiply(candidate.filter(ImageFilter.MaxFilter(3)), dim)
            candidate = ImageChops.lighter(grown, candidate)
        if _count(candidate) - base_count <= budget:
            mask = candidate
        else:
            break

    # 5. Round off an outline that arrived already stepped, then grow and
    #    soften it so the cut is anti-aliased rather than staircased.
    #
    #    Blurring the mask and re-thresholding it at halfway is what does the
    #    rounding: it is a contour smooth, so it cuts the corner off a step
    #    instead of voting pixel by pixel. A median was tried first and is not
    #    strong enough - it only reaches as far as its radius, and on the
    #    smallest photograph in the catalogue the steps are wider than that.
    mask = mask.filter(ImageFilter.GaussianBlur(SMOOTH))
    mask = mask.point(lambda v: 255 if v >= 128 else 0)
    mask = mask.filter(ImageFilter.MaxFilter(2 * GROW + 1))
    mask = mask.filter(ImageFilter.GaussianBlur(FEATHER))
    return mask


def _label(mask: Image.Image):
    """Label the connected islands of un-masked pixels in one pass.

    Each row is scanned into runs and runs that overlap on adjacent rows are
    unioned, which is far cheaper than a flood fill per island: 0.1s against
    about a minute for a 1200px master.

    Returns (find, size, border, box, rows) where the arrays are indexed by
    run id, box is (left, top, right, bottom) per island, and rows holds the
    (start, end, id) runs for each row.
    """
    w, h = mask.size
    data = mask.tobytes()
    parent: list[int] = []
    size: list[int] = []
    border: list[bool] = []
    box: list[list[int]] = []

    def find(a: int) -> int:
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    def union(a: int, b: int) -> None:
        ra, rb = find(a), find(b)
        if ra == rb:
            return
        if size[ra] < size[rb]:
            ra, rb = rb, ra
        parent[rb] = ra
        size[ra] += size[rb]
        border[ra] = border[ra] or border[rb]
        ba, bb = box[ra], box[rb]
        ba[0] = min(ba[0], bb[0])
        ba[1] = min(ba[1], bb[1])
        ba[2] = max(ba[2], bb[2])
        ba[3] = max(ba[3], bb[3])

    rows: list[list[tuple[int, int, int]]] = []
    previous: list[tuple[int, int, int]] = []
    for y in range(h):
        row = data[y * w:(y + 1) * w]
        runs: list[tuple[int, int, int]] = []
        x = 0
        while x < w:
            if row[x]:                      # masked already, not a candidate
                x += 1
                continue
            start = x
            while x < w and not row[x]:
                x += 1
            index = len(parent)
            parent.append(index)
            size.append(x - start)
            border.append(start == 0 or x == w or y == 0 or y == h - 1)
            box.append([start, y, x - 1, y])
            runs.append((start, x, index))
        i = j = 0
        while i < len(previous) and j < len(runs):
            ps, pe, pi = previous[i]
            cs, ce, ci = runs[j]
            if pe > cs and ce > ps:
                union(pi, ci)
            if pe < ce:
                i += 1
            else:
                j += 1
        rows.append(runs)
        previous = runs
    return find, size, border, box, rows


def _despeckle(mask: Image.Image) -> Image.Image:
    """Claim the islands of JPEG grit stranded in the backdrop.

    An island is grit if it reaches no border and stays under SPECK; the
    garment fails both tests by orders of magnitude, so it is never a
    candidate, and a drawstring is part of the garment rather than an island.
    """
    find, size, border, _box, rows = _label(mask)
    painted = mask.load()
    for y, runs in enumerate(rows):
        for start, end, index in runs:
            root = find(index)
            if border[root] or size[root] >= SPECK:
                continue
            for x in range(start, end):
                painted[x, y] = 255
    return mask


def _clean_dust(im: Image.Image) -> Image.Image:
    """Wipe the specks of dirt sitting in the margin of a white backdrop.

    The photographs that did not arrive on black still carry a little dust,
    and a single dark pixel in a corner of the source becomes a visible smudge
    once the image is enlarged. Those specks sit against white, so the
    despeckle above cannot see them: it looks for islands inside a backdrop
    that was flood filled, and here nothing was.

    A speck is taken only if it is smaller than SPECK and sits wholly within
    BAND of an edge. Both halves are load-bearing:

    * the size rules out a garment that runs off the frame, like the hood and
      hem of basic-hoodie-big-yale, which reach the edge as one huge island;
    * the position rules out anything on the garment itself.

    Brightness cannot do this job on its own, and two stricter-looking rules
    were tried and discarded for assuming the garment is dark. Taking the
    largest dark island as the garment erased 9,183 pixels of fine print from
    yale-bowl-t-shirt; taking the bounding box of every large island still
    erased 3,909, because that shirt is cream, so its collar, cuffs and print
    are all in the top half and the box stops at the chest. A cream garment is
    lighter than WHITE and simply is not dark, so only the margin is safe
    ground.
    """
    w, h = im.size
    r, g, b = im.split()
    lightest = ImageChops.lighter(ImageChops.lighter(r, g), b)
    light = lightest.point(lambda v: 255 if v >= WHITE else 0)

    band = round(min(w, h) * BAND)
    find, size, _border, box, rows = _label(light)

    painted = im.load()
    for y, runs in enumerate(rows):
        for start, end, index in runs:
            root = find(index)
            if size[root] >= SPECK:
                continue
            left, top, right, bottom = box[root]
            in_margin = (right < band or left > w - 1 - band
                         or bottom < band or top > h - 1 - band)
            if not in_margin:
                continue
            for x in range(start, end):
                painted[x, y] = (255, 255, 255)
    return im


def _count(mask: Image.Image) -> int:
    """How many pixels the mask claims."""
    return sum(i * n for i, n in enumerate(mask.histogram())) // 255


def _upscale(im: Image.Image) -> Image.Image:
    """Bring every photo up to a common master size.

    The catalogue arrives between 450 and 900 pixels wide while the product
    page renders around 560 CSS pixels - which on any screen above 1x means
    the browser was enlarging most of them, and browsers enlarge softly.
    Giving every image a 1200px master means the browser reduces instead,
    which is always crisp.
    """
    if im.width >= TARGET:
        return im
    scale = TARGET / im.width
    return im.resize((TARGET, round(im.height * scale)), Image.LANCZOS)


def _trim_frame(im: Image.Image) -> Image.Image:
    """Cut off a thin dark border drawn around the edge of a photograph.

    One source, district-tri-blend-t-shirt-vintage-shield, arrives with a
    single black pixel ruled right around it, like a picture frame. Nothing
    else in the pipeline removes it: the border fill does claim it, but the
    ring is only two or three pixels wide once enlarged, which is thinner than
    the outline smoothing, so the smoothing hands it straight back and the
    frame survives into the finished image.

    A frame is told from a black backdrop by what sits just inside it. On a
    frame the next ring in is white; on the 45 photographs that really are
    shot on black, it is black too, and those must not be cropped.
    """
    w, h = im.size
    px = im.load()

    def dark_fraction(d: int) -> float:
        edge = ([(x, d) for x in range(d, w - d)]
                + [(x, h - 1 - d) for x in range(d, w - d)]
                + [(d, y) for y in range(d, h - d)]
                + [(w - 1 - d, y) for y in range(d, h - d)])
        if not edge:
            return 0.0
        return sum(1 for x, y in edge if max(px[x, y]) <= FRAME_LEVEL) / len(edge)

    depth = 0
    while depth < FRAME_MAX and dark_fraction(depth) > 0.85:
        depth += 1
    if not depth or dark_fraction(depth) > 0.3:
        return im                           # no frame, or a black backdrop
    return im.crop((depth, depth, w - depth, h - depth))


def _square(im: Image.Image) -> Image.Image:
    """Pad a photograph out to a square on white.

    Ten of the catalogue photographs are portrait - two of them 1200x1800 -
    and the product card is square. A portrait image in a square box is fitted
    to its height, which leaves the card's own cream showing down both sides
    and makes those products look like a different shop. Padding to square on
    white instead keeps the garment's proportions and lets the image meet the
    edges of the card like every other one.
    """
    w, h = im.size
    if w == h:
        return im
    side = max(w, h)
    square = Image.new("RGB", (side, side), (255, 255, 255))
    square.paste(im, ((side - w) // 2, (side - h) // 2))
    return square.resize((TARGET, TARGET), Image.LANCZOS)


def _sharpen(im: Image.Image) -> Image.Image:
    """Restore the edge definition JPEG removed.

    Applied to the photograph before the backdrop is cut out. Doing it after
    ran the unsharp across the mask boundary as well, which turned a smooth
    silhouette into a visibly stepped one.
    """
    return im.filter(ImageFilter.UnsharpMask(radius=1.2, percent=80, threshold=3))


def repaint(im: Image.Image, name: str = "") -> tuple[Image.Image, bool]:
    # Enlarge first, then cut. Doing it the other way round feathered the edge
    # at 568 pixels and then stretched that softness to 1200, which is what
    # made the silhouettes look blurry.
    im = _upscale(_trim_frame(im.convert("RGB")))
    mask = backdrop_mask(im, name)
    if mask is None:
        return _square(_clean_dust(_sharpen(im))), False
    out = _sharpen(im)
    out.paste(Image.new("RGB", im.size, (255, 255, 255)), (0, 0), mask)
    return _square(_clean_dust(out)), True


def main() -> int:
    if not ZIP_PATH.is_file():
        print(f"Cannot find the pristine originals at {ZIP_PATH}", file=sys.stderr)
        return 1

    repainted = 0
    with zipfile.ZipFile(ZIP_PATH) as archive:
        names = sorted(
            n for n in archive.namelist()
            if n.startswith("data/products/") and n.endswith(".jpg")
        )
        for index, name in enumerate(names, 1):
            stem = pathlib.Path(name).name
            override = EDITED / stem
            if override.is_file():
                source = Image.open(override)
            else:
                source = Image.open(io.BytesIO(archive.read(name)))
            out, did = repaint(source, pathlib.Path(name).stem)
            out.save(DEST / pathlib.Path(name).name, "JPEG", quality=QUALITY, optimize=True)
            repainted += did
            if index % 20 == 0:
                print(f"  {index}/{len(names)}")

    print(f"done: {len(names)} images, {repainted} backdrops repainted")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
