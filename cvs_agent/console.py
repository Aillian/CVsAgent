from rich.console import Console
from rich.panel import Panel
from typing import Optional

class CVSConsole:
    """
    Wrapper around Rich console to standardize logging format.
    """
    def __init__(self):
        self._console = Console()

    def print_panel(self, text: str, style: str = "bold green"):
        """Prints a panel with the given text."""
        self._console.print(Panel(text, style=style))

    def log(self, section: str, message: str, style: str = "blue"):
        """
        Logs a message in the format: [Section]: Message
        
        Args:
            section: The component name (e.g., 'Agent_Pipeline')
            message: The message to display
            style: The rich style to apply (default: 'blue')
        """
        self._console.print(f"[{style}][{section}]: {message}[/{style}]")

    def print(self, text: str):
        """Standard print wrapper."""
        self._console.print(text)

    def status(self, message: str, spinner: str = "dots"):
        """Returns a status spinner context manager."""
        return self._console.status(message, spinner=spinner)

    def print_statistics(self, total: int, successful: int, failed: int, total_time: float):
        """
        Prints a summary table of the execution statistics.
        """
        from rich.table import Table
        
        avg_time = total_time / total if total > 0 else 0
        
        table = Table(title="Execution Statistics")
        table.add_column("Metric", style="cyan", no_wrap=True)
        table.add_column("Value", style="magenta")
        
        table.add_row("Total CVs Processed", str(total))
        table.add_row("Successful", str(successful))
        table.add_row("Failed", str(failed))
        table.add_row("Total Execution Time", f"{total_time:.2f}s")
        table.add_row("Average Time per CV", f"{avg_time:.2f}s")
        
        self._console.print(table)

# Global instance for easy import
console = CVSConsole()
