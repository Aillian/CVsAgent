from typing import Optional, Any, List, Dict
import copy
from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from langchain.agents.structured_output import ProviderStrategy
from langchain_core.rate_limiters import InMemoryRateLimiter
from .console import console

try:
    from .schema import CV_SCHEMA
except ImportError:
    from schema import CV_SCHEMA

try:
    from .prompts import get_system_prompt
except ImportError:
    from prompts import get_system_prompt

class CVExtractor:
    """
    Handles PDF CV data extraction using LangChain agents with structured output.
    Uses rate limiting and dynamic schema modification.
    """
    def __init__(self, 
                 model_name: str = "gpt-5-mini-2025-08-07", 
                 api_key: Optional[str] = None,
                 custom_fields: Optional[List[str]] = None,
                 job_description: Optional[str] = None):
        
        # 0. Initialize Rate Limiter
        # Limits to ~1 request per 2 seconds (0.5 rps) to be safe, checking every 100ms
        self.rate_limiter = InMemoryRateLimiter(
            requests_per_second=0.5,
            check_every_n_seconds=0.1,
            max_bucket_size=10
        )

        # 1. Initialize LLM with Rate Limiter
        self.llm = init_chat_model(
            model_name, 
            temperature=0, 
            api_key=api_key,
            rate_limiter=self.rate_limiter
        )
        
        # 2. Dynamic Schema Construction
        self.schema = copy.deepcopy(CV_SCHEMA)
        self.job_description = job_description
        self.custom_fields = custom_fields or []

        # Add Custom Fields
        if self.custom_fields:
            for field in self.custom_fields:
                if field not in self.schema["properties"]:
                    self.schema["properties"][field] = {
                        "type": "string",
                        "description": f"Extract the value for {field} as a concise string."
                    }
                    self.schema["required"].append(field)

        # Add Job Matching Fields
        if self.job_description:
            self.schema["properties"]["target_role_match"] = {
                "type": "object",
                "properties": {
                    "suitable": {
                        "type": "boolean",
                        "description": "True if the candidate is suitable for the target position, False otherwise."
                    },
                    "reason": {
                        "type": "string",
                        "description": "Brief reason for the suitability assessment. MAX 100 WORDS."
                    }
                },
                "required": ["suitable", "reason"],
                "description": "Assessment of candidate suitability for the specific target role."
            }
            self.schema["required"].append("target_role_match")

        # 3. Generate System Prompt
        dynamic_prompt = get_system_prompt(
            job_description=self.job_description
        )

        # 4. Create Agent
        self.agent = create_agent(
            model=self.llm,
            response_format=ProviderStrategy(self.schema),
            system_prompt=dynamic_prompt
        )

    def extract(self, text: str) -> Dict[str, Any]:
        """
        Extracts structured data from a single CV text.
        """
        console.log("Agent_Pipeline", "Invoking agent for single extraction...", style="dim")
        try:
            result = self.agent.invoke({
                "messages": [{"role": "user", "content": f"Extract structured information from the following CV:\n\n{text}"}]
            })
            return result["structured_response"]
        except Exception as e:
            console.log("Agent_Pipeline", f"Error extracting data: {e}", style="bold red")
            return {}

    def batch_extract(self, texts: List[str]) -> List[Dict[str, Any]]:
        """
        Extracts structured data from multiple CV texts in a batch.
        """
        console.log("Agent_Pipeline", f"Preparing batch request for {len(texts)} documents...", style="cyan")
        try:
            inputs = [{"messages": [{"role": "user", "content": f"Extract structured information from the following CV:\n\n{text}"}]} for text in texts]
            
            # Agent batch call efficiently handles concurrent requests respecting the rate limiter
            results = self.agent.batch(inputs)
            
            # Extract structured_response from each result
            return [res["structured_response"] for res in results]
        except Exception as e:
            console.log("Agent_Pipeline", f"Error in batch extraction: {e}", style="bold red")
            return [{} for _ in texts]
