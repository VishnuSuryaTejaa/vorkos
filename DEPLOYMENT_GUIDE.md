# 🚀 Deployment Guide

Follow these steps to get your Vorkos app live.

## Part 1: Backend (Render)

1.  **Sign up/Login** to [Render](https://render.com/).
2.  Click **"New +"** -> **"Web Service"**.
3.  Connect your GitHub repository: `VishnuSuryaTejaa/vorkos`.
4.  **Configure the Service**:
    -   **Name**: `vorkos-backend` (or similar)
    -   **Region**: Closest to you (e.g., Singapore, Frankfurt, Oregon)
    -   **Branch**: `main`
    -   **Root Directory**: `.` (leave empty or set to root)
    -   **Runtime**: `Python 3`
    -   **Build Command**: `pip install -r requirements.txt`
    -   **Start Command**: `gunicorn backend.app:app`
5.  **Environment Variables** (Scroll down to "Environment"):
    -   Add `GROQ_API_KEY`: (Paste your key)
    -   Add `JINA_API_KEY`: (Paste your key)
    -   Add `PYTHON_VERSION`: `3.11.0` (Optional, good for stability)
6.  Click **"Create Web Service"**.
7.  **Wait** for the deployment to finish. You will get a URL like `https://vorkos-backend.onrender.com`.
    -   **Copy this URL**. You need it for the frontend.

## Part 2: Frontend (Vercel)

1.  **Sign up/Login** to [Vercel](https://vercel.com/new).
2.  Import your GitHub repository: `VishnuSuryaTejaa/vorkos`.
3.  **Configure Project**:
    -   **Framework Preset**: Vite (should detect automatically)
    -   **Root Directory**: Click "Edit" and select `frontend`. **(Crucial Step)**
    -   **Build Command**: `vite build` (Default)
    -   **Output Directory**: `dist` (Default)
4.  **Environment Variables**:
    -   Add `VITE_API_URL`: Paste the **Render Backend URL** you copied (e.g., `https://vorkos-backend.onrender.com`).
        -   *Note: Ensure there is NO trailing slash `/` at the end of the URL.*
5.  Click **"Deploy"**.
6.  **Done!** Vercel will give you a live URL (e.g., `https://vorkos.vercel.app`).

## Troubleshooting

-   **Backend not starting?** Check the "Logs" tab in Render for errors.
-   **Frontend can't connect?**
    -   Check Chrome DevTools -> Network tab.
    -   If requests go to `localhost:5001`, you didn't set `VITE_API_URL` correctly in Vercel.
    -   If requests get "CORS" errors, the backend `cors` setup might need tuning (current setup allows `*` so it should work).
