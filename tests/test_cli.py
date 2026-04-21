"""End-to-end CLI tests — each invokes ``python main.py`` in a subprocess.

The mock extractor (selected via ``CVSAGENT_MOCK_EXTRACTOR``) means no network
is needed; we exercise argument parsing, the loader, the cache, the mapper,
and all exporters through the real CLI boundary.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent


def run_cli(args: list[str], env: dict, cwd: Path, timeout: int = 60) -> subprocess.CompletedProcess:
    """Invoke ``python main.py <args>`` with a clean workspace cwd."""
    cmd = [sys.executable, str(ROOT / "main.py"), *args]
    return subprocess.run(
        cmd,
        env=env,
        cwd=str(cwd),
        stdin=subprocess.DEVNULL,  # avoid pytest's captured stdin on Windows
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        encoding="utf-8",           # Windows default is cp1252; force UTF-8
        errors="replace",
        timeout=timeout,
    )


# --- CLI surface ---------------------------------------------------------


def test_help_exits_zero(workspace, cli_env):
    result = run_cli(["--help"], env=cli_env, cwd=workspace)
    assert result.returncode == 0, result.stderr
    assert "CVsAgent" in result.stdout
    assert "--format" in result.stdout


def test_version_flag(workspace, cli_env):
    result = run_cli(["--version"], env=cli_env, cwd=workspace)
    assert result.returncode == 0, result.stderr
    assert "CVsAgent" in result.stdout


def test_missing_api_key_fails_cleanly(workspace):
    env = {"PATH": "", "SystemRoot": r"C:\Windows", "PYTHONPATH": str(ROOT)}
    env.pop("OPENAI_API_KEY", None)
    env["CVSAGENT_MOCK_EXTRACTOR"] = "tests.mock_extractor:MockExtractor"
    # Still need minimal OS env on Windows for subprocess to start.
    import os
    env["SYSTEMROOT"] = os.environ.get("SYSTEMROOT", r"C:\Windows")
    result = run_cli(
        ["--cv-dir", str(workspace / "CVs"), "--output-dir", str(workspace / "Output")],
        env=env,
        cwd=workspace,
    )
    assert result.returncode == 2, result.stderr + result.stdout
    assert "OpenAI API key" in (result.stdout + result.stderr)


# --- Happy path ----------------------------------------------------------


@pytest.mark.usefixtures("two_cvs")
def test_end_to_end_xlsx(workspace, cli_env):
    out_dir = workspace / "Output"
    result = run_cli(
        [
            "--cv-dir", str(workspace / "CVs"),
            "--output-dir", str(out_dir),
            "--format", "xlsx",
            "--yes",
            "--no-cache",
        ],
        env=cli_env,
        cwd=workspace,
    )
    assert result.returncode == 0, result.stdout + result.stderr

    xlsx_files = list(out_dir.glob("*.xlsx"))
    assert len(xlsx_files) == 1, f"expected one xlsx, got {xlsx_files}"

    # Validate contents.
    import pandas as pd

    df = pd.read_excel(xlsx_files[0])
    assert len(df) == 2
    names = set(df["Full Name"])
    assert names == {"Alice Example", "Bob Example"}
    assert "Rating" in df.columns
    assert df.columns[-1] == "Rating"  # Rating must stay last column


@pytest.mark.usefixtures("two_cvs")
def test_end_to_end_csv(workspace, cli_env):
    out_file = workspace / "Output" / "results.csv"
    result = run_cli(
        [
            "--cv-dir", str(workspace / "CVs"),
            "--output-dir", str(workspace / "Output"),
            "--format", "csv",
            "--output-file", "results.csv",
            "--yes", "--no-cache",
        ],
        env=cli_env,
        cwd=workspace,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert out_file.exists()
    content = out_file.read_text(encoding="utf-8-sig")
    assert "Alice Example" in content
    assert "Bob Example" in content


@pytest.mark.usefixtures("two_cvs")
def test_end_to_end_json(workspace, cli_env):
    out_file = workspace / "Output" / "results.json"
    result = run_cli(
        [
            "--cv-dir", str(workspace / "CVs"),
            "--output-dir", str(workspace / "Output"),
            "--format", "json",
            "--output-file", "results.json",
            "--yes", "--no-cache",
        ],
        env=cli_env,
        cwd=workspace,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(out_file.read_text(encoding="utf-8"))
    assert len(payload) == 2
    assert {row["Full Name"] for row in payload} == {"Alice Example", "Bob Example"}


# --- Dynamic fields / job description ------------------------------------


@pytest.mark.usefixtures("two_cvs")
def test_custom_fields_end_up_as_columns(workspace, cli_env):
    out_file = workspace / "Output" / "custom.json"
    result = run_cli(
        [
            "--cv-dir", str(workspace / "CVs"),
            "--output-dir", str(workspace / "Output"),
            "--format", "json",
            "--output-file", "custom.json",
            "--add-fields", "VisaStatus", "DriverLicense",
            "--yes", "--no-cache",
        ],
        env=cli_env,
        cwd=workspace,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    rows = json.loads(out_file.read_text(encoding="utf-8"))
    assert rows[0]["VisaStatus"] == "mock-VisaStatus"
    assert rows[0]["DriverLicense"] == "mock-DriverLicense"


@pytest.mark.usefixtures("two_cvs")
def test_job_description_adds_match_columns(workspace, cli_env, tmp_path):
    jd_file = tmp_path / "jd.txt"
    jd_file.write_text("Senior Python Developer with ML experience.", encoding="utf-8")

    out_file = workspace / "Output" / "match.json"
    result = run_cli(
        [
            "--cv-dir", str(workspace / "CVs"),
            "--output-dir", str(workspace / "Output"),
            "--format", "json",
            "--output-file", "match.json",
            "--job-description-file", str(jd_file),
            "--yes", "--no-cache",
        ],
        env=cli_env,
        cwd=workspace,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    rows = json.loads(out_file.read_text(encoding="utf-8"))
    for r in rows:
        assert "Target Role Match" in r
        assert "Match Reason" in r


# --- Dry run + empty input paths -----------------------------------------


@pytest.mark.usefixtures("two_cvs")
def test_dry_run_does_not_write_output(workspace, cli_env):
    result = run_cli(
        [
            "--cv-dir", str(workspace / "CVs"),
            "--output-dir", str(workspace / "Output"),
            "--dry-run",
            "--yes",
        ],
        env=cli_env,
        cwd=workspace,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert list((workspace / "Output").glob("*.xlsx")) == []
    assert list((workspace / "Output").glob("*.csv")) == []
    assert list((workspace / "Output").glob("*.json")) == []
    assert "Dry run" in result.stdout


def test_empty_cv_dir_returns_nonzero(workspace, cli_env):
    result = run_cli(
        [
            "--cv-dir", str(workspace / "CVs"),
            "--output-dir", str(workspace / "Output"),
            "--yes", "--no-cache",
        ],
        env=cli_env,
        cwd=workspace,
    )
    assert result.returncode == 1, result.stdout + result.stderr
    assert "No CVs found" in (result.stdout + result.stderr)


# --- Cache ---------------------------------------------------------------


@pytest.mark.usefixtures("two_cvs")
def test_cache_hits_on_second_run(workspace, cli_env):
    cache_dir = workspace / ".cvsagent_cache"
    base_args = [
        "--cv-dir", str(workspace / "CVs"),
        "--output-dir", str(workspace / "Output"),
        "--cache-dir", str(cache_dir),
        "--format", "json",
        "--yes",
    ]

    first = run_cli(base_args + ["--output-file", "r1.json"], env=cli_env, cwd=workspace)
    assert first.returncode == 0, first.stdout + first.stderr
    assert len(list(cache_dir.glob("*.json"))) == 2

    second = run_cli(base_args + ["--output-file", "r2.json"], env=cli_env, cwd=workspace)
    assert second.returncode == 0, second.stdout + second.stderr
    # Second run must report at least one cached hit in the stats table.
    assert "Served From Cache" in second.stdout
    # Extract the "Served From Cache" row and confirm it is > 0.
    for line in second.stdout.splitlines():
        if "Served From Cache" in line:
            assert " 2 " in line or line.rstrip().endswith(" 2")
            break
    else:
        pytest.fail("Statistics table missing Served From Cache row")
