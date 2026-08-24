export type Role = 'resident' | 'admin'
export type ComplaintStatus = 'OPEN' | 'IN_PROGRESS' | 'RESOLVED'
export type ComplaintPriority = 'LOW' | 'MEDIUM' | 'HIGH'

export interface UserOut {
  id: number
  name: string
  email: string
  role: Role
  flat_number?: string | null
  created_at: string
}

export interface ComplaintHistoryOut {
  id: number
  event_type: 'CREATED' | 'STATUS_CHANGE' | 'PRIORITY_CHANGE' | 'NOTE'
  previous_status?: ComplaintStatus | null
  new_status?: ComplaintStatus | null
  previous_priority?: ComplaintPriority | null
  new_priority?: ComplaintPriority | null
  note?: string | null
  actor_name: string
  created_at: string
}

export interface ComplaintOut {
  id: number
  reference_code: string
  category: string
  description: string
  photo_path?: string | null
  status: ComplaintStatus
  priority: ComplaintPriority
  created_at: string
  updated_at: string
  resolved_at?: string | null
  resident_id: number
  resident_name?: string | null
  is_overdue: boolean
  days_open: number
  sla_message: string
}

export interface ComplaintDetailOut extends ComplaintOut {
  history: ComplaintHistoryOut[]
}

export interface NoticeOut {
  id: number
  title: string
  content: string
  is_important: boolean
  author_name: string
  created_at: string
}

export interface DashboardOut {
  total_complaints: number
  open_count: number
  in_progress_count: number
  resolved_count: number
  overdue_count: number
  overdue_high_priority_count: number
  by_category: Record<string, number>
  by_priority: Record<string, number>
  overdue_threshold_days: number
}
