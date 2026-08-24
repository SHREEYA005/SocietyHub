import { useEffect, useMemo, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { api } from '../lib/api'
import type { ComplaintOut } from '../lib/types'
import StatusBadge from '../components/StatusBadge'
import PriorityBadge from '../components/PriorityBadge'

const CATEGORIES = ['Plumbing', 'Electrical', 'Elevator', 'Security', 'Housekeeping', 'Parking', 'Other']

export default function AdminComplaints() {
  const [params, setParams] = useSearchParams()
  const [complaints, setComplaints] = useState<ComplaintOut[] | null>(null)
  const [error, setError] = useState('')

  const category = params.get('category') || ''
  const status = params.get('status') || ''
  const priority = params.get('priority') || ''
  const overdueOnly = params.get('overdue_only') === 'true'
  const search = params.get('search') || ''

  useEffect(() => {
    const qs = new URLSearchParams()
    if (category) qs.set('category', category)
    if (status) qs.set('status', status)
    if (priority) qs.set('priority', priority)
    if (overdueOnly) qs.set('overdue_only', 'true')
    if (search) qs.set('search', search)

    api.get<ComplaintOut[]>(`/admin/complaints?${qs.toString()}`)
      .then(setComplaints)
      .catch(() => setError('Could not load complaints right now.'))
  }, [category, status, priority, overdueOnly, search])

  function updateParam(key: string, value: string) {
    const next = new URLSearchParams(params)
    if (value) next.set(key, value); else next.delete(key)
    setParams(next)
  }

  const summary = useMemo(() => {
    if (!complaints) return ''
    return `${complaints.length} complaint${complaints.length !== 1 ? 's' : ''}`
  }, [complaints])

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <h1>All complaints</h1>
          <p className="page-subtitle">{summary}</p>
        </div>
      </div>

      <div className="filter-bar">
        <input
          className="filter-search"
          placeholder="Search by reference or description…"
          defaultValue={search}
          onKeyDown={(e) => { if (e.key === 'Enter') updateParam('search', (e.target as HTMLInputElement).value) }}
        />
        <select value={category} onChange={(e) => updateParam('category', e.target.value)}>
          <option value="">All categories</option>
          {CATEGORIES.map((c) => <option key={c} value={c}>{c}</option>)}
        </select>
        <select value={status} onChange={(e) => updateParam('status', e.target.value)}>
          <option value="">All statuses</option>
          <option value="OPEN">Open</option>
          <option value="IN_PROGRESS">In Progress</option>
          <option value="RESOLVED">Resolved</option>
        </select>
        <select value={priority} onChange={(e) => updateParam('priority', e.target.value)}>
          <option value="">All priorities</option>
          <option value="HIGH">High</option>
          <option value="MEDIUM">Medium</option>
          <option value="LOW">Low</option>
        </select>
        <label className="filter-checkbox">
          <input type="checkbox" checked={overdueOnly} onChange={(e) => updateParam('overdue_only', e.target.checked ? 'true' : '')} />
          Overdue only
        </label>
      </div>

      {error && <div className="banner banner-error">{error}</div>}
      {complaints === null && !error && <p className="empty-state">Loading…</p>}
      {complaints && complaints.length === 0 && <p className="empty-state">No complaints match these filters.</p>}

      <div className="table-wrapper">
        {complaints && complaints.length > 0 && (
          <table className="table">
            <thead>
              <tr>
                <th>Reference</th>
                <th>Resident</th>
                <th>Category</th>
                <th>Priority</th>
                <th>Status</th>
                <th>SLA</th>
                <th>Raised</th>
              </tr>
            </thead>
            <tbody>
              {complaints.map((c) => (
                <tr key={c.id} className={c.is_overdue ? 'row-overdue' : ''}>
                  <td><Link to={`/admin/complaints/${c.id}`}>{c.reference_code}</Link></td>
                  <td>{c.resident_name}</td>
                  <td>{c.category}</td>
                  <td><PriorityBadge priority={c.priority} /></td>
                  <td><StatusBadge status={c.status} /></td>
                  <td className={c.is_overdue ? 'sla sla-overdue' : 'sla'}>{c.sla_message}</td>
                  <td>{new Date(c.created_at).toLocaleDateString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}
