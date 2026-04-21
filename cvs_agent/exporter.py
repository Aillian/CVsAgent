"""Write flattened CV rows to disk in XLSX / CSV / JSON formats."""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

from .config import DEFAULT_OUTPUT_FORMAT, DEFAULT_OUTPUT_STEM, OUTPUT_FORMATS
from .console import console


def _resolve_output_path(
    output_dir: Path,
    fmt: str,
    output_file: Optional[Path] = None,
) -> Path:
    """Build the full output path. Honours an explicit filename if provided."""
    if output_file is not None:
        output_file = Path(output_file)
        if output_file.is_absolute():
            return output_file
        return output_dir / output_file

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return output_dir / f"{DEFAULT_OUTPUT_STEM}_{timestamp}.{fmt}"


def save_results(
    results: List[Dict[str, Any]],
    output_dir: Path,
    output_format: str = DEFAULT_OUTPUT_FORMAT,
    output_file: Optional[Path] = None,
) -> Optional[Path]:
    """Persist ``results`` to ``output_dir`` in the requested format.

    Returns the absolute output path on success, or ``None`` if nothing was written.
    """
    if not results:
        console.warn("Exporter", "No results to save.")
        return None

    fmt = output_format.lower()
    if fmt not in OUTPUT_FORMATS:
        console.error(
            "Exporter",
            f"Unsupported format '{output_format}'. Supported: {', '.join(OUTPUT_FORMATS)}",
        )
        return None

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    path = _resolve_output_path(output_dir, fmt, output_file)

    try:
        if fmt == "xlsx":
            pd.DataFrame(results).to_excel(path, index=False)
        elif fmt == "csv":
            pd.DataFrame(results).to_csv(path, index=False, encoding="utf-8-sig")
        elif fmt == "json":
            path.write_text(
                json.dumps(results, indent=2, ensure_ascii=False, default=str),
                encoding="utf-8",
            )
    except Exception as exc:  # noqa: BLE001
        console.error("Exporter", f"Failed to save results: {exc}")
        return None

    console.log("Exporter", f"Results saved to [bold]{path}[/bold]", style="green")
    return path
