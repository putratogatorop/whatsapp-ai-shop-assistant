"""Pluggable LLM provider layer.

LangChain chat models all implement the same BaseChatModel interface, so LangGraph's
create_react_agent works unmodified regardless of which provider is selected. Default
provider is Groq because it has a free API tier, which keeps this whole project
runnable at zero cost.

Switch providers via the LLM_PROVIDER env var: groq | openai | anthropic | gemini
"""
from functools import lru_cache

from langchain_core.language_models.chat_models import BaseChatModel

from app.config import get_settings

_DEFAULT_MODELS = {
    "groq": "llama-3.3-70b-versatile",
    "openai": "gpt-4o-mini",
    "anthropic": "claude-sonnet-5",
    "gemini": "gemini-2.0-flash",
}


@lru_cache
def get_chat_model() -> BaseChatModel:
    settings = get_settings()
    provider = settings.llm_provider.lower()
    model = settings.llm_model or _DEFAULT_MODELS.get(provider, "")

    if provider == "groq":
        from langchain_groq import ChatGroq

        return ChatGroq(model=model, api_key=settings.groq_api_key, temperature=0.2)

    if provider == "openai":
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(model=model, api_key=settings.openai_api_key, temperature=0.2)

    if provider == "anthropic":
        from langchain_anthropic import ChatAnthropic

        return ChatAnthropic(model=model, api_key=settings.anthropic_api_key, temperature=0.2)

    if provider == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI

        return ChatGoogleGenerativeAI(model=model, google_api_key=settings.google_api_key, temperature=0.2)

    raise ValueError(f"Unknown LLM_PROVIDER: {provider!r}. Use one of: {list(_DEFAULT_MODELS)}")
