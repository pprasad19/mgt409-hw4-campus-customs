# Campus Customs — Design

Campus Customs prints Yale apparel in New Haven. The design aims to look like
that shop — warm, a little old, confident about where it is from — rather than
like a storefront template with a crest dropped into it.

Each entry says what changed, where to see it, and why it should help a shopper
stay and buy. Implementation detail lives in `output/harness.md`.

---

## Fonts

*Where to see it: any page — headings, product names and prices.*

**Fraunces** for headings, product names and prices; **Inter** for everything
else. Fraunces is a bookish high-contrast serif that sits naturally beside the
word "Yale". Using it for prices as well as headings makes the price read as
part of the product rather than as a form field. Prices and stock counts use
tabular numerals, so digits line up down the grid instead of jittering.

**Why it sells:** a distinct typeface is the fastest signal that a shop is a
real business. Shoppers judge whether a store is trustworthy in a glance, long
before they read a word.

## Colour

*Where to see it: everywhere; the half-moon button in the nav switches themes.*

Warm paper rather than cold grey, cards in near-white, Yale navy, and **brass
as the only accent** — section labels, the rule under the active nav link, the
stripe above the footer, the low-stock badge. One accent used consistently,
instead of colour scattered about.

Brass exists in two tones deliberately. The bright tone is decorative only —
rules, stripes, badge fills — because it reaches just 3.17:1 against paper,
which fails accessibility rules for small text. Labels use a darkened tone.

Every text colour meets WCAG AA, calculated rather than eyeballed, and checked
against **both** page backgrounds, since the catalogue sits on a darker one:

| | On paper | On the catalogue page |
|---|---|---|
| Headings | 16.19 | — |
| Body copy | 6.22 | — |
| Brass labels | 5.01 | 4.52 |
| Hints, breadcrumbs, counts | 5.02 | 4.52 |
| Low-stock badge | 4.89 | — |

**A full dark theme** comes with it, on the half-moon button in the nav. Not an
inverted copy: cards sit *lighter* than the page so garments stay the brightest
thing on screen, brass is lifted so it still reads as brass rather than brown,
and the white-backed photographs are knocked back slightly so they do not
glare. Primary buttons and the chat launcher turn brass, because navy on black
has nowhere to go. It follows the visitor's own system setting on a first visit
and remembers their choice after that. Contrast was recalculated for the dark
palette rather than assumed: headings 14.93, body 9.00, small labels 6.37,
prices 9.72.

**Why it sells:** warm backgrounds flatter product photography — garments read
as fabric, not cut-outs. A single disciplined accent makes a site feel designed
rather than assembled. A lot of browsing happens late and in the dark, and a
shop that blinds someone at 1am is a shop they close. And a shopper who cannot
read the price does not buy.

## Hierarchy

*Where to see it: the catalogue page, above and around the grid.*

Display headings are much larger while body text stayed where it was, so the
jump between levels is unmistakable. Every section opens with a small
letterspaced brass label — **MADE IN NEW HAVEN**, **THE CATALOGUE**, **FROM THE
SHOP ASSISTANT** — which tells you where you are before you read the heading.
The catalogue toolbar is separated from the grid by a rule, so filters read as
controls rather than as more content.

While the catalogue loads, the grid fills with shimmering placeholder cards in
the exact shape of real ones, so the page keeps its shape and nothing jumps
when the products arrive.

**Why it sells:** a shopper scanning a page should never have to work out what
matters. Strong hierarchy is what makes a site holding 102 products still feel
quick to use. And content that shifts under a cursor is the fastest way to make
a site feel cheap — and to make someone click the wrong thing.

## Product presentation

*Where to see it: the home page, the catalogue grid, and any product page.*

- **Real garments on the front page.** The hero was three abstract rectangles
  beside the headline, on the most important screen of a clothing shop, with
  102 photographs sitting unused. It is now a collage of three real garments,
  one each from Hoodies, T-Shirts and Jackets, each linking to its product, and
  the four category tiles carry real photos behind a navy scrim. Nothing is
  hardcoded: the page takes the first product in each category, so it keeps
  working if the catalogue changes.
- **One backdrop for all 102 photos.** 75 arrived on black, which beside the 27
  white ones made the grid look like two shops stitched together. They all sit
  on white now, with the garments themselves untouched.
- **Colour you can see.** All 22 colour names map to real swatches, so a card
  shows dots instead of the words "heather gray, white, red, navy blue".
  Multicolour products get a gradient; white and cream get an outline so they
  are visible against a pale card.
