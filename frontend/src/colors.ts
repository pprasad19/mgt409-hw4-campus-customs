/**
 * Colour names in the catalogue, mapped to something you can actually see.
 *
 * The catalogue uses exactly 22 colour names across all 102 products, so every
 * one is mapped by hand rather than guessed at. A shopper scanning the grid
 * can tell navy from charcoal without reading a word.
 */
const SWATCHES: Record<string, string> = {
  'navy blue': '#1b2a4a',
  navy: '#1b2a4a',
  'royal blue': '#2b4fa2',
  blue: '#2f5fa8',
  'light blue': '#a8c6e8',
  white: '#ffffff',
  ivory: '#f6f2e7',
  cream: '#f2e9d5',
  'heather gray': '#b9bcc0',
  'light gray': '#d6d8db',
  gray: '#9aa0a6',
  'dark heather gray': '#7b8085',
  'charcoal gray': '#4a4f55',
  'heather charcoal gray': '#5c6166',
  'dark heather charcoal': '#3f4448',
  black: '#1a1a1a',
  red: '#b3282d',
  'dusty coral': '#d98878',
  yellow: '#e8c547',
  gold: '#c9a227',
  green: '#2f6b4f',
  multicolor: 'linear-gradient(135deg,#b3282d 0%,#e8c547 35%,#2f6b4f 70%,#2b4fa2 100%)',
}

const FALLBACK = '#c9cdd2'

export function swatchFor(colorName: string): string {
  return SWATCHES[colorName.trim().toLowerCase()] ?? FALLBACK
}

/** True when a swatch needs a border to be visible against a pale card. */
export function needsOutline(colorName: string): boolean {
  const key = colorName.trim().toLowerCase()
  return ['white', 'ivory', 'cream', 'light gray'].includes(key)
}

export function isGradient(value: string): boolean {
  return value.startsWith('linear-gradient')
}
