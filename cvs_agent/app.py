"""High-level CLI / orchestration layer.

This module wires together config, loader, cache, pipeline, mapper, and
exporter. It is kept separate from :mod:`main` so the pipeline can be driven
from tests or a future UI layer without shelling out.
"""
from __future__ import annotations

import argparse
import os
import time
from pathlib import Path
from typing import List, Optional

from dotenv import load_dotenv
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)

from .cache import ExtractionCache
from .config import (
    DEFAULT_CACHE_DIR,
    DEFAULT_CV_DIR,
    DEFAULT_MODEL_OLLAMA,
    DEFAULT_MODEL_OPENAI,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_OUTPUT_FORMAT,
    DEFAULT_PROVIDER,
    DEFAULT_RATE_LIMIT_RPS,
    MAX_CV_COUNT_WARN,
    OUTPUT_FORMATS,
    PROVIDER_OLLAMA,
    PROVIDER_OPENAI,
    SUPPORTED_PROVIDERS,
    RunConfig,
)
from .console import console
from .exporter import save_results
from .loader import LoadedDocument, load_cvs
from .mapper import flatten_cv
from .pipeline import CVExtractor
from .utils import file_sha256, mask_api_key


def _load_extractor_class():
    """Resolve the extractor class, honouring the test/override env var."""
    override = os.getenv("CVSAGENT_MOCK_EXTRACTOR")
    if not override:
        return CVExtractor
    module_path, _, class_name = override.partition(":")
    if not module_path or not class_name:
        raise ValueError(
            "CVSAGENT_MOCK_EXTRACTOR must look like 'module.path:ClassName'"
        )
    import importlib
    module = importlib.import_module(module_path)
    return getattr(module, class_name)


# --- Argument parsing ----------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="cvsagent",
        description="CVsAgent: extract structured data from CVs using an LLM.",
    )

    # --- Inputs / outputs ---
    parser.add_argument("--cv-dir", default=str(DEFAULT_CV_DIR),
                        help="Directory containing input PDF/DOCX CVs.")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR),
                        help="Directory for the generated report.")
    parser.add_argument("--output-file", default=None,
                        help="Explicit output filename (overrides auto-naming).")
    parser.add_argument("--format", choices=OUTPUT_FORMATS, default=DEFAULT_OUTPUT_FORMAT,
                        help="Output format.")

    # --- Provider / model ---
    parser.add_argument("--provider", choices=SUPPORTED_PROVIDERS, default=DEFAULT_PROVIDER,
                        help="LLM provider.")
    parser.add_argument("--model", default=None,
                        help="Model name (defaults depend on provider).")
    parser.add_argument("--api-key", default=None,
                        help="API key (prefer OPENAI_API_KEY env var — CLI args leak to shell history).")
    parser.add_argument("--ollama-base-url", default=os.getenv("OLLAMA_BASE_URL"),
                        help="Ollama server URL (default: http://localhost:11434).")
    parser.add_argument("--rate-limit-rps", type=float, default=DEFAULT_RATE_LIMIT_RPS,
                        help="OpenAI rate limit in requests/second.")

    # --- Dynamic fields ---
    parser.add_argument("--add-fields", nargs="+", default=None,
                        help="Additional custom fields to extract (e.g. VisaStatus DriverLicense).")
    parser.add_argument("--job-description", default=None,
                        help="Job description text to match candidates against.")
    parser.add_argument("--job-description-file", default=None,
                        help="Path to a text file with the job description.")

    # --- Features ---
    parser.add_argument("--no-cache", action="store_true",
                        help="Disable the on-disk extraction cache.")
    parser.add_argument("--clear-cache", action="store_true",
                        help="Clear the cache before running.")
    parser.add_argument("--cache-dir", default=str(DEFAULT_CACHE_DIR),
                        help="Cache directory (default: .cvsagent_cache).")
    parser.add_argument("--ocr", action="store_true",
                        help="Run OCR on PDFs that yield no text (requires pytesseract + pdf2image).")

    # --- UX ---
    parser.add_argument("--dry-run", action="store_true",
                        help="Load documents and print a cost estimate without calling the LLM.")
    parser.add_argument("--skip-prompts", "-s", action="store_true",
                        help="Skip all interactive prompts (accept defaults).")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Enable debug-level logging.")
    parser.add_argument("--log-file", default=None,
                        help="Mirror logs to this file in addition to the console.")
    parser.add_argument("--version", action="version",
                        version=f"CVsAgent {_get_version()}")

    return parser


