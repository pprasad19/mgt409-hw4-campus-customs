import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../auth/useAuth'

const MIN_PASSWORD_LENGTH = 8

export default function CreateAccount() {
  const { signUp, user, logOut } = useAuth()
  const navigate = useNavigate()

  const [form, setForm] = useState({
    firstName: '',
    lastName: '',
    email: '',
    password: '',
    confirmPassword: '',
  })
  const [error, setError] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)

  const passwordsMatch =
    form.confirmPassword.length === 0 || form.password === form.confirmPassword

  function update(field: keyof typeof form) {
    return (event: React.ChangeEvent<HTMLInputElement>) =>
      setForm((prev) => ({ ...prev, [field]: event.target.value }))
  }

  if (user) {
    return (
      <div className="page auth-page">
        <div className="auth-card">
          <span className="eyebrow">Signed in</span>
          <h1>You already have an account.</h1>
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

    if (form.password !== form.confirmPassword) {
      setError('Passwords do not match.')
      return
    }
    if (form.password.length < MIN_PASSWORD_LENGTH) {
      setError(`Password must be at least ${MIN_PASSWORD_LENGTH} characters.`)
      return
    }

    setIsSubmitting(true)
    try {
      await signUp({
        first_name: form.firstName,
        last_name: form.lastName,
        email: form.email,
        password: form.password,
        confirm_password: form.confirmPassword,
      })
      navigate('/')
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'Could not create the account.')
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="page auth-page">
      <div className="auth-card">
        <span className="eyebrow">Join the shop</span>
        <h1>Create an account</h1>
        <p className="lede">Save your sizes and keep your conversations with the assistant.</p>

        <form className="auth-form" onSubmit={handleSubmit}>
          {error && (
            <p className="form-error" role="alert">
              {error}
            </p>
          )}

          <div className="field-row">
            <label>
              First name
              <input type="text" value={form.firstName} onChange={update('firstName')} required />
            </label>
            <label>
              Last name
              <input type="text" value={form.lastName} onChange={update('lastName')} required />
            </label>
          </div>

          <label>
            Email
            <input
              type="email"
              value={form.email}
              onChange={update('email')}
              placeholder="you@yale.edu"
              autoComplete="email"
              required
            />
          </label>

          <label>
            Password
            <input
              type="password"
              value={form.password}
              onChange={update('password')}
              autoComplete="new-password"
              minLength={MIN_PASSWORD_LENGTH}
              required
            />
            <small className="field-hint">At least {MIN_PASSWORD_LENGTH} characters.</small>
          </label>

          <label>
            Confirm password
            <input
              type="password"
              value={form.confirmPassword}
              onChange={update('confirmPassword')}
              autoComplete="new-password"
              aria-invalid={!passwordsMatch}
              required
            />
            {!passwordsMatch && <small className="field-hint is-error">Passwords do not match.</small>}
          </label>

          <button type="submit" className="btn btn-primary btn-lg btn-block" disabled={isSubmitting}>
            {isSubmitting ? 'Creating account...' : 'Create account'}
          </button>
        </form>

        <p className="auth-switch">
          Already have an account? <Link to="/login">Log in</Link>
        </p>
      </div>
    </div>
  )
}
