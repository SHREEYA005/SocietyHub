import { FormEvent, useEffect, useState } from 'react'
import { api, ApiError } from '../lib/api'
import type { NoticeOut } from '../lib/types'

export default function AdminNotices() {
  const [notices, setNotices] = useState<NoticeOut[] | null>(null)
  const [title, setTitle] = useState('')
  const [content, setContent] = useState('')
  const [important, setImportant] = useState(false)
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  function load() {
    api.get<NoticeOut[]>('/notices').then(setNotices).catch(() => setNotices([]))
  }
  useEffect(load, [])

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setError('')
    setSubmitting(true)
    try {
      await api.post('/notices', { title, content, is_important: important })
      setTitle(''); setContent(''); setImportant(false)
      load()
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Could not post the notice.')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="page">
      <h1>Notice board</h1>
      <p className="page-subtitle">Post announcements. Important notices are pinned and emailed to residents.</p>

      <div className="split-layout">
        <form onSubmit={handleSubmit} className="form panel">
          <h2>New notice</h2>
          <label>Title
            <input required value={title} onChange={(e) => setTitle(e.target.value)} placeholder="e.g. Water supply maintenance on Sunday" />
          </label>
          <label>Content
            <textarea required rows={5} value={content} onChange={(e) => setContent(e.target.value)} placeholder="Details residents need to know…" />
          </label>
          <label className="filter-checkbox">
            <input type="checkbox" checked={important} onChange={(e) => setImportant(e.target.checked)} />
            Mark as important (pins to top and emails all residents)
          </label>
          {error && <div className="form-error">{error}</div>}
          <button className="btn btn-primary" type="submit" disabled={submitting}>
            {submitting ? 'Posting…' : 'Post notice'}
          </button>
        </form>

        <section className="panel">
          <h2>Published notices</h2>
          {notices === null && <p className="empty-state">Loading…</p>}
          {notices && notices.length === 0 && <p className="empty-state">No notices posted yet.</p>}
          <ul className="notice-list">
            {notices?.map((n) => (
              <li key={n.id} className={n.is_important ? 'notice-card notice-important' : 'notice-card'}>
                {n.is_important && <span className="notice-pin">📌 Important</span>}
                <h3>{n.title}</h3>
                <p>{n.content}</p>
                <div className="notice-meta">{n.author_name} · {new Date(n.created_at).toLocaleString()}</div>
              </li>
            ))}
          </ul>
        </section>
      </div>
    </div>
  )
}
