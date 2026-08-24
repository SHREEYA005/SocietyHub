import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../lib/api'
import type { ComplaintOut, NoticeOut } from '../lib/types'
import StatusBadge from '../components/StatusBadge'
import PriorityBadge from '../components/PriorityBadge'
import { useAuth } from '../lib/AuthContext'

export default function ResidentDashboard() {
  const { user } = useAuth()
  const [complaints, setComplaints] = useState<ComplaintOut[] | null>(null)
  const [notices, setNotices] = useState<NoticeOut[] | null>(null)
  const [error, setError] = useState('')

  useEffect(() => {
    Promise.all([api.get<ComplaintOut[]>('/complaints'), api.get<NoticeOut[]>('/notices')])
      .then(([c, n]) => { setComplaints(c); setNotices(n) })
      .catch(() => setError('Could not load your dashboard right now. Please refresh.'))
  }, [])

  const counts = {
    total: complaints?.length ?? 0,
    open: complaints?.filter((c) => c.status === 'OPEN').length ?? 0,
    inProgress: complaints?.filter((c) => c.status === 'IN_PROGRESS').length ?? 0,
    resolved: complaints?.filter((c) => c.status === 'RESOLVED').length ?? 0,
    overdue: complaints?.filter((c) => c.is_overdue).length ?? 0,
  }

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <h1>Welcome back, {user?.name.split(' ')[0]}</h1>
          <p className="page-subtitle">Here's what's happening with your maintenance requests.</p>
        </div>
        <Link to="/complaints/new" className="btn btn-primary">Raise a complaint</Link>
      </div>

      {error && <div className="banner banner-error">{error}</div>}

      <div className="stat-grid">
        <StatCard label="Total complaints" value={counts.total} />
        <StatCard label="Open" value={counts.open} tone="open" />
        <StatCard label="In progress" value={counts.inProgress} tone="progress" />
        <StatCard label="Resolved" value={counts.resolved} tone="resolved" />
        <StatCard label="Overdue" value={counts.overdue} tone="overdue" />
      </div>

      <div className="split-layout">
        <section className="panel">
          <h2>Your complaints</h2>
          {complaints === null && <p className="empty-state">Loading…</p>}
          {complaints && complaints.length === 0 && (
            <p className="empty-state">You haven't raised any complaints yet.</p>
          )}
          <ul className="complaint-list">
            {complaints?.map((c) => (
              <li key={c.id}>
                <Link to={`/complaints/${c.id}`} className="complaint-row">
                  <div className="complaint-row-main">
                    <span className="complaint-ref">{c.reference_code}</span>
                    <span className="complaint-category">{c.category}</span>
                  </div>
                  <div className="complaint-row-meta">
                    <PriorityBadge priority={c.priority} />
                    <StatusBadge status={c.status} />
                    <span className={c.is_overdue ? 'sla sla-overdue' : 'sla'}>{c.sla_message}</span>
                  </div>
                </Link>
              </li>
            ))}
          </ul>
        </section>

        <section className="panel">
          <h2>Notice board</h2>
          {notices === null && <p className="empty-state">Loading…</p>}
          {notices && notices.length === 0 && <p className="empty-state">No notices posted yet.</p>}
          <ul className="notice-list">
            {notices?.map((n) => (
              <li key={n.id} className={n.is_important ? 'notice-card notice-important' : 'notice-card'}>
                {n.is_important && <span className="notice-pin">📌 Important</span>}
                <h3>{n.title}</h3>
                <p>{n.content}</p>
                <div className="notice-meta">{n.author_name} · {new Date(n.created_at).toLocaleDateString()}</div>
              </li>
            ))}
          </ul>
        </section>
      </div>
    </div>
  )
}

function StatCard({ label, value, tone }: { label: string; value: number; tone?: string }) {
  return (
    <div className={`stat-card ${tone ? `stat-card-${tone}` : ''}`}>
      <div className="stat-value">{value}</div>
      <div className="stat-label">{label}</div>
    </div>
  )
}
