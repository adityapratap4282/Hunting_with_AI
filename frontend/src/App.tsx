import { useCallback, useEffect, useMemo, useState } from 'react'
import { TabButton } from './components/TabButton'
import type {
  DashboardPayload,
  JobPost,
  RankingResult,
  ReferralTarget,
  Resume,
  ResumeVersion,
  SettingsPayload,
} from './lib/types'

const tabs = [
  { id: 'dashboard', label: 'Dashboard' },
  { id: 'resume', label: 'Resume Conveyor' },
  { id: 'jobs', label: 'Job Intake' },
  { id: 'ranking', label: 'Ranking' },
  { id: 'referrals', label: 'Referral Copilot' },
  { id: 'settings', label: 'Settings' },
] as const

type TabId = (typeof tabs)[number]['id']

const emptyDashboard: DashboardPayload = {
  metrics: {
    resume_count: 0,
    job_count: 0,
    referral_count: 0,
  },
  latest_resumes: [],
  latest_jobs: [],
  referral_queue: [],
}

async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, {
    headers: {
      'Content-Type': 'application/json',
      ...(init?.headers ?? {}),
    },
    ...init,
  })

  if (!response.ok) {
    const detail = await response.text()
    throw new Error(detail || `Request failed with ${response.status}`)
  }

  return response.json() as Promise<T>
}

