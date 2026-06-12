import os
import json
import time
import requests
import re
import pytz
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta

# ==============================================================================
# SECTION 1: SETTING UP THE "ADDRESS BOOK" (CONFIGURATION)
# ==============================================================================

WEBHOOK_URL = "https://discord.com/api/webhooks/1507607044331536434/DBXk5Nuq1MWn9ROMBc-S7M3sCqD-PgyTOw676rXEY3kyAJ2ViRojOKphYb5mb7-5ty_X"
POSTED_JOBS_FILE = "posted_jobs.json"
EASTERN_TZ = pytz.timezone('US/Eastern')

# AI SEARCH CONFIG
SERPER_API_KEY = "465dd23e1e1816618110e6018adc31597456177c" 

# Common headers to prevent blocks
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}

CATEGORIES = ["quality-assurance", "data", "software-dev", "business", "engineering", "customer-support"]
KEYWORDS_SEARCH = ["manual testing", "underwriter", "risk examiner", "metrology", "QA", "Software Tester", "Credit Risk Analyst", "Quality Assurance", "Building Automation", "Data Center Technician", "HVAC Apprentice", "Field Service Technician"]

REMOTIVE_BASE_API = "https://remotive.com/api/remote-jobs"
ARBEITNOW_API = "https://www.arbeitnow.com/api/job-board-api"
HIMALAYAS_BASE_API = "https://himalayas.app/jobs/api/search"
JOBICY_API = "https://jobicy.com/api/v2/remote-jobs"
REMOTE_OK_API = "https://remoteok.com/api"
THE_MUSE_API = "https://www.themuse.com/api/public/jobs"
WWR_RSS_URL = "https://weworkremotely.com/categories/remote-programming-jobs.rss"

# Inclusion Keywords (Entry to Mid Level focus)
QA_KEYWORDS = [
    "qa", "manual", "tester", "quality assurance", "testing", "quality control", "test engineer",
    "risk examiner", "underwriter", "metrology", "sdet", "assurance engineer", "chaos performance",
    "reliability engineer", "release engineer", "health information specialist", "entry level", "junior",
    "claims examiner", "reinsurance", "governance", "associate", "mid level", "mid-level", "backend sdet", "manual tester", "automation",
    "building automation", "controls technician", "bas technician", "ddc technician", "data center technician", "hvac apprentice", "hvac helper", "field service technician"
]

# Exclusion Keywords (To filter out high-level roles)
EXCLUSION_KEYWORDS = [
    r'\bsenior\b', r'\bsr\b', r'\blead\b', r'\bprincipal\b', r'\bstaff\b', 
    r'\bmanager\b', r'\bdirector\b', r'\bvp\b', r'\biii\b', r'\biv\b', r'\bv\b', 
    r'\bexpert\b', r'\barchitect\b', r'\bhead of\b'
]

LOCATION_MARKERS = [
    r'\busa\b', r'\bunited states\b', r'\bamerica\b', 
    r'\bus\b', r'\bga\b', r'georgia\s*,\s*usa',
    r'remote\s*-\s*us', r'remote\s*us'
]

GA_CITIES = [
    "atlanta", "sandy springs", "roswell", "alpharetta", "marietta", 
    "smyrna", "dunwoody", "brookhaven", "decatur", "lawrenceville",
    "norcross", "kennesaw", "woodstock", "cumming", "duluth", "mableton"
]

# ==============================================================================
# SECTION 2: THE "FILING SYSTEM" (DATA MANAGEMENT)
# ==============================================================================

def load_posted_jobs():
    if os.path.exists(POSTED_JOBS_FILE):
        try:
            with open(POSTED_JOBS_FILE, 'r') as f:
                return set(json.load(f))
        except:
            return set()
    return set()

def save_posted_jobs(posted_jobs):
    with open(POSTED_JOBS_FILE, 'w') as f:
        json.dump(list(posted_jobs), f)

# ==============================================================================
# SECTION 3: THE "JUDGE" (FILTERING LOGIC)
# ==============================================================================

def is_qa_job(title):
    """
    Checks if the job is a target role and NOT a high-level (Senior/Lead) role.
    """
    title_lower = title.lower()
    
    # Check for target keywords
    is_target = any(keyword in title_lower for keyword in QA_KEYWORDS)
    
    # Check for high-level exclusions
    is_high_level = any(re.search(excl, title_lower) for excl in EXCLUSION_KEYWORDS)
    
    return is_target and not is_high_level

def is_usa_location(location):
    if not location:
        return False
    location_lower = location.lower()
    if any(re.search(marker, location_lower) for marker in LOCATION_MARKERS):
        return True
    if any(city in location_lower for city in GA_CITIES):
        return True
    return False

# ==============================================================================
# SECTION 4: THE "RUNNERS" (FETCHING DATA)
# ==============================================================================

