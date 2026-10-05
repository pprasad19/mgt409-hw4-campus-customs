const MESSAGES = [
  'Printed in New Haven',
  'Free pickup on Broadway',
  'Every residential college',
  'XS through XXL',
  'Student-budget pricing',
  'Ask the shop assistant anything',
]

/**
 * The thin scrolling band above the nav.
 *
 * Real storefronts open with a line about what they stand for. This carries
 * the shop's promises without taking up page space, and the motion gives the
 * top of the page a pulse before anything has loaded.
 */
export default function Ticker() {
  // Rendered twice so the loop has no visible seam.
  const reel = [...MESSAGES, ...MESSAGES]

  return (
    <div className="ticker" aria-hidden="true">
      <div className="ticker-track">
        {reel.map((message, index) => (
          <span className="ticker-item" key={index}>
            {message}
            <span className="ticker-dot">&bull;</span>
          </span>
        ))}
      </div>
    </div>
  )
}
