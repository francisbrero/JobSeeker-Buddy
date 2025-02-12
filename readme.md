# JobSeeker Buddy

JobSeeker Buddy is an application designed to streamline the job application process by automatically generating tailored cover letters and resumes based on your personal data and scraped job posting details.

## Overview

**JobSeeker Buddy** simplifies job applications by:

- Uploading your core assets (resume, LinkedIn profile, and work experience details).
- Creating a job-specific application folder by scraping job posting data.
- Generating a custom cover letter and modified resume based on your data and the job requirements.
- Providing a chat interface for reviewing and iterating on generated documents with real-time streaming of AI reasoning steps.

## Project Structure

- **Backend**: Built using FastAPI to handle user asset uploads, job scraping, document generation, and feedback processing. It integrates with Firestore for data storage and connects to a local LLM (via LMStudio) or OpenAI for generating documents.
- **Frontend**: A Streamlit-based interface that allows users to upload their assets, create new applications, view generated documents, and submit feedback for further iterations.

## Running the Application

Make the script executable with the following command in Terminal:

```bash
chmod +x start.sh
```

Then run the script: 

```bash
./start.sh
```

This script will sequentially activate the venv, install dependencies, start the backend in the background, and finally launch the Streamlit application in the foreground. Adjust the filenames if your Streamlit file has a different name.

## Installation

1. **Set up a Python virtual environment (optional but recommended):**

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows, use: venv\Scripts\activate
```

2. **Install the required dependencies:**

```bash
pip install -r requirements.txt
```

3. **Configure Firebase:**

Obtain your Firebase service account credentials.
Place your credentials JSON file in an appropriate location and update the path in main.py accordingly.

4. **Configure LLM Usage:**

By default, the application uses a local LLM. To use the OpenAI model, set the following environment variables:

```bash
export USE_OPENAI=true
export OPENAI_API_KEY=your_openai_api_key
```

## Running the Application

### Start the Backend Server

Navigate to the project root.

Run the FastAPI backend using uvicorn:

```bash
python main.py
```

The backend server will start on http://localhost:8000.

### Start the Frontend Application

Open a new terminal window.

Run the Streamlit app:

```bash
streamlit run app.py
```
The Streamlit interface will open in your default browser.

## Deployment

### Backend Deployment (Render)

1. **Create a Render Account:**
   - Sign up at [render.com](https://render.com)
   - Create a new Web Service

2. **Configure Your Web Service:**
   - Connect your GitHub repository
   - Select the branch to deploy
   - Set Build Command: `pip install -r requirements.txt`
   - Set Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - Choose instance type (recommend starting with free tier)

3. **Set Environment Variables:**
   ```
   FIREBASE_CREDENTIALS={"your":"firebase-credentials-json"}
   USE_OPENAI=true  # if using OpenAI
   OPENAI_API_KEY=your_openai_api_key
   ```

4. **Update CORS Settings:**
   - Add your Streamlit Cloud URL to the allowed origins in `main.py`

### Frontend Deployment (Streamlit Cloud)

1. **Create a Streamlit Cloud Account:**
   - Sign up at [share.streamlit.io](https://share.streamlit.io)
   - Connect your GitHub repository

2. **Deploy Your App:**
   - Select your repository and branch
   - Set the main file path to `app.py`
   - Add the following secrets in the Streamlit Cloud dashboard:
     ```
     BACKEND_URL=https://your-render-app.onrender.com
     ```

3. **Advanced Settings:**
   - Set Python version if needed
   - Configure memory limits if required

### Post-Deployment Steps

1. **Update Configuration:**
   - Ensure all API endpoints in the frontend code point to your Render backend URL
   - Verify CORS settings allow communication between frontend and backend

2. **Testing:**
   - Test the complete workflow in production
   - Verify file uploads and processing
   - Check API communication between frontend and backend

3. **Monitoring:**
   - Set up logging in Render dashboard
   - Monitor application performance and errors
   - Set up alerts for critical errors

### Production Considerations

- Enable SSL/TLS encryption
- Implement rate limiting
- Set up proper error logging
- Configure automatic backups for Firebase
- Monitor API usage and costs
- Set up CI/CD pipelines for automated deployment

## Features & Workflow

### User Asset Upload:

Upload your resume, LinkedIn profile (PDF), and work experience details.
These assets are stored in the main asset folder and referenced in Firestore.

### New Application Creation:

Provide a job posting URL.
The app scrapes job details and creates a unique application folder.

### Document Generation:

The backend calls the local LLM or OpenAI model to generate a cover letter and customize your resume based on your uploaded assets and the scraped job details.
Generated documents are saved and versioned in Firestore.

### Feedback & Iteration:

Use the chat interface to provide feedback on the generated documents.
The system regenerates the documents incorporating your feedback, maintaining a version history.

## Customization & Future Improvements

Streaming Enhancements: Implement websockets for a more interactive streaming experience.
Enhanced Security: Improve data protection and access control for user data.
Additional Integrations: Extend capabilities to include more detailed user profiles and additional scraping sources.
