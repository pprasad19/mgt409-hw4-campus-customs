import { Link } from 'react-router-dom'
import { formatPrice, type ProductSummary } from '../api'
import ColorSwatches from './ColorSwatches'

interface ProductCardProps {
  product: ProductSummary
  /** Above-the-fold cards load eagerly so the grid paints without a scroll. */
  eager?: boolean
  /** Position in the grid, used to stagger the reveal. */
  index?: number
}

/** Below this, the shop is nearly out and the shopper deserves a nudge. */
const LOW_STOCK_THRESHOLD = 12

export default function ProductCard({ product, eager = false, index = 0 }: ProductCardProps) {
  const soldOut = product.total_stock === 0
  const lowStock = !soldOut && product.total_stock <= LOW_STOCK_THRESHOLD

  return (
    <Link
      to={`/products/${product.product_id}`}
      className="product-card"
      // Cards fade in one after another rather than all at once. Capped so a
      // 102-product grid does not take a visible age to appear.
      style={{ animationDelay: `${Math.min(index, 11) * 45}ms` }}
    >
      <div className="product-card-image">
        <img src={product.image_url} alt={product.name} loading={eager ? 'eager' : 'lazy'} />
        {soldOut && <span className="stock-flag">Sold out</span>}
        {lowStock && <span className="stock-flag stock-flag-low">Only {product.total_stock} left</span>}
        <span className="product-card-peek">View details</span>
      </div>
      <div className="product-card-body">
        <span className="product-card-category">{product.category}</span>
        <h3 className="product-card-name">{product.name}</h3>
        <p className="product-card-description">{product.short_description}</p>
        <div className="product-card-foot">
          <span className="product-card-price">{formatPrice(product.price)}</span>
          <ColorSwatches colors={product.colors} />
        </div>
      </div>
    </Link>
  )
}
