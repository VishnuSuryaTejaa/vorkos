# ⚡ Vorkos — Architecture & Agent Documentation

> **"The Entire Job Market. One Interface."**

---

## What Is Vorkos?

**Vorkos** is an **Autonomous Job Aggregator** — an AI agent that deploys parallel scouts across the web, deep-reads full job descriptions, and uses LLM intelligence to curate precision-matched results.

| Term | Applies? | Explanation |
|------|:--------:|-------------|
| **AI Agent** | ✅ | Perceives (web search), reasons (LLM analysis), acts (curated results) |
| **Agentic Pipeline** | ✅ | 5-step autonomous pipeline: Scout → Memory → Deep Read → Analysis → Store |
| **LLM-Powered Tool** | ✅ | Llama 3.3 70B via Groq for intelligent reasoning |
| **RAG (Lightweight)** | ⚠️ | Retrieves web data, then generates — no vector DB |

---

## System Architecture

```
┌──────────────────────────────────────────────────────────┐
│                   FRONTEND (React + Vite)                 │
│                    localhost:5173                          │
│                                                           │
│   Hero: "Stop Searching. Start Applying."                 │
│   Command Center: Role + Region + Type + Freshness        │
│   Trust Bar: LinkedIn · Indeed · Glassdoor · Wellfound     │
│   Resume Calibration: PDF → AI profile matching           │
│   CTA: [⚡ Deploy Agents]                                 │
│   Results: Stats → Agent Report (MD) → Raw Intelligence   │
└────────────────────┬─────────────────────────────────────┘
                     │ POST /api/hunt
                     │ POST /api/resume/upload
                     │ GET  /api/options
                     ▼
┌──────────────────────────────────────────────────────────┐
│                   BACKEND (Flask)                          │
│                   localhost:5001                           │
│                                                           │
│  ┌──────────────────────────────────────────────────┐     │
│  │          5-STEP AGENTIC PIPELINE                  │     │
│  │                                                   │     │
│  │  1. PARALLEL SCOUT (DuckDuckGo × 3 threads)      │     │
│  │  2. MEMORY CHECK (SQLite deduplication)           │     │
│  │  3. DEEP READER (Jina AI full-text extraction)    │     │
│  │  4. AI ANALYSIS (Groq + Llama 3.3 70B)           │     │
│  │  5. MEMORY STORE (Index new jobs)                 │     │
│  └──────────────────────────────────────────────────┘     │
└──────────────────────────────────────────────────────────┘
         │                    │                  │
         ▼                    ▼                  ▼
  ┌─────────────┐    ┌──────────────┐    ┌─────────────┐
  │  DuckDuckGo  │    │  Groq Cloud   │    │  Jina AI    │
  │  × 3 threads │    │  Llama 3.3    │    │  Reader     │
  └─────────────┘    └──────────────┘    └─────────────┘
```

---

## API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/options` | GET | Dropdown data: 45+ roles, 9 regions, types, filters, memory count |
| `/api/hunt` | POST | Deploy agents — runs full 5-step pipeline |
| `/api/resume/upload` | POST | Upload PDF, extract via PyPDF2 |
| `/api/memory/clear` | POST | Purge indexed job memory |

---

## File Breakdown

| File | Role |
|------|------|
| `app.py` | Flask orchestrator |
| `job_engine.py` | Core intelligence: search, deep reading, AI analysis |
| `job_memory.py` | SQLite memory layer |
| `App.jsx` | React UI — Vorkos command center |
| `index.css` | Sunrise/sunset dark theme |
| `index.html` | HTML shell — Vorkos title, ⚡ favicon |

---

## Tech Stack

| Component | Technology | Cost |
|-----------|-----------|:----:|
| Web Server | Flask | Free |
| Web Search | ddgs (DuckDuckGo) × 3 threads | Free |
| AI / LLM | Groq + Llama 3.3 70B | Free |
| Deep Reader | Jina AI Reader | Free |
| Resume Parser | PyPDF2 | Free |
| Memory | SQLite | Free |
| Frontend | React + Vite | Free |
| Markdown | react-markdown | Free |
| Icons | Lucide React | Free |
| Animation | Framer Motion | Free |

---

## Design System

### Sunrise/Sunset Sky Palette

| Token | Value | Usage |
|-------|-------|-------|
| `--sun` | `#f97316` | Primary accent, CTA, highlights |
| `--sun-light` | `#fb923c` | Hover states, links |
| `--rose` | `#f43f5e` | Gradient endpoint, badges |
| `--rose-light` | `#fb7185` | Brand accent gradient |
| `--amber` | `#fbbf24` | Warm highlight |
| `--sky-deep` | `#7c3aed` | Twilight tones |
| `--bg` | `#0a0a12` | Deep night sky background |

### Typography
| Font | Usage |
|------|-------|
| DM Sans | Body, labels, buttons |
| JetBrains Mono | Stats, badges, code |
