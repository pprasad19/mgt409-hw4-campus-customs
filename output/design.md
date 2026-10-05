# Campus Customs — Design

Campus Customs prints Yale apparel in New Haven. The design aims to look like
that shop — warm, a little old, confident about where it is from — rather than
like a storefront template with a crest dropped into it.

## At a glance

| Area | What changed | Why it sells |
| --- | --- | --- |
| **Fonts** | Fraunces for headings, names and prices; Inter for the interface; tabular numerals | A distinct typeface is the fastest signal a shop is a real business |
| **Colour** | Warm paper, Yale navy, brass as the single accent, plus a full dark theme | Warm backgrounds flatter garments; one disciplined accent reads as designed, not assembled |
| **Hierarchy** | Much larger display sizes, a brass eyebrow label per section, skeleton cards while loading | A shopper should never have to work out what matters |
| **Product presentation** | Real garments on the front page, one white backdrop across all 102, colour swatches, stock badges, colour as a chooser | Colour and availability decide whether a garment is worth a click, and both used to require reading |
| **Chat feel** | Avatar and gradient header, pulsing dot, four quick replies, typing dots | An empty chat box asks the shopper to invent a question; most close it instead |
| **Motion** | Ticker, growing underline, tile sweep, hero drift, login shake — all off under reduced motion | Motion tells you the site is responding, and has to be optional |

Detail below. Implementation and the accessibility measurements are in
`output/harness.md`.

---

## Fonts

*Where to see it: any page — headings, product names and prices.*

**Fraunces** for headings, product names and prices; **Inter** for everything
else. Fraunces is a bookish high-contrast serif that sits naturally beside the
word "Yale". Using it for prices as well as headings makes the price read as
part of the product rather than as a form field. Prices and stock counts use
tabular numerals, so digits line up down the grid instead of jittering.

**Why it sells:** a distinct typeface is the fastest signal that a shop is a
real business. Shoppers judge a store in a glance, long before they read a word.

## Colour

*Where to see it: everywhere; the half-moon button in the nav switches themes.*

Warm paper rather than cold grey, cards in near-white, Yale navy, and **brass
as the only accent** — section labels, the rule under the active nav link, the
stripe above the footer, the low-stock badge. Brass exists in two tones
deliberately: the bright one is decorative only, because it fails contrast rules
for small text, so labels use a darkened version.

**Every text colour meets WCAG AA**, calculated rather than eyeballed, and
checked against *both* page backgrounds since the catalogue sits on a darker one.
The figures are in `harness.md`.

**A full dark theme** comes with it. Not an inverted copy: cards sit *lighter*
than the page so garments stay the brightest thing on screen, brass is lifted so
it still reads as brass rather than brown, and the white-backed photographs are
knocked back slightly so they do not glare. Primary buttons and the chat launcher
turn brass, because navy on black has nowhere to go. It follows the visitor's
system setting on a first visit and remembers their choice after.

**Why it sells:** warm backgrounds flatter product photography — garments read
as fabric, not cut-outs. A single disciplined accent makes a site feel designed
rather than assembled. A lot of browsing happens late and in the dark, and a
shop that blinds someone at 1am is a shop they close.

## Hierarchy

*Where to see it: the catalogue page, above and around the grid.*

Display headings are much larger while body text stayed where it was, so the
jump between levels is unmistakable. Every section opens with a small
letterspaced brass label — **MADE IN NEW HAVEN**, **THE CATALOGUE**, **FROM THE
SHOP ASSISTANT** — which tells you where you are before you read the heading.
The catalogue toolbar is separated from the grid by a rule, so filters read as
controls rather than more content. While the catalogue loads, the grid fills with
shimmering placeholder cards in the exact shape of real ones, so nothing jumps
when products arrive.

**Why it sells:** strong hierarchy is what makes a site holding 102 products
still feel quick. Content that shifts under a cursor is the fastest way to make
a site feel cheap — and to make someone click the wrong thing.

## Product presentation

*Where to see it: the home page, the catalogue grid, and any product page.*

- **Real garments on the front page.** The hero was three abstract rectangles
  beside the headline — on the most important screen of a clothing shop, with
  102 photographs sitting unused. It is now a collage of three real garments,
  one each from Hoodies, T-Shirts and Jackets, and the four category tiles carry
  real photos behind a navy scrim. Nothing is hardcoded, so it survives a
  catalogue change.