def fetch_google_ai_jobs():
    if SERPER_API_KEY == "REPLACE_ME":
        print("Skipping Google AI Search: No API Key found.")
        return []

    print("Using Google AI to crawl for recently posted jobs on accredited ATS platforms...")
    url = "https://google.serper.dev/search"
    all_google_jobs = []
    
    queries = [
        'site:boards.greenhouse.io ("manual QA" OR "Risk Examiner") "United States"',
        'site:jobs.lever.co ("Underwriter" OR "Manual Tester") "Remote"',
        'site:ashbyhq.com ("QA" OR "Underwriter") "USA"',
        'site:smartrecruiters.com ("Manual testing" OR "Risk") "United States"',
        'site:applytojob.com ("Manual Tester" OR "QA") "Remote"',
        'site:workable.com "Risk Examiner" "USA"',
        'site:jobvite.com "Underwriter" "Remote"',
        'site:recruitee.com "Manual QA" "USA"',
        'site:linkedin.com/jobs "Manual Testing" "Remote"',
        'site:indeed.com/viewjob "Underwriter" "Remote"'
    ]

    for query in queries:
        payload = json.dumps({"q": query, "tbm": "nws"})
        headers = {'X-API-KEY': SERPER_API_KEY, 'Content-Type': 'application/json'}
        
        try:
            response = requests.post(url, headers=headers, data=payload, timeout=15)
            if response.status_code == 200:
                results = response.json().get('news', [])
                for item in results:
                    title = item.get('title', 'Unknown Job')
                    link = item.get('link', '')
                    snippet = item.get('snippet', '').lower()
                    
                    if is_qa_job(title) and (is_usa_location(snippet) or "remote" in snippet):
                        all_google_jobs.append({
                            "title": title,
                            "company": "Accredited ATS Search",
                            "location": "Verified Remote/US",
                            "link": link
                        })
            time.sleep(1)
        except Exception as e:
            print(f"Google AI Search error for query '{query}': {e}")
            
    return all_google_jobs

def fetch_remotive_jobs():
    print("Fetching from Remotive (Multiple Categories)...")
    all_jobs = []
    for cat in CATEGORIES:
        try:
            url = f"{REMOTIVE_BASE_API}?category={cat}"
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                for job in data.get('jobs', []):
                    location = job.get('candidate_required_location', 'Remote')
                    if is_qa_job(job['title']) and is_usa_location(location):
                        all_jobs.append({
                            "title": job['title'],
                            "company": job['company_name'],
                            "location": location,
                            "link": job['url']
                        })
            time.sleep(1)
        except Exception as e:
            print(f"Error fetching {cat} from Remotive: {e}")
    return all_jobs

def fetch_arbeitnow_jobs():
    print("Fetching from Arbeitnow...")
    try:
        response = requests.get(ARBEITNOW_API, timeout=10)
        if response.status_code == 200:
            data = response.json()
            jobs = []
            for job in data.get('data', []):
                location = job.get('location', 'Remote')
                if is_qa_job(job['title']) and is_usa_location(location):
                    jobs.append({
                        "title": job['title'],
                        "company": job['company_name'],
                        "location": location,
                        "link": job['url']
                    })
            return jobs
    except Exception as e:
        print(f"Error fetching from Arbeitnow: {e}")
    return []

def fetch_himalayas_jobs():
    print("Fetching from Himalayas (Multiple Keywords)...")
    all_jobs = []
    for kw in KEYWORDS_SEARCH:
        try:
            url = f"{HIMALAYAS_BASE_API}?q={kw.replace(' ', '+')}"
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                for job in data.get('jobs', []):
                    location = job.get('locationRestrictions', 'Remote')
                    loc_str = str(location)
                    if is_qa_job(job['title']) and is_usa_location(loc_str):
                        all_jobs.append({
                            "title": job['title'],
                            "company": job['companyName'],
                            "location": loc_str,
                            "link": job['applicationLink']
                        })
            time.sleep(1)
        except Exception as e:
            print(f"Error fetching {kw} from Himalayas: {e}")
    return all_jobs

def fetch_jobicy_jobs():
    print("Fetching from Jobicy...")
    try:
        response = requests.get(JOBICY_API, timeout=10)
        if response.status_code == 200:
            data = response.json()
            jobs = []
            for job in data.get('jobs', []):
                location = job.get('jobGeo', 'Remote')
                if is_qa_job(job['jobTitle']) and is_usa_location(location):
                    jobs.append({
                        "title": job['jobTitle'],
                        "company": job['companyName'],
                        "location": location,
                        "link": job['url']
                    })
            return jobs
    except Exception as e:
        print(f"Error fetching from Jobicy: {e}")
    return []

