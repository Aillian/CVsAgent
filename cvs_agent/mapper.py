"""Flatten structured ``CVData``-shaped dicts into a single tabular row.

The LLM returns a nested structure; exporters want a flat dict per candidate
so that it maps cleanly to a spreadsheet column layout.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from .utils import join_list


def flatten_cv(
    filename: str,
    data: Dict[str, Any],
    custom_fields: Optional[List[str]] = None,
    include_target_match: bool = False,
) -> Dict[str, Any]:
    """Flatten a structured CV dict into a single-row mapping suitable for Excel/CSV."""
    custom_fields = custom_fields or []

    education_list = data.get("education") or []
    education_str = "; ".join(
        f"{ed.get('degree', '')} in {ed.get('major', '')} at "
        f"{ed.get('university', '')} ({ed.get('graduation_date', '')})"
        for ed in education_list
    )

    work_list = data.get("work_experience") or []
    companies_str = join_list([w.get("company", "") for w in work_list])
    roles_str = join_list([w.get("job_title", "") for w in work_list])
    responsibilities_str = "; ".join(
        f"{w.get('company', '')}: " + join_list(w.get("responsibilities", []))
        for w in work_list
    )

    languages_list = data.get("languages") or []
    languages_str = join_list(
        [
            f"{l.get('language')} ({l.get('proficiency') or 'n/a'})"
            for l in languages_list
            if l.get("language")
        ]
    )

    row: Dict[str, Any] = {
        "Filename": filename,
        # --- Identity & Contact ---
        "Full Name": data.get("full_name"),
        "Email Address": data.get("email_address"),
        "Phone Number": data.get("phone_number"),
        "LinkedIn URL": data.get("linkedin_url"),
        "Portfolio URLs": join_list(data.get("portfolio_urls")),
        "City": data.get("location_city"),
        "Country": data.get("location_country"),
        # --- Professional Summary ---
        "Professional Summary": data.get("professional_summary"),
        # --- Education ---
        "Education History": education_str,
        # --- Work Experience ---
        "Years of Experience": data.get("years_of_experience"),
        "Management Level": data.get("management_level"),
        "Companies": companies_str,
        "Job Titles": roles_str,
        "Key Responsibilities": responsibilities_str,
        # --- Skills ---
        "Technical Skills": join_list(data.get("top_5_technical_skills")),
        "Soft Skills": join_list(data.get("top_5_soft_skills")),
        "Languages": languages_str,
        # --- Projects ---
        "Key Projects": join_list(data.get("top_5_key_projects")),
        # --- Certifications & Awards ---
        "Certifications": join_list(data.get("top_5_certifications")),
        "Awards": join_list(data.get("top_5_awards")),
        # --- Analysis ---
        "Nationality": data.get("nationality"),
        "Employment Status": data.get("current_employment_status"),
        "Suitable Positions": join_list(data.get("top_5_suitable_positions")),
    }

    # --- Dynamic: Custom Fields ---
    for field in custom_fields:
        row[field] = data.get(field, "")

    # --- Dynamic: Target Job Match ---
    if include_target_match:
        match = data.get("target_role_match") or {}
        row["Target Role Match"] = match.get("suitable")
        row["Match Reason"] = match.get("reason")

    # Ensure rating is the last column for easy scanning.
    row["Rating"] = data.get("candidate_rating")

    return row
