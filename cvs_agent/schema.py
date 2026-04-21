CV_SCHEMA = {
    "title": "CVData",
    "type": "object",
    "description": "Structured extraction of CV/Resume data. Be precise and concise.",
    "properties": {
        # --- Identity & Contact ---
        "full_name": {
            "type": "string",
            "description": "The full name of the candidate. Example: 'John Doe'."
        },
        "email_address": {
            "type": "string",
            "description": "The primary email address. Example: 'john.doe@example.com'."
        },
        "phone_number": {
            "type": "string",
            "description": "The primary phone number. Example: '+1 (555) 123-4567'."
        },
        "linkedin_url": {
            "type": "string",
            "description": "URL to the candidate's LinkedIn profile."
        },
        "portfolio_urls": {
            "type": "array",
            "items": {"type": "string"},
            "description": "List of portfolio URLs, personal websites, or GitHub profiles."
        },
        "location_city": {
            "type": "string",
            "description": "Current city of residence. Example: 'San Francisco'."
        },
        "location_country": {
            "type": "string",
            "description": "Current country of residence. Example: 'USA'."
        },

        # --- Professional Summary ---
        "professional_summary": {
            "type": "string",
            "description": "A concise summary of the candidate's background and goals. DIRECT AND SHORT. MAX 100 WORDS."
        },

        # --- Education ---
        "education": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "university": {"type": "string", "description": "Name of the institution."},
                    "degree": {"type": "string", "description": "Degree obtained (e.g., Bachelor, Master, PhD)."},
                    "major": {"type": "string", "description": "Field of study/Major."},
                    "gpa": {"type": "string", "description": "GPA if listed (e.g., '3.8/4.0')."},
                    "graduation_date": {"type": "string", "description": "Date of graduation (e.g., 'May 2020')."}
                },
                "required": ["university", "degree"]
            },
            "description": "List of distinct educational degrees."
        },

        # --- Work Experience ---
        "work_experience": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "company": {"type": "string", "description": "Name of the company."},
                    "job_title": {"type": "string", "description": "Title of the role."},
                    "is_current": {"type": "boolean", "description": "True if this is the current role."},
                    "responsibilities": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Top 5 key responsibilities/achievements. EACH ITEM DIRECT AND SHORT. MAX 100 WORDS TOTAL FOR ALL ITEMS."
                    }
                },
                "required": ["company", "job_title", "responsibilities"]
            },
            "description": "List of professional roles, ordered reverse-chronologically."
        },
        "years_of_experience": {
            "type": "number",
            "description": "Total calculated years of professional experience. Example: 4.5"
        },
        "management_level": {
            "type": "string",
            "description": "Inferred management level (e.g., 'Senior', 'Entry-level')."
        },

        # --- Skills ---
        "top_5_technical_skills": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Top 5 technical skills/tools (e.g., 'Python', 'React'). DIRECT AND SHORT."
        },
        "top_5_soft_skills": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Top 5 soft skills (e.g., 'Leadership', 'Communication'). DIRECT AND SHORT."
        },
        "languages": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "language": {"type": "string", "description": "Language name."},
                    "proficiency": {"type": "string", "description": "Proficiency level."}
                },
                "required": ["language"]
            },
            "description": "List of languages and proficiencies."
        },

        # --- Projects, Certs, Awards ---
        "top_5_key_projects": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Top 5 significant projects. DIRECT AND SHORT. MAX 100 WORDS EACH."
        },
        "top_5_certifications": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Top 5 relevant certifications. DIRECT AND SHORT."
        },
        "top_5_awards": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Top 5 awards or honors. DIRECT AND SHORT."
        },

        # --- Analysis ---
        "nationality": {
            "type": "string",
            "description": "Candidate's nationality."
        },
        "current_employment_status": {
            "type": "string",
            "description": "Current status (e.g., 'Employed', 'Open to work')."
        },
        "top_5_suitable_positions": {
            "type": "array",
            "items": {"type": "string"},
            "description": "List of top 5 most suitable job positions based on skills/experience. DIRECT AND SHORT."
        },
        "candidate_rating": {
            "type": "number",
            "description": "Overall rating 0-10 based on profile strength."
        }
    },
    "required": [
        "full_name", "email_address", "phone_number", "professional_summary",
        "work_experience", "top_5_technical_skills", "top_5_soft_skills", 
        "top_5_key_projects", "candidate_rating", "companies", "jobs_title"
    ]
}
