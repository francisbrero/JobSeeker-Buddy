# JobSeeker Buddy

JobSeeker Buddy is an application designed to streamline the job application process by automatically generating tailored cover letters and resumes based on your personal data and scraped job posting details.

## Overview

**JobSeeker Buddy** simplifies job applications by:

- Uploading your core assets (resume, LinkedIn profile, and work experience details).
- Creating a job-specific application folder by scraping job posting data via Tavily.
- Generating a custom cover letter and modified resume based on your data and the job requirements.
- Providing a chat interface for reviewing and iterating on generated documents with real-time streaming of AI reasoning steps.

## Project Structure

- **Backend**: Built using FastAPI to handle user asset uploads, job scraping, document generation, and feedback processing. It integrates with Firestore for data storage and connects to a local LLM (via LMStudio) for generating documents.
- **Frontend**: A Streamlit-based interface that allows users to upload their assets, create new applications, view generated documents, and submit feedback for further iterations.

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
Running the Application

## Start the Backend Server

Navigate to the backend directory (if separate) or ensure you’re in the project root.

Run the FastAPI backend using uvicorn:

```bash
python main.py
```

The backend server will start on http://localhost:8000.

## Start the Tavily Application

Open a new terminal window.

Run tavily

```bash
python tavily.py
```

The tavily scraping service will start on http://localhost:5001.

## Start the Frontend Application

Open a new terminal window.

Run the Streamlit app:

```bash
streamlit run app.py
```

The Streamlit interface will open in your default browser.

## Features & Workflow

### User Asset Upload:

Upload your resume, LinkedIn profile (PDF), and work experience details.
These assets are stored in the main asset folder and referenced in Firestore.
New Application Creation:

Provide a job posting URL.
The app uses Tavily to scrape job details and creates a unique application folder.

### Document Generation:

The backend calls the local LLM to generate a cover letter and customize your resume based on your uploaded assets and the scraped job details.
Generated documents are saved and versioned in Firestore.

### Feedback & Iteration:

Use the chat interface to provide feedback on the generated documents.
The system regenerates the documents incorporating your feedback, maintaining a version history.

## Customization & Future Improvements

Streaming Enhancements: Implement websockets for a more interactive streaming experience.
Enhanced Security: Improve data protection and access control for user data.
Additional Integrations: Extend capabilities to include more detailed user profiles and additional scraping sources.
