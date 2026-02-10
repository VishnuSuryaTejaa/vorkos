import { useState, useEffect, useRef } from 'react'
import axios from 'axios'
import ReactMarkdown from 'react-markdown'
import { Search, MapPin, Briefcase, Loader2, ChevronDown, ExternalLink, Clock, FileText, Database, Trash2, ChevronUp, Upload, Tag, Sparkles, Eye, EyeOff, Zap, Shield, BarChart3, Radar } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import './App.css'

// Convert bare URLs to clickable markdown links
function preprocessAnalysis(text) {
  if (!text) return ''
  return text.replace(
    /(?<!\]\()(?<!\[)(https?:\/\/[^\s\)>\]]+)/g,
    (url) => {
      const clean = url.replace(/[.,;:!?]+$/, '')
      try {
        const hostname = new URL(clean).hostname.replace('www.', '')
        return `[${hostname}](${clean})`
      } catch {
        return `[Link](${clean})`
      }
    }
  )
}

const PLATFORMS = ['LinkedIn', 'Indeed', 'Glassdoor', 'Wellfound', 'Greenhouse', 'Lever', 'Naukri']

function App() {
  const [jobTitle, setJobTitle] = useState('')
  const [location, setLocation] = useState('')
  const [loading, setLoading] = useState(false)
  const [results, setResults] = useState(null)
  const [error, setError] = useState(null)
  const [jobRoles, setJobRoles] = useState([])
  const [locations, setLocations] = useState([])
  const [timeFilters, setTimeFilters] = useState([])
  const [timeFilter, setTimeFilter] = useState('past_week')
  const [jobTypes, setJobTypes] = useState([])
  const [jobType, setJobType] = useState('any')
  const [showResume, setShowResume] = useState(false)
  const [resumeStatus, setResumeStatus] = useState('')
  const [resumePreview, setResumePreview] = useState('')
  const [memoryCount, setMemoryCount] = useState(0)
  const [showRaw, setShowRaw] = useState(false)
  const fileInputRef = useRef(null)

  // API Configuration
  const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:5001'

  useEffect(() => {
    const fetchOptions = async () => {
      try {
        const res = await axios.get(`${API_BASE_URL}/api/options`)
        setJobRoles(res.data.job_roles)
        setLocations(res.data.locations)
        setTimeFilters(res.data.time_filters || [])
        setJobTypes(res.data.job_types || [])
        setMemoryCount(res.data.memory_count || 0)
        if (res.data.job_roles.length > 0) setJobTitle(res.data.job_roles[0])
        if (res.data.locations.length > 0) setLocation(res.data.locations[0])
        if (res.data.time_filters?.length > 0) setTimeFilter(res.data.time_filters[1]?.value || 'past_week')
        if (res.data.has_resume) { setResumeStatus('uploaded'); setResumePreview('Profile calibrated from previous session') }
      } catch {
        setJobRoles(["Machine Learning Engineer", "Full Stack Developer", "Data Scientist"])
        setLocations(["Remote", "India", "United States"])
        setJobTitle("Machine Learning Engineer")
        setLocation("Remote")
      }
    }
    fetchOptions()
  }, [])

  const handleSearch = async (e) => {
    e.preventDefault()
    setLoading(true); setError(null); setResults(null)
    try {
      const res = await axios.post(`${API_BASE_URL}/api/hunt`, { job_title: jobTitle, location, time_filter: timeFilter, job_type: jobType })
      setResults(res.data)
      setMemoryCount(prev => prev + (res.data.new_jobs || 0))
    } catch (err) {
      setError(err.response?.data?.error || "Agent deployment failed. Ensure backend is operational.")
    } finally { setLoading(false) }
  }

  const handleFileUpload = async (e) => {
    const file = e.target.files[0]
    if (!file) return
    if (!file.name.toLowerCase().endsWith('.pdf')) { setResumeStatus('error'); setResumePreview('Only PDF files accepted'); return }
    setResumeStatus('uploading')
    const formData = new FormData(); formData.append('file', file)
    try {
      const res = await axios.post(`${API_BASE_URL}/api/resume/upload`, formData, { headers: { 'Content-Type': 'multipart/form-data' } })
      setResumeStatus('uploaded')
      setResumePreview(`${file.name} — ${res.data.pages} page(s), ${res.data.length} chars analyzed`)
    } catch (err) { setResumeStatus('error'); setResumePreview(err.response?.data?.error || 'Calibration failed') }
  }

  const handleClearMemory = async () => {
    try { await axios.post(`${API_BASE_URL}/api/memory/clear`); setMemoryCount(0) } catch { }
  }

  return (
    <div className="app-container">
      <div className="main-wrapper">

        {/* ═══ HERO ═══ */}
        <header className="header">
          <motion.div initial={{ opacity: 0, y: -15 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5 }}>
            <div className="brand">
              <div className="brand-icon"><Radar size={20} /></div>
              <h1 className="brand-name">Vor<span className="brand-accent">kos</span></h1>
            </div>
            <h2 className="hero-headline">Stop Searching. Start Applying.</h2>
            <p className="hero-sub">
              The internet is fragmented. <strong>Vorkos</strong> unifies it. We deploy autonomous AI agents to scout, filter, and rank job listings from every corner of the web — so you never miss an opportunity again.
            </p>
          </motion.div>
        </header>

        <main className="main-content">

          {/* ═══ COMMAND CENTER ═══ */}
          <section className="search-section" aria-label="Job Search Command Center">
            <form onSubmit={handleSearch} className="search-form">
              <div className="form-grid-4">
                <div className="form-group">
                  <label className="form-label"><Briefcase size={12} /> Role</label>
                  <div className="select-wrapper">
                    <select required value={jobTitle} onChange={(e) => setJobTitle(e.target.value)} className="form-select">
                      {jobRoles.map((r, i) => <option key={i} value={r}>{r}</option>)}
                    </select>
                    <ChevronDown size={14} className="select-icon" />
                  </div>
                </div>
                <div className="form-group">
                  <label className="form-label"><MapPin size={12} /> Region</label>
                  <div className="select-wrapper">
                    <select required value={location} onChange={(e) => setLocation(e.target.value)} className="form-select">
                      {locations.map((l, i) => <option key={i} value={l}>{l}</option>)}
                    </select>
                    <ChevronDown size={14} className="select-icon" />
                  </div>
                </div>
                <div className="form-group">
                  <label className="form-label"><Tag size={12} /> Type</label>
                  <div className="select-wrapper">
                    <select value={jobType} onChange={(e) => setJobType(e.target.value)} className="form-select">
                      {jobTypes.length > 0 ? jobTypes.map((t, i) => <option key={i} value={t.value}>{t.label}</option>) : (
                        <><option value="any">Any</option><option value="internship">Internship</option><option value="fulltime">Full-Time</option></>
                      )}
                    </select>
                    <ChevronDown size={14} className="select-icon" />
                  </div>
                </div>
                <div className="form-group">
                  <label className="form-label"><Clock size={12} /> Freshness</label>
                  <div className="select-wrapper">
                    <select value={timeFilter} onChange={(e) => setTimeFilter(e.target.value)} className="form-select">
                      {timeFilters.length > 0 ? timeFilters.map((f, i) => <option key={i} value={f.value}>{f.label}</option>) : (
                        <><option value="past_day">Past 24h</option><option value="past_week">Past Week</option><option value="past_month">Past Month</option></>
                      )}
                    </select>
                    <ChevronDown size={14} className="select-icon" />
                  </div>
                </div>
              </div>

              {/* Resume Calibration */}
              <div className="resume-section">
                <button type="button" className="resume-toggle" onClick={() => setShowResume(!showResume)}>
                  <Shield size={12} />
                  {resumeStatus === 'uploaded' ? '✓ Profile Calibrated — Precision Matching Active' : 'Calibrate Match Algorithm'}
                  {showResume ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
                </button>
                <AnimatePresence>
                  {showResume && (
                    <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }} exit={{ opacity: 0, height: 0 }} className="resume-content">
                      <div className="upload-area" onClick={() => fileInputRef.current?.click()}>
                        <input ref={fileInputRef} type="file" accept=".pdf" onChange={handleFileUpload} style={{ display: 'none' }} />
                        {resumeStatus === 'uploading' ? (
                          <div className="upload-status"><Loader2 size={20} className="animate-spin" /><span>Analyzing profile...</span></div>
                        ) : resumeStatus === 'uploaded' ? (
                          <div className="upload-status upload-success"><Shield size={20} /><span>{resumePreview}</span><span className="upload-hint">Click to recalibrate</span></div>
                        ) : resumeStatus === 'error' ? (
                          <div className="upload-status upload-error"><span>✕ {resumePreview}</span><span className="upload-hint">Click to retry</span></div>
                        ) : (
                          <div className="upload-status">
                            <Upload size={20} />
                            <span className="upload-main">Upload your CV to calibrate</span>
                            <span className="upload-hint">Our AI doesn't just match keywords — it understands your experience to find roles where you're a top candidate.</span>
                          </div>
                        )}
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>

              <button type="submit" disabled={loading} className="submit-btn">
                {loading ? (
                  <><Loader2 className="animate-spin" size={18} /><span>Agents Deployed — Scanning...</span></>
                ) : (
                  <><Zap size={18} /><span>Deploy Agents</span></>
                )}
              </button>
            </form>

            {/* Trust Bar */}
            <div className="trust-bar">
              <p className="trust-label">Aggregating intelligence from</p>
              <div className="trust-platforms">
                {PLATFORMS.map((p, i) => <span key={i} className="trust-platform">{p}</span>)}
              </div>
            </div>
          </section>

          {/* ═══ ERROR ═══ */}
          <AnimatePresence>
            {error && (
              <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }} exit={{ opacity: 0, height: 0 }} className="error-container">
                <p>⚠ {error}</p>
              </motion.div>
            )}
          </AnimatePresence>

          {/* ═══ EMPTY STATE ═══ */}
          {!results && !loading && !error && (
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.3 }} className="empty-state">
              <div className="empty-icon"><Radar size={32} /></div>
              <h3 className="empty-headline">"The job market is noisy. Silence it."</h3>
              <p className="empty-sub">Select your role above to deploy your personal headhunter.</p>
              <div className="empty-steps">
                <div className="step-item">
                  <div className="step-num">01</div>
                  <div><strong>Deep Scout</strong><br /><span>Parallel agents scan major boards and hidden career pages simultaneously.</span></div>
                </div>
                <div className="step-item">
                  <div className="step-num">02</div>
                  <div><strong>Noise Cancellation</strong><br /><span>Llama 3.3 filters out spam, stale listings, and irrelevant noise.</span></div>
                </div>
                <div className="step-item">
                  <div className="step-num">03</div>
                  <div><strong>Fit Analysis</strong><br /><span>We deep-read full descriptions and cross-reference with your resume for precision scoring.</span></div>
                </div>
              </div>
            </motion.div>
          )}

          {/* ═══ RESULTS ═══ */}
          <AnimatePresence>
            {results && (
              <motion.section initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="results-container" aria-label="Search Results">

                {/* Stats */}
                <div className="stats-bar" role="status" aria-label="Search Statistics">
                  <div className="stat-item">
                    <span className="stat-value">{results.jobs_found}</span>
                    <span className="stat-label">Scanned</span>
                  </div>
                  <div className="stat-item stat-new">
                    <span className="stat-value">{results.new_jobs || 0}</span>
                    <span className="stat-label">New Matches</span>
                  </div>
                  <div className="stat-item stat-seen">
                    <span className="stat-value">{results.seen_jobs || 0}</span>
                    <span className="stat-label">Previously Seen</span>
                  </div>
                </div>

                {/* AI Analysis */}
                <article className="analysis-card" aria-labelledby="analysis-heading">
                  <header className="analysis-header">
                    <div className="analysis-header-left">
                      <Sparkles size={15} className="analysis-icon" aria-hidden="true" />
                      <h2 id="analysis-heading" className="analysis-title">Agent Report</h2>
                    </div>
                    <span className="analysis-badge">Llama 3.3 · 70B</span>
                  </header>
                  <div className="analysis-content markdown-body">
                    <ReactMarkdown
                      components={{
                        a: ({ href, children }) => (
                          <a href={href} target="_blank" rel="noreferrer" className="md-link">
                            {children} <ExternalLink size={11} />
                          </a>
                        ),
                        h3: ({ children }) => <h3 className="md-h3">{children}</h3>,
                        strong: ({ children }) => <strong className="md-strong">{children}</strong>,
                        p: ({ children }) => <p className="md-p">{children}</p>,
                      }}
                    >
                      {preprocessAnalysis(results.analysis)}
                    </ReactMarkdown>
                  </div>
                </article>

                {/* Source Links */}
                <div className="raw-links-card">
                  <button className="raw-links-header" onClick={() => setShowRaw(!showRaw)}>
                    <span className="raw-links-header-left">
                      {showRaw ? <EyeOff size={13} /> : <Eye size={13} />}
                      <span>Raw Intelligence</span>
                    </span>
                    <span className="raw-links-badge">{results.jobs_found} endpoints</span>
                  </button>
                  <AnimatePresence>
                    {showRaw && (
                      <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }} exit={{ opacity: 0, height: 0 }}>
                        <div className="raw-links-grid">
                          {results.raw_jobs.map((job, idx) => (
                            <a key={idx} href={job.href} target="_blank" rel="noreferrer" className={`job-link ${job.is_new ? 'job-new' : 'job-seen'}`}>
                              <div className="job-link-content">
                                <h4 className="job-link-title">
                                  {job.is_new && <span className="new-badge">NEW</span>}
                                  {job.title}
                                </h4>
                                <p className="job-link-url">{job.href}</p>
                              </div>
                              <ExternalLink size={13} className="job-link-arrow" />
                            </a>
                          ))}
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </div>

              </motion.section>
            )}
          </AnimatePresence>
        </main>

        {/* ═══ FOOTER ═══ */}
        <footer className="footer">
          <div className="footer-content">
            <span>Vorkos · Powered by Groq, Llama 3.3, and Jina AI</span>
            <span className="footer-dev">Developed by <strong>Vishnu Surya Teja</strong> · <a href="https://mail.google.com/mail/?view=cm&to=Vishnusuryatejavst@gmail.com" target="_blank" rel="noreferrer" className="footer-contact">Contact</a></span>
            <div className="memory-controls">
              <span className="memory-badge"><Database size={10} /> {memoryCount} indexed</span>
              {memoryCount > 0 && (
                <button onClick={handleClearMemory} className="clear-memory-btn"><Trash2 size={10} /> Purge</button>
              )}
            </div>
          </div>
        </footer>
      </div>
    </div>
  )
}

export default App
