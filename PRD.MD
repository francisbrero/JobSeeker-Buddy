# Job Seeker Buddy - Product Requirements Document

## 1. Overview

### 1.1 Product Name
**JobSeeker Buddy**

### 1.2 Purpose
**JobSeeker Buddy** is designed to simplify and automate the process of applying to jobs. It assists users by:
1. Creating a tailored cover letter based on the user’s experience and the specific job requirements.
2. Generating a slightly modified version of the user’s resume, customized for the target job.

### 1.3 Objectives
1. **Reduce friction** for job applicants by generating application materials quickly and accurately.
2. **Improve application quality** through targeted cover letters and resumes.
3. **Leverage AI** to personalize documents without misleading or fabricating skills and experiences.
4. **Streamlined user experience** with an intuitive chat interface for feedback loops.

---

## 2. Key Features & Requirements

### 2.1 Folder System and Document Management
- **Main Asset Folder**
  - Stores the user’s original resume, LinkedIn profile (PDF), and a text file with unstructured work experience details.
- **Application Folder (per job)**
  - Created each time the user wants to apply for a new job.
  - Stores:
    - Job posting data (scraped content).
    - Generated cover letter.
    - Modified resume.
    - Any feedback or instructions from the user.

### 2.2 Job Posting Scraper (Tavily Integration)
- Prompt the user for a **job opening link** when creating a new application folder.
- Automatically **scrape job information** (company, role, responsibilities, requirements, location, etc.) using Tavily.
- Parse and store the scraped data in the newly created folder for reference and generation.

### 2.3 Document Generation
- **Cover Letter Generation**
  - Uses the scraped job information and the user’s data (resume text, LinkedIn, unstructured experience) to draft a cover letter.
  - Tailors language to the job description while preserving the user’s actual experience.
- **Resume Customization**
  - Slight modifications to the user’s primary resume to highlight the most relevant skills and experiences for the specific job.
  - Must not fabricate or misrepresent the user’s experience.

### 2.4 User Feedback & Iteration
- A chat interface prompts the user to review the generated documents.
- The user can provide **feedback** on any aspect (tone, content, emphasis, highlights).
- The system will **regenerate** the documents incorporating this feedback.

### 2.5 AI/LLM Architecture
- **Reasoning Model** (e.g., GPT-like model running locally on LMStudio)
  - Processes user data and job requirements to decide how to tailor the content.
  - Streams intermediate reasoning steps so the user can see how it is deriving the final document.
- **Chat Completion Model** (also running locally or a local instance from LMStudio)
  - Used for the user interface’s conversation flow, refining responses, and maintaining context.
- **Streaming Output**
  - Both the reasoning steps and final generated content are streamed in real-time in the chat UI.

### 2.6 Platform & Deployment
- **Frontend**: Could be a web-based interface (React/Next.js, Streamlit, or similar) deployed to a cloud platform (e.g., Vercel).
- **Backend**:
  - Node.js or Python-based server for orchestrating:
    - Interactions with the local LLM (LMStudio).
    - Document generation requests.
    - Tavily-based scraping.
  - No containers are required based on the user’s preference.
- **Data Store**: Firestore or a similar NoSQL cloud database for:
  - Storing references to user documents and job application folders.
  - Storing user feedback, generated documents, etc.
- **Local LLM**: Models run on LMStudio locally. The app communicates with them via standard APIs or local endpoints.

---

## 3. Functional Requirements

1. **User Account Setup (Optional)**
   - Basic user profile creation (if needed) or local usage with single user scenario.
   - Storage of user’s core assets in a “Main Asset Folder.”

2. **Create New Application Folder**
   - Prompt user for job link.
   - Scrape job details from the link using Tavily.
   - Store the scraped details in the job-specific folder in Firestore (or an equivalent).

3. **Generate Documents**
   - **Cover Letter**:
     - Must reference job requirements and user’s relevant experience.
     - Should not contain false claims or fabricated experience.
   - **Resume**:
     - Slight modifications to highlight relevant experiences matching the scraped job posting.
     - Store both the original resume and the newly generated version in the job folder.

4. **Chat Interface**
   - Display ongoing **“Reasoning”** stream (model’s chain of thought).
   - Display **draft output** stream (cover letter or resume text).
   - Enable user input/feedback, which triggers a new iteration of the generation process.

5. **Revision Process**
   - Capture user’s feedback in the conversation.
   - Regenerate the documents incorporating the feedback.
   - Keep version history in the job folder.

6. **File Management**
   - Maintain folder structure in Firestore for easy retrieval and reference.

7. **Security & Compliance** 
   - Basic data protection with Firestore’s default security.
   - No advanced compliance requirements specified.
   - Ensure not to store any data in the local LLM beyond transient generation steps.

---

## 4. Technical Requirements

1. **Backend**
   - **Programming Language**: Python.
   - **Scraper**: Tavily integration for scraping the job posting.
   - **Database**: Firestore for storing user’s data (documents, job folders, logs).

2. **Local LLM Integration**
   - **LMStudio** to host two local models:
     - **Reasoning Model**: Possibly a GPT-like model with chain-of-thought streaming.
     - **Chat Model**: For conversation and interaction with the user.
   - The app communicates with LMStudio via a local network endpoint, following OpenAI-like API standards (e.g., /v1/chat/completions and /v1/completions).

3. **Frontend**
   - **Web-based interface**: 
     - Deployment on Streamlit-based application (cloud-hosted).
   - Must support **streaming** of both the chain-of-thought and final content to the user’s screen in real time.

4. **Versioning**
   - Keep track of multiple versions of resumes and cover letters in the job folder.

5. **Scalability**
   - Firestore for horizontal scaling of data storage.
   - LLM runs locally with possible resource limitations; performance depends on local hardware.

---

## 5. User Flow

1. **User signs in / opens the app** (or single-user scenario).
2. **Initial Setup**:
   - Upload or confirm presence of main assets (resume, LinkedIn PDF, unstructured data).
3. **Creating an Application**:
   - User clicks **“New Application”** or similar button.
   - App asks for **job link**.
   - Tavily scrapes job data and stores it in Firestore.
4. **Generating Draft Documents**:
   - The local LLM is called with user data + job data.
   - The system streams its reasoning and then provides a draft cover letter and updated resume.
5. **User Feedback**:
   - The user reviews the documents in a chat interface.
   - The user types comments (e.g., “Highlight my data engineering experience more”).
   - A second iteration triggers the LLM to update documents accordingly.
6. **Finalization**:
   - Final documents are stored in the application folder in Firestore.
   - User can download or copy/paste them for submission.