function App() {
  const [activeTab, setActiveTab] = useState<TabId>('dashboard')
  const [dashboard, setDashboard] = useState<DashboardPayload>(emptyDashboard)
  const [resumes, setResumes] = useState<Resume[]>([])
  const [jobs, setJobs] = useState<JobPost[]>([])
  const [referrals, setReferrals] = useState<ReferralTarget[]>([])
  const [settings, setSettings] = useState<SettingsPayload | null>(null)
  const [rankings, setRankings] = useState<RankingResult[]>([])
  const [selectedResumeVersionId, setSelectedResumeVersionId] = useState<number | null>(null)
  const [loading, setLoading] = useState(true)
  const [busyAction, setBusyAction] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  const refreshAll = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const [dashboardData, resumesData, jobsData, referralsData, settingsData] = await Promise.all([
        api<DashboardPayload>('/api/dashboard'),
        api<Resume[]>('/api/resumes'),
        api<JobPost[]>('/api/jobs'),
        api<ReferralTarget[]>('/api/referrals'),
        api<SettingsPayload>('/api/settings'),
      ])
      setDashboard(dashboardData)
      setResumes(resumesData)
      setJobs(jobsData)
      setReferrals(referralsData)
      setSettings(settingsData)
      const flattenedVersions = resumesData.flatMap((resume) => resume.versions)
      const latestVersion = flattenedVersions[flattenedVersions.length - 1]
      setSelectedResumeVersionId((current) => current ?? latestVersion?.id ?? null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown startup error')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    void refreshAll()
  }, [refreshAll])

  const resumeVersions = useMemo(
    () => resumes.flatMap((resume) => resume.versions.map((version) => ({ ...version, resumeName: resume.name }))),
    [resumes],
  )

  async function handleResumeSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const form = new FormData(event.currentTarget)
    setBusyAction('resume')
    setError(null)
    try {
      await api<Resume>('/api/resumes', {
        method: 'POST',
        body: JSON.stringify({
          name: form.get('name'),
          summary: form.get('summary') || null,
          initial_version: {
            version_label: form.get('versionLabel'),
            source_text: form.get('sourceText'),
          },
        }),
      })
      event.currentTarget.reset()
      await refreshAll()
      setActiveTab('dashboard')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to save resume')
    } finally {
      setBusyAction(null)
    }
  }

  async function handleJobSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const form = new FormData(event.currentTarget)
    setBusyAction('job')
    setError(null)
    try {
      await api<JobPost>('/api/jobs', {
        method: 'POST',
        body: JSON.stringify({
          title: form.get('title'),
          company_name: form.get('companyName') || null,
          source: form.get('source') || 'manual',
          source_url: form.get('sourceUrl') || null,
          location: form.get('location') || null,
          employment_type: form.get('employmentType') || null,
          jd_text: form.get('jdText'),
          freshness_bucket: form.get('freshnessBucket') || null,
          source_posted_at_raw: form.get('postedText') || null,
        }),
      })
      event.currentTarget.reset()
      await refreshAll()
      setActiveTab('ranking')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to save job')
    } finally {
      setBusyAction(null)
    }
  }

  async function handleReferralSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const form = new FormData(event.currentTarget)
    setBusyAction('referral')
    setError(null)
    try {
      await api<ReferralTarget>('/api/referrals', {
        method: 'POST',
        body: JSON.stringify({
          company_name: form.get('companyName'),
          full_name: form.get('fullName'),
          title: form.get('title') || null,
          linkedin_url: form.get('linkedinUrl') || null,
          lead_source: form.get('leadSource') || null,
          notes: form.get('notes') || null,
        }),
      })
      event.currentTarget.reset()
      await refreshAll()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to save referral target')
    } finally {
      setBusyAction(null)
    }
  }

  async function handleRankingRun() {
    if (!selectedResumeVersionId || jobs.length === 0) {
      setError('Add at least one resume version and one job before running ranking.')
      return
    }

    setBusyAction('ranking')
    setError(null)
    try {
      const results = await api<RankingResult[]>('/api/ranking/score', {
        method: 'POST',
        body: JSON.stringify({
          resume_version_id: selectedResumeVersionId,
          job_post_ids: jobs.map((job) => job.id),
        }),
      })
      setRankings(results)
      setActiveTab('ranking')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to run ranking')
    } finally {
      setBusyAction(null)
    }
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <div className="mx-auto flex max-w-7xl flex-col gap-6 px-6 py-8">
        <header className="rounded-3xl border border-slate-800 bg-gradient-to-br from-slate-900 via-slate-900 to-slate-800 p-6 shadow-2xl shadow-slate-950/60">
          <div className="flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
            <div>
              <p className="text-sm uppercase tracking-[0.3em] text-blue-300">Hunting with AI</p>
              <h1 className="mt-3 text-4xl font-semibold text-white">One-click local job search operating system</h1>
              <p className="mt-3 max-w-3xl text-sm text-slate-300">
                FastAPI now serves the UI and API together, so the local app can be launched from one starter script.
              </p>
            </div>
            <div className="rounded-2xl border border-amber-500/30 bg-amber-500/10 px-4 py-3 text-sm text-amber-100">
              <strong>LinkedIn note:</strong> use manual lead import and saved searches. Avoid automated scraping or mass outreach from your account.
            </div>
          </div>
        </header>

        <nav className="flex flex-wrap gap-3">
          {tabs.map((tab) => (
            <TabButton key={tab.id} active={tab.id === activeTab} onClick={() => setActiveTab(tab.id)}>
              {tab.label}
            </TabButton>
          ))}
          <button
            className="rounded-xl border border-slate-700 bg-slate-900 px-4 py-2 text-sm text-slate-200 hover:border-slate-500"
            onClick={() => void refreshAll()}
          >
            Refresh data
          </button>
        </nav>

        {error ? <div className="rounded-2xl border border-rose-500/30 bg-rose-500/10 p-4 text-sm text-rose-100">{error}</div> : null}

        {loading ? <LoadingPanel /> : null}

        {!loading && activeTab === 'dashboard' ? (
          <DashboardTab dashboard={dashboard} onRunRanking={() => void handleRankingRun()} busyAction={busyAction} />
        ) : null}

        {!loading && activeTab === 'resume' ? <ResumeTab resumes={resumes} onSubmit={handleResumeSubmit} busyAction={busyAction} /> : null}

        {!loading && activeTab === 'jobs' ? <JobsTab jobs={jobs} onSubmit={handleJobSubmit} busyAction={busyAction} /> : null}

        {!loading && activeTab === 'ranking' ? (
          <RankingTab
            jobs={jobs}
            rankings={rankings}
            resumeVersions={resumeVersions}
            selectedResumeVersionId={selectedResumeVersionId}
            setSelectedResumeVersionId={setSelectedResumeVersionId}
            onRunRanking={() => void handleRankingRun()}
            busyAction={busyAction}
          />
        ) : null}

        {!loading && activeTab === 'referrals' ? (
          <ReferralsTab referrals={referrals} onSubmit={handleReferralSubmit} busyAction={busyAction} />
        ) : null}

        {!loading && activeTab === 'settings' ? <SettingsTab settings={settings} /> : null}
      </div>
    </div>
  )
}