def fetch_remoteok_jobs():
    print("Fetching from Remote OK...")
    try:
        response = requests.get(REMOTE_OK_API, headers=HEADERS, timeout=15)
        if response.status_code == 200:
            data = response.json()
            jobs = []
            # Skip first item (legal notice)
            for job in data[1:]:
                if is_qa_job(job.get('position', '')) and is_usa_location(job.get('location', '')):
                    jobs.append({
                        "title": job['position'],
                        "company": job['company'],
                        "location": job['location'],
                        "link": job['url']
                    })
            return jobs
    except Exception as e:
        print(f"Error fetching from Remote OK: {e}")
    return []

def fetch_muse_jobs():
    print("Fetching from The Muse...")
    try:
        # Search for first 2 pages
        all_jobs = []
        for page in [0, 1]:
            params = {"page": page, "location": "Remote"}
            response = requests.get(THE_MUSE_API, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                for job in data.get('results', []):
                    title = job.get('name', '')
                    company = job.get('company', {}).get('name', 'Unknown')
                    location = job.get('locations', [{}])[0].get('name', 'Remote')
                    link = job.get('refs', {}).get('landing_page', '')
                    
                    if is_qa_job(title) and is_usa_location(location):
                        all_jobs.append({
                            "title": title,
                            "company": company,
                            "location": location,
                            "link": link
                        })
            time.sleep(1)
        return all_jobs
    except Exception as e:
        print(f"Error fetching from The Muse: {e}")
    return []

def fetch_wwr_jobs():
    print("Fetching from We Work Remotely...")
    try:
        response = requests.get(WWR_RSS_URL, timeout=10)
        if response.status_code == 200:
            root = ET.fromstring(response.content)
            jobs = []
            for item in root.findall('.//item'):
                full_title = item.find('title').text
                link = item.find('link').text
                
                company = "We Work Remotely"
                title = full_title
                if ":" in full_title:
                    parts = full_title.split(":", 1)
                    company = parts[0].strip()
                    title = parts[1].strip()
                
                if is_qa_job(title):
                    jobs.append({
                        "title": title,
                        "company": company,
                        "location": "Remote",
                        "link": link
                    })
            return jobs
    except Exception as e:
        print(f"Error fetching from WWR: {e}")
    return []

# ==============================================================================
# SECTION 5: THE "MESSENGER" (DISCORD INTEGRATION)
# ==============================================================================

def send_discord_message(content):
    if not content:
        return
    try:
        requests.post(WEBHOOK_URL, json={"content": content})
    except Exception as e:
        print(f"Error sending to Discord: {e}")

def get_job_report(new_jobs):
    now = datetime.now(EASTERN_TZ).strftime("%Y-%m-%d %H:%M:%S")
    report = f"🚀 **Hourly Job Update - {now}**\n\n### **Target Roles Found (New/Verified)**\n"
    
    for job in new_jobs:
        report += f"- [{job['title']} @ {job['company']}]({job['link']}) ({job['location']})\n"
    
    report += "\n**Accreditation Note:** Now scanning Greenhouse, Lever, Ashby, The Muse, WWR, RemoteOK, and more."
    return report

# ==============================================================================
# SECTION 6: THE "BRAIN" (MAIN LOOP)
# ==============================================================================

def main():
    print(f"[{datetime.now(EASTERN_TZ)}] Job Automation Script Started.")
    posted_jobs = load_posted_jobs()
    
    while True:
        now = datetime.now(EASTERN_TZ)
        
        if 9 <= now.hour <= 23:
            all_jobs = []
            
            # Fetch from all sources
            all_jobs.extend(fetch_google_ai_jobs())
            all_jobs.extend(fetch_remotive_jobs())
            all_jobs.extend(fetch_arbeitnow_jobs())
            all_jobs.extend(fetch_himalayas_jobs())
            all_jobs.extend(fetch_jobicy_jobs())
            all_jobs.extend(fetch_remoteok_jobs())
            all_jobs.extend(fetch_muse_jobs())
            all_jobs.extend(fetch_wwr_jobs())

            # Filter for unique jobs not yet posted
            new_jobs_to_post = []
            for job in all_jobs:
                # Use title, company, and link to create a unique ID
                job_id = f"{job['title']}|{job['company']}|{job['link']}"
                if job_id not in posted_jobs:
                    new_jobs_to_post.append(job)
                    posted_jobs.add(job_id)
            
            if new_jobs_to_post:
                # Post in batches of 10 to avoid Discord limits
                for i in range(0, len(new_jobs_to_post), 10):
                    batch = new_jobs_to_post[i:i+10]
                    print(f"[{now}] Posting {len(batch)} new jobs...")
                    report = get_job_report(batch)
                    send_discord_message(report)
                    time.sleep(2)
                
                save_posted_jobs(posted_jobs)
            else:
                print(f"[{now}] No new jobs to post this hour.")
            
            # Wait for 1 hour before next run
            time.sleep(3600)
        else:
            print(f"[{now}] Outside posting window (9AM-11PM). Sleeping for 15 mins...")
            time.sleep(900)

if __name__ == "__main__":
    main()
