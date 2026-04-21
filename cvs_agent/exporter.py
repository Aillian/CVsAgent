import os
import pandas as pd
from typing import List, Dict, Any
from .console import console

def save_results(results: List[Dict[str, Any]], output_dir: str):
    """
    Saves the extracted results to an Excel file.
    
    Args:
        results: List of dictionaries containing the flattened CV data.
        output_dir: Directory to save the output file.
    """
    if not results:
        console.log("Exporter", "No results to save.", style="yellow")
        return

    try:
        # Create DataFrame
        df = pd.DataFrame(results)
        
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)
        
        # Define output path
        output_path = os.path.join(output_dir, "CVs_Info_Extracted.xlsx")
        
        # Save to Excel
        df.to_excel(output_path, index=False)
        
        console.log("Exporter", f"Results successfully saved to [bold]{output_path}[/bold]", style="green")
        
    except Exception as e:
        console.log("Exporter", f"Failed to save results: {e}", style="bold red")
