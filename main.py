import os
import uuid
import json
import requests
import uvicorn
import asyncio
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Query
from pydantic import BaseModel
from firebase_admin import credentials, firestore
import firebase_admin
from dotenv import load_dotenv
import PyPDF2
from bs4 import BeautifulSoup
import openai
import re
import streamlit as st

load_dotenv()

# Initialize Firebase Admin SDK (make sure to provide the correct path to your credentials JSON)
cred = credentials.Certificate("./firebase_credentials.json")
firebase_admin.initialize_app(cred)
db = firestore.client()
# get the LLM_API_URL from the environment variables
LLM_API_URL = os.getenv("LLM_API_URL")

# Determine whether to use local LLM or OpenAI model
USE_OPENAI = os.getenv("USE_OPENAI", "false").lower() == "true"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = os.getenv("OPENAI_API_KEY")
client = openai  # alias for clarity with updated API usage

app = FastAPI(title="JobSeeker Buddy Backend")

# Directories for file storage
ASSETS_DIR = "assets"
APPLICATIONS_DIR = "applications"
os.makedirs(ASSETS_DIR, exist_ok=True)
os.makedirs(APPLICATIONS_DIR, exist_ok=True)

# Update any URLs or references to point to the deployed app
APP_URL = "https://jobseekerbuddy.streamlit.app/"

# ------------------------------
# Data Models
# ------------------------------
class ApplicationRequest(BaseModel):
    job_link: str
    user_id: str

class GenerateRequest(BaseModel):
    application_id: str
    user_id: str

class FeedbackRequest(BaseModel):
    application_id: str
    user_id: str
    feedback: str

# ------------------------------
# Endpoints
# ------------------------------

def read_file_content(file_path):
    if (file_path.lower().endswith('.pdf')):
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                content = ''
                for page in pdf_reader.pages:
                    content += page.extract_text()
                return content
        except Exception as e:
            print(f"Error reading PDF file: {e}")
            return None
    else:
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()
        except Exception as e:
            print(f"Error reading file: {e}")
            return None

def parse_document_with_openai(file_path: str) -> str:
    """
    Parse the document using OpenAI's GPT-4o-mini.
    """
    content = read_file_content(file_path)
    if content is None:
        return "Error: Could not read the file."
    
    prompt = f"Extract and summarize the key information from the following document:\n\n{content}"
    return call_openai_model(prompt, model="gpt-4o-mini")

# 1. Upload Main Assets (Resume, LinkedIn PDF, Experience Details)
@app.post("/upload_assets")
async def upload_assets(
    user_id: str = Form(...),
    resume: UploadFile = File(...),
    linkedin: UploadFile = File(...),
    experience: UploadFile = File(...)
):
    user_folder = os.path.join(ASSETS_DIR, user_id)
    os.makedirs(user_folder, exist_ok=True)
    
    # Save files locally
    resume_path = os.path.join(user_folder, f"resume_{resume.filename}")
    linkedin_path = os.path.join(user_folder, f"linkedin_{linkedin.filename}")
    experience_path = os.path.join(user_folder, f"experience_{experience.filename}")
    
    with open(resume_path, "wb") as f:
        f.write(await resume.read())
    with open(linkedin_path, "wb") as f:
        f.write(await linkedin.read())
    with open(experience_path, "wb") as f:
        f.write(await experience.read())
    
    # Parse documents using OpenAI
    parsed_resume = parse_document_with_openai(resume_path)
    parsed_linkedin = parse_document_with_openai(linkedin_path)
    parsed_experience = parse_document_with_openai(experience_path)
    
    # Store file references and parsed content in Firestore under the "users" collection
    user_ref = db.collection("users").document(user_id)
    user_ref.set({
        "resume": resume_path,
        "linkedin": linkedin_path,
        "experience": experience_path,
        "parsed_resume": parsed_resume,
        "parsed_linkedin": parsed_linkedin,
        "parsed_experience": parsed_experience,
    }, merge=True)
    
    return {"message": "Assets uploaded and parsed successfully", "user_id": user_id}

# 2. Create New Application Folder with Job Scraping via Tavily
def scrape_job_posting(job_link: str):
    """
    Scrape job posting details directly within the FastAPI application.
    """
    try:
        resp = requests.get(job_link)
        resp.raise_for_status()  # Raise an HTTPError for bad responses
        html = resp.text
        soup = BeautifulSoup(html, 'html.parser')
        text = soup.get_text(separator="\n")
        job_info = extract_job_info_from_text(text)
        return job_info
    except requests.exceptions.RequestException as e:
        # Log the error details
        print(f"Error scraping job posting: {e}")
        raise HTTPException(status_code=500, detail=f"Error scraping job posting: {e}")

