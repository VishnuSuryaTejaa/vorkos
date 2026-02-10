import datetime
import re
import requests
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from tavily import TavilyClient
from groq import Groq
from job_memory import filter_new_jobs, mark_jobs_seen

# Initialize Tavily client
TAVILY_API_KEY = os.environ.get("TAVILY_API_KEY")
tavily_client = TavilyClient(api_key=TAVILY_API_KEY) if TAVILY_API_KEY else None

# Time limit mapping
TIME_LIMITS = {
    "past_day": "d",
    "past_week": "w",
    "past_month": "m",
}

# Keywords that indicate a stale/closed/irrelevant result
STALE_KEYWORDS = [
    "months ago", "year ago", "years ago", "closed", "expired",
    "no longer accepting", "position filled", "this job is closed",
]

# Domains that are NOT job boards
JUNK_DOMAINS = [
    "zhihu.com", "baidu.com", "quora.com", "stackoverflow.com",
    "reddit.com/r/", "medium.com", "youtube.com", "udemy.com",
    "coursera.org", "geeksforgeeks.org", "tutorialspoint.com",
    "w3schools.com", "wikipedia.org",
]


def is_likely_stale(result):
    """Pre-filter: check if a result looks stale or irrelevant."""
    title = result.get('title', '').lower()
    body = result.get('body', '').lower()
    href = result.get('href', '').lower()
    combined = f"{title} {body}"

    for keyword in STALE_KEYWORDS:
        if keyword in combined:
            return True

    for domain in JUNK_DOMAINS:
        if domain in href:
            return True

    old_year_pattern = re.compile(r'\b(201\d|202[0-4])\b')
    if old_year_pattern.search(combined):
        date_context = re.compile(r'(posted|published|updated|date|ago|since).{0,30}(201\d|202[0-4])')
        if date_context.search(combined):
            return True

    return False


# ==========================================
# UPGRADE 1: DEEP READER (Jina AI)
# ==========================================
def fetch_full_job_content(url):
    """
    Fetch full page text using Jina AI Reader.
    Jina converts messy HTML into clean, LLM-ready markdown for free.
    """
    try:
        jina_url = f"https://r.jina.ai/{url}"
        response = requests.get(jina_url, timeout=8, headers={
            "Accept": "text/plain"
        })
        if response.status_code == 200:
            # Limit to 3000 chars to save Groq tokens
            text = response.text[:3000]
            return text
        return ""
    except Exception as e:
        print(f"  ⚠️ Deep read failed for {url[:40]}...: {e}")
        return ""


def deep_read_jobs(jobs, max_jobs=8):
    """
    UPGRADE 1: For the top N jobs, fetch full page content in parallel.
    This gives the AI 3000 chars of context instead of ~160 char snippets.
    """
    print(f"📖 Deep reading top {min(len(jobs), max_jobs)} job pages...")

    def read_single(job):
        content = fetch_full_job_content(job['href'])
        if content:
            job['full_content'] = content
            print(f"  ✅ Deep read: {job['title'][:40]}...")
        else:
            job['full_content'] = job.get('body', '')
        return job

    # Read pages in parallel (3 at a time to respect rate limits)
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {executor.submit(read_single, job): job for job in jobs[:max_jobs]}
        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                print(f"  ⚠️ Deep read error: {e}")

    # Jobs beyond max_jobs keep their original snippet
    for job in jobs[max_jobs:]:
        job['full_content'] = job.get('body', '')

    return jobs


