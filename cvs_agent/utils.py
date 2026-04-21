from typing import List, Optional

def join_list(lst: Optional[List[str]], separator: str = ", ") -> str:
    """
    Joins a list of strings with a separator, handling None values safely.
    
    Args:
        lst (List[str] | None): The list to join.
        separator (str): The separator string to use.
        
    Returns:
        str: The joined string or an empty string if input is None/empty.
    """
    return separator.join(lst or [])
