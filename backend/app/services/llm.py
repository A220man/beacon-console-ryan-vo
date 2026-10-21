"""LLM provider adapters for opt-in explanations."""
import json
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Optional
import httpx


@dataclass
class LLMResponse:
    content: str
    provider: str
    model: str
    usage: Optional[dict] = None


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    def __init__(self, api_key: str, base_url: str, model: str, timeout: int = 30):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout

    @abstractmethod
    async def generate(self, prompt: str, system_prompt: Optional[str] = None) -> LLMResponse:
        """Generate a response from the LLM."""
        pass

    def _get_headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }


class OpenAICompatibleProvider(LLMProvider):
    """OpenAI-compatible provider (OpenAI, LiteLLM, OpenRouter, Ollama)."""

    async def generate(self, prompt: str, system_prompt: Optional[str] = None) -> LLMResponse:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.2,
            "max_tokens": 2000,
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers=self._get_headers(),
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

        choice = data["choices"][0]
        return LLMResponse(
            content=choice["message"]["content"],
            provider="openai-compatible",
            model=self.model,
            usage=data.get("usage"),
        )


class AnthropicProvider(LLMProvider):
    """Anthropic Messages API provider."""

    def _get_headers(self) -> dict[str, str]:
        return {
            "x-api-key": self.api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01",
        }

    async def generate(self, prompt: str, system_prompt: Optional[str] = None) -> LLMResponse:
        payload = {
            "model": self.model,
            "max_tokens": 2000,
            "temperature": 0.2,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system_prompt:
            payload["system"] = system_prompt

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/v1/messages",
                headers=self._get_headers(),
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

        content = "".join(block["text"] for block in data["content"] if block["type"] == "text")
        return LLMResponse(
            content=content,
            provider="anthropic",
            model=self.model,
            usage=data.get("usage"),
        )


class GeminiProvider(LLMProvider):
    """Google Gemini generateContent API provider."""

    async def generate(self, prompt: str, system_prompt: Optional[str] = None) -> LLMResponse:
        contents = []
        if system_prompt:
            contents.append({"role": "user", "parts": [{"text": system_prompt}]})
            contents.append({"role": "model", "parts": [{"text": "Understood."}]})
        contents.append({"role": "user", "parts": [{"text": prompt}]})

        payload = {
            "contents": contents,
            "generationConfig": {
                "temperature": 0.2,
                "maxOutputTokens": 2000,
            },
        }

        url = f"{self.base_url}/models/{self.model}:generateContent?key={self.api_key}"

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()

        content = data["candidates"][0]["content"]["parts"][0]["text"]
        return LLMResponse(
            content=content,
            provider="gemini",
            model=self.model,
            usage=data.get("usageMetadata"),
        )


def get_llm_provider(
    provider: str,
    api_key: str,
    base_url: str,
    model: str,
    timeout: int = 30,
) -> LLMProvider:
    """Factory function to get the appropriate LLM provider."""
    provider = provider.lower()
    if provider in ("openai-compatible", "openai", "litellm", "openrouter", "ollama"):
        return OpenAICompatibleProvider(api_key, base_url, model, timeout)
    elif provider == "anthropic":
        return AnthropicProvider(api_key, base_url, model, timeout)
    elif provider == "gemini":
        return GeminiProvider(api_key, base_url, model, timeout)
    else:
        raise ValueError(f"Unknown LLM provider: {provider}")


async def generate_explanation(
    skill_name: str,
    skill_display_name: str,
    input_params: dict,
    deterministic_result: dict,
    settings,
) -> dict:
    """Generate an LLM explanation for a skill execution result.
    
    Returns a dict with explanation content and metadata, or error info.
    """
    if not settings.llm_api_key:
        return {
            "status": "skipped",
            "reason": "LLM_API_KEY not configured",
            "advisory": True,
        }

    provider_name = settings.llm_provider
    model = settings.llm_model
    base_url = settings.llm_base_url
    timeout = settings.llm_timeout_seconds

    try:
        provider = get_llm_provider(provider_name, settings.llm_api_key, base_url, model, timeout)
    except ValueError as e:
        return {
            "status": "error",
            "error": str(e),
            "advisory": True,
        }

    # Build prompt based on skill type
    if skill_name == "locus-compare":
        prompt = build_locus_compare_prompt(skill_display_name, input_params, deterministic_result)
    elif skill_name == "field-onboarding":
        prompt = build_field_onboarding_prompt(skill_display_name, input_params, deterministic_result)
    else:
        prompt = build_generic_prompt(skill_display_name, input_params, deterministic_result)

    system_prompt = (
        "You are a scientific assistant explaining the results of a deterministic workflow execution. "
        "The workflow ran without LLM involvement. Your explanation is ADVISORY ONLY and labeled as such. "
        "Do not claim the LLM performed the analysis. Ground your explanation in the provided deterministic results. "
        "Be concise, accurate, and highlight limitations."
    )

    try:
        response = await provider.generate(prompt, system_prompt)
        return {
            "status": "completed",
            "explanation": response.content,
            "provider": response.provider,
            "model": response.model,
            "usage": response.usage,
            "advisory": True,
        }
    except httpx.HTTPStatusError as e:
        return {
            "status": "error",
            "error": f"Provider error: {e.response.status_code}",
            "advisory": True,
        }
    except Exception as e:
        return {
            "status": "error",
            "error": f"Generation failed: {type(e).__name__}",
            "advisory": True,
        }


def build_locus_compare_prompt(display_name: str, input_params: dict, result: dict) -> str:
    """Build prompt for locus compare explanation."""
    steps = result.get("steps", {})
    output = result.get("output", {})
    return (
        f"Skill: {display_name}\n"
        f"Input: chromosome={input_params.get('chromosome')}, "
        f"region={input_params.get('start')}-{input_params.get('end')}, "
        f"sentinel_snp={input_params.get('sentinel_snp')}, "
        f"population={input_params.get('population')}\n"
        f"Deterministic result:\n"
        f"- GWAS fetch: {steps.get('gwas_fetch', {}).get('variants_found', 'N/A')} variants\n"
        f"- eQTL fetch: {steps.get('eqtl_fetch', {}).get('variants_found', 'N/A')} variants\n"
        f"- LD compute: {steps.get('ld_compute', {}).get('variants_with_ld', 'N/A')} variants with LD\n"
        f"- Render: {steps.get('render', {}).get('panels', 'N/A')} panels generated\n"
        f"- Palindromic variants excluded: {output.get('palindromic_excluded', 'N/A')}\n"
        f"Provide a brief scientific explanation of what this locus compare plot shows, "
        f"what the four panels represent, and any caveats about the deterministic results."
    )


def build_field_onboarding_prompt(display_name: str, input_params: dict, result: dict) -> str:
    """Build prompt for field onboarding explanation."""
    steps = result.get("steps", {})
    prereqs = steps.get("prerequisites", {})
    ladder = steps.get("ladder", [])
    return (
        f"Skill: {display_name}\n"
        f"Topic: {input_params.get('topic')}\n"
        f"Mode: {input_params.get('mode', 'onboard')}\n"
        f"Deterministic result:\n"
        f"- Maturity: {steps.get('maturity', 'N/A')}\n"
        f"- Prerequisites assessed: {len(prereqs.get('frameworks', []))} frameworks\n"
        f"- Ladder progress: {sum(1 for r in ladder if r.get('complete'))}/{len(ladder)} rungs complete\n"
        f"- Diagnostic questions: {len(steps.get('diagnostic_questions', []))}\n"
        f"Provide a brief explanation of the onboarding structure, what the user should focus on next, "
        f"and any caveats about the deterministic assessment."
    )


def build_generic_prompt(display_name: str, input_params: dict, result: dict) -> str:
    """Build generic prompt for unknown skills."""
    return (
        f"Skill: {display_name}\n"
        f"Input: {json.dumps(input_params)}\n"
        f"Deterministic result: {json.dumps(result)}\n"
        f"Provide a brief explanation of what this skill does and what the results mean."
    )