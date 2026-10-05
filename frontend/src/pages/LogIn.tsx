import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../auth/useAuth'

export default function LogIn() {
  const { logIn, user, logOut } = useAuth()
  const navigate = useNavigate()

  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)

  if (user) {
    return (
      <div className="page auth-page">
        <div className="auth-card">
          <span className="eyebrow">Signed in</span>
          <h1>You are logged in.</h1>
          <p className="lede">
            Signed in as <strong>{user.email}</strong>.
          </p>
          <div className="auth-form">
            <Link to="/products" className="btn btn-primary btn-lg btn-block">
              Go shopping
            </Link>
            <button type="button" className="btn btn-outline btn-block" onClick={logOut}>
              Log out
            </button>
          </div>
        </div>
      </div>
    )
  }

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault()
    setError(null)
    setIsSubmitting(true)
    try {
      await logIn(email, password)
      navigate('/')
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'Could not log in.')
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="page auth-page">
      <div className="auth-card">
        <span className="eyebrow">Welcome back</span>
        <h1>Log in</h1>
        <p className="lede">Sign in to pick up where you left off.</p>

        <form className="auth-form" onSubmit={handleSubmit}>
          {error && (
            <p className="form-error" role="alert">
              {error}
            </p>
          )}

          <label>
            Email
            <input
              type="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              placeholder="you@yale.edu"
              autoComplete="email"
              required
            />
          </label>

          <label>
            Password
            <input
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              autoComplete="current-password"
              required
            />
          </label>

          <button type="submit" className="btn btn-primary btn-lg btn-block" disabled={isSubmitting}>
            {isSubmitting ? 'Signing in...' : 'Log in'}
          </button>
        </form>

        <p className="auth-switch">
          New here? <Link to="/create-account">Create an account</Link>
        </p>
      </div>
    </div>
  )
}
