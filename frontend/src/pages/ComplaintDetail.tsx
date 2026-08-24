import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { api, fileUrl } from '../lib/api'
import type { ComplaintDetailOut } from '../lib/types'
import StatusBadge from '../components/StatusBadge'
import PriorityBadge from '../components/PriorityBadge'
import Timeline from '../components/Timeline'

export default function ComplaintDetail() {
  const { id } = useParams()
  const [complaint, setComplaint] = useState<ComplaintDetailOut | null>(null)
  const [error, setError] = useState('')

  useEffect(() => {
    api.get<ComplaintDetailOut>(`/complaints/${id}`)
      .then(setComplaint)
      .catch(() => setError('This complaint could not be found, or you do not have access to it.'))
  }, [id])

  if (error) return <div className="page"><div className="banner banner-error">{error}</div><Link to="/dashboard">← Back to dashboard</Link></div>
  if (!complaint) return <div className="page-loading">Loading…</div>

  const photo = fileUrl(complaint.photo_path)

  return (
    <div className="page page-narrow">
      <Link to="/dashboard" className="back-link">← Back to dashboard</Link>

      <div className="detail-header">
        <div>
          <h1>{complaint.reference_code}</h1>
          <p className="page-subtitle">{complaint.category}</p>
        </div>
        <div className="detail-badges">
          <PriorityBadge priority={complaint.priority} />
          <StatusBadge status={complaint.status} />
        </div>
      </div>

      {complaint.is_overdue && (
        <div className="banner banner-warning">This complaint is overdue — {complaint.sla_message}.</div>
      )}

      <div className="panel">
        <h2>Details</h2>
        <p className="detail-description">{complaint.description}</p>
        {photo && (
          <img src={photo} alt="Complaint attachment" className="complaint-photo" />
        )}
        <dl className="detail-grid">
          <div><dt>Raised on</dt><dd>{new Date(complaint.created_at).toLocaleString()}</dd></div>
          <div><dt>Last updated</dt><dd>{new Date(complaint.updated_at).toLocaleString()}</dd></div>
          <div><dt>Days open</dt><dd>{complaint.days_open}</dd></div>
          <div><dt>SLA</dt><dd>{complaint.sla_message}</dd></div>
        </dl>
      </div>

      <div className="panel">
        <h2>Activity timeline</h2>
        <Timeline events={complaint.history} />
      </div>
    </div>
  )
}
