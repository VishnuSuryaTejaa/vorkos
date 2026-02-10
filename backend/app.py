from flask import Flask, request, jsonify
try:
    from backend.job_engine import scout_for_jobs, deep_read_jobs, analyze_jobs_with_groq
    from backend.job_memory import filter_new_jobs, mark_jobs_seen, get_seen_count, clear_memory
except ImportError:
    from job_engine import scout_for_jobs, deep_read_jobs, analyze_jobs_with_groq
    from job_memory import filter_new_jobs, mark_jobs_seen, get_seen_count, clear_memory
import os
import io
import PyPDF2
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Groq API key for Llama 3.3 analysis
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# In-memory resume storage (persists while server is running)
USER_RESUME = {"text": ""}

# Job role options — expanded list
JOB_ROLES = [
    # AI/ML
    "Machine Learning Engineer",
    "AI Research Intern",
    "Data Scientist",
    "Data Analyst",
    "Deep Learning Engineer",
    "NLP Engineer",
    "Computer Vision Engineer",
    "MLOps Engineer",
    # Web Development
    "MERN Stack Developer",
    "Full Stack Developer",
    "Frontend Developer",
    "Backend Developer",
    "React JS Developer",
    "Node.js Developer",
    "Next.js Developer",
    "Angular Developer",
    "Vue.js Developer",
    # Software Engineering
    "Junior Software Engineer",
    "Software Engineer",
    "Senior Software Engineer",
    "Python Developer",
    "Java Developer",
    "Go Developer",
    "Rust Developer",
    "C++ Developer",
    # Mobile
    "Android Developer",
    "iOS Developer",
    "Flutter Developer",
    "React Native Developer",
    # Infrastructure & DevOps
    "DevOps Engineer",
    "Cloud Engineer",
    "Site Reliability Engineer",
    "AWS Solutions Architect",
    "Kubernetes Engineer",
    # Data & Analytics
    "Data Engineer",
    "Database Administrator",
    "Business Intelligence Analyst",
    "ETL Developer",
    # Security & Other
    "Cybersecurity Analyst",
    "Blockchain Developer",
    "QA Engineer",
    "Technical Writer",
    "UI/UX Designer",
    "Product Manager",
    "Scrum Master",
]

# Location options
LOCATIONS = [
    "Remote",
    "India",
    "Bangalore",
    "Hyderabad",
    "Mumbai",
    "Delhi NCR",
    "Chennai",
    "Pune",
    "United States",
    "United Kingdom",
    "Germany",
    "Canada",
    "Australia",
    "Singapore",
    "Dubai",
    "Netherlands",
    "Japan",
]

# Job type options
JOB_TYPES = [
    {"value": "any", "label": "Any Type"},
    {"value": "internship", "label": "🎓 Internship"},
    {"value": "fulltime", "label": "💼 Full Time"},
    {"value": "parttime", "label": "⏰ Part Time"},
    {"value": "contract", "label": "📄 Contract"},
    {"value": "freelance", "label": "🌐 Freelance"},
]

# Time filter options
TIME_FILTERS = [
    {"value": "past_day", "label": "⚡ Past 24 Hours"},
    {"value": "past_week", "label": "📅 Past Week"},
    {"value": "past_month", "label": "📆 Past Month"},
]

@app.after_request
def after_request(response):
    """Add CORS headers to every response"""
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type,Authorization'
    response.headers['Access-Control-Allow-Methods'] = 'GET,POST,OPTIONS'
    return response

@app.route('/api/options', methods=['GET', 'OPTIONS'])
def get_options():
    """Return dropdown data + memory stats"""
    if request.method == 'OPTIONS':
        return jsonify({})
    return jsonify({
        "job_roles": JOB_ROLES,
        "locations": LOCATIONS,
        "time_filters": TIME_FILTERS,
        "job_types": JOB_TYPES,
        "memory_count": get_seen_count(),
        "has_resume": bool(USER_RESUME["text"].strip()),
    })

# --- Resume Endpoints ---
@app.route('/api/resume', methods=['GET', 'POST', 'OPTIONS'])
def handle_resume():
    """Save or retrieve the user's resume text."""
    if request.method == 'OPTIONS':
        return jsonify({})
    
    if request.method == 'POST':
        data = request.json
        USER_RESUME["text"] = data.get('resume_text', '')
        return jsonify({"status": "saved", "length": len(USER_RESUME["text"])})
    
    # GET
    return jsonify({"resume_text": USER_RESUME["text"]})

