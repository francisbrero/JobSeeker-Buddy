import os
import json
import re
import requests
from flask import Flask, request, jsonify
from bs4 import BeautifulSoup
import openai

app = Flask(__name__)

# Set your OpenAI API key from an environment variable
openai.api_key = os.getenv("OPENAI_API_KEY")
client = openai  # alias for clarity with updated API usage

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

@app.route('/extract', methods=['GET'])
def extract():
    """
    Endpoint that accepts a 'url' query parameter.
    It fetches the job posting page, extracts its text, and then uses the extraction function
    to parse standard job fields.
    """
    url = request.args.get("url")
    if not url:
        return jsonify({"error": "Missing 'url' parameter"}), 400

    try:
        # Fetch the webpage content
        resp = requests.get(url)
        if resp.status_code != 200:
            return jsonify({"error": f"Failed to fetch URL. Status code: {resp.status_code}"}), 400

        html = resp.text

        # Parse the HTML to extract text content.
        soup = BeautifulSoup(html, 'html.parser')
        text = soup.get_text(separator="\n")

        # Extract the structured job information using the OpenAI API call
        job_info = extract_job_info_from_text(text)
        return jsonify(job_info)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Run the API service on port 5001
    app.run(host="0.0.0.0", port=5001)
