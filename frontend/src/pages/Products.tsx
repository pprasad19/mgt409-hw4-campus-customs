import { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { fetchCategories, fetchProducts, type ProductSummary } from '../api'
import { swatchFor } from '../colors'
import ProductCard from '../components/ProductCard'

const SIZES = ['Any', 'XS', 'S', 'M', 'L', 'XL', 'XXL']

export default function Products() {
  const [searchParams, setSearchParams] = useSearchParams()
  const category = searchParams.get('category') ?? 'All'
  const search = searchParams.get('search') ?? ''
  const size = searchParams.get('size') ?? 'Any'
  const color = searchParams.get('color') ?? ''

  const [draftSearch, setDraftSearch] = useState(search)
  const [categories, setCategories] = useState<string[]>([])
  const [products, setProducts] = useState<ProductSummary[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchCategories()
      .then(setCategories)
      .catch(() => setCategories([]))
  }, [])

  useEffect(() => {
    setDraftSearch(search)
  }, [search])

  useEffect(() => {
    let cancelled = false
    setIsLoading(true)
    setError(null)

    fetchProducts({ search, category, size, color })
      .then((result) => {
        if (!cancelled) setProducts(result)
      })
      .catch(() => {
        if (!cancelled) setError('Could not load products. Is the backend running on port 8000?')
      })
      .finally(() => {
        if (!cancelled) setIsLoading(false)
      })

    return () => {
      cancelled = true
    }
  }, [search, category, size, color])

  function updateParams(next: { category?: string; search?: string; size?: string; color?: string }) {
    const params = new URLSearchParams(searchParams)
    for (const [key, value] of Object.entries(next)) {
      if (!value || value === 'All' || value === 'Any') {
        params.delete(key)
      } else {
        params.set(key, value)
      }
    }
    setSearchParams(params)
  }

  return (
    <div className="page">
      <header className="page-head">
        <span className="eyebrow">The Catalogue</span>
        <h1>Products</h1>
        <p className="lede">
          Everything we print, in one place. Filter by style or search for a color, a team, or a
          residential college.
        </p>
      </header>

      <div className="toolbar">
        <form
          className="search-form"
          onSubmit={(event) => {
            event.preventDefault()
            updateParams({ search: draftSearch })
          }}
        >
          <input
            type="search"
            value={draftSearch}
            onChange={(event) => setDraftSearch(event.target.value)}
            placeholder="Search navy, hockey, Branford..."
            aria-label="Search products"
          />
          <button type="submit" className="btn btn-primary">
            Search
          </button>
        </form>

        <div className="chip-row" role="group" aria-label="Filter by category">
          {['All', ...categories].map((option) => (
            <button
              key={option}
              type="button"
              className={option === category ? 'chip is-active' : 'chip'}
              onClick={() => updateParams({ category: option })}
            >
              {option}
            </button>
          ))}
        </div>

        {color && (
          <div className="active-filters">
            <span className="chip-row-label">Colour</span>
            <button
              type="button"
              className="chip chip-dismiss is-active"
              onClick={() => updateParams({ color: '' })}
              title="Clear colour filter"
            >
              <span className="pill-dot" style={{ background: swatchFor(color) }} aria-hidden="true" />
              {color}
              <span className="chip-x" aria-hidden="true">×</span>
            </button>
          </div>
        )}

        {/* Size filter: shows only products actually in stock in that size,
            so a shopper never opens a product to find their size is gone. */}
        <div className="chip-row size-filter" role="group" aria-label="Filter by size in stock">
          <span className="chip-row-label">In stock in</span>
          {SIZES.map((option) => (
            <button
              key={option}
              type="button"
              className={option === size ? 'chip is-active' : 'chip'}
              onClick={() => updateParams({ size: option })}
            >
              {option}
            </button>
          ))}
        </div>
      </div>

      {isLoading && (
        /* Skeletons rather than a spinner: the page keeps its shape while the
           catalogue loads, so nothing jumps when the products arrive. */
        <div className="product-grid" aria-hidden="true">
          {Array.from({ length: 8 }).map((_, index) => (
            <div className="skeleton-card" key={index}>
              <div className="skeleton-image" />
              <div className="skeleton-lines">
                <span className="skeleton-line skeleton-line-sm" />
                <span className="skeleton-line" />
                <span className="skeleton-line skeleton-line-md" />
              </div>
            </div>
          ))}
        </div>
      )}
      {error && <p className="status-note status-error">{error}</p>}

      {!isLoading && !error && (
        <>
          <p className="result-count">
            {products.length} {products.length === 1 ? 'product' : 'products'}
            {category !== 'All' && ` in ${category}`}
            {size !== 'Any' && ` in stock in ${size}`}
            {color && ` in ${color}`}
            {search && ` matching "${search}"`}
          </p>

          {products.length === 0 ? (
            <p className="status-note">
              Nothing matched that. Try a broader search, or clear the filters.
            </p>
          ) : (
            <div className="product-grid">
              {products.map((product, index) => (
                <ProductCard
                  key={product.product_id}
                  product={product}
                  eager={index < 8}
                  index={index}
                />
              ))}
            </div>
          )}
        </>
      )}
    </div>
  )
}
