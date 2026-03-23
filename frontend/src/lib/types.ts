export interface Company {
  id: number
  name: string
  website?: string | null
  industry?: string | null
}

export interface ResumeVersion {
  id: number
  version_label: string
  source_text: string
  created_at: string
}

export interface Resume {
  id: number
  name: string
  summary?: string | null
  versions: ResumeVersion[]
}

export interface JobPost {
  id: number
  title: string
  source: string
  source_url?: string | null
  location?: string | null
  employment_type?: string | null
  jd_text: string
  freshness_bucket?: string | null
  dedupe_key: string
  company?: Company | null
}

export interface RankingResult {
  job_post_id: number
  score: number
  title_score: number
  skill_score: number
  freshness_score: number
  llm_score: number
  explanation: string
  gap_summary: string
}

export interface OutreachMessage {
  id: number
  message_type: string
  body: string
  status: string
  reminder_at?: string | null
}

export interface ReferralTarget {
  id: number
  status: string
  full_name: string
  title?: string | null
  linkedin_url?: string | null
  lead_source?: string | null
  notes?: string | null
  company: Company
  messages: OutreachMessage[]
}

export interface SettingsPayload {
  ai_provider: string
  model_name: string
  routing_notes: string[]
}

export interface DashboardPayload {
  metrics: Record<string, number>
  latest_resumes: Resume[]
  latest_jobs: JobPost[]
  referral_queue: ReferralTarget[]
}
