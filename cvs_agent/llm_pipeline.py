from typing import Optional, Any
from langchain.agents import create_agent
try:
    from .schema import CVData
except ImportError:
    from schema import CVData

from langchain.chat_models import init_chat_model

try:
    from .prompts import SYSTEM_PROMPT
except ImportError:
    from prompts import SYSTEM_PROMPT

class CVExtractor:
    def __init__(self, model_name: str = "gpt-5-mini-2025-08-07", api_key: Optional[str] = None):
        # Initialize the model using init_chat_model for better generalization
        # passing api_key in kwargs if it's for openai, though standardization might vary.
        # usually api_key is picked up from env or passed as kwarg depending on provider.
        self.llm = init_chat_model(model_name, temperature=0, api_key=api_key)
        
        # Create the agent using the model instance
        # Note: tools list is optional but good to be explicit
        self.agent = create_agent(
            model=self.llm,
            tools=[],
            response_format=CVData,
            system_prompt=SYSTEM_PROMPT
        )

    def extract(self, text: str) -> CVData:
        """
        Extracts structured data from a single CV text.
        """
        try:
            result = self.agent.invoke({
                "messages": [{"role": "user", "content": f"Extract structured information from the following CV:\n\n{text}"}]
            })
            return result["structured_response"]
        except Exception as e:
            print(f"Error extracting data: {e}")
            return CVData()

    def batch_extract(self, texts: List[str]) -> List[CVData]:
        """
        Extracts structured data from multiple CV texts in a batch.
        """
        try:
            inputs = [{"messages": [{"role": "user", "content": f"Extract structured information from the following CV:\n\n{text}"}]} for text in texts]
            results = self.agent.batch(inputs)
            
            # Extract structured_response from each result
            return [res["structured_response"] for res in results]
        except Exception as e:
            print(f"Error in batch extraction: {e}")
            # Return empty CVData objects for failed batch to match input length, or empty list
            # Ideally we want to map failures, but for now returning empty list or partials might be tricky without index.
            # Let's return a list of empty CVData of same length to be safe if completely failed,
            # or usually batch raises exception.
            return [CVData() for _ in texts]