function LoadingPanel() {
  return <section className="rounded-2xl border border-slate-800 bg-slate-900 p-6 text-sm text-slate-300">Loading local app data…</section>
}

function DashboardTab({
  dashboard,
  onRunRanking,
  busyAction,
}: {
  dashboard: DashboardPayload
  onRunRanking: () => void
  busyAction: string | null
}) {
  const metrics = [
    { label: 'Resume Versions', value: dashboard.metrics.resume_count, hint: 'Stored master resumes' },
    { label: 'Jobs Ingested', value: dashboard.metrics.job_count, hint: 'Normalized job posts' },
    { label: 'Referral Leads', value: dashboard.metrics.referral_count, hint: 'Tracked outreach targets' },
  ]

  return (
    <section className="grid gap-6 lg:grid-cols-[1.3fr_0.7fr]">
      <div className="space-y-6">
        <div className="grid gap-4 md:grid-cols-3">
          {metrics.map((metric) => (
            <article key={metric.label} className="rounded-2xl border border-slate-800 bg-slate-900 p-5">
              <p className="text-sm text-slate-400">{metric.label}</p>
              <p className="mt-3 text-3xl font-semibold text-white">{metric.value}</p>
              <p className="mt-2 text-sm text-slate-400">{metric.hint}</p>
            </article>
          ))}
        </div>

        <article className="rounded-2xl border border-slate-800 bg-slate-900 p-6">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <h2 className="text-xl font-semibold">Recent jobs</h2>
            <button className="rounded-xl bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-500" onClick={onRunRanking}>
              {busyAction === 'ranking' ? 'Scoring…' : 'Score all jobs'}
            </button>
          </div>
          <div className="mt-4 space-y-3">
            {dashboard.latest_jobs.length === 0 ? <EmptyState message="Add a job post from the Job Intake tab to start ranking." /> : null}
            {dashboard.latest_jobs.map((job) => (
              <div key={job.id} className="rounded-xl border border-slate-800 bg-slate-950 p-4">
                <p className="font-medium text-white">{job.title}</p>
                <p className="mt-1 text-sm text-slate-400">{job.company?.name ?? 'Unknown company'} · {job.location ?? 'Location pending'}</p>
                <p className="mt-2 text-sm text-slate-300">{job.source} · freshness: {job.freshness_bucket ?? 'unclassified'}</p>
              </div>
            ))}
          </div>
        </article>
      </div>

      <article className="rounded-2xl border border-slate-800 bg-slate-900 p-6">
        <h2 className="text-xl font-semibold">Referral queue</h2>
        <div className="mt-4 space-y-3">
          {dashboard.referral_queue.length === 0 ? <EmptyState message="Add referral targets and their first message drafts will appear here." /> : null}
          {dashboard.referral_queue.map((target) => (
            <div key={target.id} className="rounded-xl border border-slate-800 bg-slate-950 p-4">
              <p className="font-medium text-white">{target.full_name}</p>
              <p className="text-sm text-slate-400">{target.title ?? 'Role pending'} · {target.company.name}</p>
              <p className="mt-2 text-sm text-slate-300">Status: {target.status}</p>
            </div>
          ))}
        </div>
      </article>
    </section>
  )
}

