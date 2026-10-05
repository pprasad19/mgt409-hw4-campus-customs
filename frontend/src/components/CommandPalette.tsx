import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { fetchProducts, formatPrice, type ProductSummary } from '../api'

/**
 * Press Ctrl+K (or Cmd+K) anywhere to search the whole catalogue.
 *
 * The catalogue is fetched once on first open and filtered in the browser, so
 * typing is instant - no request per keystroke. Arrow keys move, Enter opens,
 * Escape closes.
 */
export default function CommandPalette() {
  const [isOpen, setIsOpen] = useState(false)
  const [query, setQuery] = useState('')
  const [all, setAll] = useState<ProductSummary[]>([])
  const [active, setActive] = useState(0)
  const inputRef = useRef<HTMLInputElement>(null)
  const navigate = useNavigate()

  useEffect(() => {
    function onKey(event: KeyboardEvent) {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === 'k') {
        event.preventDefault()
        setIsOpen((open) => !open)
      }
      if (event.key === 'Escape') setIsOpen(false)
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [])

  useEffect(() => {
    if (!isOpen) return
    setQuery('')
    setActive(0)
    inputRef.current?.focus()
    if (all.length === 0) {
      fetchProducts().then(setAll).catch(() => setAll([]))
    }
  }, [isOpen, all.length])

  if (!isOpen) return null

  const needle = query.trim().toLowerCase()
  const results = (
    needle
      ? all.filter((p) =>
          [p.name, p.category, p.colors.join(' ')].join(' ').toLowerCase().includes(needle),
        )
      : all
  ).slice(0, 7)

  function open(product: ProductSummary) {
    setIsOpen(false)
    navigate(`/products/${product.product_id}`)
  }

  function onKeyDown(event: React.KeyboardEvent) {
    if (event.key === 'ArrowDown') {
      event.preventDefault()
      setActive((i) => Math.min(i + 1, results.length - 1))
    } else if (event.key === 'ArrowUp') {
      event.preventDefault()
      setActive((i) => Math.max(i - 1, 0))
    } else if (event.key === 'Enter' && results[active]) {
      event.preventDefault()
      open(results[active])
    }
  }

  return (
    <div className="palette-backdrop" onClick={() => setIsOpen(false)}>
      <div
        className="palette"
        role="dialog"
        aria-label="Search the catalogue"
        onClick={(event) => event.stopPropagation()}
      >
        <div className="palette-input-row">
          <span className="palette-icon" aria-hidden="true">⌕</span>
          <input
            ref={inputRef}
            value={query}
            onChange={(event) => {
              setQuery(event.target.value)
              setActive(0)
            }}
            onKeyDown={onKeyDown}
            placeholder="Search every product..."
            aria-label="Search every product"
          />
          <kbd className="palette-kbd">esc</kbd>
        </div>

        <ul className="palette-results">
          {results.map((product, index) => (
            <li key={product.product_id}>
              <button
                type="button"
                className={index === active ? 'palette-item is-active' : 'palette-item'}
                onMouseEnter={() => setActive(index)}
                onClick={() => open(product)}
              >
                <img src={product.image_url} alt="" />
                <span className="palette-item-text">
                  <strong>{product.name}</strong>
                  <small>{product.category}</small>
                </span>
                <span className="palette-item-price">{formatPrice(product.price)}</span>
              </button>
            </li>
          ))}
          {results.length === 0 && <li className="palette-empty">Nothing matches "{query}"</li>}
        </ul>

        <footer className="palette-foot">
          <span><kbd>↑</kbd><kbd>↓</kbd> move</span>
          <span><kbd>↵</kbd> open</span>
          <span>{all.length} products</span>
        </footer>
      </div>
    </div>
  )
}
