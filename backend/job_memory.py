"""
SQLite "Brain Implant" — Long-Term Memory for Digital Headhunter

Stores seen job URLs so the agent doesn't show you the same job twice.
Creates a tiny `jobs.db` file in the backend directory.
"""

import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'jobs.db')


def init_db():
    """Create the seen_jobs table if it doesn't exist."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS seen_jobs (
            url TEXT PRIMARY KEY,
            title TEXT,
            date_seen TEXT,
            job_title_query TEXT,
            location_query TEXT
        )
    ''')
    conn.commit()
    conn.close()


def is_job_seen(url):
    """Check if a job URL has been seen before."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT 1 FROM seen_jobs WHERE url = ?', (url,))
    result = cursor.fetchone()
    conn.close()
    return result is not None


def filter_new_jobs(jobs):
    """
    Takes a list of job dicts, returns two lists:
    - new_jobs: jobs not seen before (with is_new=True flag added)
    - seen_jobs: jobs already in the database (with is_new=False flag added)
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    new_jobs = []
    seen_jobs = []
    
    for job in jobs:
        cursor.execute('SELECT 1 FROM seen_jobs WHERE url = ?', (job['href'],))
        if cursor.fetchone():
            job['is_new'] = False
            seen_jobs.append(job)
        else:
            job['is_new'] = True
            new_jobs.append(job)
    
    conn.close()
    return new_jobs, seen_jobs


def mark_jobs_seen(jobs, job_title_query="", location_query=""):
    """Store job URLs in the database so we don't show them again."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    now = datetime.now().isoformat()
    
    for job in jobs:
        try:
            cursor.execute(
                'INSERT OR IGNORE INTO seen_jobs (url, title, date_seen, job_title_query, location_query) VALUES (?, ?, ?, ?, ?)',
                (job['href'], job.get('title', ''), now, job_title_query, location_query)
            )
        except Exception as e:
            print(f"Error storing job: {e}")
    
    conn.commit()
    conn.close()


def get_seen_count():
    """Get total number of seen jobs."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM seen_jobs')
    count = cursor.fetchone()[0]
    conn.close()
    return count


def clear_memory():
    """Reset the memory — clear all seen jobs."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM seen_jobs')
    conn.commit()
    conn.close()


# Initialize the database on import
init_db()
