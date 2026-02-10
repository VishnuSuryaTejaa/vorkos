# Vorkos 🎯

**The Autonomous Job Aggregator.**

Vorkos is an AI-powered job search engine that deploys autonomous agents to scout, filter, and rank job listings from across the entire web (LinkedIn, Indeed, Glassdoor, and more). Stop searching, start applying.

![Vorkos UI Preview](https://github.com/user-attachments/assets/placeholder.png)

## Features

- **🚀 Autonomous Agents**: Deploys parallel scouts to find jobs 24/7.
- **🧠 Deep Reader**: AI reads full job descriptions to understand true fit.
- **⚡ Resume Calibration**: Upload your resume for precision matching and gap analysis.
- **💾 Long-Term Memory**: Remembers every job it has seen to prevent duplicates.
- **🌅 Sunrise UI**: Beautiful, distraction-free interface designed for focus.

## Tech Stack

- **Frontend**: React, Vite, Tailwind CSS (Custom)
- **Backend**: Python, Flask
- **AI Engine**: Groq (Llama 3.3 70B), Jina AI (Deep Reader)
- **Database**: SQLite (Local Memory)

## Getting Started

### Prerequisites

- Python 3.8+
- Node.js 16+
- API Keys for Groq and Jina AI (set in `.env`)

### Installation

1.  **Clone the repository**
    ```bash
    git clone https://github.com/VishnuSuryaTejaa/vorkos.git
    cd vorkos
    ```

2.  **Backend Setup**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    ```

3.  **Frontend Setup**
    ```bash
    cd frontend
    npm install
    ```

4.  **Environment Variables**
    Create a `.env` file in the root directory:
    ```env
    GROQ_API_KEY=your_groq_key
    JINA_API_KEY=your_jina_key
    ```

### Running the App

1.  **Start the Backend**
    ```bash
    # From root
    python3 backend/app.py
    ```

2.  **Start the Frontend**
    ```bash
    # In a new terminal, from frontend/
    npm run dev
    ```

    Visit `http://localhost:5173` to start your job hunt.

## Deployment

### Frontend (Vercel)

The frontend is a standard Vite React app.
1.  Push to GitHub.
2.  Import project in Vercel.
3.  Set "Build Command" to `npm run build` and "Output Directory" to `dist`.
4.  Deploy!

### Backend (Render)

The backend is a Flask app.
1.  Push to GitHub.
2.  Create a "Web Service" in Render.
3.  Connect your repo.
4.  Set "Build Command" to `pip install -r requirements.txt`.
5.  Set "Start Command" to `gunicorn backend.app:app` (Make sure `gunicorn` is in `requirements.txt`).
6.  Add your environment variables in Render dashboard.

## License

MIT
# vorkos
