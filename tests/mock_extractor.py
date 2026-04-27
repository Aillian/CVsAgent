"""Deterministic drop-in replacement for ``CVExtractor`` used by tests.

The real CVExtractor talks to OpenAI / Ollama. Here we expose a class with the
same constructor signature and ``extract`` / ``extract_batch`` /
``estimate_cost`` methods, but that returns canned data keyed off the CV text
so each test fixture produces predictable rows.

Tests activate it by setting::

    os.environ["CVSAGENT_MOCK_EXTRACTOR"] = "tests.mock_extractor:MockExtractor"

Because ``cvs_agent.app`` honours that env var, the CLI then uses this class
without any further wiring.
"""
from __future__ import annotations

import os
from typing import Any, Dict, List, Optional


def _canned_result(text: str, custom_fields: List[str], with_target_match: bool) -> Dict[str, Any]:
    """Return a fixed, realistic-looking CV dict derived from keywords in text."""
    lower = text.lower()
    if "alice" in lower:
        base = {
            "full_name": "Alice Example",
            "email_address": "alice@example.com",
            "phone_number": "+1-555-0100",
            "linkedin_url": "https://linkedin.com/in/alice",
            "portfolio_urls": ["https://github.com/alice"],
            "location_city": "Berlin",
            "location_country": "Germany",
            "professional_summary": "Senior Python engineer with ML experience.",
            "education": [
                {
                    "university": "TU Berlin",
                    "degree": "MSc",
                    "major": "Computer Science",
                    "gpa": "3.9/4.0",
                    "graduation_date": "June 2020",
                }
            ],
            "work_experience": [
                {
                    "company": "Acme",
                    "job_title": "Senior Python Developer",
                    "is_current": True,
                    "responsibilities": ["Built RAG pipelines", "Mentored juniors"],
                }
            ],
            "years_of_experience": 6.0,
            "management_level": "Senior",
            "top_5_technical_skills": ["Python", "LangChain", "AWS", "Docker", "Postgres"],
            "top_5_soft_skills": ["Communication", "Mentorship", "Problem solving", "Ownership", "Empathy"],
            "languages": [{"language": "English", "proficiency": "Fluent"}],
            "top_5_key_projects": ["CV Extraction Agent"],
            "top_5_certifications": ["AWS Solutions Architect"],
            "top_5_awards": [],
            "nationality": "German",
            "current_employment_status": "Employed",
            "top_5_suitable_positions": ["Senior ML Engineer", "Tech Lead"],
            "candidate_rating": 8.7,
        }
    else:
        base = {
            "full_name": "Bob Example",
            "email_address": "bob@example.com",
            "phone_number": "+1-555-0200",
            "linkedin_url": None,
            "portfolio_urls": [],
            "location_city": "Remote",
            "location_country": "USA",
            "professional_summary": "Frontend developer.",
            "education": [
                {
                    "university": "MIT",
                    "degree": "BSc",
                    "major": "Mathematics",
                    "gpa": None,
                    "graduation_date": "May 2022",
                }
            ],
            "work_experience": [
                {
                    "company": "Globex",
                    "job_title": "Frontend Engineer",
                    "is_current": True,
                    "responsibilities": ["Built React apps"],
                }
            ],
            "years_of_experience": 2.5,
            "management_level": "Mid",
            "top_5_technical_skills": ["TypeScript", "React", "CSS"],
            "top_5_soft_skills": ["Collaboration"],
            "languages": [{"language": "English", "proficiency": "Native"}],
            "top_5_key_projects": [],
            "top_5_certifications": [],
            "top_5_awards": [],
            "nationality": "American",
            "current_employment_status": "Employed",
            "top_5_suitable_positions": ["Frontend Engineer"],
            "candidate_rating": 6.5,
        }

    for f in custom_fields:
        base[f] = f"mock-{f}"

    if with_target_match:
        suitable = "senior" in base.get("professional_summary", "").lower()
        base["target_role_match"] = {
            "suitable": suitable,
            "reason": "Mock assessment based on keywords.",
        }
    return base


class MockExtractor:
    """Drop-in replacement for ``cvs_agent.pipeline.CVExtractor``."""

    def __init__(
        self,
        model_name: str,
        provider: str = "openai",
        api_key: Optional[str] = None,
        ollama_base_url: Optional[str] = None,
        custom_fields: Optional[List[str]] = None,
        job_description: Optional[str] = None,
        rate_limit_rps: float = 0.5,
    ) -> None:
        self.model_name = model_name
        self.provider = provider
        self.custom_fields = list(custom_fields or [])
        self.job_description = job_description

    def extract(self, text: str) -> Dict[str, Any]:
        if os.getenv("CVSAGENT_FAIL_ON_EXTRACT"):
            raise AssertionError("extract() should not be used by batch mode")
        return _canned_result(
            text=text,
            custom_fields=self.custom_fields,
            with_target_match=bool(self.job_description),
        )

    def extract_batch(self, texts: List[str], max_concurrency: int):
        fail_index = os.getenv("CVSAGENT_MOCK_BATCH_FAIL_INDEX")
        for index in reversed(range(len(texts))):
            if fail_index is not None and index == int(fail_index):
                yield index, {}
                continue
            yield index, _canned_result(
                text=texts[index],
                custom_fields=self.custom_fields,
                with_target_match=bool(self.job_description),
            )

    def estimate_cost(self, texts: List[str]) -> Optional[Dict[str, float]]:
        total = sum(len(t) for t in texts)
        return {
            "input_tokens": total // 4,
            "output_tokens": 1000 * len(texts),
            "usd": 0.001 * len(texts),
        }
