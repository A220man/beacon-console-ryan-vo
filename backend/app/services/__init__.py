# Services package - business logic layer
from app.services.llm import (
    LLMProvider,
    LLMResponse,
    OpenAICompatibleProvider,
    AnthropicProvider,
    GeminiProvider,
    get_llm_provider,
    generate_explanation,
)