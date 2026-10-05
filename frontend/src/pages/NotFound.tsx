import { Link } from 'react-router-dom'

export default function NotFound() {
  return (
    <div className="page">
      <header className="page-head">
        <span className="eyebrow">404</span>
        <h1>That page took a different walk.</h1>
        <p className="lede">The link you followed does not lead anywhere in the shop.</p>
      </header>
      <Link to="/" className="btn btn-primary btn-lg">
        Back to the shop
      </Link>
    </div>
  )
}
