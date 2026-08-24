import type { ComplaintPriority } from '../lib/types'

export default function PriorityBadge({ priority }: { priority: ComplaintPriority }) {
  return <span className={`badge badge-priority-${priority.toLowerCase()}`}>{priority}</span>
}
