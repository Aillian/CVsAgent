"""Pydantic schema for CV data extraction.

Using Pydantic models gives us:
- Automatic validation of LLM output
- IDE autocomplete and type safety
- Readable error messages on schema mismatch
- Easy JSON-schema generation for LLM providers
"""
from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class Education(BaseModel):
    university: str = Field(..., description="Name of the institution.")
    degree: str = Field(..., description="Degree obtained (e.g., Bachelor, Master, PhD).")
    major: Optional[str] = Field(None, description="Field of study/Major.")
    gpa: Optional[str] = Field(None, description="GPA if listed (e.g., '3.8/4.0').")
    graduation_date: Optional[str] = Field(
        None, description="Date of graduation (e.g., 'May 2020')."
    )


class WorkExperience(BaseModel):
    company: str = Field(..., description="Name of the company.")
    job_title: str = Field(..., description="Title of the role.")
    is_current: Optional[bool] = Field(None, description="True if this is the current role.")
    responsibilities: List[str] = Field(
        default_factory=list,
        description=(
            "Top 5 key responsibilities/achievements. EACH ITEM DIRECT AND SHORT. "
            "MAX 100 WORDS TOTAL FOR ALL ITEMS."
        ),
    )


class Language(BaseModel):
    language: str = Field(..., description="Language name.")
    proficiency: Optional[str] = Field(None, description="Proficiency level.")


class TargetRoleMatch(BaseModel):
    suitable: bool = Field(
        ..., description="True if the candidate is suitable for the target position."
    )
    reason: str = Field(
        ..., description="Brief reason for the suitability assessment. MAX 100 WORDS."
    )


class CVData(BaseModel):
    """Structured extraction of CV/Resume data. Be precise and concise."""

    # --- Identity & Contact ---
    full_name: str = Field(..., description="The full name of the candidate.")
    email_address: Optional[str] = Field(None, description="The primary email address.")
    phone_number: Optional[str] = Field(None, description="The primary phone number.")
    linkedin_url: Optional[str] = Field(None, description="LinkedIn profile URL.")
    portfolio_urls: List[str] = Field(
        default_factory=list,
        description="Portfolio URLs, personal websites, or GitHub profiles.",
    )
    location_city: Optional[str] = Field(None, description="Current city of residence.")
    location_country: Optional[str] = Field(None, description="Current country of residence.")

    # --- Professional Summary ---
    professional_summary: Optional[str] = Field(
        None,
        description="Concise background summary. DIRECT AND SHORT. MAX 100 WORDS.",
    )

    # --- Education ---
    education: List[Education] = Field(
        default_factory=list, description="List of distinct educational degrees."
    )

    # --- Work Experience ---
    work_experience: List[WorkExperience] = Field(
        default_factory=list,
        description="Professional roles, ordered reverse-chronologically.",
    )
    years_of_experience: Optional[float] = Field(
        None, description="Total calculated years of professional experience."
    )
    management_level: Optional[str] = Field(
        None, description="Inferred management level (e.g., 'Senior', 'Entry-level')."
    )

    # --- Skills ---
    top_5_technical_skills: List[str] = Field(
        default_factory=list, description="Top 5 technical skills/tools."
    )
    top_5_soft_skills: List[str] = Field(
        default_factory=list, description="Top 5 soft skills."
    )
    languages: List[Language] = Field(
        default_factory=list, description="Languages and proficiencies."
    )

    # --- Projects, Certs, Awards ---
    top_5_key_projects: List[str] = Field(
        default_factory=list,
        description="Top 5 significant projects. DIRECT AND SHORT. MAX 100 WORDS EACH.",
    )
    top_5_certifications: List[str] = Field(
        default_factory=list, description="Top 5 relevant certifications."
    )
    top_5_awards: List[str] = Field(
        default_factory=list, description="Top 5 awards or honors."
    )

    # --- Analysis ---
    nationality: Optional[str] = Field(None, description="Candidate's nationality.")
    current_employment_status: Optional[str] = Field(
        None, description="Current status (e.g., 'Employed', 'Open to work')."
    )
    top_5_suitable_positions: List[str] = Field(
        default_factory=list,
        description="Top 5 most suitable job positions based on skills/experience.",
    )
    candidate_rating: Optional[float] = Field(
        None, description="Overall rating 0-10 based on profile strength."
    )

    # --- Optional: job-description-driven ---
    target_role_match: Optional[TargetRoleMatch] = Field(
        None,
        description="Assessment of candidate suitability for the specific target role.",
    )


def build_dynamic_schema(
    custom_fields: Optional[List[str]] = None,
    with_target_match: bool = False,
) -> dict:
    """Build a JSON schema dict with optional custom fields / job-match addition.

    We return a plain JSON schema (not a dynamic Pydantic subclass) because some
    LangChain provider strategies accept a schema dict directly, and this keeps
    runtime behaviour simple and explicit.
    """
    schema = CVData.model_json_schema()

    # Strip target_role_match if not requested (it's optional in the model anyway,
    # but keeping it out of the schema guides the LLM to skip it).
    if not with_target_match:
        schema.get("properties", {}).pop("target_role_match", None)

    if custom_fields:
        props = schema.setdefault("properties", {})
        for field in custom_fields:
            if field not in props:
                props[field] = {
                    "type": "string",
                    "description": (
                        f"Extract the value for {field} as a concise string. "
                        "Return an empty string if not found."
                    ),
                }

    return schema