# ==========================================
# SCOUT (Tavily - Never Blocked on Render)
# ==========================================
def scout_for_jobs(job_title, location, time_filter="past_week", job_type="any"):
    """
    Tavily search with job type filtering.
    Never blocked on Render, works 100% of the time.
    """
    if not tavily_client:
        return []
    
    print(f"🕵️ Tavily scouting for: {job_title} in {location} (type: {job_type})...")
    
    # Build type-specific search keywords
    type_keywords = {
        "internship": "internship OR intern OR trainee",
        "fulltime": "full-time OR full time OR permanent",
        "parttime": "part-time OR part time",
        "contract": "contract OR freelance OR temporary",
        "freelance": "freelance OR remote contract",
        "any": "jobs",
    }
    type_kw = type_keywords.get(job_type, "jobs")
    
    # Construct the search query
    query = f"{job_title} {type_kw} in {location}"
    
    try:
        # Tavily searches and reads the content in one go
        # NO domain restrictions - search the entire web for job postings
        response = tavily_client.search(
            query=query,
            search_depth="basic",
            max_results=25,  # Increased for more diverse results
        )
        
        # Normalize data for Groq
        normalized_jobs = []
        for result in response.get('results', []):
            job = {
                "title": result.get('title', ''),
                "href": result.get('url', ''),
                "body": result.get('content', '')  # Tavily gives us the text content directly!
            }
            
            # Pre-filter stale results
            if not is_likely_stale(job):
                normalized_jobs.append(job)
            else:
                print(f"  🗑️  Pre-filtered: {job['title'][:50]}...")
        
        print(f"✅ Found {len(normalized_jobs)} raw jobs after pre-filtering.")
        return normalized_jobs[:20]
    
    except Exception as e:
        print(f"❌ Scout Error: {e}")
        return []


