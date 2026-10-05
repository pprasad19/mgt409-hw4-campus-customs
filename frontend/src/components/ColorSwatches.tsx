import { isGradient, needsOutline, swatchFor } from '../colors'

/**
 * The colours a product comes in, as dots rather than a list of words.
 *
 * Scanning a grid of 102 products, colour is the fastest filter a human has.
 * Reading "heather gray, white, red, navy blue" takes a beat; seeing four dots
 * takes none.
 */
export default function ColorSwatches({
  colors,
  max = 5,
  size = 'sm',
}: {
  colors: string[]
  max?: number
  size?: 'sm' | 'lg'
}) {
  if (colors.length === 0) return null

  const shown = colors.slice(0, max)
  const extra = colors.length - shown.length

  return (
    <ul className={`swatches swatches-${size}`} aria-label={`Colours: ${colors.join(', ')}`}>
      {shown.map((color) => {
        const value = swatchFor(color)
        return (
          <li
            key={color}
            className={needsOutline(color) ? 'swatch swatch-outlined' : 'swatch'}
            style={isGradient(value) ? { backgroundImage: value } : { background: value }}
            title={color}
          />
        )
      })}
      {extra > 0 && <li className="swatch-more">+{extra}</li>}
    </ul>
  )
}
