import os
import uuid
import json
import requests
import uvicorn
import asyncio
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from pydantic import BaseModel
from firebase_admin import credentials, firestore
import firebase_admin
from dotenv import load_dotenv
load_dotenv()

# Initialize Firebase Admin SDK (make sure to provide the correct path to your credentials JSON)
cred = credentials.Certificate("./firebase_credentials.json")
firebase_admin.initialize_app(cred)
db = firestore.client()
# get the LLM_API_URL from the environment variables
LLM_API_URL = os.getenv("LLM_API_URL")


app = FastAPI(title="JobSeeker Buddy Backend")

# Directories for file storage
ASSETS_DIR = "assets"
APPLICATIONS_DIR = "applications"
os.makedirs(ASSETS_DIR, exist_ok=True)
os.makedirs(APPLICATIONS_DIR, exist_ok=True)

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
    
    # Store file references in Firestore under the "users" collection
    user_ref = db.collection("users").document(user_id)
    user_ref.set({
        "resume": resume_path,
        "linkedin": linkedin_path,
        "experience": experience_path,
    }, merge=True)
    
    return {"message": "Assets uploaded successfully", "user_id": user_id}

# 2. Create New Application Folder with Job Scraping via Tavily
def scrape_job_posting(job_link: str):
    # Assumes Tavily API endpoint is available locally at port 5001.
    tavily_url = "http://localhost:5001/scrape"
    try:
        response = requests.get(tavily_url, params={"url": job_link})
        if response.status_code == 200:
            return response.json()  # Expected: { company, role, responsibilities, requirements, location, ... }
        else:
            raise Exception("Tavily scraping failed with status code " + str(response.status_code))
    except Exception as e:
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
    Call the local LMStudio reasoning model.
    This example uses a streaming response.
    """
    reasoning_url = LLM_API_URL+"/v1/completions"
    payload = {"prompt": prompt, "stream": False, "max_tokens": 50000}    
    response = requests.post(reasoning_url, json=payload, stream=False)
    response_data = response.json()
    # write the full response to a file for debugging in a /debug folder. Create the file if it doesn't exist.
    with open("debug/reasoning_response.json", "w") as f:
        json.dump(response_data, f)

    return response_data.get("choices", [{}])[0].get("text", "")

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
    
    # Build prompts for cover letter and resume customization
    cover_letter_prompt = (
        f"Generate a cover letter based on the following job details: {job_details} "
        f"and the user's experience from resume at {user_data.get('resume')} and details from {user_data.get('experience')}."
    )
    resume_prompt = (
        f"Modify the resume to highlight the most relevant experiences for the job described as: {job_details}. "
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
    
    # Build new prompts that include the user feedback
    cover_letter_prompt = (
        f"Based on the previous cover letter and the following feedback: '{feedback_text}', "
        f"regenerate the cover letter for the job described as: {job_details}. "
        f"Use user resume at {user_data.get('resume')} and experience details from {user_data.get('experience')}."
    )
    resume_prompt = (
        f"Based on the previous resume and feedback: '{feedback_text}', "
        f"regenerate the resume to better highlight relevant experiences for the job: {job_details}."
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

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
