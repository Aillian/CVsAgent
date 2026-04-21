import argparse
import os
import time
from dotenv import load_dotenv
from typing import List

# Internal imports
from cvs_agent.loader import load_cvs
from cvs_agent.agent_pipeline import CVExtractor
from cvs_agent.console import console
from cvs_agent.exporter import save_results
from cvs_agent.utils import join_list

def process_cvs(cv_dir: str, output_dir: str, model: str, api_key: str, 
                add_fields: List[str] = None, job_description: str = None):
    """
    Main orchestration logic for CV extraction and processing.
    """
    
    # Start: logging setup
    console.print_panel(f"[bold green]Starting CVsAgent[/bold green]\nModel: [cyan]{model}[/cyan]")
    
    if add_fields:
        console.log("Agent_Pipeline", f"Custom Fields Configured: {add_fields}")
    if job_description:
        console.log("Agent_Pipeline", "Target Job Description Loaded")

    # 1. Initialize Extraction Pipeline
    extractor = CVExtractor(
        model_name=model, 
        api_key=api_key,
        custom_fields=add_fields,
        job_description=job_description
    )
    
    # 2. Load Documents
    start_time = time.time()
    console.log("CVs_Loader", "Loading CVs from directory...")
    
    with console.status("Loading...", spinner="dots"):
        documents = load_cvs(cv_dir)
    
    if not documents:
        console.log("CVs_Loader", "No CVs found to process.", style="bold red")
        return

    console.log("CVs_Loader", f"Found {len(documents)} CVs. Preparing for extraction...")
    
    # Prepare text list
    cv_texts = []
    filenames = []
    
    for doc in documents:
        filename = doc.metadata.get("source", "Unknown")
        cv_texts.append(doc.page_content)
        filenames.append(filename)

    # 3. Batch Extraction
    console.log("CVs_extractor", f"Starting extraction for {len(cv_texts)} CVs...", style="bold yellow")
    batch_start_time = time.time()
    
    with console.status("Processing Batch...", spinner="dots"):
        extracted_data_list = extractor.batch_extract(cv_texts)
    
    batch_duration = time.time() - batch_start_time
    console.log("CVs_extractor", f"Batch extraction completed in {batch_duration:.2f}s", style="green")

    # 4. Process Results (Mapping)
    results = []
    successful = 0
    failed = 0
    
    for i, data in enumerate(extracted_data_list):
        filename = filenames[i]
        
        try:
             # -- Flatten Nested Structures --
            education_list = data.get("education", []) or []
            education_str = "; ".join([f"{ed.get('degree', '')} in {ed.get('major', '')} at {ed.get('university', '')} ({ed.get('graduation_date', '')})" for ed in education_list])
            
            work_list = data.get("work_experience", []) or []
            companies_str = join_list([w.get("company", "") for w in work_list])
            roles_str = join_list([w.get("job_title", "") for w in work_list])
            responsibilities_str = "; ".join([f"{w.get('company', '')}: " + join_list(w.get("responsibilities", [])) for w in work_list])
            
            # -- Construct Flat Dictionary --
            flat_row = {
                "Filename": filename,
                
                # --- Identity & Contact ---
                "Full Name": data.get("full_name"),
                "Email Address": data.get("email_address"),
                "Phone Number": data.get("phone_number"),
                "LinkedIn URL": data.get("linkedin_url"),
                "Portfolio URLs": join_list(data.get("portfolio_urls", [])),
                "City": data.get("location_city"),
                "Country": data.get("location_country"),

                # --- Professional Summary ---
                "Professional Summary": data.get("professional_summary"),

                # --- Education ---
                "Education History": education_str,
                
                # --- Work Experience ---
                "Years of Experience": data.get("years_of_experience"),
                "Management Level": data.get("management_level"),
                "Companies": companies_str,
                "Job Titles": roles_str,
                "Key Responsibilities": responsibilities_str,
                
                # --- Skills ---
                "Technical Skills": join_list(data.get("top_5_technical_skills", [])),
                "Soft Skills": join_list(data.get("top_5_soft_skills", [])),
                "Languages": join_list([f"{l.get('language')} ({l.get('proficiency')})" for l in (data.get("languages", []) or [])]),

                # --- Projects ---
                "Key Projects": join_list(data.get("top_5_key_projects", [])),
                
                # --- Certifications & Awards ---
                "Certifications": join_list(data.get("top_5_certifications", [])),
                "Awards": join_list(data.get("top_5_awards", [])),
                
                # --- Analysis ---
                "Nationality": data.get("nationality"),
                "Employment Status": data.get("current_employment_status"),
                "Suitable Positions": join_list(data.get("top_5_suitable_positions", [])),
            }

            # --- Dynamic: Custom Fields ---
            if add_fields:
                for field in add_fields:
                    flat_row[field] = data.get(field, "")

            # --- Dynamic: Target Job Match ---
            if job_description:
                 match_data = data.get("target_role_match", {})
                 flat_row["Target Role Match"] = match_data.get("suitable")
                 flat_row["Match Reason"] = match_data.get("reason")

            # --- Output Reordering: Ensure Rating is Last ---
            flat_row["Rating"] = data.get("candidate_rating")

            results.append(flat_row)
            successful += 1
        except Exception as e:
            console.log("Data_Mapper", f"Error mapping result for {filename}: {e}", style="bold red")
            failed += 1

    # 5. Save Results (via Exporter)
    save_results(results, output_dir)
    
    # 6. Display Statistics
    total_time = time.time() - start_time
    console.print_statistics(len(documents), successful, failed, total_time)

def main():
    parser = argparse.ArgumentParser(description="CVsAgent: Extract structured data from CVs.")
    parser.add_argument("--cv_dir", default="CVs", help="Directory containing PDF CVs")
    parser.add_argument("--output_dir", default="Output", help="Directory to save output")
    parser.add_argument("--model", default="gpt-5-mini-2025-08-07", help="LLM model to use")
    parser.add_argument("--api_key", help="OpenAI API Key")
    
    # Dynamic arguments
    parser.add_argument("--add_fields", nargs='+', help="List of custom fields to extract (e.g., 'DriverLicense' 'VisaStatus')")
    parser.add_argument("--job_description_file", help="Path to a text file containing the target job description")
    parser.add_argument("--job_description", help="Text string of the target job description (alternative to file)")
    
    args = parser.parse_args()
    
    load_dotenv()
    api_key = args.api_key or os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        console.print("[bold red]Error: OpenAI API Key is required. Provide it via --api_key or OPENAI_API_KEY env var.[/bold red]")
        return

    # Load Job Description if provided
    job_desc = args.job_description
    if args.job_description_file:
        try:
            with open(args.job_description_file, 'r', encoding='utf-8') as f:
                job_desc = f.read()
            console.log("Config", f"Loaded job description from {args.job_description_file}")
        except Exception as e:
            console.log("Config", f"Error loading job description file: {e}", style="bold red")
            return

    process_cvs(args.cv_dir, args.output_dir, args.model, api_key, 
                add_fields=args.add_fields, job_description=job_desc)

if __name__ == "__main__":
    main()