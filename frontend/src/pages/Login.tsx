import { FormEvent, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../lib/AuthContext'
import { ApiError } from '../lib/api'

export default function Login() {
  const { login, user } = useAuth()
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setError('')
    setSubmitting(true)
    try {
      await login(email, password)
      navigate('/')
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Something went wrong. Please try again.')
    } finally {
      setSubmitting(false)
    }
  }

  if (user) navigate(user.role === 'admin' ? '/admin' : '/dashboard')

  return (
    <div className="auth-page">
      <div className="auth-card">
        <h1 className="auth-brand">SocietyHub</h1>
        <p className="auth-subtitle">Sign in to manage your society's maintenance requests.</p>
        <form onSubmit={handleSubmit} className="form">
          <label>Email
            <input type="email" required value={email} onChange={(e) => setEmail(e.target.value)} placeholder="you@example.com" />
          </label>
          <label>Password
            <input type="password" required value={password} onChange={(e) => setPassword(e.target.value)} placeholder="••••••••" />
          </label>
          {error && <div className="form-error">{error}</div>}
          <button className="btn btn-primary" type="submit" disabled={submitting}>
            {submitting ? 'Signing in…' : 'Sign in'}
          </button>
        </form>
        <p className="auth-switch">
          New here? <Link to="/register">Create a resident account</Link>
        </p>
        <div className="demo-hint">
          <strong>Demo credentials</strong>
          <div>Admin: admin@societyhub.dev / AdminPass123!</div>
          <div>Resident: arjun.mehta@societyhub.dev / ResidentPass123!</div>
        </div>
      </div>
    </div>
  )
}
