# Vorkos

**The Autonomous Job Aggregator & Agentic Career OS.**

> *The job market is fragmented and noisy. Vorkos solves the signal-to-noise problem by treating job discovery as an engineering challenge: Aggregation → Normalization → Semantic Analysis.*

## ⚡️ Overview

Vorkos is an open-source, AI-powered agent that automates the entire top-of-funnel job search process. Unlike traditional scrapers that rely on keyword matching, Vorkos deploys autonomous agents to scout listings from multiple sources (LinkedIn, Indeed, Glassdoor) and uses **Llama 3.3 (via Groq)** to semantically analyze the *full* job description.

The system acts as a personalized headhunter, filtering out "ghost jobs," mismatched experience levels, and irrelevant listings before they ever reach your dashboard.

## 🚀 Key Features

* **Agentic Scouting:** Parallel execution of search scripts ensures 24/7 coverage of major job boards without rate-limiting bottlenecks.
* **Semantic Analysis:** Uses **Groq** (Llama 3.3-70B) to understand nuance in job descriptions (e.g., distinguishing "Java" from "JavaScript" or "3 years exp" from "Entry Level").
* **Deep-Read Capability:** Integrated with **Jina AI** to parse full HTML job posts into structured JSON, ensuring the AI reads the entire context, not just the metadata snippet.
* **Memory & Deduplication:** SQLite-backed persistence layer prevents duplicate listings and tracks "seen" jobs.
* **Distraction-Free UI:** A clean, "Sunrise" themed interface built with React & Tailwind, designed for focused application workflows.

## 🛠 Tech Stack

* **Frontend:** React, Vite, Tailwind CSS (Custom Design System)
* **Backend:** Python, Flask, Gunicorn
* **AI Inference:** Groq Cloud (Llama 3.3 70B Versatile)
* **Parsing:** Jina AI Reader (HTML-to-Text)
* **Database:** SQLite (Local/Embedded)
* **Search:** DuckDuckGo Search API (Aggregator)

## 🏗 Architecture

The system follows a linear agentic pipeline:

1. **Scout:** The `scout_for_jobs` module queries aggregators for raw links based on user parameters.
2. **Filter:** A lightweight regex filter discards obvious mismatches (e.g., "Senior" for a "Junior" role).
3. **Extract:** Jina AI fetches and sanitizes the full job description text.
4. **Reason:** The LLM (Llama 3) analyzes the text against the user's resume/profile to assign a "Fit Score."
5. **Present:** The frontend renders the curated list, sorted by relevance and freshness.

## 💻 Local Development

To run the full stack locally:

### 1. Clone the Repository

```bash
git clone https://github.com/VishnuSuryaTejaa/vorkos.git
cd vorkos
```

### 2. Backend Setup

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure Environment
# Create a .env file in the root directory (or backend/)
echo "GROQ_API_KEY=your_key_here" >> .env
echo "JINA_API_KEY=your_key_here" >> .env
```

### 3. Frontend Setup

```bash
cd frontend
npm install
```

### 4. Launch Application

**Terminal 1 (Backend):**

```bash
python3 backend/app.py
# Server running at http://localhost:5001
```

**Terminal 2 (Frontend):**

```bash
npm run dev
# Client running at http://localhost:5173
```

## 🌍 Deployment

### Backend (Render/Railway)

The backend is stateless and container-ready.

1. Push code to GitHub.
2. Create a new Web Service on Render.
3. **Build Command:** `pip install -r requirements.txt`
4. **Start Command:** `gunicorn backend.app:app`
5. **Environment:** Add `GROQ_API_KEY` and `JINA_API_KEY` in the dashboard.

### Frontend (Vercel/Netlify)

1. Import repository to Vercel.
2. **Build Command:** `npm run build`
3. **Output Directory:** `dist`
4. **Environment:** Set `VITE_API_URL` to your live backend URL.

## 📄 License

This project is open-source and available under the [MIT License](https://www.google.com/search?q=LICENSE). Contributions and forks are welcome.
