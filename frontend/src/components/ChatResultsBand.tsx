import { useEffect, useRef } from 'react'
import { Link } from 'react-router-dom'
import { useChatResults } from '../chat/useChatResults'
import ProductCard from './ProductCard'

/**
 * Products the shop agent found, rendered into the page itself.
 *
 * Uses the same ProductCard as the Products grid, so these cards behave
 * exactly like catalogue cards: clicking one opens the single-item page built
 * in Problem 3.
 */
export default function ChatResultsBand() {
  const { products, query, totalMatches, searchTerms, revision, clear } = useChatResults()
  const bandRef = useRef<HTMLElement>(null)

  // The band mounts at the top of the page. A shopper who is scrolled down
  // would otherwise never see their results appear - and worse, the inserted
  // band pushes the page content down under them. Scrolling to it makes the
  // answer visible and keeps the jump from being disorienting.
  useEffect(() => {
    if (revision === 0 || products.length === 0) return

    const band = bandRef.current
    if (!band) return

    const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches
    band.scrollIntoView({ behavior: reduceMotion ? 'auto' : 'smooth', block: 'start' })

    // Smooth scrolling is a no-op in some environments, which would leave the
    // results off-screen - the exact failure this effect exists to prevent.
    // If nothing has moved shortly after, snap instead.
    const fallback = window.setTimeout(() => {
      const rect = band.getBoundingClientRect()
      const offScreen = rect.bottom < 0 || rect.top > window.innerHeight
      if (offScreen) band.scrollIntoView({ block: 'start' })
    }, 400)

    return () => window.clearTimeout(fallback)
  }, [revision, products.length])

  if (products.length === 0) return null

  // The link uses searchTerms (what was actually searched), never the display
  // label - a heading like "Yale tailgate gear" matches nothing in the catalogue.
  const hasMore = totalMatches !== null && searchTerms !== null && totalMatches > products.length

  return (
    <section className="chat-results" ref={bandRef} aria-label="Products from your chat">
      <div className="chat-results-inner">
        <header className="chat-results-head">
          <div>
            <span className="eyebrow">From the shop assistant</span>
            <h2>
              {query ? query.charAt(0).toUpperCase() + query.slice(1) : 'Suggested for you'}
              <span className="chat-results-count">
                {hasMore
                  ? `${products.length} of ${totalMatches}`
                  : `${products.length} ${products.length === 1 ? 'item' : 'items'}`}
              </span>
            </h2>
          </div>

          <div className="chat-results-actions">
            {hasMore && (
              <Link
                to={`/products?search=${encodeURIComponent(searchTerms)}`}
                className="btn btn-outline"
              >
                See all {totalMatches}
              </Link>
            )}
            <button type="button" className="btn btn-ghost" onClick={clear}>
              Clear
            </button>
          </div>
        </header>

        <div className="product-grid">
          {products.map((product, index) => (
            <ProductCard key={product.product_id} product={product} eager={index < 8} index={index} />
          ))}
        </div>
      </div>
    </section>
  )
}
