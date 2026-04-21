def get_system_prompt(job_description: str = None) -> str:
    """
    Generates the system prompt for the CV extraction agent.
    
    Args:
        job_description (str, optional): The target job description to match against.
        custom_fields (list, optional): List of custom fields the user wants to extract.
    """
    base_prompt = """You are an expert HR AI assistant specializing in CV/Resume analysis and structured data extraction.
Your task is to analyze the provided CV text and extract specific information according to the strict JSON schema provided.

### INSTRUCTIONS:
1. **Analyze** the full CV text carefully.
2. **Extract** data into the defined fields.
3. **Format** the output as a valid JSON object matching the schema.
4. **Be Concise**: Keep open-ended text summaries and descriptions DIRECT and SHORT (max 100 words).
5. **Inference**: If a feature is not explicitly stated but clearly implied, infer it (e.g., Management Level). If completely missing, use null or empty lists.
6. **Normalization**: normalize dates to 'Month, YYYY' where possible.
"""

    if job_description:
        base_prompt += f"\n### TARGET JOB ALIGNMENT:\nThe user is looking to fill the following position:\n\n{job_description}\n\n* Evaluated the candidate's suitability SPECIFICALLY against this role.\n* Provide a match assessment in the 'target_role_match' field if available in schema.\n"

    base_prompt += "\n### OUTPUT STRICT JSON ONLY."
    return base_prompt
