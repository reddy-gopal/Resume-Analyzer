import os
import google.generativeai as genai
from dotenv import load_dotenv
import json

load_dotenv()

def analyze_with_gemini(resume_text, jd_text):
    
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        return {"error": "GOOGLE_API_KEY not found."}

    try:
        genai.configure(api_key=api_key)
        generation_config = {
            "temperature": 0.2,
            "response_mime_type": "application/json",
        }
        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            generation_config=generation_config
        )
    except Exception as e:
        return {"error": f"Error configuring Gemini model: {e}"}

    prompt = f"""
    You are an expert AI recruitment assistant. Your task is to analyze a candidate's resume against a job description.

    Analyze the provided documents and return a JSON object with the following exact structure:
    {{
      "overall_score": <An integer score from 0-100 representing the overall match>,
      "matching_skills": [<A list of key skills from the job description that ARE PRESENT in the resume>],
      "missing_skills": [<A list of key skills from the job description that ARE MISSING from the resume>],
      "feedback": <A detailed, professional, and personalized feedback report in markdown format. Give actionable advice on how the candidate can improve their resume to better match this job, especially by incorporating the missing skills.>
    }}

    **Job Description:**
    ---
    {jd_text}
    ---

    **Candidate's Resume:**
    ---
    {resume_text}
    ---

    Provide the analysis in the specified JSON format.
    """

    try:
        response = model.generate_content(prompt)
        cleaned_json_string = response.text.strip().replace("```json", "").replace("```", "")
        return json.loads(cleaned_json_string)
    except Exception as e:
        return {"error": f"An error occurred during API call: {e}"}