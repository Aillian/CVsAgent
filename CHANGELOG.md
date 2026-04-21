# Changelog

All notable changes to this project will be documented here. The format is
based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this
project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] – 2026-04-21

First open-source release. Everything below is relative to the previous
pre-release internal version.

### Added
- Pydantic `CVData` schema for robust LLM output validation.
- Local-LLM support via `--provider ollama`.
- DOCX résumé support alongside PDF.
- Optional OCR fallback (`--ocr`) for scanned PDFs via `pytesseract`+`pdf2image`.
- On-disk cache keyed by SHA-256 of each CV file; skipped CVs are never re-billed.
- `--format csv|xlsx|json` output with timestamped filenames and `--output-file`
  override.
- Rich progress bar with ETA + stage names.
- Pre-run token and USD cost estimate (OpenAI only).
- Interactive PII warning before transmitting CV text to a cloud provider.
- Partial results are streamed to `Output/.partial.jsonl` so a crash never
  discards completed work.
- Retry with exponential backoff on LLM failures (via `tenacity`).
- `--dry-run`, `--verbose`, `--log-file`, `--clear-cache`, `--yes` CLI flags.
- Multi-stage `Dockerfile` (builder → base → cli → ui) with a non-root user and
  a UI target wired up for a future web interface.
- Integration test suite that invokes `python main.py` end-to-end with mocked
  LLM calls.
- `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `SECURITY.md`, `CHANGELOG.md`,
  `.env.example`, `.dockerignore`, and GitHub issue/PR templates.

### Changed
- Split `main.py` into a thin entrypoint + `cvs_agent.app` orchestration layer.
- Extracted mapping logic into `cvs_agent/mapper.py`.
- All constants, defaults, and env-driven settings centralised in
  `cvs_agent/config.py`.
- Loader now uses `pathlib`, logs via the shared `console`, and validates file
  size against a 20 MB cap.
- Output files are timestamped by default to prevent accidental overwrites.
- `Dockerfile` base updated to `python:3.12-slim`.
- `.gitignore` case-corrected and expanded; committed sample CV and output
  files removed.
- `requirements.txt` reduced from 75 transitive pins to ~10 direct deps.

### Removed
- Dead/broken `cvs_agent/llm_pipeline.py` (imports referenced non-existent
  symbols and was never called).
- Invalid `required: [companies, jobs_title]` entries from the old JSON schema.
- Committed personal CV (`CVs/Ali Abuharb's CV.pdf`) and output spreadsheet.

### Fixed
- Schema validation errors caused by required fields that did not exist in the
  schema's `properties`.
- `.gitignore` case mismatch that prevented extraction output from being
  ignored on case-sensitive filesystems.
- Broken relative-imports workaround (`try: from .x / except: from x`) by
  adding `cvs_agent/__init__.py`.
