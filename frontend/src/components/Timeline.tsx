import type { ComplaintHistoryOut } from '../lib/types'

function describeEvent(h: ComplaintHistoryOut): string {
  switch (h.event_type) {
    case 'CREATED':
      return 'Complaint created'
    case 'STATUS_CHANGE':
      return `Status changed: ${h.previous_status ?? '—'} → ${h.new_status ?? '—'}`
    case 'PRIORITY_CHANGE':
      return `Priority changed: ${h.previous_priority ?? '—'} → ${h.new_priority ?? '—'}`
    default:
      return 'Note added'
  }
}

export default function Timeline({ events }: { events: ComplaintHistoryOut[] }) {
  if (events.length === 0) {
    return <p className="empty-state">No activity yet.</p>
  }
  return (
    <ol className="timeline">
      {events.map((h) => (
        <li key={h.id} className="timeline-item">
          <div className="timeline-dot" />
          <div className="timeline-content">
            <div className="timeline-title">{describeEvent(h)}</div>
            {h.note && <div className="timeline-note">"{h.note}"</div>}
            <div className="timeline-meta">
              By {h.actor_name} · {new Date(h.created_at).toLocaleString()}
            </div>
          </div>
        </li>
      ))}
    </ol>
  )
}
