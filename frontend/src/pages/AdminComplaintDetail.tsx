import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { api, fileUrl, ApiError } from '../lib/api'
import type { ComplaintDetailOut, ComplaintStatus, ComplaintPriority } from '../lib/types'
import StatusBadge from '../components/StatusBadge'
import PriorityBadge from '../components/PriorityBadge'
import Timeline from '../components/Timeline'

const NEXT_STATUS: Record<ComplaintStatus, ComplaintStatus[]> = {
  OPEN: ['IN_PROGRESS', 'RESOLVED'],
  IN_PROGRESS: ['OPEN', 'RESOLVED'],
  RESOLVED: [],
}

export default function AdminComplaintDetail() {
  const { id } = useParams()
  const [complaint, setComplaint] = useState<ComplaintDetailOut | null>(null)
  const [error, setError] = useState('')
  const [note, setNote] = useState('')
  const [priority, setPriority] = useState<ComplaintPriority>('MEDIUM')
  const [busy, setBusy] = useState(false)
  const [toast, setToast] = useState('')

  function load() {
    api.get<ComplaintDetailOut>(`/complaints/${id}`)
      .then((c) => { setComplaint(c); setPriority(c.priority) })
      .catch(() => setError('This complaint could not be found.'))
  }

  useEffect(load, [id])

  async function changeStatus(newStatus: ComplaintStatus) {
    setBusy(true)
    setError('')
    try {
      if (complaint?.status === 'RESOLVED' && newStatus === 'OPEN') {
        if (!note.trim()) { setError('Please add a note explaining why this complaint is being reopened.'); setBusy(false); return }
        await api.patch(`/complaints/${id}/reopen`, { status: newStatus, note })
      } else {
        await api.patch(`/complaints/${id}/status`, { status: newStatus, note: note || undefined })
      }
      setNote('')
      setToast(`Status updated to ${newStatus.replace('_', ' ')}. Resident has been notified by email.`)
      load()
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Could not update status.')
    } finally {
      setBusy(false)
    }
  }

  async function changePriority() {
    if (!complaint || priority === complaint.priority) return
    setBusy(true)
    setError('')
    try {
      await api.patch(`/complaints/${id}/priority`, { priority, note: note || undefined })
      setToast(`Priority updated to ${priority}.`)
      load()
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Could not update priority.')
    } finally {
      setBusy(false)
    }
  }

  if (error && !complaint) return <div className="page"><div className="banner banner-error">{error}</div><Link to="/admin/complaints">← Back</Link></div>
  if (!complaint) return <div className="page-loading">Loading…</div>

  const photo = fileUrl(complaint.photo_path)
  const nextOptions = complaint.status === 'RESOLVED' ? ['OPEN'] : NEXT_STATUS[complaint.status]

  return (
    <div className="page page-narrow">
      <Link to="/admin/complaints" className="back-link">← Back to all complaints</Link>

      <div className="detail-header">
        <div>
          <h1>{complaint.reference_code}</h1>
          <p className="page-subtitle">{complaint.category} · Raised by {complaint.resident_name}</p>
        </div>
        <div className="detail-badges">
          <PriorityBadge priority={complaint.priority} />
          <StatusBadge status={complaint.status} />
        </div>
      </div>

      {complaint.is_overdue && (
        <div className="banner banner-warning">Overdue — {complaint.sla_message}.</div>
      )}
      {toast && <div className="banner banner-success">{toast}</div>}
      {error && <div className="banner banner-error">{error}</div>}

      <div className="panel">
        <h2>Details</h2>
        <p className="detail-description">{complaint.description}</p>
        {photo && <img src={photo} alt="Complaint attachment" className="complaint-photo" />}
        <dl className="detail-grid">
          <div><dt>Raised on</dt><dd>{new Date(complaint.created_at).toLocaleString()}</dd></div>
          <div><dt>Days open</dt><dd>{complaint.days_open}</dd></div>
          <div><dt>SLA</dt><dd>{complaint.sla_message}</dd></div>
        </dl>
      </div>

      <div className="panel">
        <h2>Manage complaint</h2>
        <label>Note <span className="optional">(shown to the resident, e.g. what was done)</span>
          <textarea rows={3} value={note} onChange={(e) => setNote(e.target.value)} placeholder="e.g. Plumber assigned, will visit tomorrow morning." />
        </label>

        <div className="manage-row">
          <div>
            <span className="manage-label">Priority</span>
            <select value={priority} onChange={(e) => setPriority(e.target.value as ComplaintPriority)}>
              <option value="LOW">Low</option>
              <option value="MEDIUM">Medium</option>
              <option value="HIGH">High</option>
            </select>
            <button className="btn btn-secondary" onClick={changePriority} disabled={busy || priority === complaint.priority}>
              Update priority
            </button>
          </div>
        </div>

        <div className="manage-row">
          <span className="manage-label">Move to</span>
          <div className="status-actions">
            {nextOptions.length === 0 && <span className="empty-state">No further transitions available.</span>}
            {nextOptions.map((s) => (
              <button key={s} className="btn btn-secondary" disabled={busy} onClick={() => changeStatus(s as ComplaintStatus)}>
                {s.replace('_', ' ')}
              </button>
            ))}
          </div>
        </div>
      </div>

      <div className="panel">
        <h2>Activity timeline</h2>
        <Timeline events={complaint.history} />
      </div>
    </div>
  )
}
