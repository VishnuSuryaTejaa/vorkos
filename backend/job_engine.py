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
    # Time indicators
    "months ago", "month ago", "year ago", "years ago", 
    "weeks ago",  # For strict time filtering
    
    # Status indicators
    "closed", "expired", "filled",
    "no longer accepting", "position filled", "this job is closed",
    "application deadline has passed", "position has been filled",
]

# Domains that are NOT job boards
JUNK_DOMAINS = [
    "zhihu.com", "baidu.com", "quora.com", "stackoverflow.com",
    "reddit.com/r/", "medium.com", "youtube.com", "udemy.com",
    "coursera.org", "geeksforgeeks.org", "tutorialspoint.com",
    "w3schools.com", "wikipedia.org",
]


def is_likely_stale(result, time_filter="past_week"):
    """Pre-filter: check if a result looks stale or irrelevant based on time_filter."""
    title = result.get('title', '').lower()
    body = result.get('body', '').lower()
    href = result.get('href', '').lower()
    combined = f"{title} {body}"

    # Check global stale keywords
    for keyword in STALE_KEYWORDS:
        if keyword in combined:
            return True

    # Time-filter specific checks (AGGRESSIVE filtering)
    if time_filter == "past_day":
        # For 24hr filter, reject anything with days/weeks/months
        strict_patterns = [
            "days ago", "day ago", " 1 day ago", " 2 days ago",
            "yesterday", "week ago", "weeks ago", "month ago", "months ago"
        ]
        if any(pattern in combined for pattern in strict_patterns):
            return True
            
        # Also reject if it says "posted" with a specific old date
        if re.search(r'(posted|published).*\d{1,2}\s+(january|february|march|april|may|june|july|august|september|october|november|december)', combined):
            return True
            
    elif time_filter == "past_week":
        # For week filter, reject weeks/months
        week_patterns = ["weeks ago", "month ago", "months ago"]
        if any(pattern in combined for pattern in week_patterns):
            return True
            
    # For all filters, check if mentions specific old months
    recent_month_check = re.search(r'(posted|published|updated).*\d{1,2}\s+months?\s+ago', combined)
    if recent_month_check:
        # Extract number of months
        month_match = re.search(r'(\d+)\s+months?\s+ago', combined)
        if month_match:
            months_ago = int(month_match.group(1))
            if months_ago >= 1:  # Any mention of months ago = stale
                return True

    # Check junk domains
    for domain in JUNK_DOMAINS:
        if domain in href:
            return True

    # Check for old years (2019-2024)
    old_year_pattern = re.compile(r'\b(201\d|202[0-4])\b')
    if old_year_pattern.search(combined):
        date_context = re.compile(r'(posted|published|updated|date|ago|since).{0,30}(201\d|202[0-4])')
        if date_context.search(combined):
            return True

    return False