@app.post("/new_application")
async def new_application(app_request: ApplicationRequest):
    user_id = app_request.user_id
    job_link = app_request.job_link
    
    # Scrape job details using Tavily integration
    job_details = scrape_job_posting(job_link)
    
    # Create a unique application folder
    application_id = str(uuid.uuid4())
    application_folder = os.path.join(APPLICATIONS_DIR, application_id)
    os.makedirs(application_folder, exist_ok=True)
    
    # Save job details locally for reference
    job_details_path = os.path.join(application_folder, "job_details.json")
    with open(job_details_path, "w") as f:
        json.dump(job_details, f)
    
    # Create a document in Firestore for the new application
    app_doc = {
        "user_id": user_id,
        "job_link": job_link,
        "job_details": job_details,
        "application_folder": application_folder,
        "versions": []
    }
    db.collection("applications").document(application_id).set(app_doc)
    
    return {"message": "Application created", "application_id": application_id, "job_details": job_details}

# 3. LLM Integration Functions (Simulated local calls)
def call_reasoning_model(prompt: str):
    """
    Call the reasoning model.
    This example uses a streaming response.
    """
    if (USE_OPENAI):
        return call_openai_model(prompt, model="o1-mini")
    else:
        return call_local_model(prompt)

def call_local_model(prompt: str):
    """
    Call the local LMStudio reasoning model.
    """
    reasoning_url = LLM_API_URL + "/v1/completions"
    payload = {"prompt": prompt, "stream": False, "max_tokens": 50000}
    response = requests.post(reasoning_url, json=payload, stream=False)
    response_data = response.json()
    with open("debug/reasoning_response.json", "w") as f:
        json.dump(response_data, f)
    return response_data.get("choices", [{}])[0].get("text", "")

def call_openai_model(prompt: str, model: str = "gpt-4o-mini"):
    """
    Call the OpenAI model.
    """
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}]
        # "max_completion_tokens": 50000,
    }
    response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
    with open("debug/openai_response.json", "w") as f:
        json.dump(response.json(), f)
    response_data = response.json()
    content = response_data["choices"][0]["message"]["content"]    
    return content

def call_chat_model(messages: list):
    """
    Call the local LMStudio chat model.
    """
    chat_url = LLM_API_URL+"/v1/chat/completions"
    payload = {"messages": messages, "stream": True}
    response = requests.post(chat_url, json=payload, stream=True)
    response_data = response.json()
    return response_data["choices"][0]["text"]

# 4. Generate Documents (Cover Letter & Customized Resume)
@app.post("/generate_documents")
async def generate_documents(gen_request: GenerateRequest):
    application_id = gen_request.application_id
    user_id = gen_request.user_id
    
    # Retrieve user asset references from Firestore
    user_ref = db.collection("users").document(user_id)
    user_data = user_ref.get().to_dict()
    if not user_data:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Retrieve application data from Firestore
    app_ref = db.collection("applications").document(application_id)
    app_data = app_ref.get().to_dict()
    if not app_data:
        raise HTTPException(status_code=404, detail="Application not found")
    
    job_details = app_data.get("job_details", {})
    
    # Build prompts for cover letter and resume customization using parsed and raw text
    cover_letter_prompt = (
        f"Generate a cover letter based on the following job details: {job_details} "
        f"and the user's experience from parsed resume: {user_data.get('parsed_resume')} "
        f"and parsed LinkedIn profile: {user_data.get('parsed_linkedin')}."
    )
    resume_prompt = (
        f"Modify the resume to highlight the most relevant experiences for the job described as: {job_details}. "
        f"Use the parsed resume: {user_data.get('parsed_resume')} and parsed LinkedIn profile: {user_data.get('parsed_linkedin')}. "
        "Do not fabricate any information."
    )
    
    # Generate cover letter by streaming reasoning steps from the LLM
    cover_letter_content = call_reasoning_model(cover_letter_prompt)
    
    # Generate customized resume similarly
    resume_content = call_reasoning_model(resume_prompt)
    
    # Save generated documents in the application folder
    application_folder = app_data["application_folder"]
    cover_letter_path = os.path.join(application_folder, "cover_letter.txt")
    resume_path = os.path.join(application_folder, "custom_resume.txt")
    with open(cover_letter_path, "w") as f:
        f.write(cover_letter_content)
    with open(resume_path, "w") as f:
        f.write(resume_content)
    
    # Record this version in Firestore
    version_entry = {
        "cover_letter": cover_letter_path,
        "resume": resume_path,
        "feedback": None
    }
    app_ref.update({
        "versions": firestore.ArrayUnion([version_entry])
    })
    
    return {
        "message": "Documents generated",
        "cover_letter": cover_letter_content,
        "resume": resume_content
    }

