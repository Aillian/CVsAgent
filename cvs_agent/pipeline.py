"""LLM-backed CV extraction pipeline.

Responsibilities:
- Build a LangChain agent against OpenAI or a local Ollama model
- Inject a dynamic JSON schema (with optional custom fields and job match)
- Run extraction per-CV with retry/backoff so a single transient failure does
  not abort the whole batch
- Expose a token/cost estimator for the CLI confirmation step
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from .config import (
    DEFAULT_RATE_LIMIT_BUCKET,
    PROVIDER_OLLAMA,
    PROVIDER_OPENAI,
    RETRY_ATTEMPTS,
    RETRY_BASE_SECONDS,
)
from .console import console
from .prompts import get_system_prompt
from .schema import build_dynamic_schema


# Approximate USD per 1K tokens for the default model. Users can override by
# editing this mapping — it is only used to print a pre-run cost estimate.
COST_PER_1K_TOKENS_USD: Dict[str, Dict[str, float]] = {
    "gpt-5-mini": {"input": 0.00025, "output": 0.002},
    "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
    "gpt-4o": {"input": 0.0025, "output": 0.010},
}


def _resolve_cost(model: str) -> Optional[Dict[str, float]]:
    for prefix, pricing in COST_PER_1K_TOKENS_USD.items():
        if model.startswith(prefix):
            return pricing
    return None


class ExtractionError(RuntimeError):
    """Raised when the LLM call fails after all retries."""


class CVExtractor:
    """LangChain-agent-based extractor with provider abstraction."""

    def __init__(
        self,
        model_name: str,
        provider: str = PROVIDER_OPENAI,
        api_key: Optional[str] = None,
        ollama_base_url: Optional[str] = None,
        custom_fields: Optional[List[str]] = None,
        job_description: Optional[str] = None,
        rate_limit_rps: float = 0.5,
    ) -> None:
        self.model_name = model_name
        self.provider = provider
        self.custom_fields = list(custom_fields or [])
        self.job_description = job_description

        self.llm = self._build_llm(
            provider=provider,
            model_name=model_name,
            api_key=api_key,
            ollama_base_url=ollama_base_url,
            rate_limit_rps=rate_limit_rps,
        )

        self.schema = build_dynamic_schema(
            custom_fields=self.custom_fields,
            with_target_match=bool(job_description),
        )

        self.agent = self._build_agent(self.llm, self.schema, job_description)

    # --- LLM + agent construction -----------------------------------------
    @staticmethod
    def _build_llm(
        provider: str,
        model_name: str,
        api_key: Optional[str],
        ollama_base_url: Optional[str],
        rate_limit_rps: float,
    ):
        if provider == PROVIDER_OLLAMA:
            try:
                from langchain_ollama import ChatOllama  # type: ignore
            except ImportError as exc:
                raise RuntimeError(
                    "Ollama provider requested but `langchain-ollama` is not installed. "
                    "Install with: pip install langchain-ollama"
                ) from exc
            kwargs: Dict[str, Any] = {"model": model_name, "temperature": 0}
            if ollama_base_url:
                kwargs["base_url"] = ollama_base_url
            return ChatOllama(**kwargs)

        if provider != PROVIDER_OPENAI:
            raise ValueError(f"Unsupported provider: {provider}")

        from langchain.chat_models import init_chat_model
        from langchain_core.rate_limiters import InMemoryRateLimiter

        rate_limiter = InMemoryRateLimiter(
            requests_per_second=rate_limit_rps,
            check_every_n_seconds=0.1,
            max_bucket_size=DEFAULT_RATE_LIMIT_BUCKET,
        )
        return init_chat_model(
            model_name,
            model_provider="openai",
            temperature=0,
            api_key=api_key,
            rate_limiter=rate_limiter,
        )

    @staticmethod
    def _build_agent(llm, schema: dict, job_description: Optional[str]):
        from langchain.agents import create_agent
        from langchain.agents.structured_output import ProviderStrategy

        return create_agent(
            model=llm,
            response_format=ProviderStrategy(schema),
            system_prompt=get_system_prompt(job_description=job_description),
        )

    # --- Extraction -------------------------------------------------------
    def _invoke_once(self, text: str) -> Dict[str, Any]:
        result = self.agent.invoke(
            {
                "messages": [
                    {
                        "role": "user",
                        "content": f"Extract structured information from the following CV:\n\n{text}",
                    }
                ]
            }
        )
        data = result.get("structured_response")
        if data is None:
            raise ExtractionError("Agent returned no structured_response")
        # LangChain may return a Pydantic model — normalise to dict.
        if hasattr(data, "model_dump"):
            data = data.model_dump()
        return data

    def extract(self, text: str) -> Dict[str, Any]:
        """Extract structured data from a single CV with retry/backoff."""

        @retry(
            stop=stop_after_attempt(RETRY_ATTEMPTS),
            wait=wait_exponential(multiplier=RETRY_BASE_SECONDS, min=1, max=30),
            retry=retry_if_exception_type(Exception),
            reraise=True,
        )
        def _run() -> Dict[str, Any]:
            return self._invoke_once(text)

        try:
            return _run()
        except Exception as exc:  # noqa: BLE001
            console.error("Pipeline", f"Extraction failed after retries: {exc}")
            return {}

    # --- Cost estimation --------------------------------------------------
    def estimate_cost(self, texts: List[str]) -> Optional[Dict[str, float]]:
        """Return a rough USD cost estimate for ``texts``.

        Returns None when we do not have pricing for the configured model
        (e.g. local Ollama runs).
        """
        if self.provider != PROVIDER_OPENAI:
            return None
        pricing = _resolve_cost(self.model_name)
        if pricing is None:
            return None

        try:
            import tiktoken

            try:
                enc = tiktoken.encoding_for_model(self.model_name)
            except KeyError:
                enc = tiktoken.get_encoding("cl100k_base")
            prompt_overhead = len(enc.encode(get_system_prompt(self.job_description)))
            input_tokens = sum(len(enc.encode(t)) for t in texts) + prompt_overhead * len(texts)
        except Exception:  # noqa: BLE001 - fall back to a crude estimate
            input_tokens = sum(len(t) // 4 for t in texts) + 800 * len(texts)

        # Assume outputs are ~1k tokens each — CV JSON is usually <800 tokens.
        output_tokens = 1000 * len(texts)

        usd = (
            (input_tokens / 1000) * pricing["input"]
            + (output_tokens / 1000) * pricing["output"]
        )
        return {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "usd": usd,
        }
