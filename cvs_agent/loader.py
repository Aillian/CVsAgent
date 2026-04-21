import os
import concurrent.futures
from typing import List, Optional
from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document

def load_single_pdf(file_path: str) -> Optional[Document]:
    """
    Helper function to load a single PDF file.
    Returns a Document object or None if valid loading fails.
    """
    try:
        loader = PyPDFLoader(file_path)
        docs = loader.load()
        if not docs:
            return None
            
        # Combine all pages into one document
        full_text = "\n".join([doc.page_content for doc in docs])
        filename = os.path.basename(file_path)
        return Document(page_content=full_text, metadata={"source": filename})
    except Exception as e:
        print(f"Error loading {os.path.basename(file_path)}: {e}")
        return None

def load_cvs(directory: str) -> List[Document]:
    """
    Loads all PDF CVs from the specified directory in parallel using ThreadPoolExecutor.
    """
    documents = []
    
    if not os.path.exists(directory):
        print(f"Directory not found: {directory}")
        return documents

    # Gather all PDF paths
    pdf_files = [
        os.path.join(directory, f) 
        for f in os.listdir(directory) 
        if f.lower().endswith(".pdf")
    ]

    if not pdf_files:
        return documents

    # Use ThreadPoolExecutor for I/O bound parallel loading
    # Adjust max_workers as needed (default is usually number of processors * 5)
    with concurrent.futures.ThreadPoolExecutor() as executor:
        # Map the loading function to the files
        results = executor.map(load_single_pdf, pdf_files)
        
        # Collect non-None results
        for doc in results:
            if doc:
                documents.append(doc)
                print(f"Loaded: {doc.metadata['source']}")

    return documents