# 5. Process User Feedback and Regenerate Documents
@app.post("/feedback")
async def process_feedback(feedback_request: FeedbackRequest):
    application_id = feedback_request.application_id
    user_id = feedback_request.user_id
    feedback_text = feedback_request.feedback
    
    # Fetch application data
    app_ref = db.collection("applications").document(application_id)
    app_data = app_ref.get().to_dict()
    if not app_data:
        raise HTTPException(status_code=404, detail="Application not found")
    
    # Retrieve user data
    user_ref = db.collection("users").document(user_id)
    user_data = user_ref.get().to_dict()
    
    job_details = app_data.get("job_details", {})
    
    # Build new prompts that include the user feedback using parsed and raw text
    cover_letter_prompt = (
        f"Based on the previous cover letter and the following feedback: '{feedback_text}', "
        f"regenerate the cover letter for the job described as: {job_details}. "
        f"Use parsed resume: {user_data.get('parsed_resume')} and parsed LinkedIn profile: {user_data.get('parsed_linkedin')}."
    )
    resume_prompt = (
        f"Based on the previous resume and feedback: '{feedback_text}', "
        f"regenerate the resume to better highlight relevant experiences for the job: {job_details}. "
        f"Use parsed resume: {user_data.get('parsed_resume')} and parsed LinkedIn profile: {user_data.get('parsed_linkedin')}."
    )
    
    # Regenerate cover letter
    new_cover_letter = call_reasoning_model(cover_letter_prompt)
    
    # Regenerate resume
    new_resume = call_reasoning_model(resume_prompt)
    
    # Save new versions with unique filenames
    application_folder = app_data["application_folder"]
    cover_letter_path = os.path.join(application_folder, f"cover_letter_{uuid.uuid4().hex}.txt")
    resume_path = os.path.join(application_folder, f"custom_resume_{uuid.uuid4().hex}.txt")
    with open(cover_letter_path, "w") as f:
        f.write(new_cover_letter)
    with open(resume_path, "w") as f:
        f.write(new_resume)
    
    # Update version history in Firestore
    version_entry = {
        "cover_letter": cover_letter_path,
        "resume": resume_path,
        "feedback": feedback_text
    }
    app_ref.update({
        "versions": firestore.ArrayUnion([version_entry])
    })
    
    return {
        "message": "Documents regenerated with feedback",
        "cover_letter": new_cover_letter,
        "resume": new_resume
    }

# 6. Retrieve User Assets
@app.get("/user_assets/{user_id}")
async def get_user_assets(user_id: str):
    user_ref = db.collection("users").document(user_id)
    user_data = user_ref.get().to_dict()
    if not user_data:
        raise HTTPException(status_code=404, detail="User not found")
    return user_data

# New: Convert the Flask extraction endpoint to FastAPI
@app.get("/extract")
async def extract(url: str = Query(...)):
    """
    FastAPI endpoint for extracting job posting details.
    """
    try:
        job_info = scrape_job_posting(url)
        return job_info
    except Exception as e:
        return {"error": str(e)}

# Helper function to clean up the JSON output from the model
def clean_json_output(text):
    """
    Attempt to clean up the output from the model.
    This example uses a simple regex to remove extraneous text before and after the JSON.
    """
    # Find the first occurrence of a JSON object in the string.
    match = re.search(r'\{.*\}', text, re.DOTALL)
    if match:
        return match.group(0)
    return text

def extract_job_info_from_text(text):
    """
    Uses the OpenAI API (GPT-4o) to extract standard job posting fields
    from the given text, with strong instructions to output valid JSON.
    """
    prompt = f"""
You are an expert job posting parser. Given the following job posting text, extract and map the information into the following fields:
- company
- role
- location
- salary
- description of the role
- key responsibilities
- requirements

Return ONLY valid JSON (with no additional commentary) following this exact format:
{{
  "company": "<company name or empty string>",
  "role": "<role name or empty string>",
  "location": "<location or empty string>",
  "salary": "<salary or empty string>",
  "description of the role": "<description or empty string>",
  "key responsibilities": [ "<responsibility 1>", "<responsibility 2>", ... ],
  "requirements": [ "<requirement 1>", "<requirement 2>", ... ]
}}

If any field is missing from the job posting, use an empty string (or an empty list for the list fields). Do not include any other text.
Job posting text:
{text}
    """
    try:
        # Call the OpenAI API using the updated API method with GPT-4o
        completion = client.chat.completions.create(
            model="gpt-4o",  # Specify the GPT-4 optimized model
            messages=[
                {"role": "system", "content": "You are a helpful assistant specialized in parsing job postings."},
                {"role": "user", "content": prompt}
            ]
        )
        # Retrieve the response from the model
        result = completion.choices[0].message.content
        
        # Clean the output to isolate the JSON if extraneous text is present
        cleaned_result = clean_json_output(result)
        
        parsed = json.loads(cleaned_result)
        return parsed
    except Exception as e:
        return {"error": "Extraction failed", "details": str(e)}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

# If you have any sharing or linking functionality, update it like:
if st.button("Share this app"):
    st.markdown(f"Share this app: {APP_URL}")