function ResumeTab({
  resumes,
  onSubmit,
  busyAction,
}: {
  resumes: Resume[]
  onSubmit: (event: React.FormEvent<HTMLFormElement>) => Promise<void>
  busyAction: string | null
}) {
  return (
    <section className="grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
      <form className="rounded-2xl border border-slate-800 bg-slate-900 p-6" onSubmit={(event) => void onSubmit(event)}>
        <h2 className="text-xl font-semibold">Resume Conveyor</h2>
        <div className="mt-5 grid gap-4">
          <InputField label="Resume name" name="name" placeholder="Master Data Resume" required />
          <InputField label="Summary" name="summary" placeholder="Data analyst profile focused on SQL, BI, and Python" />
          <InputField label="Version label" name="versionLabel" placeholder="master-v1" required />
          <TextareaField label="Resume text" name="sourceText" placeholder="Paste your master resume text here…" required />
          <button className="w-fit rounded-xl bg-blue-600 px-5 py-3 text-sm font-medium text-white hover:bg-blue-500" type="submit">
            {busyAction === 'resume' ? 'Saving…' : 'Save resume'}
          </button>
        </div>
      </form>
      <article className="rounded-2xl border border-slate-800 bg-slate-900 p-6">
        <h2 className="text-xl font-semibold">Stored resume versions</h2>
        <div className="mt-4 space-y-3">
          {resumes.length === 0 ? <EmptyState message="No resumes yet. Save your master resume to create the first version." /> : null}
          {resumes.map((resume) => (
            <div key={resume.id} className="rounded-xl border border-slate-800 bg-slate-950 p-4">
              <p className="font-medium text-white">{resume.name}</p>
              <p className="mt-1 text-sm text-slate-400">{resume.summary ?? 'No summary yet'}</p>
              <div className="mt-3 space-y-2 text-sm text-slate-300">
                {resume.versions.map((version) => (
                  <div key={version.id} className="rounded-lg border border-slate-800 p-3">
                    <p>{version.version_label}</p>
                    <p className="mt-1 text-xs text-slate-500">{new Date(version.created_at).toLocaleString()}</p>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      </article>
    </section>
  )
}

function JobsTab({
  jobs,
  onSubmit,
  busyAction,
}: {
  jobs: JobPost[]
  onSubmit: (event: React.FormEvent<HTMLFormElement>) => Promise<void>
  busyAction: string | null
}) {
  return (
    <section className="grid gap-6 lg:grid-cols-[1fr_1fr]">
      <form className="rounded-2xl border border-slate-800 bg-slate-900 p-6" onSubmit={(event) => void onSubmit(event)}>
        <h2 className="text-xl font-semibold">Job Intake</h2>
        <div className="mt-5 grid gap-4">
          <InputField label="Job title" name="title" placeholder="Data Analyst" required />
          <InputField label="Company name" name="companyName" placeholder="Acme Insights" />
          <div className="grid gap-4 md:grid-cols-2">
            <InputField label="Source" name="source" placeholder="manual" />
            <InputField label="Freshness bucket" name="freshnessBucket" placeholder="24h / 7d / 30d" />
          </div>
          <InputField label="Source URL" name="sourceUrl" placeholder="https://example.com/job/123" />
          <div className="grid gap-4 md:grid-cols-2">
            <InputField label="Location" name="location" placeholder="India / Remote" />
            <InputField label="Employment type" name="employmentType" placeholder="Full-time" />
          </div>
          <InputField label="Posted text" name="postedText" placeholder="Posted 2 days ago" />
          <TextareaField label="Job description text" name="jdText" placeholder="Paste the JD here…" required />
          <button className="w-fit rounded-xl bg-blue-600 px-5 py-3 text-sm font-medium text-white hover:bg-blue-500" type="submit">
            {busyAction === 'job' ? 'Saving…' : 'Save job'}
          </button>
        </div>
      </form>
      <article className="rounded-2xl border border-slate-800 bg-slate-900 p-6">
        <h2 className="text-xl font-semibold">Normalized jobs</h2>
        <div className="mt-4 space-y-3">
          {jobs.length === 0 ? <EmptyState message="No jobs stored yet. Paste one JD to create your first normalized record." /> : null}
          {jobs.map((job) => (
            <div key={job.id} className="rounded-xl border border-slate-800 bg-slate-950 p-4">
              <p className="font-medium text-white">{job.title}</p>
              <p className="mt-1 text-sm text-slate-400">{job.company?.name ?? 'Unknown company'} · {job.location ?? 'Unknown location'}</p>
              <p className="mt-2 text-sm text-slate-300">{job.source} · freshness {job.freshness_bucket ?? 'n/a'}</p>
              <p className="mt-2 line-clamp-3 text-sm text-slate-400">{job.jd_text}</p>
            </div>
          ))}
        </div>
      </article>
    </section>
  )
}

function RankingTab({
  jobs,
  rankings,
  resumeVersions,
  selectedResumeVersionId,
  setSelectedResumeVersionId,
  onRunRanking,
  busyAction,
}: {
  jobs: JobPost[]
  rankings: RankingResult[]
  resumeVersions: Array<ResumeVersion & { resumeName: string }>
  selectedResumeVersionId: number | null
  setSelectedResumeVersionId: (id: number) => void
  onRunRanking: () => void
  busyAction: string | null
}) {
  const rankingMap = new Map(rankings.map((item) => [item.job_post_id, item]))

  return (
    <section className="rounded-2xl border border-slate-800 bg-slate-900 p-6">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <h2 className="text-xl font-semibold">Hybrid ranking</h2>
          <p className="mt-2 text-sm text-slate-400">Rule-based scoring handles title, skills, and freshness, while the stored explanation is LLM-ready for later upgrades.</p>
        </div>
        <div className="flex flex-wrap items-end gap-3">
          <label className="grid gap-2 text-sm text-slate-300">
            <span>Resume version</span>
            <select
              className="rounded-xl border border-slate-700 bg-slate-950 px-3 py-2"
              value={selectedResumeVersionId ?? ''}
              onChange={(event) => setSelectedResumeVersionId(Number(event.target.value))}
            >
              <option value="" disabled>
                Select a resume version
              </option>
              {resumeVersions.map((version) => (
                <option key={version.id} value={version.id}>
                  {version.resumeName} · {version.version_label}
                </option>
              ))}
            </select>
          </label>
          <button className="rounded-xl bg-blue-600 px-5 py-3 text-sm font-medium text-white hover:bg-blue-500" onClick={onRunRanking}>
            {busyAction === 'ranking' ? 'Scoring…' : 'Run ranking'}
          </button>
        </div>
      </div>

      <div className="mt-6 grid gap-4 lg:grid-cols-2 xl:grid-cols-3">
        {jobs.length === 0 ? <EmptyState message="Add jobs before running ranking." /> : null}
        {jobs.map((job) => {
          const result = rankingMap.get(job.id)
          return (
            <article key={job.id} className="rounded-2xl border border-slate-800 bg-slate-950 p-5">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <h3 className="font-medium text-white">{job.title}</h3>
                  <p className="text-sm text-slate-400">{job.company?.name ?? 'Unknown company'}</p>
                </div>
                <span className="rounded-full bg-emerald-500/15 px-3 py-1 text-sm font-medium text-emerald-300">
                  {result ? result.score.toFixed(1) : '--'}
                </span>
              </div>
              <p className="mt-3 text-xs uppercase tracking-[0.2em] text-slate-500">Freshness: {job.freshness_bucket ?? 'n/a'}</p>
              <div className="mt-4 space-y-2 text-sm text-slate-300">
                <p>{result?.explanation ?? 'Run ranking to generate an explanation.'}</p>
                <p className="text-slate-400">{result?.gap_summary ?? 'Gap summary will appear after scoring.'}</p>
              </div>
            </article>
          )
        })}
      </div>
    </section>
  )
}

function ReferralsTab({
  referrals,
  onSubmit,
  busyAction,
}: {
  referrals: ReferralTarget[]
  onSubmit: (event: React.FormEvent<HTMLFormElement>) => Promise<void>
  busyAction: string | null
}) {
  return (
    <section className="grid gap-6 lg:grid-cols-[1fr_1fr]">
      <form className="rounded-2xl border border-slate-800 bg-slate-900 p-6" onSubmit={(event) => void onSubmit(event)}>
        <h2 className="text-xl font-semibold">Referral Copilot</h2>
        <div className="mt-5 grid gap-4">
          <InputField label="Company name" name="companyName" placeholder="Acme Insights" required />
          <InputField label="Employee name" name="fullName" placeholder="Priya Sharma" required />
          <InputField label="Title" name="title" placeholder="Senior Data Analyst" />
          <InputField label="LinkedIn profile URL" name="linkedinUrl" placeholder="https://www.linkedin.com/in/..." />
          <InputField label="Lead source" name="leadSource" placeholder="Saved LinkedIn search URL" />
          <TextareaField label="Notes" name="notes" placeholder="Why this person is a strong referral target…" />
          <button className="w-fit rounded-xl bg-blue-600 px-5 py-3 text-sm font-medium text-white hover:bg-blue-500" type="submit">
            {busyAction === 'referral' ? 'Saving…' : 'Save referral target'}
          </button>
        </div>
      </form>
      <article className="rounded-2xl border border-slate-800 bg-slate-900 p-6">
        <h2 className="text-xl font-semibold">Queued outreach</h2>
        <div className="mt-4 space-y-3">
          {referrals.length === 0 ? <EmptyState message="No referral targets yet. Add a lead to create an initial connection draft." /> : null}
          {referrals.map((target) => (
            <div key={target.id} className="rounded-xl border border-slate-800 bg-slate-950 p-4">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <p className="font-medium text-white">{target.full_name}</p>
                  <p className="text-sm text-slate-400">{target.title ?? 'Title pending'} · {target.company.name}</p>
                </div>
                <span className="rounded-full bg-blue-500/15 px-3 py-1 text-xs font-medium uppercase tracking-[0.2em] text-blue-300">{target.status}</span>
              </div>
              <p className="mt-3 text-sm text-slate-300">{target.notes ?? 'No notes yet.'}</p>
              {target.messages[0] ? <p className="mt-3 rounded-lg border border-slate-800 p-3 text-sm text-slate-400">Draft: {target.messages[0].body}</p> : null}
            </div>
          ))}
        </div>
      </article>
    </section>
  )
}

function SettingsTab({ settings }: { settings: SettingsPayload | null }) {
  return (
    <section className="grid gap-6 lg:grid-cols-[1fr_1fr]">
      <article className="rounded-2xl border border-slate-800 bg-slate-900 p-6">
        <h2 className="text-xl font-semibold">AI routing</h2>
        {settings ? (
          <div className="mt-5 space-y-4 text-sm text-slate-300">
            <div className="rounded-xl border border-slate-800 bg-slate-950 p-4">
              <p className="font-medium text-white">Provider</p>
              <p className="mt-2">{settings.ai_provider}</p>
            </div>
            <div className="rounded-xl border border-slate-800 bg-slate-950 p-4">
              <p className="font-medium text-white">Recommended model</p>
              <p className="mt-2">{settings.model_name}</p>
            </div>
          </div>
        ) : (
          <EmptyState message="Settings will appear once the backend responds." />
        )}
      </article>
      <article className="rounded-2xl border border-slate-800 bg-slate-900 p-6">
        <h2 className="text-xl font-semibold">Operational notes</h2>
        <ul className="mt-4 space-y-3 text-sm text-slate-300">
          {(settings?.routing_notes ?? []).map((note) => (
            <li key={note}>• {note}</li>
          ))}
        </ul>
      </article>
    </section>
  )
}

function InputField({ label, name, placeholder, required = false }: { label: string; name: string; placeholder: string; required?: boolean }) {
  return (
    <label className="grid gap-2 text-sm text-slate-300">
      <span>{label}</span>
      <input className="rounded-xl border border-slate-700 bg-slate-950 p-4" name={name} placeholder={placeholder} required={required} />
    </label>
  )
}

function TextareaField({ label, name, placeholder, required = false }: { label: string; name: string; placeholder: string; required?: boolean }) {
  return (
    <label className="grid gap-2 text-sm text-slate-300">
      <span>{label}</span>
      <textarea className="min-h-40 rounded-xl border border-slate-700 bg-slate-950 p-4" name={name} placeholder={placeholder} required={required} />
    </label>
  )
}

function EmptyState({ message }: { message: string }) {
  return <div className="rounded-xl border border-dashed border-slate-700 bg-slate-950 p-4 text-sm text-slate-400">{message}</div>
}

export default App