@app.route('/api/resume/upload', methods=['POST', 'OPTIONS'])
def upload_resume():
    """Upload a PDF resume — extract text using PyPDF2."""
    if request.method == 'OPTIONS':
        return jsonify({})
    
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400
    
    if not file.filename.lower().endswith('.pdf'):
        return jsonify({"error": "Only PDF files are supported"}), 400
    
    try:
        # Read PDF and extract text
        pdf_bytes = io.BytesIO(file.read())
        reader = PyPDF2.PdfReader(pdf_bytes)
        
        text = ""
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
        
        if not text.strip():
            return jsonify({"error": "Could not extract text from PDF. Try a different file."}), 400
        
        # Store the resume text
        USER_RESUME["text"] = text.strip()
        print(f"📋 Resume uploaded: {file.filename} ({len(text)} chars, {len(reader.pages)} pages)")
        
        return jsonify({
            "status": "uploaded",
            "filename": file.filename,
            "pages": len(reader.pages),
            "length": len(text),
            "preview": text[:300] + "..." if len(text) > 300 else text,
        })
    except Exception as e:
        return jsonify({"error": f"Failed to parse PDF: {str(e)}"}), 500

# --- Clear Memory ---
@app.route('/api/memory/clear', methods=['POST', 'OPTIONS'])
def clear_job_memory():
    """Reset the job memory database."""
    if request.method == 'OPTIONS':
        return jsonify({})
    clear_memory()
    return jsonify({"status": "cleared"})

@app.route('/api/hunt', methods=['POST', 'OPTIONS'])
def hunt_jobs():
    if request.method == 'OPTIONS':
        return jsonify({})

    data = request.json
    job_title = data.get('job_title')
    location = data.get('location')
    time_filter = data.get('time_filter', 'past_week')
    job_type = data.get('job_type', 'any')

    if not all([job_title, location]):
        return jsonify({"error": "Missing required fields: job_title, location"}), 400

    print(f"\n{'='*60}")
    print(f"🕵️  HUNT: {job_title} in {location} (Filter: {time_filter}, Type: {job_type})")
    print(f"{'='*60}")

    # --- STEP 1: Parallel Scout (job_type baked into queries) ---
    raw_jobs = scout_for_jobs(job_title, location, time_filter, job_type=job_type)
    if not raw_jobs:
        return jsonify({
            "jobs_found": 0,
            "new_jobs": 0,
            "raw_jobs": [],
            "analysis": "❌ No fresh jobs found. Try 'Past Month' filter or different search terms."
        })

    # --- STEP 2: SQLite Dedup ---
    new_jobs, seen_jobs = filter_new_jobs(raw_jobs)
    print(f"💾 Memory check: {len(new_jobs)} NEW, {len(seen_jobs)} already seen")

    # Combine: new jobs first, then seen jobs
    all_jobs = new_jobs + seen_jobs

    # --- STEP 3: Deep Reader ---
    if new_jobs:
        all_jobs = deep_read_jobs(all_jobs, max_jobs=8)

    # --- STEP 4: AI Analysis with Resume ---
    resume_text = USER_RESUME.get("text", "")
    print(f"📋 Resume: {'Loaded (' + str(len(resume_text)) + ' chars)' if resume_text else 'Not provided'}")
    print(f"⚡ Analyzing {len(all_jobs)} results with Groq...")

    analysis = analyze_jobs_with_groq(
        all_jobs, job_title, location, GROQ_API_KEY,
        time_filter=time_filter,
        resume_text=resume_text,
        job_type=job_type
    )

    # --- STEP 5: Store new jobs in memory ---
    if new_jobs:
        mark_jobs_seen(new_jobs, job_title, location)
        print(f"💾 Stored {len(new_jobs)} new jobs in memory")

    print(f"✅ Hunt complete! Total: {len(all_jobs)}, New: {len(new_jobs)}")
    print(f"{'='*60}\n")

    return jsonify({
        "jobs_found": len(all_jobs),
        "new_jobs": len(new_jobs),
        "seen_jobs": len(seen_jobs),
        "raw_jobs": [{
            "title": j["title"],
            "href": j["href"],
            "body": j["body"],
            "is_new": j.get("is_new", True)
        } for j in all_jobs],
        "analysis": analysis
    })

if __name__ == '__main__':
    app.run(debug=True, port=5001, host='0.0.0.0')