- **One backdrop for all 102 photos.** 75 arrived on black, which beside the 27
  white ones made the grid look like two shops stitched together. All of them
  sit on white now, square, with the garments themselves untouched.
- **Colour and stock you can see.** All 22 colour names map to real swatches, so
  a card shows dots instead of the words "heather gray, white, red, navy blue".
  Sold-out items get a crimson flag, and anything down to its last twelve units
  gets a brass "Only 9 left", taken from the real inventory count.
- **The card behaves as one object** — the photo zooms gently on hover, a VIEW
  DETAILS bar slides up from the bottom edge, and cards fade in 45ms apart so
  102 products arrive in a wave rather than snapping into place.
- **The product page is for choosing; the catalogue is for browsing.** Each
  colour selects that variant the way sizes do, and the button reads "Add navy ·
  M to bag" — an earlier version sent you off to every navy product in the shop,
  which is the opposite of what someone on a product page wants. Tags are links,
  so "baseball" leads to the other baseball pieces, and the colour *filter*
  still lives on the catalogue page.

**Why it sells:** colour and availability decide whether a garment is worth a
click, and both used to require reading. A consistent backdrop is what makes 102
items read as a catalogue rather than a scrapbook, and it makes colour honest — a
navy hoodie on black looks unlit; on white it looks like the thing that arrives.
"Only 9 left" is true, and it is the kind of nudge that turns browsing into
buying.

## Chat feel

*Where to see it: the Chat with us button, bottom right of every page.*

A CC avatar and a gradient header, so the panel belongs to the shop. A pulsing
green dot on the launcher. **Four quick replies** on the opening screen — *What
hoodies do you have? · Anything for my residential college? · What is in stock
in XL? · Something warm for a game* — one tap each, gone once the conversation
starts. Three animated dots while the agent works, rather than the word
"Looking...". The panel scales up out of the launcher; each message rises into
place.

**Why it sells:** the quick replies are the most valuable change here. An empty
chat box asks the shopper to invent a question, and most people close it instead.
The typing dots matter too — the agent takes a few seconds to search, and a live
indicator is the difference between "thinking" and "broken".

## Motion

*Where to see it: the ticker above the nav; hover a category tile on the home page.*

A slow ticker above the nav carries the shop's promises. The active nav link is
underlined by a brass rule that grows from nothing. Category tiles get a brass
rule sweeping across on hover. The hero panels drift on a nine-second loop. A
failed login shakes. Every animation marks a state change — something appeared,
is loading, or is now selected. Nothing moves just to move, and **all of it is
switched off under `prefers-reduced-motion`**.

**Why it sells:** motion is what separates a page from an interface; it tells you
the site is responding to you. It also has to be optional — motion makes some
people ill, and a shop that ignores that is a shop they leave.

---

## Also: finding things fast

**Ctrl K** (or Cmd K) anywhere opens a command palette over the whole catalogue,
filtered in the browser so typing is instant. Hidden on phones, where there is
no Ctrl key. The catalogue page is for browsing; this is for the shopper who
already knows what they want.

## Accessibility

Every piece of visible text was measured against the colour actually behind it,
in both themes and at phone width. Five faults were found and fixed: two colours
that passed on one background but not the other, eleven rules painting text in
navy that vanished in dark mode, no visible focus outline on dark form fields, a
flash of the light page on every load, and a 375px phone that could be dragged
sideways. A shopper who cannot read the price or stop the page sliding under
their thumb does not buy. Measurements in `harness.md`.

## Leftovers from the Vite template

Three things were still the scaffolding the project was generated from, which is
the opposite of what this problem asks for:

- **The browser tab showed the Vite logo.** `public/favicon.svg` was still the
  default — a purple lightning bolt (`#863bff`) on a Yale apparel shop, visible
  on every tab and bookmark. It is now the same navy badge and CC monogram as
  the brand mark in the nav, with the brass rule under it.
- **`frontend/README.md` was the React + Vite template text**, opening "This
  template provides a minimal setup to get React working in Vite". Replaced
  with what the folder actually holds and a pointer to the project README.
- **Three unused template assets** — `react.svg`, `vite.svg` and `hero.png` —
  referenced by nothing. Removed, along with the empty folder.

The favicon is the one that mattered: a tab icon is the smallest piece of
branding a shop has, and leaving the framework's logo there undoes the point of
every other change on this page.
