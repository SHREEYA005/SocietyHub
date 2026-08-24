import { FormEvent, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api, ApiError } from '../lib/api'
import type { ComplaintDetailOut } from '../lib/types'

const CATEGORIES = ['Plumbing', 'Electrical', 'Elevator', 'Security', 'Housekeeping', 'Parking', 'Other']

export default function NewComplaint() {
  const navigate = useNavigate()
  const [category, setCategory] = useState(CATEGORIES[0])
  const [description, setDescription] = useState('')
  const [photo, setPhoto] = useState<File | null>(null)
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setError('')
    setSubmitting(true)
    try {
      const form = new FormData()
      form.append('category', category)
      form.append('description', description)
      if (photo) form.append('photo', photo)
      const created = await api.postForm<ComplaintDetailOut>('/complaints', form)
      navigate(`/complaints/${created.id}`, { state: { justCreated: true } })
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Could not submit your complaint. Please try again.')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="page page-narrow">
      <h1>Raise a complaint</h1>
      <p className="page-subtitle">Give the maintenance team enough detail to act quickly.</p>

      <form onSubmit={handleSubmit} className="form panel">
        <label>Category
          <select value={category} onChange={(e) => setCategory(e.target.value)}>
            {CATEGORIES.map((c) => <option key={c} value={c}>{c}</option>)}
          </select>
        </label>

        <label>
          Description
          <textarea
            required
            minLength={10}
            maxLength={4000}
            rows={6}
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Describe the issue: what's happening, where, and since when."
          />
          <span className="char-count">{description.length}/4000</span>
        </label>

        <label>Photo <span className="optional">(optional, JPEG/PNG/WebP, max 5MB)</span>
          <input
            type="file"
            accept="image/jpeg,image/png,image/webp"
            onChange={(e) => setPhoto(e.target.files?.[0] ?? null)}
          />
        </label>

        {error && <div className="form-error">{error}</div>}

        <div className="form-actions">
          <button type="button" className="btn btn-ghost" onClick={() => navigate(-1)}>Cancel</button>
          <button type="submit" className="btn btn-primary" disabled={submitting}>
            {submitting ? 'Submitting…' : 'Submit complaint'}
          </button>
        </div>
      </form>
    </div>
  )
}
