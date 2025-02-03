import uvicorn
from fastapi import FastAPI, HTTPException, Query
import requests
from bs4 import BeautifulSoup

app = FastAPI(title="Tavily Job Scraper")

@app.get("/scrape")
def scrape(url: str = Query(..., description="Job posting URL")):
    try:
        # Fetch the job posting page
        response = requests.get(url)
        if response.status_code != 200:
            raise HTTPException(status_code=500, detail="Unable to retrieve job posting from the provided URL")
        
        # Parse the HTML content
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract job details:
        # - Assume the job title is in an <h1> tag.
        # - Assume the company name is in an element with class "company".
        # - Assume the job location is in an element with class "location".
        role = soup.find('h1').get_text().strip() if soup.find('h1') else "Job Title Not Found"
        company_elem = soup.find(class_="company")
        company = company_elem.get_text().strip() if company_elem else "Company Not Found"
        location_elem = soup.find(class_="location")
        location = location_elem.get_text().strip() if location_elem else "Location Not Found"
        
        # For demonstration, we provide dummy responsibilities and requirements.
        responsibilities = [
            "Analyze and develop software solutions.",
            "Collaborate with team members to meet deadlines.",
            "Participate in code reviews and agile practices."
        ]
        requirements = [
            "Bachelor's degree in a relevant field.",
            "3+ years of experience in software development.",
            "Strong communication and teamwork skills."
        ]
        
        job_data = {
            "company": company,
            "role": role,
            "responsibilities": responsibilities,
            "requirements": requirements,
            "location": location
        }
        return job_data

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5001)