def _get_version() -> str:
    try:
        from cvs_agent import __version__
        return __version__
    except Exception:  # pragma: no cover
        return "0.0.0"


# --- Config resolution ---------------------------------------------------


def _resolve_model(provider: str, explicit: Optional[str]) -> str:
    if explicit:
        return explicit
    if provider == PROVIDER_OLLAMA:
        return os.getenv("CVSAGENT_MODEL", DEFAULT_MODEL_OLLAMA)
    return os.getenv("CVSAGENT_MODEL", DEFAULT_MODEL_OPENAI)


def _load_job_description(args: argparse.Namespace) -> Optional[str]:
    if args.job_description_file:
        try:
            return Path(args.job_description_file).read_text(encoding="utf-8")
        except OSError as exc:
            console.error("Config", f"Could not read job description file: {exc}")
            return None
    return args.job_description


def args_to_config(args: argparse.Namespace) -> Optional[RunConfig]:
    provider = args.provider
    api_key: Optional[str] = args.api_key
    if provider == PROVIDER_OPENAI:
        api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not api_key:
            console.error(
                "Config",
                "OpenAI API key required. Set OPENAI_API_KEY in your environment or .env file.",
            )
            return None

    job_desc = _load_job_description(args)
    if args.job_description_file and job_desc is None:
        return None  # error already logged

    return RunConfig(
        cv_dir=Path(args.cv_dir),
        output_dir=Path(args.output_dir),
        output_format=args.format,
        output_file=Path(args.output_file) if args.output_file else None,
        provider=provider,
        model=_resolve_model(provider, args.model),
        api_key=api_key,
        ollama_base_url=args.ollama_base_url,
        rate_limit_rps=args.rate_limit_rps,
        custom_fields=list(args.add_fields or []),
        job_description=job_desc,
        use_cache=not args.no_cache,
        cache_dir=Path(args.cache_dir),
        ocr=args.ocr,
        dry_run=args.dry_run,
        verbose=args.verbose,
        log_file=Path(args.log_file) if args.log_file else None,
        skip_prompts=args.skip_prompts,
    )


# --- Orchestration -------------------------------------------------------


def _pii_warning(cfg: RunConfig) -> bool:
    """Warn the user about sending PII to a 3rd party. Returns True to continue."""
    if cfg.provider == PROVIDER_OLLAMA:
        return True  # local model — no external transmission
    if cfg.skip_prompts:
        return True
    return console.confirm(
        "CV contents will be sent to OpenAI for processing. Continue?",
        default=True,
    )


def _print_run_banner(cfg: RunConfig) -> None:
    console.print_panel(
        f"[bold green]Starting CVsAgent[/bold green]\n"
        f"Provider: [cyan]{cfg.provider}[/cyan]   "
        f"Model: [cyan]{cfg.model}[/cyan]\n"
        f"CVs: [cyan]{cfg.cv_dir}[/cyan]   "
        f"Output: [cyan]{cfg.output_dir}[/cyan] ({cfg.output_format})\n"
        f"Cache: [cyan]{'on' if cfg.use_cache else 'off'}[/cyan]   "
        f"API key: [cyan]{mask_api_key(cfg.api_key)}[/cyan]"
    )
    if cfg.custom_fields:
        console.log("Config", f"Custom fields: {cfg.custom_fields}")
    if cfg.job_description:
        console.log("Config", "Target job description loaded")


