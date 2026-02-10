#!/usr/bin/env python3
"""
Test script for Tavily + Groq integration
"""
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add backend to path
sys.path.append('backend')

from job_engine import scout_for_jobs, analyze_jobs_with_groq

def test_tavily_groq():
    """Test the Tavily scout + Groq brain integration"""
    
    # Test parameters
    job_title = "Software Engineer"
    location = "Bangalore"
    time_filter = "past_week"
    
    print("=" * 60)
    print("🧪 Testing Tavily + Groq Hybrid Architecture")
    print("=" * 60)
    print(f"Job Title: {job_title}")
    print(f"Location: {location}")
    print(f"Time Filter: {time_filter}")
    print("=" * 60)
    
    # Step 1: Scout for jobs using Tavily
    print("\n🔍 STEP 1: Scout Phase (Tavily)")
    print("-" * 60)
    jobs = scout_for_jobs(job_title, location, time_filter)
    
    if not jobs:
        print("❌ No jobs found. Check your Tavily API key.")
        return
    
    print(f"\n✅ Scout found {len(jobs)} jobs")
    print("\nFirst job preview:")
    print(f"  Title: {jobs[0]['title'][:60]}...")
    print(f"  URL: {jobs[0]['href'][:60]}...")
    print(f"  Content length: {len(jobs[0]['body'])} chars")
    
    # Step 2: Analyze with Groq
    print("\n\n🧠 STEP 2: Brain Phase (Groq)")
    print("-" * 60)
    
    groq_api_key = os.environ.get("GROQ_API_KEY")
    if not groq_api_key:
        print("❌ GROQ_API_KEY not found in environment")
        return
    
    analysis = analyze_jobs_with_groq(
        jobs, 
        job_title, 
        location, 
        groq_api_key,
        time_filter
    )
    
    print("\n" + "=" * 60)
    print("📊 FINAL ANALYSIS")
    print("=" * 60)
    print(analysis)
    print("\n" + "=" * 60)
    print("✅ Test Complete!")
    print("=" * 60)

if __name__ == "__main__":
    test_tavily_groq()