def is_search_page(url):
    """
    Detect if a URL is a search/aggregator/filter page vs a direct job posting.
    
    We want to REJECT:
    - Search pages (indeed.com/jobs?q=...)
    - Job board index/listing pages (python.org/jobs, company.com/careers)
    - Filter pages
    
    We want to KEEP:
    - Direct job postings with specific IDs (indeed.com/viewjob?jk=123)
    - Company-specific job pages (company.com/careers/position-123)
    
    Returns:
        True if the URL is a search/listing page (should be filtered out)
        False if it's a direct job posting (should be kept)
    """
    url_lower = url.lower()
    
    # Extract the path part (without domain and query params) for analysis
    from urllib.parse import urlparse
    parsed = urlparse(url_lower)
    path = parsed.path.rstrip('/')  # Remove trailing slash
    query = parsed.query
    
    # FIRST: Check for confirmed direct job posting patterns (KEEP these)
    direct_job_patterns = [
        # Indeed
        '/viewjob', '/rc/clk?jk=', '/company/', '/cmp/',
        
        # LinkedIn
        '/jobs/view/', '/postings/',
        
        # Glassdoor
        '/job-listing/', '/partner/joblisting',
        
        # Naukri (specific job pages)
        '/job-listings/', '-job-details-',
        
        # Monster
        '/job-opening/',
        
        # Company career pages with specific job IDs/slugs
        '/position/', '/opening/', '/role/',
        '/vacancy/', '/vacancies/', '/apply/',
        
        # ATS systems (Greenhouse, Lever, Workday)
        'greenhouse.io/jobs/', 'lever.co/jobs/', 'myworkdayjobs.com/',
        'bamboohr.com/jobs/', 'smartrecruiters.com/jobs/',
        
        # Job-specific indicators
        '/jobid=', '/job_id=', '/job-id-', '/posting-',
    ]
    
    for pattern in direct_job_patterns:
        if pattern in url_lower:
            return False  # Confirmed job posting, KEEP it
    
    # SECOND: Aggressive filtering of listing/index pages
    
    # Pattern 1: Job board index pages (python.org/jobs, github.com/jobs)
    # These typically end with /jobs or /careers without further path
    if path.endswith('/jobs') or path == '/jobs':
        return True  # It's a listing page, FILTER it
    
    if path.endswith('/careers') or path == '/careers':
        # Exception: if there's a slug after /careers/, it might be a specific job
        if path.count('/') <= 1:  # Just /careers, no job slug
            return True
    
    # Pattern 2: Job board paths without specific IDs
    listing_paths = [
        '/jobs/all', '/jobs/list', '/jobs/latest', '/jobs/open',
        '/careers/all', '/careers/list', '/careers/open',
        '/opportunities', '/openings',
    ]
    for listing_path in listing_paths:
        if listing_path in path:
            return True
    
    # Pattern 3: Search/filter query patterns
    search_patterns = [
        # Generic search patterns
        '/jobs?', '/jobs/search', '/search?', '/search/',
        'jobs?q=', '?q=', '&q=', '/q-', '/l-',
        
        # Job board specific search patterns
        '/jobs-in-', '/-jobs-', '/Search/', '/collections/',
        'job/jobs.htm', '/jobs/collections', '/job-search',
        
        # Naukri patterns
        'naukri.com/jobs-in', 'naukri.com/-jobs',
        
        # Indeed patterns
        '/pagead/clk?mo=r&',  # Indeed's redirect pages
        
        # Filter/category pages
        '/browse/', '/category/', '/filter/',
    ]
    
    for pattern in search_patterns:
        if pattern in url_lower:
            return True  # Search page, FILTER it
    
    # Pattern 4: Query parameters that indicate search/filter (not job-specific)
    if query:
        # Has query params - check if they're search-related
        search_params = ['?q=', '&q=', 'search=', 'filter=', 'location=', 'category=']
        has_search_param = any(param in url_lower for param in search_params)
        
        # Check for job-specific params
        job_params = ['jk=', 'job_id=', 'jobid=', 'id=', 'posting=', 'gh_jid=']
        has_job_param = any(param in url_lower for param in job_params)
        
        if has_search_param and not has_job_param:
            return True  # Search params without job ID = listing page
    
    # Pattern 5: Specific domain patterns known to be listing pages
    listing_domains = [
        # If URL is just domain.com/jobs with nothing after
        'python.org/jobs',
        'github.com/jobs',
        'stackoverflow.com/jobs',
        'djangojobs.net',
    ]
    
    for domain_pattern in listing_domains:
        if domain_pattern in url_lower and len(path.split('/')) <= 2:
            return True
    
    # Pattern 6: Path depth heuristic
    # Most direct job postings have deeper paths or specific identifiers
    # Example: /careers/engineering/senior-dev-123 (good)
    # vs: /careers (bad - listing page)
    if ('/jobs' in path or '/careers' in path):
        # Count slashes - if path is shallow, likely a listing page
        path_depth = len([p for p in path.split('/') if p])
        if path_depth == 1:  # Just /jobs or /careers
            return True
    
    # Default: If we're not sure, let it through (conservative)
    # Better to let some listings through than filter real jobs
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
            # Limit to 1500 chars to save Groq tokens (was 2000)
            text = response.text[:1500]
            return text
        return ""
    except Exception as e:
        print(f"  ⚠️ Deep read failed for {url[:40]}...: {e}")
        return ""


