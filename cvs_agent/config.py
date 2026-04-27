"""Centralised configuration for CVsAgent.

All constants, default paths, and environment-driven settings live here so the
rest of the codebase reads from a single source of truth.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

# --- Paths ---------------------------------------------------------------

ROOT_DIR = Path(__file__).resolve().parent.parent
DEFAULT_CV_DIR = Path(os.getenv("CVSAGENT_CV_DIR", "CVs"))
DEFAULT_OUTPUT_DIR = Path(os.getenv("CVSAGENT_OUTPUT_DIR", "output"))
DEFAULT_CACHE_DIR = Path(os.getenv("CVSAGENT_CACHE_DIR", ".cvsagent_cache"))

# --- Providers & models --------------------------------------------------

PROVIDER_OPENAI = "openai"
PROVIDER_OLLAMA = "ollama"
SUPPORTED_PROVIDERS = (PROVIDER_OPENAI, PROVIDER_OLLAMA)

DEFAULT_PROVIDER = os.getenv("CVSAGENT_PROVIDER", PROVIDER_OPENAI)
DEFAULT_MODEL_OPENAI = os.getenv("CVSAGENT_MODEL", "gpt-5-mini-2025-08-07")
DEFAULT_MODEL_OLLAMA = "llama3.1"

# --- Supported input extensions -----------------------------------------

SUPPORTED_EXTENSIONS = (".pdf", ".docx")

# --- Output --------------------------------------------------------------

OUTPUT_FORMATS = ("xlsx", "csv", "json")
DEFAULT_OUTPUT_FORMAT = "xlsx"
DEFAULT_OUTPUT_STEM = "CVs_Info_Extracted"

# --- Safety limits -------------------------------------------------------

MAX_PDF_BYTES = 20 * 1024 * 1024          # 20 MB hard cap per file
MAX_CV_COUNT_WARN = 200                    # warn above this many files

# --- Rate-limit / retry --------------------------------------------------

DEFAULT_RATE_LIMIT_RPS = float(os.getenv("CVSAGENT_RATE_LIMIT_RPS", "0.5"))
DEFAULT_RATE_LIMIT_BUCKET = 10
DEFAULT_BATCH_WORKERS_OPENAI = 4
DEFAULT_BATCH_WORKERS_OLLAMA = 1
RETRY_ATTEMPTS = 3
RETRY_BASE_SECONDS = 2.0


@dataclass
class RunConfig:
    """Resolved configuration for a single CLI invocation."""

    cv_dir: Path = DEFAULT_CV_DIR
    output_dir: Path = DEFAULT_OUTPUT_DIR
    output_format: str = DEFAULT_OUTPUT_FORMAT
    output_file: Optional[Path] = None

    provider: str = DEFAULT_PROVIDER
    model: str = DEFAULT_MODEL_OPENAI
    api_key: Optional[str] = None
    ollama_base_url: Optional[str] = None

    rate_limit_rps: float = DEFAULT_RATE_LIMIT_RPS
    batch_workers: int = DEFAULT_BATCH_WORKERS_OPENAI

    custom_fields: List[str] = field(default_factory=list)
    job_description: Optional[str] = None

    use_cache: bool = True
    cache_dir: Path = DEFAULT_CACHE_DIR

    ocr: bool = False
    dry_run: bool = False
    verbose: bool = False
    log_file: Optional[Path] = None
    skip_prompts: bool = False  # skip interactive confirmations
