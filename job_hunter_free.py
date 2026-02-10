import os
from ddgs import DDGS
import google.generativeai as genai

# ==========================================
# 1. CONFIGURATION
# ==========================================
# ⚠️ YOU ONLY NEED ONE KEY NOW! ⚠️
GEMINI_API_KEY = "AIzaSyBBhOa1LMmr2sKjWLINlAr-gj4AWr-ykjM"

# ==========================================
# 2. THE MENU SYSTEM
# ==========================================
def get_user_job_choice():
    print("\n" + "="*40)
    print("      🦆 FREELANCE JOB HUNTER 🦆      ")
    print("="*40)
    
    job_options = [
        "Machine Learning Engineer",
        "MERN Stack Developer",
        "Python Developer",
        "Data Scientist",
        "React JS Developer",
        "AI Research Intern",
        "Junior Software Engineer"
    ]

    for index, job in enumerate(job_options):
        print(f" [{index + 1}] {job}")
    print(" [0] Type a custom job title...")

    choice = input("\n👉 Enter the number of the job you want: ")

    try:
        choice_index = int(choice) - 1
        if choice_index == -1:
            return input("✍️  Enter your custom job title: ")
        elif 0 <= choice_index < len(job_options):
            return job_options[choice_index]
        else:
            return "Machine Learning Engineer"
    except ValueError:
        return "Machine Learning Engineer"

# ==========================================
# 3. THE FREELANCER (DuckDuckGo Search)
# ==========================================
def scout_for_jobs(job_title, location):
    print(f"\n🦆 Scout is searching DuckDuckGo for: {job_title}...")
    
    # We construct a query to look for jobs on LinkedIn and Greenhouse
    # "t=w" is a special DuckDuckGo code for "Time = Past Week"
    # query = f'{job_title} {location} site:linkedin.com/jobs OR site:boards.greenhouse.io'
    query = f'{job_title} {location} jobs'
    
    results = []
    
    # We use the DDGS (DuckDuckGo Search) tool
    # region="in-en" means "India - English"
    with DDGS() as ddgs:
        # We ask for 10 results from the past week (timelimit='w')
        # region='wt-wt' means "No Region" (Wait for global results to debugging)
        search_results = ddgs.text(query, timelimit='m', max_results=10)
        
        for r in search_results:
            results.append(r)
            
    return results

# ==========================================
# 4. THE BRAIN (Gemini Analysis)
# ==========================================
def analyze_jobs_with_gemini(job_list, job_title, location):
    print("🧠  Brain is filtering for the best matches...")
    
    genai.configure(api_key=GEMINI_API_KEY)
    # Note: Using "gemini-flash-latest" as a fallback for free tier
    model = genai.GenerativeModel('gemini-flash-latest')

    job_text = ""
    for i, job in enumerate(job_list):
        # DuckDuckGo gives us 'title', 'href' (link), and 'body' (snippet)
        job_text += f"Result {i+1}: \n- Title: {job['title']}\n- Link: {job['href']}\n- Summary: {job['body']}\n\n"

    prompt = f"""
    I am looking for a job as a '{job_title}' in '{location}'.
    
    Here are the raw search results from the web:
    {job_text}
    
    TASK:
    1. Analyze these results. 
    2. IGNORE general login pages or profile pages. Look for specific job postings.
    3. Select the TOP 3 most relevant specific job openings.
    
    OUTPUT FORMAT:
    --------------------------------------------------
    Job: [Job Title]
    --------------------------------------------------
    🔗 Link: [Insert Link]
    💡 Why it fits: [Explain based on the summary]
    """

    response = model.generate_content(prompt)
    return response.text

# ==========================================
# 5. EXECUTION
# ==========================================
if __name__ == "__main__":
    selected_job = get_user_job_choice()
    location = "India"
    
    # 1. Send the Freelancer (DuckDuckGo)
    raw_jobs = scout_for_jobs(selected_job, location)
    
    if not raw_jobs:
        print("❌ Scout found no recent jobs. Try broadening your search.")
    else:
        print(f"✅ Scout found {len(raw_jobs)} recent results.")
        
        # 2. Ask the Brain (Gemini)
        final_report = analyze_jobs_with_gemini(raw_jobs, selected_job, location)
        
        print("\n" + "="*40)
        print("       YOUR PERSONAL JOB REPORT       ")
        print("="*40 + "\n")
        print(final_report)