def deep_read_jobs(jobs, max_jobs=20):
    """
    CRITICAL: Deep read ALL jobs to get full page content with REAL dates.
    Tavily snippets often say "Posted today" but actual page shows old dates.
    Increased max_jobs to ensure we validate ALL job dates properly.
    """
    print(f"📖 Deep reading ALL {min(len(jobs), max_jobs)} job pages for date validation...")

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
    
    print(f"🕵️ Tavily scouting for: {job_title} in {location} (type: {job_type}, time: {time_filter})...")
    
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
    
    # Map time_filter to Tavily days parameter (STRICT filtering at source)
    time_to_days = {
        "past_day": 1,     # Only last 24 hours
        "past_week": 7,    # Only last 7 days
        "past_month": 30,  # Only last 30 days
    }
    days_limit = time_to_days.get(time_filter, 7)
    
    # Construct the search query
    query = f"{job_title} {type_kw} in {location}"
    
    try:
        # Tavily searches and reads the content in one go
        # Using days parameter for strict time filtering
        response = tavily_client.search(
            query=query,
            search_depth="basic",
            max_results=25,
            days=days_limit,  # CRITICAL: Only return results from last N days
        )
        
        # Normalize data for Groq
        normalized_jobs = []
        for result in response.get('results', []):
            job = {
                "title": result.get('title', ''),
                "href": result.get('url', ''),
                "body": result.get('content', '')  # Tavily gives us the text content directly!
            }
            
            # Pre-filter: stale results AND search/aggregator pages
            is_stale = is_likely_stale(job, time_filter)  # Pass time_filter for strict checking
            is_search = is_search_page(job['href'])
            
            if not is_stale and not is_search:
                normalized_jobs.append(job)
            else:
                # Log why it was filtered
                if is_stale and is_search:
                    reason = "stale + search page"
                elif is_stale:
                    reason = f"stale (filter: {time_filter})"
                else:
                    reason = "search/aggregator page"
                print(f"  🗑️  Filtered ({reason}): {job['title'][:50]}...")
        
        print(f"✅ Found {len(normalized_jobs)} direct job postings after filtering.")
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

    # Define the core analysis function
    def execute_analysis(current_api_key, key_name):
        print(f"🤖 Agent activated using {key_name} key...")
        client = Groq(api_key=current_api_key)
        
        # --- 1. Prepare Evidence ---
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

        ⚠️ CRITICAL DATE VALIDATION RULES ⚠️
        The job listings you receive may contain MISLEADING date information in snippets.
        You MUST validate dates using the FULL CONTENT field.
        
        DATE VALIDATION PROTOCOL:
        1. Check the FULL CONTENT for date indicators: "years ago", "months ago", "weeks ago", "days ago"
        2. If you see "2 years ago", "6 months ago", "3 weeks ago" in content → REJECT IMMEDIATELY
        3. If no clear recent date is visible → ASSUME IT'S OLD and REJECT
        4. ONLY accept jobs that explicitly show: "today", "yesterday", "1 day ago", "2 days ago" for past_day filter
        5. For past_week: ONLY accept "today", "yesterday", "X days ago" where X ≤ 7
        6. If a job page shows date indicators like "2yr", "6yr", "months" → IMMEDIATE REJECTION

        Your Prime Directives:
        1. FILTER RUTHLESSLY: {freshness_persona.get(time_filter, freshness_persona["past_week"])}
        2. DATE VALIDATION: Check FULL CONTENT for actual dates. Snippets LIE. Trust only full page content.
        3. JOB TYPE FILTER: {job_type_instruction}
        4. DETECT SEO SPAM: Articles, LinkedIn profiles (not job posts), forums, tutorials — BURN THEM.
        5. PRIORITIZE "NEW" JOBS: Jobs marked "NEW ✨" should rank higher.
        6. CHECK FOR "CLOSED": If content says "closed", "expired", "position filled" — REJECT.
        7. NO DATE VISIBLE = OLD JOB: If you can't clearly see a recent date, REJECT IT.
        8. NEVER INVENT: If fewer than 3 good jobs exist, stop early. Do NOT hallucinate.
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

        # Job type display
        type_display = f" ({job_type.upper()})" if job_type != "any" else ""

        # --- 4. The Mission ---
        user_prompt = f"""
        MISSION: Find the top 5 ACTIVE{type_display} job openings for '{job_title}' in '{location}'.
        CURRENT DATE: {datetime.date.today().strftime("%B %d, %Y")}
        TIME FILTER: {time_filter}

        Here is the raw data stream from the web:
        {job_text}

        ⚠️ CRITICAL: Each job's CONTENT field contains the FULL PAGE TEXT.
        The snippet may say "Posted today" but the full content shows the REAL date.
        You MUST read the FULL CONTENT carefully for date indicators.

        --------------------------------------------------
        YOUR ANALYSIS PROCESS (Mental Scratchpad):
        For EACH job match:
        0. FIRST: Scan the CONTENT for date indicators ("years ago", "yr", "months ago", etc.)
        1. Does CONTENT show "years ago", "yr", "6 months ago", "2 weeks ago"? → REJECT IMMEDIATELY.
        2. Does the content say "closed", "expired", "filled"? → REJECT.
        3. Is the title a person's name/profile (not a job)? → REJECT.
        4. Is the URL a blog, tutorial, or forum? → REJECT.
        5. Is it from a job board or company careers page? → Check date anyway.
        6. Does it mention tech stacks, "hiring", "apply now", salary? → Good sign, but CHECK DATE FIRST.
        7. Does the job type match "{job_type}"? → If not, REJECT.
        8. Can you see a clear, recent date matching {time_filter}? → If NO, REJECT.
        --------------------------------------------------
        {resume_section}

        FINAL OUTPUT FORMAT:

        ### 🏆 TOP JOB MATCH [1]
        **Job Title:** [Exact Title]
        **Company:** [Company Name]
        **Type:** [Internship / Full-Time / Contract / etc.]
        **Location:** [Where]
        **Freshness:** [e.g. "Posted today", "2 days ago"]
        {{
        '**Fit Score:** [0-100%]' if resume_text else ''
        }}
        **Why it matches:** [1 sentence]
        {{
        '**✅ Matches:** [Skills you have that match]' if resume_text else ''
        }}
        {{
        '**⚠️ Gaps:** [Skills required but missing from resume]' if resume_text else ''
        }}
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

    # --- EXECUTION STRATEGY: STRICT PRIMARY → BACKUP FAILOVER ---
    
    # 1. Attempt with Primary Key
    primary_key = os.environ.get("GROQ_API_KEY") or api_key
    backup_key = os.environ.get("GROQ_API_KEY_BACKUP")
    
    if not primary_key:
        return "❌ Configuration Error: No Primary API Key found."

    try:
        return execute_analysis(primary_key, "PRIMARY")
    except Exception as e:
        error_str = str(e)
        
        # Check for Rate Limit (429)
        if "429" in error_str or "rate_limit" in error_str.lower():
            print(f"⚠️ Primary Key hit RATE LIMIT! Initiating failover protocol...")
            
            if backup_key:
                print(f"🔄 Failover: Retrying with BACKUP key...")
                try:
                    return execute_analysis(backup_key, "BACKUP 🛡️")
                except Exception as e2:
                    return f"❌ Critical Failure: Both API keys failed. Backup Error: {str(e2)}"
            else:
                return f"❌ Rate limit hit on Primary Key and NO Backup Key configured."
        
        # Return other errors immediately
        return f"❌ Analysis Error: {error_str}"
