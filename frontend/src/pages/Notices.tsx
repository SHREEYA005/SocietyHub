import { useEffect, useState } from 'react'
import { api } from '../lib/api'
import type { NoticeOut } from '../lib/types'

export default function Notices() {
  const [notices, setNotices] = useState<NoticeOut[] | null>(null)

  useEffect(() => {
    api.get<NoticeOut[]>('/notices').then(setNotices).catch(() => setNotices([]))
  }, [])

  return (
    <div className="page page-narrow">
      <h1>Notice board</h1>
      <p className="page-subtitle">Announcements from the society management.</p>

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
    </div>
  )
}
