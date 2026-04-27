"""Shared pytest fixtures â€” builds throw-away CV files and a clean workspace."""
from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path
from typing import Callable

import pytest

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


# --- Helpers -------------------------------------------------------------


def _write_docx(path: Path, text: str) -> None:
    from docx import Document

    doc = Document()
    for line in text.splitlines():
        doc.add_paragraph(line)
    doc.save(str(path))


ALICE_TEXT = """Alice Example
alice@example.com | +1-555-0100 | Berlin, Germany
Senior Python engineer with 6 years of experience in LangChain, AWS, and ML."""

BOB_TEXT = """Bob Example
bob@example.com | +1-555-0200 | Remote, USA
Frontend developer. TypeScript, React, CSS."""


# --- Fixtures ------------------------------------------------------------


@pytest.fixture()
def workspace(tmp_path: Path) -> Path:
    """A tmp workspace with empty CVs/ and output/ directories."""
    (tmp_path / "CVs").mkdir()
    (tmp_path / "output").mkdir()
    return tmp_path


@pytest.fixture()
def make_cv(workspace: Path) -> Callable[[str, str], Path]:
    """Factory that writes a DOCX CV file into the workspace and returns its path."""

    def _make(filename: str, text: str) -> Path:
        path = workspace / "CVs" / filename
        _write_docx(path, text)
        return path

    return _make


@pytest.fixture()
def two_cvs(make_cv) -> None:
    make_cv("alice.docx", ALICE_TEXT)
    make_cv("bob.docx", BOB_TEXT)


@pytest.fixture()
def cli_env(monkeypatch: pytest.MonkeyPatch) -> dict:
    """Base environment for CLI subprocess calls.

    - injects the mock extractor so no real LLM is contacted
    - sets a dummy API key so the OpenAI provider path passes validation
    - makes `cvs_agent` importable from the repo root
    """
    env = os.environ.copy()
    env["CVSAGENT_MOCK_EXTRACTOR"] = "tests.mock_extractor:MockExtractor"
    env["OPENAI_API_KEY"] = "sk-test-dummy"
    # Force UTF-8 I/O so Rich's fancy unicode never hits a cp1252 console on Windows.
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUTF8"] = "1"
    # Ensure the subprocess can import both the package and the tests module.
    existing = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = str(ROOT) + (os.pathsep + existing if existing else "")
    # Disable any user-level .env that might point to a real key.
    env.pop("CVSAGENT_PROVIDER", None)
    env.pop("CVSAGENT_MODEL", None)
    return env


@pytest.fixture(autouse=True)
def _clean_stray_partials(workspace: Path):
    """Remove incremental partials between tests so assertions stay clean."""
    yield
    partial = workspace / "output" / ".partial.jsonl"
    if partial.exists():
        partial.unlink()
    cache = workspace / ".cvsagent_cache"
    if cache.exists():
        shutil.rmtree(cache, ignore_errors=True)