# ==========================================
# THE BRAIN — God-Tier Prompting + Resume Matching
# ==========================================
def analyze_jobs_with_groq(job_list, job_title, location, api_key, time_filter="past_week", resume_text="", job_type="any"):
    """
    UPGRADE 2: Now includes Resume Matchmaker for Fit Score + Gap analysis.
    Uses deep-read content when available.
    Automatically falls back to backup API key if rate limit is hit.
    """
    if not job_list:
        return "No jobs found to analyze."

    print("⚡ Groq Forensic Analysis starting...")

    # Get backup API key from environment
    backup_api_key = os.environ.get("GROQ_API_KEY_BACKUP")
    
    # Function to attempt analysis with a given API key
    def attempt_analysis(key_to_use, is_backup=False):
        client = Groq(api_key=key_to_use)
        
        if is_backup:
            print("🔄 Retrying with backup API key...")

        # --- 1. Prepare Evidence (with deep content when available) ---
        job_text = ""
        for i, job in enumerate(job_list):
            full_content = job.get('full_content', job.get('body', ''))
            job_text += f"""
            [JOB MATCH #{i+1}]
            - URL: {job['href']}
            - TITLE: {job['title']}
            - CONTENT: {full_content[:2500]}
            - NEW: {"YES ✨" if job.get('is_new', True) else "PREVIOUSLY SEEN"}
            """

        # --- 2. The Persona ---
        freshness_persona = {
            "past_day": "If a job looks older than 24 HOURS, discard it immediately.",
            "past_week": "If a job looks older than 7 DAYS, discard it immediately.",
            "past_month": "If a job looks older than 30 DAYS, discard it immediately.",
        }

        # Job type filter instruction
        job_type_labels = {
            "internship": "ONLY include INTERNSHIP positions. Reject full-time, contract, or senior roles.",
            "fulltime": "ONLY include FULL-TIME positions. Reject internships, part-time, or contract roles.",
            "parttime": "ONLY include PART-TIME positions. Reject full-time or internship roles.",
            "contract": "ONLY include CONTRACT positions. Reject permanent or internship roles.",
            "freelance": "ONLY include FREELANCE or REMOTE CONTRACT positions.",
            "any": "Include any job type (internship, full-time, contract, etc.).",
        }
        job_type_instruction = job_type_labels.get(job_type, job_type_labels["any"])

        system_prompt = f"""
        You are an Elite Technical Recruiter and Forensic Job Analyst.
        Your standard is perfection. You DO NOT tolerate old, stale, or irrelevant results.

        Your Prime Directives:
        1. FILTER RUTHLESSLY: {freshness_persona.get(time_filter, freshness_persona["past_week"])}
        2. JOB TYPE FILTER: {job_type_instruction}
        3. DETECT SEO SPAM: Articles, LinkedIn profiles (not job posts), forums, tutorials — BURN THEM.
        4. PRIORITIZE "NEW" JOBS: Jobs marked "NEW ✨" should rank higher.
        5. CHECK FOR "CLOSED": If content says "closed", "expired", "position filled" — REJECT.
        6. NEVER INVENT: If fewer than 3 good jobs exist, stop early. Do NOT hallucinate.
        """

        # --- 3. Resume matching section ---
        resume_section = ""
        if resume_text and resume_text.strip():
            resume_section = f"""

        📋 CANDIDATE RESUME:
        {resume_text[:2000]}

        ADDITIONAL TASK — RESUME MATCHING:
        For each job, compare the requirements against the candidate's resume and provide:
        - **Fit Score (0-100%)**: How well the candidate matches
        - **✅ Matches**: Skills/experience the candidate HAS that the job requires
        - **⚠️ Gaps**: Skills the job requires but the candidate LACKS
        """

        # Job type label for display
        type_display = f" ({job_type.upper()})" if job_type != "any" else ""

        # --- 4. The Mission ---
        user_prompt = f"""
        MISSION: Find the top 5 ACTIVE{type_display} job openings for '{job_title}' in '{location}'.
        CURRENT DATE: {datetime.date.today().strftime("%B %d, %Y")}

        Here is the raw data stream from the web:
        {job_text}

        --------------------------------------------------
        YOUR ANALYSIS PROCESS (Mental Scratchpad):
        For EACH job match:
        1. Does the content say "posted 5 months ago", "closed", "expired", "6yr"? → REJECT.
        2. Is the title a person's name/profile (not a job)? → REJECT.
        3. Is the URL a blog, tutorial, or forum? → REJECT.
        4. Is it from a job board or company careers page? → STRONG KEEP.
        5. Does it mention tech stacks, "hiring", "apply now", salary? → KEEP.
        6. Does the job type match "{job_type}"? → If not, REJECT.
        --------------------------------------------------
        {resume_section}

        FINAL OUTPUT FORMAT:

        ### 🏆 TOP JOB MATCH [1]
        **Job Title:** [Exact Title]
        **Company:** [Company Name]
        **Type:** [Internship / Full-Time / Contract / etc.]
        **Location:** [Where]
        **Freshness:** [e.g. "Posted today", "2 days ago"]
        {
        '**Fit Score:** [0-100%]' if resume_text else ''
        }
        **Why it matches:** [1 sentence]
        {
        '**✅ Matches:** [Skills you have that match]' if resume_text else ''
        }
        {
        '**⚠️ Gaps:** [Skills required but missing from resume]' if resume_text else ''
        }
        **Direct Link:** [Full URL]

        (Repeat for Top 2-5. Stop early if fewer exist. DO NOT INVENT JOBS.)

        If ZERO real job postings pass your filters, say:
        "❌ No fresh, legitimate job postings found. Try 'Past Month' filter or search directly on LinkedIn/Indeed."
        """

        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.3,
        )
        return chat_completion.choices[0].message.content

    # Try with primary key first
    try:
        return attempt_analysis(api_key, is_backup=False)
    except Exception as e:
        error_str = str(e)
        
        # Check if it's a rate limit error (429)
        if "429" in error_str or "rate_limit_exceeded" in error_str.lower():
            print(f"⚠️ Rate limit hit on primary key: {error_str[:100]}...")
            
            # Try backup key if available
            if backup_api_key:
                try:
                    return attempt_analysis(backup_api_key, is_backup=True)
                except Exception as backup_error:
                    return f"Error in Groq analysis (backup also failed): {str(backup_error)}"
            else:
                return f"Error in Groq analysis: {error_str}"
        else:
            # For non-rate-limit errors, return immediately
            return f"Error in Groq analysis: {error_str}"

