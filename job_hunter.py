import os
from googleapiclient.discovery import build
import google.generativeai as genai

# ==========================================
# 1. CONFIGURATION (Fill these in!)
# ==========================================
# ⚠️ PASTE YOUR KEYS HERE AGAIN ⚠️
GOOGLE_API_KEY = "AIzaSyBBhOa1LMmr2sKjWLINlAr-gj4AWr-ykjM"
SEARCH_ENGINE_ID = "940c49f564a414e20"
GEMINI_API_KEY = "AIzaSyB0-nvyrgO5lcgENaYCvKPmxFOOKz30nLM"

# ==========================================
# 2. THE MENU SYSTEM (New Feature!)
# ==========================================
def get_user_job_choice():
    """
    Displays a menu and gets the user's choice.
    """
    print("\n" + "="*40)
    print("      🤖 DIGITAL HEADHUNTER MENU 🤖      ")
    print("="*40)
    
    # The List of Jobs (You can add more here!)
    job_options = [
        "Machine Learning Engineer",
        "MERN Stack Developer",
        "Python Developer",
        "Data Scientist",
        "React JS Developer",
        "AI Research Intern",
        "Junior Software Engineer"
    ]

    # Display the list
    for index, job in enumerate(job_options):
        print(f" [{index + 1}] {job}")
    print(" [0] Type a custom job title...")

    # Ask the user to choose
    choice = input("\n👉 Enter the number of the job you want: ")

    # Logic to handle the choice
    try:
        choice_index = int(choice) - 1
        if choice_index == -1: # User chose 0
            custom_job = input("✍️  Enter your custom job title: ")
            return custom_job
        elif 0 <= choice_index < len(job_options):
            return job_options[choice_index]
        else:
            print("❌ Invalid number. Defaulting to Machine Learning Engineer.")
            return "Machine Learning Engineer"
    except ValueError:
        print("❌ Invalid input. Defaulting to Machine Learning Engineer.")
        return "Machine Learning Engineer"

# ==========================================
# 3. THE SCOUT (Updated for Freshness!)
# ==========================================
def scout_for_jobs(query):
    print(f"\n🕵️  Scout is looking for RECENT jobs: {query}...")
    
    service = build("customsearch", "v1", developerKey=GOOGLE_API_KEY)
    
    # 🆕 NEW: dateRestrict='w1' 
    # This tells Google: "Only show results from the last 1 Week"
    # You can change 'w1' to 'd3' for last 3 days.
    result = service.cse().list(
        q=query, 
        cx=SEARCH_ENGINE_ID,
        dateRestrict='w1' 
    ).execute()
    
    return result.get('items', [])

# ==========================================
# 4. THE BRAIN (Gemini Analysis)
# ==========================================
def analyze_jobs_with_gemini(job_list, job_title, location):
    print("🧠  Brain is filtering for the best matches...")
    
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-2.0-flash')

    job_text = ""
    for i, job in enumerate(job_list):
        # We include the 'snippet' which is the summary Google shows
        job_text += f"Result {i+1}: \n- Title: {job['title']}\n- Link: {job['link']}\n- Summary: {job['snippet']}\n\n"

    prompt = f"""
    I am looking for a job as a '{job_title}' in '{location}'.
    
    Here are the raw search results from Google (filtered for the last week):
    {job_text}
    
    TASK:
    1. Analyze these results. 
    2. IGNORE general job boards homepages (like just "linkedin.com" or "naukri.com"). Look for specific job postings.
    3. Select the TOP 3 most relevant specific job openings.
    4. Format the output nicely.
    
    OUTPUT FORMAT:
    --------------------------------------------------
    Job 1: [Job Title] at [Company Name (if visible)]
    --------------------------------------------------
    🔗 Link: [Insert Link]
    💡 Why it fits: [Explain why this is a good match based on the summary]
    
    (Repeat for Job 2 and 3)
    """

    response = model.generate_content(prompt)
    return response.text

# ==========================================
# 5. EXECUTION
# ==========================================
if __name__ == "__main__":
    # 1. Get the job title from the Menu
    selected_job = get_user_job_choice()
    
    # 2. Define location (You can change this or make it an input too!)
    location = "India"
    
    # 3. Create the smart query
    # We search specifically on LinkedIn and Greenhouse (a popular detailed job board)
    # OR implies it can look in either place
    search_query = f'"{selected_job}" {location} (site:linkedin.com/jobs OR site:boards.greenhouse.io)'
    
    # 4. Run the Scout
    raw_jobs = scout_for_jobs(search_query)
    
    if not raw_jobs:
        print("❌ Scout found no recent jobs. Try broadening your search.")
    else:
        print(f"✅ Scout found {len(raw_jobs)} recent results.")
        
        # 5. Run the Brain
        final_report = analyze_jobs_with_gemini(raw_jobs, selected_job, location)
        
        print("\n" + "="*40)
        print("       YOUR PERSONAL JOB REPORT       ")
        print("="*40 + "\n")
        print(final_report)
