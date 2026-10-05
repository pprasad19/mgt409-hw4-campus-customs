import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { fetchProducts, type ProductSummary } from '../api'
import ProductCard from '../components/ProductCard'

const CATEGORY_TILES = [
  { label: 'Hoodies', blurb: 'For 8am sections and 8pm libraries.' },
  { label: 'Crewnecks', blurb: 'The layer that goes with everything.' },
  { label: 'T-Shirts', blurb: 'Lightweight, year-round, everyday blue.' },
  { label: 'Jackets', blurb: 'Built for a New Haven November.' },
]

/** Categories the hero collage draws from, in order of preference. */
const HERO_CATEGORIES = ['Hoodies', 'T-Shirts', 'Jackets']

export default function Home() {
  const [products, setProducts] = useState<ProductSummary[]>([])

  // One request for the whole catalogue; the hero, the tiles and the featured
  // strip all read from it. Nothing is hardcoded, so the page keeps working
  // if the catalogue changes.
  useEffect(() => {
    fetchProducts()
      .then(setProducts)
      .catch(() => setProducts([]))
  }, [])

  const firstIn = (category: string) => products.find((p) => p.category === category)

  const heroPhotos = HERO_CATEGORIES.map(firstIn).filter(
    (p): p is ProductSummary => p !== undefined,
  )
  const featured = products.slice(0, 4)

  return (
    <div className="page home">
      <section className="hero">
        <div className="hero-copy">
          <span className="eyebrow">Made in New Haven</span>
          <h1>
            Wear the place
            <br />
            that made you.
          </h1>
          <p>
            Campus Customs prints Yale apparel for the people who actually live here - the
            suitemates, the section-mates, the sideline regulars, and the families who drive up
            for one weekend in November and talk about it all year. Soft cotton, honest prices,
            and a bulldog on the chest.
          </p>
          <div className="hero-actions">
            <Link to="/products" className="btn btn-primary btn-lg">
              Shop the catalogue
            </Link>
            <Link to="/about" className="btn btn-outline btn-lg">
              Our story
            </Link>
          </div>
        </div>

        {/* Real garments, not placeholder blocks. Each one links to its product. */}
        <div className="hero-collage">
          {heroPhotos.map((product, index) => (
            <Link
              key={product.product_id}
              to={`/products/${product.product_id}`}
              className={`hero-photo hero-photo-${index + 1}`}
              aria-label={product.name}
            >
              <img src={product.image_url} alt={product.name} />
              <span className="hero-photo-tag">{product.name}</span>
            </Link>
          ))}
        </div>
      </section>

      <section className="section">
        <div className="section-head">
          <h2>Find your layer</h2>
          <Link to="/products" className="section-link">
            See everything &rarr;
          </Link>
        </div>
        <div className="tile-grid">
          {CATEGORY_TILES.map((tile) => {
            const sample = firstIn(tile.label)
            return (
              <Link
                key={tile.label}
                to={`/products?category=${encodeURIComponent(tile.label)}`}
                className="tile"
              >
                {sample && (
                  <img className="tile-photo" src={sample.image_url} alt="" loading="lazy" />
                )}
                <span className="tile-body">
                  <h3>{tile.label}</h3>
                  <p>{tile.blurb}</p>
                  <span className="tile-cta">Browse {tile.label.toLowerCase()} &rarr;</span>
                </span>
              </Link>
            )
          })}
        </div>
      </section>

      {featured.length > 0 && (
        <section className="section">
          <div className="section-head">
            <h2>Fresh off the press</h2>
            <Link to="/products" className="section-link">
              All products &rarr;
            </Link>
          </div>
          <div className="product-grid">
            {featured.map((product, index) => (
              <ProductCard key={product.product_id} product={product} eager index={index} />
            ))}
          </div>
        </section>
      )}

      <section className="section promise-band">
        <div className="promise">
          <h3>Every college, every team</h3>
          <p>
            Branford to Pierson, baseball to fencing, Divinity to the School of Management. If
            you belong to a corner of this campus, there is something here with your name on it.
          </p>
        </div>
        <div className="promise">
          <h3>Student-budget pricing</h3>
          <p>
            Nothing in the shop runs past the price of a textbook. We would rather see the shirt
            on a hundred people than make a margin on five.
          </p>
        </div>
        <div className="promise">
          <h3>Real stock, shown plainly</h3>
          <p>
            Sizes sell out and we say so. If your size is gone, the page tells you before you get
            attached to it.
          </p>
        </div>
      </section>

      <section className="section cta-band">
        <h2>Tailgate weather is coming.</h2>
        <p>Layer up before the away crowd gets here.</p>
        <Link to="/products" className="btn btn-primary btn-lg">
          Shop now
        </Link>
      </section>
    </div>
  )
}
