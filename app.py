import streamlit as st
import requests

# Set backend URL (adjust if necessary)
BACKEND_URL = "http://localhost:8000"

st.title("JobSeeker Buddy")

# ------------------------------
# User Setup & Asset Upload
# ------------------------------
st.sidebar.header("User Setup")
user_id = st.sidebar.text_input("Enter User ID", value="user123")

if user_id:
    response = requests.get(f"{BACKEND_URL}/user_assets/{user_id}")
    if response.status_code == 200:
        user_assets = response.json()
        st.sidebar.write("Existing Assets:")
        st.sidebar.write(f"Resume: {user_assets.get('resume')}")
        st.sidebar.write(f"LinkedIn: {user_assets.get('linkedin')}")
        st.sidebar.write(f"Experience: {user_assets.get('experience')}")
    else:
        st.sidebar.write("No existing assets found for this user.")

uploaded_resume = st.sidebar.file_uploader("Upload Resume", type=["pdf", "docx", "txt"])
uploaded_linkedin = st.sidebar.file_uploader("Upload LinkedIn Profile (PDF)", type=["pdf"])
uploaded_experience = st.sidebar.file_uploader("Upload Experience Details (txt)")

if st.sidebar.button("Upload Assets"):
    if user_id and uploaded_resume and uploaded_linkedin and uploaded_experience:
        files = {
            "resume": uploaded_resume,
            "linkedin": uploaded_linkedin,
            "experience": uploaded_experience
        }
        response = requests.post(
            f"{BACKEND_URL}/upload_assets",
            data={"user_id": user_id},
            files=files
        )
        if response.status_code == 200:
            st.sidebar.success("Assets uploaded successfully!")
        else:
            st.sidebar.error("Failed to upload assets.")
    else:
        st.sidebar.error("Please provide a User ID and upload all required files.")

# ------------------------------
# New Application Creation
# ------------------------------
st.header("New Job Application")
job_link = st.text_input("Enter Job Posting URL")

if st.button("Create Application"):
    if job_link and user_id:
        payload = {"job_link": job_link, "user_id": user_id}
        response = requests.post(f"{BACKEND_URL}/new_application", json=payload)
        if response.status_code == 200:
            data = response.json()
            application_id = data.get("application_id")
            st.success(f"Application created with ID: {application_id}")
            st.session_state.application_id = application_id
            st.session_state.job_details = data.get("job_details")
        else:
            error_message = response.json().get("detail", "Unknown error occurred")
            st.error(f"Failed to create application: {error_message}")
    else:
        st.error("Please provide a job posting URL and User ID.")

# ------------------------------
# Document Generation
# ------------------------------
st.header("Generate Documents")
if "application_id" in st.session_state:
    if st.button("Generate Cover Letter & Resume"):
        payload = {"application_id": st.session_state.application_id, "user_id": user_id}
        with st.spinner("Generating documents..."):
            response = requests.post(f"{BACKEND_URL}/generate_documents", json=payload)
            if response.status_code == 200:
                data = response.json()
                st.subheader("Cover Letter")
                st.text_area("Cover Letter", data.get("cover_letter"), height=300)
                st.subheader("Customized Resume")
                st.text_area("Resume", data.get("resume"), height=300)
            else:
                st.error("Document generation failed.")

# ------------------------------
# Feedback & Iteration
# ------------------------------
st.header("Feedback & Iteration")
feedback = st.text_input("Enter your feedback for the generated documents")
if st.button("Submit Feedback"):
    if "application_id" in st.session_state and feedback:
        payload = {
            "application_id": st.session_state.application_id,
            "user_id": user_id,
            "feedback": feedback
        }
        with st.spinner("Regenerating documents with feedback..."):
            response = requests.post(f"{BACKEND_URL}/feedback", json=payload)
            if response.status_code == 200:
                data = response.json()
                st.subheader("Updated Cover Letter")
                st.text_area("Cover Letter", data.get("cover_letter"), height=300)
                st.subheader("Updated Resume")
                st.text_area("Resume", data.get("resume"), height=300)
            else:
                st.error("Feedback processing failed.")
    else:
        st.error("Please provide feedback and ensure an application exists.")
