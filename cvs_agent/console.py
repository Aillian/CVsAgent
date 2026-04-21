"""Rich-based console wrapper used everywhere in the package.

Centralising logging here means modules never have to reach for `print`, and we
can optionally fan out to a log file for long batch runs.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.logging import RichHandler
from rich.panel import Panel
from rich.table import Table


class CVSConsole:
    """Wrapper around Rich console to standardise log format + file logging."""

    def __init__(self) -> None:
        self._console = Console()
        self._logger: Optional[logging.Logger] = None

    # --- Logging setup -----------------------------------------------------
    def setup_logging(
        self,
        verbose: bool = False,
        log_file: Optional[Path] = None,
    ) -> None:
        """Attach file/console logging handlers.

        Console output still goes through Rich via `log()` directly — this only
        mirrors events into a plain text file when `log_file` is provided.
        """
        level = logging.DEBUG if verbose else logging.INFO
        handlers: list[logging.Handler] = [RichHandler(console=self._console, show_path=False, show_time=False)]
        if log_file is not None:
            log_file = Path(log_file)
            log_file.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(log_file, encoding="utf-8")
            file_handler.setFormatter(
                logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
            )
            handlers.append(file_handler)

        logging.basicConfig(level=level, handlers=handlers, force=True)
        self._logger = logging.getLogger("cvsagent")

    # --- Output helpers ----------------------------------------------------
    def print_panel(self, text: str, style: str = "bold green") -> None:
        self._console.print(Panel(text, style=style))

    def log(self, section: str, message: str, style: str = "blue") -> None:
        """Log a structured `[Section]: Message` line to console (+ file)."""
        self._console.print(f"[{style}][{section}]: {message}[/{style}]")
        if self._logger is not None:
            self._logger.info("[%s] %s", section, message)

    def warn(self, section: str, message: str) -> None:
        self.log(section, message, style="yellow")

    def error(self, section: str, message: str) -> None:
        self._console.print(f"[bold red][{section}]: {message}[/bold red]")
        if self._logger is not None:
            self._logger.error("[%s] %s", section, message)

    def print(self, text: str) -> None:
        self._console.print(text)

    def status(self, message: str, spinner: str = "dots"):
        return self._console.status(message, spinner=spinner)

    def confirm(self, message: str, default: bool = False) -> bool:
        """Ask a yes/no question on the CLI. Falls back to ``default`` if input is not a TTY."""
        import sys

        if not sys.stdin.isatty():
            return default
        suffix = "[Y/n]" if default else "[y/N]"
        self._console.print(f"[bold]{message}[/bold] {suffix} ", end="")
        try:
            reply = input().strip().lower()
        except EOFError:
            return default
        if not reply:
            return default
        return reply in ("y", "yes")

    def print_statistics(
        self, total: int, successful: int, failed: int, cached: int, total_time: float
    ) -> None:
        avg_time = total_time / total if total > 0 else 0.0
        table = Table(title="Execution Statistics")
        table.add_column("Metric", style="cyan", no_wrap=True)
        table.add_column("Value", style="magenta")
        table.add_row("Total CVs Processed", str(total))
        table.add_row("Successful", str(successful))
        table.add_row("Failed", str(failed))
        table.add_row("Served From Cache", str(cached))
        table.add_row("Total Execution Time", f"{total_time:.2f}s")
        table.add_row("Average Time per CV", f"{avg_time:.2f}s")
        self._console.print(table)


# Global instance for easy import
console = CVSConsole()
