"""AI provider abstraction — Ollama (default/free) + Claude API (advanced).

Usage:
    provider = get_ai_provider()
    result = await provider.generate_doc_update(current_section, code_diff, commit_messages)
"""

from __future__ import annotations

import os
from abc import ABC, abstractmethod

import httpx


class AIProvider(ABC):
    """Abstract base for AI doc generation providers."""

    @abstractmethod
    async def generate_doc_update(
        self,
        current_section: str,
        code_diff: str,
        commit_messages: list[str],
        instruction: str = "Update this documentation section to reflect the code changes. Keep style consistent.",
    ) -> str:
        """Generate an updated doc section based on code changes."""
        ...

    @abstractmethod
    async def classify_changes(self, commit_messages: list[str]) -> str:
        """Classify commit messages into: major | minor | patch."""
        ...


class OllamaProvider(AIProvider):
    """Free, local AI via Ollama. Runs on the ollama Docker container."""

    def __init__(self, base_url: str = "http://ollama:11434", model: str = "llama3.1:8b") -> None:
        self.base_url = base_url
        self.model = model

    async def generate_doc_update(
        self, current_section: str, code_diff: str, commit_messages: list[str],
        instruction: str = "Update this documentation section to reflect the code changes. Keep style consistent.",
    ) -> str:
        prompt = f"""{instruction}

## Current Documentation
{current_section}

## Code Changes (diff)
{code_diff[:3000]}

## Commit Messages
{chr(10).join(f'- {m}' for m in commit_messages)}

## Updated Documentation
"""
        async with httpx.AsyncClient(timeout=120.0) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json={"model": self.model, "prompt": prompt, "stream": False},
                )
                response.raise_for_status()
                return response.json().get("response", "")
            except Exception as e:
                return f"[AI generation failed: {e}]"

    async def classify_changes(self, commit_messages: list[str]) -> str:
        prompt = f"""Classify these git commits as one of: major, minor, patch.
- major: breaking changes, API restructure
- minor: new features, new sections
- patch: fixes, refactoring, documentation updates

Commits:
{chr(10).join(f'- {m}' for m in commit_messages)}

Answer with only one word: major, minor, or patch."""

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json={"model": self.model, "prompt": prompt, "stream": False},
                )
                response.raise_for_status()
                result = response.json().get("response", "").strip().lower()
                if result in ("major", "minor", "patch"):
                    return result
                return "patch"
            except Exception:
                return "patch"


class ClaudeProvider(AIProvider):
    """Anthropic Claude API provider. Requires ANTHROPIC_API_KEY env var.

    Install: pip install anthropic
    Set: ANTHROPIC_API_KEY=sk-ant-...
    """

    def __init__(self, model: str = "claude-sonnet-4-20250514") -> None:
        self.model = model
        self.api_key = os.environ.get("ANTHROPIC_API_KEY", "")

    async def generate_doc_update(
        self, current_section: str, code_diff: str, commit_messages: list[str],
        instruction: str = "Update this documentation section to reflect the code changes. Keep style consistent.",
    ) -> str:
        if not self.api_key:
            return "[Claude API key not configured. Set ANTHROPIC_API_KEY env var.]"

        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                response = await client.post(
                    "https://api.anthropic.com/v1/messages",
                    headers={
                        "x-api-key": self.api_key,
                        "anthropic-version": "2023-06-01",
                        "content-type": "application/json",
                    },
                    json={
                        "model": self.model,
                        "max_tokens": 4096,
                        "messages": [{
                            "role": "user",
                            "content": f"""{instruction}

## Current Documentation
{current_section}

## Code Changes (diff)
{code_diff[:8000]}

## Commit Messages
{chr(10).join(f'- {m}' for m in commit_messages)}

Return ONLY the updated documentation section, nothing else.""",
                        }],
                    },
                )
                response.raise_for_status()
                content = response.json().get("content", [])
                return content[0]["text"] if content else ""
            except Exception as e:
                return f"[Claude API error: {e}]"

    async def classify_changes(self, commit_messages: list[str]) -> str:
        if not self.api_key:
            return "patch"

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(
                    "https://api.anthropic.com/v1/messages",
                    headers={
                        "x-api-key": self.api_key,
                        "anthropic-version": "2023-06-01",
                        "content-type": "application/json",
                    },
                    json={
                        "model": self.model,
                        "max_tokens": 10,
                        "messages": [{
                            "role": "user",
                            "content": f"Classify these commits as major/minor/patch. Reply with one word only.\n{chr(10).join(commit_messages)}",
                        }],
                    },
                )
                response.raise_for_status()
                result = response.json()["content"][0]["text"].strip().lower()
                return result if result in ("major", "minor", "patch") else "patch"
            except Exception:
                return "patch"


def get_ai_provider() -> AIProvider:
    """Factory: returns Claude if API key is set, otherwise Ollama."""
    if os.environ.get("ANTHROPIC_API_KEY"):
        return ClaudeProvider()
    return OllamaProvider(
        base_url=os.environ.get("OLLAMA_URL", "http://ollama:11434"),
        model=os.environ.get("OLLAMA_MODEL", "smollm2:135m"),
    )
