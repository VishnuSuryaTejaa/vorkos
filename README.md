# Vorkos

**The Autonomous Job Aggregator & Agentic Career OS.**

> *The job market is fragmented and noisy. Vorkos solves the signal-to-noise problem by treating job discovery as an engineering challenge: Aggregation → Normalization → Semantic Analysis.*

## ⚡️ Overview

Vorkos is an open-source, AI-powered agent that automates the entire top-of-funnel job search process. Unlike traditional scrapers that rely on keyword matching, Vorkos uses **Tavily AI** to search the entire web for job listings from diverse sources (company career pages, LinkedIn, Indeed, Glassdoor, and more), then uses **Llama 3.3 (via Groq)** to semantically analyze the *full* job description.

The system acts as a personalized headhunter, filtering out "ghost jobs," mismatched experience levels, and irrelevant listings before they ever reach your dashboard.

## 🚀 Key Features

* **Intelligent Web Search:** Uses **Tavily AI** to search the entire web for job listings from diverse sources - company career pages (SAP, Dell, Boeing, Microsoft), job boards (LinkedIn, Indeed, Glassdoor), and more.
* **Semantic Analysis:** Uses **Groq** (Llama 3.3-70B) to understand nuance in job descriptions (e.g., distinguishing "Java" from "JavaScript" or "3 years exp" from "Entry Level").
* **Deep-Read Capability:** Tavily automatically provides full job content, ensuring the AI reads the entire context, not just metadata snippets.
* **Memory & Deduplication:** SQLite-backed persistence layer prevents duplicate listings and tracks "seen" jobs.
* **Distraction-Free UI:** A clean, "Sunrise" themed interface built with React & Tailwind, designed for focused application workflows.
* **Production-Ready:** Fully compatible with Render, Railway, and other cloud platforms - no blocking or rate-limiting issues.

## 🛠 Tech Stack

* **Frontend:** React, Vite, Custom CSS Design System
* **Backend:** Python, Flask, Gunicorn
* **AI Inference:** Groq Cloud (Llama 3.3 70B Versatile)
* **Web Search:** Tavily AI (Professional Search API)
* **Database:** SQLite (Local/Embedded)
* **Deployment:** Render (Backend), Vercel (Frontend)

## 🏗 Architecture

The system follows a hybrid agentic pipeline:

1. **Scout (Tavily):** The `scout_for_jobs` module searches the entire web for job listings using Tavily AI, returning full content from diverse sources.
2. **Pre-Filter:** A lightweight regex filter discards obvious mismatches (e.g., "Senior" for a "Junior" role, stale postings).
3. **Brain (Groq):** The LLM (Llama 3.3) analyzes the full job content against the user's resume/profile to assign a "Fit Score."
4. **Memory:** SQLite tracks seen jobs and prevents duplicates.
5. **Present:** The frontend renders the curated list, sorted by relevance and freshness.

## 📄 License

This project is open-source and available under the [MIT License](https://www.google.com/search?q=LICENSE). Contributions and forks are welcome.