def run(cfg: RunConfig) -> int:
    """Run one end-to-end extraction. Returns a process exit code."""
    console.setup_logging(verbose=cfg.verbose, log_file=cfg.log_file)
    _print_run_banner(cfg)

    # --- 1. Load documents ---
    start_time = time.time()
    with console.status("Loading CVs...", spinner="dots"):
        documents: List[LoadedDocument] = load_cvs(cfg.cv_dir, ocr_fallback=cfg.ocr)

    if not documents:
        console.warn("Loader", "No CVs found to process.")
        return 1

    if len(documents) > MAX_CV_COUNT_WARN and not cfg.skip_prompts:
        if not console.confirm(
            f"About to process {len(documents)} CVs — continue?", default=True
        ):
            console.warn("Runner", "Aborted by user.")
            return 130

    # --- 2. Cache setup ---
    cache = ExtractionCache(cfg.cache_dir, enabled=cfg.use_cache)
    if cfg.use_cache:
        for doc in documents:
            doc.sha256 = file_sha256(doc.path)

    # --- 3. Build extractor ---
    # `CVSAGENT_MOCK_EXTRACTOR=module.path:ClassName` lets tests (or power
    # users) substitute the LLM layer without touching the rest of the code.
    try:
        extractor_cls = _load_extractor_class()
        extractor = extractor_cls(
            model_name=cfg.model,
            provider=cfg.provider,
            api_key=cfg.api_key,
            ollama_base_url=cfg.ollama_base_url,
            custom_fields=cfg.custom_fields,
            job_description=cfg.job_description,
            rate_limit_rps=cfg.rate_limit_rps,
        )
    except Exception as exc:  # noqa: BLE001
        console.error("Pipeline", f"Failed to initialise extractor: {exc}")
        return 2

    # --- 4. Cost estimate + confirmation ---
    to_process = [d for d in documents if cache.get(d.sha256) is None] if cfg.use_cache else list(documents)
    estimate = extractor.estimate_cost([d.text for d in to_process])
    if estimate:
        console.log(
            "Estimate",
            f"~{estimate['input_tokens']:,} input + {estimate['output_tokens']:,} "
            f"output tokens -> ~${estimate['usd']:.3f} USD",
            style="magenta",
        )

    if cfg.dry_run:
        console.print_panel(
            f"[bold yellow]Dry run[/bold yellow]\n"
            f"Would process {len(to_process)} of {len(documents)} CVs "
            f"(cache would serve {len(documents) - len(to_process)}).",
            style="yellow",
        )
        return 0

    if not _pii_warning(cfg):
        console.warn("Runner", "Aborted by user.")
        return 130

    # --- 5. Extract (serial loop so we can report progress + persist partials) ---
    results = []
    successful = cached = failed = 0
    incremental_path = cfg.output_dir / ".partial.jsonl"
    cfg.output_dir.mkdir(parents=True, exist_ok=True)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        MofNCompleteColumn(),
        TextColumn("[bold]{task.fields[name]}[/bold]"),
        TimeElapsedColumn(),
        TimeRemainingColumn(),
        console=console._console,
    ) as progress:
        task_id = progress.add_task("Extracting", total=len(documents), name="starting")

        for doc in documents:
            progress.update(task_id, name=doc.filename)
            data = cache.get(doc.sha256)
            hit_cache = data is not None

            if not hit_cache:
                data = extractor.extract(doc.text)
                if data:
                    cache.set(doc.sha256, data)

            if not data:
                failed += 1
                progress.advance(task_id)
                continue

            try:
                row = flatten_cv(
                    filename=doc.filename,
                    data=data,
                    custom_fields=cfg.custom_fields,
                    include_target_match=bool(cfg.job_description),
                )
                results.append(row)
                if hit_cache:
                    cached += 1
                else:
                    successful += 1
                # Persist partial result so a crash later does not lose work.
                with incremental_path.open("a", encoding="utf-8") as f:
                    import json as _json
                    f.write(_json.dumps(row, default=str) + "\n")
            except Exception as exc:  # noqa: BLE001
                console.error("Mapper", f"Error mapping {doc.filename}: {exc}")
                failed += 1
            progress.advance(task_id)

    # --- 6. Save + report ---
    save_results(
        results,
        output_dir=cfg.output_dir,
        output_format=cfg.output_format,
        output_file=cfg.output_file,
    )

    # Best-effort cleanup of the partial log now that the final report is saved.
    try:
        if incremental_path.exists():
            incremental_path.unlink()
    except OSError:
        pass

    total_time = time.time() - start_time
    console.print_statistics(
        total=len(documents),
        successful=successful,
        failed=failed,
        cached=cached,
        total_time=total_time,
    )
    return 0 if failed == 0 else 3


def main(argv: Optional[List[str]] = None) -> int:
    # Only load .env from the current working directory. Walking up the
    # filesystem would accidentally pick up a user's global .env, which is
    # both surprising and a test-isolation hazard.
    load_dotenv(dotenv_path=Path.cwd() / ".env", override=False)
    parser = build_parser()
    args = parser.parse_args(argv)

    cfg = args_to_config(args)
    if cfg is None:
        return 2

    # Honour --clear-cache even if caching is disabled for this run.
    if args.clear_cache:
        cleared = ExtractionCache(cfg.cache_dir, enabled=True).clear()
        console.log("Cache", f"Cleared {cleared} cached entries.")

    return run(cfg)
