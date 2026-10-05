import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import {
  fetchProduct,
  fetchRelatedProducts,
  formatPrice,
  type ProductDetail,
  type ProductSummary,
} from '../api'
import { isGradient, needsOutline, swatchFor } from '../colors'
import ProductCard from '../components/ProductCard'

export default function ProductDetailPage() {
  const { productId } = useParams<{ productId: string }>()
  const [product, setProduct] = useState<ProductDetail | null>(null)
  const [related, setRelated] = useState<ProductSummary[]>([])
  const [selectedSize, setSelectedSize] = useState<string | null>(null)
  const [selectedColor, setSelectedColor] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!productId) return
    let cancelled = false

    setIsLoading(true)
    setError(null)
    setSelectedSize(null)
    setSelectedColor(null)

    setRelated([])
    fetchRelatedProducts(productId)
      .then((result) => {
        if (!cancelled) setRelated(result)
      })
      .catch(() => {
        /* A missing suggestions strip should never block the product page. */
      })

    fetchProduct(productId)
      .then((result) => {
        if (cancelled) return
        setProduct(result)
        // Nothing to choose when the garment comes in one colour.
        if (result.colors.length === 1) setSelectedColor(result.colors[0])
      })
      .catch(() => {
        if (!cancelled) setError('We could not find that product.')
      })
      .finally(() => {
        if (!cancelled) setIsLoading(false)
      })

    return () => {
      cancelled = true
    }
  }, [productId])

  if (isLoading) {
    return (
      <div className="page">
        <p className="status-note">Loading product...</p>
      </div>
    )
  }

  if (error || !product) {
    return (
      <div className="page">
        <p className="status-note status-error">{error ?? 'Product not found.'}</p>
        <Link to="/products" className="btn btn-outline">
          Back to all products
        </Link>
      </div>
    )
  }

  const inStockSizes = product.sizes.filter((size) => size.in_stock)

  return (
    <div className="page">
      <nav className="breadcrumb" aria-label="Breadcrumb">
        <Link to="/products">Products</Link>
        <span aria-hidden="true">/</span>
        <Link to={`/products?category=${encodeURIComponent(product.category)}`}>
          {product.category}
        </Link>
        <span aria-hidden="true">/</span>
        <span className="breadcrumb-current">{product.name}</span>
      </nav>

      <div className="detail-layout">
        <div className="detail-media">
          <img src={product.image_url} alt={product.name} />
        </div>

        <div className="detail-info">
          <span className="detail-category">{product.garment_type}</span>
          <h1>{product.name}</h1>
          <p className="detail-price">{formatPrice(product.price)}</p>
          <p className="detail-description">{product.description}</p>

          <div className="detail-block">
            <h2>
              Colour{product.colors.length > 1 && <span className="muted"> &middot; choose one</span>}
            </h2>
            {/* A chooser, not a filter. Picking a colour selects the variant
                of this product, the same way picking a size does. */}
            <div className="color-row" role="group" aria-label="Choose a colour">
              {product.colors.map((color) => (
                <button
                  key={color}
                  type="button"
                  className={color === selectedColor ? 'color-button is-selected' : 'color-button'}
                  onClick={() => setSelectedColor(color)}
                  aria-pressed={color === selectedColor}
                >
                  <span
                    className={needsOutline(color) ? 'color-dot color-dot-outlined' : 'color-dot'}
                    style={
                      isGradient(swatchFor(color))
                        ? { backgroundImage: swatchFor(color) }
                        : { background: swatchFor(color) }
                    }
                    aria-hidden="true"
                  />
                  {color}
                </button>
              ))}
            </div>
          </div>

          <div className="detail-block">
            <h2>
              Sizes <span className="muted">&middot; {product.total_stock} in stock overall</span>
            </h2>
            <div className="size-row" role="group" aria-label="Select a size">
              {product.sizes.map((size) => (
                <button
                  key={size.size}
                  type="button"
                  disabled={!size.in_stock}
                  className={
                    size.size === selectedSize ? 'size-button is-selected' : 'size-button'
                  }
                  onClick={() => setSelectedSize(size.size)}
                  title={size.in_stock ? `${size.quantity} left` : 'Out of stock'}
                >
                  {size.size}
                  <small>{size.in_stock ? `${size.quantity} left` : 'Sold out'}</small>
                </button>
              ))}
            </div>
            {inStockSizes.length === 0 && (
              <p className="status-note status-error">Every size is sold out right now.</p>
            )}
          </div>

          <div className="detail-actions">
            <button
              type="button"
              className="btn btn-primary btn-lg"
              disabled={!selectedSize || !selectedColor}
            >
              {!selectedColor
                ? 'Select a colour'
                : !selectedSize
                  ? 'Select a size'
                  : `Add ${selectedColor} · ${selectedSize} to bag`}
            </button>
            <p className="muted small">Checkout is not wired up in this build.</p>
          </div>

          {product.search_tags.length > 0 && (
            <div className="detail-block">
              <h2>Tags</h2>
              {/* Each tag runs a catalogue search for that term. */}
              <ul className="pill-list">
                {product.search_tags.map((tag) => (
                  <li key={tag}>
                    <Link
                      to={`/products?search=${encodeURIComponent(tag)}`}
                      className="pill pill-quiet pill-link"
                      title={`Search for ${tag}`}
                    >
                      {tag}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </div>

      {/* Somewhere to go next. Same category, in stock, closest in price, so
          a shopper who is not sold on this one does not leave the site. */}
      {related.length > 0 && (
        <section className="related-section">
          <div className="section-head">
            <h2>More {product.category.toLowerCase()}</h2>
            <Link
              to={`/products?category=${encodeURIComponent(product.category)}`}
              className="section-link"
            >
              See all {product.category.toLowerCase()} &rarr;
            </Link>
          </div>
          <div className="product-grid">
            {related.map((item, index) => (
              <ProductCard key={item.product_id} product={item} eager index={index} />
            ))}
          </div>
        </section>
      )}
    </div>
  )
}