- **Square photographs**, matching the source photography, so a garment is
  shown whole rather than cropped to fit.
- **Stock you cannot miss.** Sold-out items get a crimson flag, and anything
  down to its last twelve units gets a brass "Only 9 left", taken from the real
  inventory count.
- **The card behaves as one object** — the photo zooms gently on hover and a
  VIEW DETAILS bar slides up from the bottom edge. Cards fade in 45ms apart, so
  102 products arrive in a wave rather than snapping into place.
- **Colour is a chooser, not a filter.** On a product page each colour selects
  that variant, the way sizes do, and the button reads "Add navy · M to bag".
  An earlier version sent you off to every navy product in the shop, which is
  the opposite of what someone on a product page wants. The colour *filter*
  still exists on the catalogue page, for people who are browsing.
- **Tags are links**, so "baseball" on one crewneck leads to the other baseball
  pieces.
- **Three products had no colours at all**, and were showing a placeholder
  description reading "Vision blocked" on the storefront. Their colours are now
  read from the photographs themselves, and the descriptions rewritten.

**Why it sells:** colour and availability are the two things that decide
whether a garment is worth a click, and both used to require reading. A
consistent backdrop is what makes 102 items read as a catalogue rather than a
scrapbook, and it makes colour honest — a navy hoodie on black looks unlit,
while the same hoodie on white looks like the thing that arrives. "Only 9 left"
is true, and it is the kind of nudge that turns browsing into buying.

## Chat feel

*Where to see it: the Chat with us button, bottom right of every page.*

A CC avatar and a gradient header, so the panel belongs to the shop. A pulsing
green dot on the launcher. **Four quick replies** on the opening screen — *What
hoodies do you have? · Anything for my residential college? · What is in stock
in XL? · Something warm for a game* — one tap each, and gone once the
conversation starts. Three animated dots while the agent works, rather than the
word "Looking...". The panel scales up out of the launcher, and each message
rises into place.

**Why it sells:** the quick replies are the most valuable change here. An empty
chat box asks the shopper to invent a question, and most people close it
instead; four concrete openers show what the assistant can do and start a
conversation in one tap. The typing dots matter too — the agent takes a few
seconds to search, and a live indicator is the difference between "thinking"
and "broken".

## Motion

*Where to see it: the ticker above the nav; hover a category tile on the home page.*

A slow ticker above the nav carries the shop's promises. The active nav link is
underlined by a brass rule that grows from nothing. Category tiles get a brass
rule sweeping across the top on hover. The hero panels drift on a nine-second
loop. A failed login shakes.

Every animation marks a state change — something appeared, something is
loading, something is now selected. Nothing moves just to move. **All of it is
switched off under `prefers-reduced-motion`**, where visitors get the same
layout instantly, with no movement at all.

**Why it sells:** motion is what separates a page from an interface; it tells
you the site is responding to you. It also has to be optional — motion makes
some people ill, and a shop that ignores that is a shop they leave.

## Finding things fast

*Where to see it: press Ctrl K (Cmd K) on any page, on a desktop browser.*

Beyond the six areas above: **Ctrl K** (or Cmd K) anywhere opens a command
palette over the whole catalogue. The 102 products are fetched once and
filtered in the browser, so typing is instant. Arrow keys move, Enter opens,
Escape closes, and each row carries the photo, category and price. It is hidden
on phones, where there is no Ctrl key to press.

**Why it sells:** the catalogue page is for browsing. This is for the shopper
who already knows what they want — typing "branford" reaches the product in
about a second, from any page on the site.

---

## Accessibility, after a review pass

Every piece of visible text was measured against the colour actually behind it,
in both themes and at phone width. Five things were wrong, and are fixed:

- Two text colours passed on the cream page but failed on the slightly darker
  catalogue page. Both now pass on either.
- Eleven rules painted text in navy, which only reads on a light page. In dark
  mode they came out dark-on-dark: "Our story" was effectively invisible, and
  the current nav link was *darker* than the inactive links beside it.
- Dark mode had no visible focus outline on the search, sign-in and chat
  fields, so a keyboard user could not tell which box they were in.
- The page flashed light before going dark on every load.
- On a 375px phone, the whole page could be dragged sideways.

**Why it sells:** a shopper who cannot read the price, cannot find the field
they are typing in, or cannot stop the page sliding under their thumb does not
buy. The full measurements are in `output/harness.md`.
