import type { ComplaintStatus } from '../lib/types'

const LABELS: Record<ComplaintStatus, string> = {
  OPEN: 'Open',
  IN_PROGRESS: 'In Progress',
  RESOLVED: 'Resolved',
}

export default function StatusBadge({ status }: { status: ComplaintStatus }) {
  return <span className={`badge badge-status-${status.toLowerCase()}`}>{LABELS[status]}</span>
}
