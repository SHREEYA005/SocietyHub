import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../lib/api'
import type { DashboardOut } from '../lib/types'

export default function AdminDashboard() {
  const [data, setData] = useState<DashboardOut | null>(null)
  const [error, setError] = useState('')

  useEffect(() => {
    api.get<DashboardOut>('/admin/dashboard')
      .then(setData)
      .catch(() => setError('Could not load the dashboard right now. Please refresh.'))
  }, [])

  if (error) return <div className="page"><div className="banner banner-error">{error}</div></div>
  if (!data) return <div className="page-loading">Loading…</div>

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <h1>Admin dashboard</h1>
          <p className="page-subtitle">
            Overdue threshold: {data.overdue_threshold_days} day{data.overdue_threshold_days !== 1 ? 's' : ''}
          </p>
        </div>
        <Link to="/admin/complaints" className="btn btn-primary">View all complaints</Link>
      </div>

      <div className="stat-grid">
        <StatCard label="Total complaints" value={data.total_complaints} />
        <StatCard label="Open" value={data.open_count} tone="open" />
        <StatCard label="In progress" value={data.in_progress_count} tone="progress" />
        <StatCard label="Resolved" value={data.resolved_count} tone="resolved" />
        <StatCard label="Overdue" value={data.overdue_count} tone="overdue" />
      </div>

      {data.overdue_count > 0 && (
        <div className="banner banner-warning">
          {data.overdue_count} overdue complaint{data.overdue_count !== 1 ? 's' : ''}
          {data.overdue_high_priority_count > 0 && (
            <> — {data.overdue_high_priority_count} {data.overdue_high_priority_count !== 1 ? 'are' : 'is'} high priority</>
          )}
          . <Link to="/admin/complaints?overdue_only=true">Review now →</Link>
        </div>
      )}

      <div className="split-layout">
        <section className="panel">
          <h2>Complaints by category</h2>
          <BarList data={data.by_category} />
        </section>
        <section className="panel">
          <h2>Complaints by priority</h2>
          <BarList data={data.by_priority} order={['HIGH', 'MEDIUM', 'LOW']} />
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

function BarList({ data, order }: { data: Record<string, number>; order?: string[] }) {
  const entries = order
    ? order.filter((k) => k in data).map((k) => [k, data[k]] as const)
    : Object.entries(data).sort((a, b) => b[1] - a[1])
  const max = Math.max(1, ...entries.map(([, v]) => v))

  if (entries.length === 0) return <p className="empty-state">No data yet.</p>

  return (
    <div className="bar-list">
      {entries.map(([label, value]) => (
        <div className="bar-row" key={label}>
          <span className="bar-label">{label}</span>
          <div className="bar-track">
            <div className="bar-fill" style={{ width: `${(value / max) * 100}%` }} />
          </div>
          <span className="bar-value">{value}</span>
        </div>
      ))}
    </div>
  )
}
