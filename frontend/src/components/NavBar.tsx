import { NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../auth/useAuth'
import ThemeToggle from './ThemeToggle'

const LINKS = [
  { to: '/', label: 'Home', end: true },
  { to: '/products', label: 'Products', end: false },
  { to: '/about', label: 'About Us', end: false },
]

export default function NavBar() {
  const { user, logOut } = useAuth()
  const navigate = useNavigate()

  return (
    <header className="navbar">
      <div className="navbar-inner">
        <NavLink to="/" className="brand">
          <span className="brand-mark">CC</span>
          <span className="brand-text">
            <strong>Campus Customs</strong>
            <small>New Haven, CT</small>
          </span>
        </NavLink>

        <nav className="nav-links" aria-label="Main">
          {LINKS.map((link) => (
            <NavLink
              key={link.to}
              to={link.to}
              end={link.end}
              className={({ isActive }) => (isActive ? 'nav-link is-active' : 'nav-link')}
            >
              {link.label}
            </NavLink>
          ))}
        </nav>

        <div className="nav-actions">
          <button
            type="button"
            className="palette-hint"
            onClick={() =>
              window.dispatchEvent(
                new KeyboardEvent('keydown', { key: 'k', ctrlKey: true, bubbles: true }),
              )
            }
            aria-label="Search the catalogue"
          >
            <span aria-hidden="true">⌕</span> Search <kbd>Ctrl K</kbd>
          </button>
          <ThemeToggle />
          {user ? (
            <>
              <span className="nav-greeting">
                Hi, {user.first_name?.trim() || user.name.split(' ')[0]}
              </span>
              <button
                type="button"
                className="btn btn-ghost"
                onClick={() => {
                  logOut()
                  navigate('/')
                }}
              >
                Log Out
              </button>
            </>
          ) : (
            <>
              <NavLink to="/login" className="btn btn-ghost">
                Log In
              </NavLink>
              <NavLink to="/create-account" className="btn btn-primary">
                Create Account
              </NavLink>
            </>
          )}
        </div>
      </div>
    </header>
  )
}
