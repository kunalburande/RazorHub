"""
Universal Multi-LLM Base Agent for RazorHub Multi-Agent Intelligence System.
Supports OpenRouter, Groq, Mistral, Qwen, xAI/Grok, Google Gemini, and OpenAI.
Includes resilient fallback to rule-based agentic business logic.
"""
import os
import json
import logging
import requests
from django.conf import settings

logger = logging.getLogger(__name__)


# Module-level set of providers that have returned permanent auth/credit errors (e.g. 401, 402)
_disabled_providers: set[str] = set()


class BaseAgent:
    """
    Abstract base for all specialized agents.
    Subclasses implement `get_system_prompt()` and `execute()`.
    """
    name: str = "base"
    default_model: str = "auto"

    def get_system_prompt(self, context: dict) -> str:
        """Return the system prompt for this agent. Override in subclasses."""
        raise NotImplementedError

    def _call_llm(self, messages: list[dict], context: dict,
                  temperature: float = 0.7, max_tokens: int = 2048) -> str:
        """
        Multi-provider LLM caller with fast 4s timeout and auto-disabling on 401/402 errors.
        Tries configured API keys in priority order:
        1. OpenRouter
        2. Groq
        3. Mistral AI
        4. xAI / Grok
        5. Qwen / DashScope
        6. Google Gemini
        7. OpenAI
        """
        system_prompt = self.get_system_prompt(context)
        formatted_messages = [{"role": "system", "content": system_prompt}]
        for m in messages:
            role = "user" if m.get("role") in ("user", "human") else "assistant"
            content = m.get("content", "") or m.get("text", "")
            if content:
                formatted_messages.append({"role": role, "content": content})

        # 1. OpenRouter
        if "openrouter" not in _disabled_providers:
            openrouter_key = os.environ.get("OPENROUTER_API_KEY") or getattr(settings, "OPENROUTER_API_KEY", None)
            if openrouter_key:
                try:
                    model = os.environ.get("OPENROUTER_MODEL", "openrouter/auto")
                    res = requests.post(
                        "https://openrouter.ai/api/v1/chat/completions",
                        headers={
                            "Authorization": f"Bearer {openrouter_key}",
                            "Content-Type": "application/json",
                            "HTTP-Referer": "https://razorhub.local",
                            "X-Title": "RazorHub",
                        },
                        json={
                            "model": model,
                            "messages": formatted_messages,
                            "temperature": temperature,
                            "max_tokens": max_tokens,
                        },
                        timeout=4
                    )
                    if res.status_code == 200:
                        data = res.json()
                        return data["choices"][0]["message"]["content"]
                    elif res.status_code in (401, 402, 403):
                        _disabled_providers.add("openrouter")
                        logger.info(f"Disabling OpenRouter (status {res.status_code})")
                except Exception as e:
                    logger.debug(f"[{self.name}] OpenRouter call error: {e}")

        # 2. Groq
        if "groq" not in _disabled_providers:
            groq_key = os.environ.get("GROQ_API_KEY") or getattr(settings, "GROQ_API_KEY", None)
            if groq_key:
                try:
                    model = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")
                    res = requests.post(
                        "https://api.groq.com/openai/v1/chat/completions",
                        headers={"Authorization": f"Bearer {groq_key}", "Content-Type": "application/json"},
                        json={
                            "model": model,
                            "messages": formatted_messages,
                            "temperature": temperature,
                            "max_tokens": max_tokens,
                        },
                        timeout=4
                    )
                    if res.status_code == 200:
                        data = res.json()
                        return data["choices"][0]["message"]["content"]
                    elif res.status_code in (401, 402, 403):
                        _disabled_providers.add("groq")
                except Exception as e:
                    logger.debug(f"[{self.name}] Groq call error: {e}")

        # 3. Mistral AI
        if "mistral" not in _disabled_providers:
            mistral_key = os.environ.get("MISTRAL_API_KEY") or getattr(settings, "MISTRAL_API_KEY", None)
            if mistral_key:
                try:
                    model = os.environ.get("MISTRAL_MODEL", "mistral-small-latest")
                    res = requests.post(
                        "https://api.mistral.ai/v1/chat/completions",
                        headers={"Authorization": f"Bearer {mistral_key}", "Content-Type": "application/json"},
                        json={
                            "model": model,
                            "messages": formatted_messages,
                            "temperature": temperature,
                            "max_tokens": max_tokens,
                        },
                        timeout=4
                    )
                    if res.status_code == 200:
                        data = res.json()
                        return data["choices"][0]["message"]["content"]
                    elif res.status_code in (401, 402, 403):
                        _disabled_providers.add("mistral")
                except Exception as e:
                    logger.debug(f"[{self.name}] Mistral call error: {e}")

        # 4. xAI / Grok
        if "xai" not in _disabled_providers:
            grok_key = os.environ.get("XAI_API_KEY") or os.environ.get("GROK_API_KEY") or getattr(settings, "GROK_API_KEY", None)
            if grok_key:
                try:
                    model = os.environ.get("GROK_MODEL", "grok-2-latest")
                    res = requests.post(
                        "https://api.x.ai/v1/chat/completions",
                        headers={"Authorization": f"Bearer {grok_key}", "Content-Type": "application/json"},
                        json={
                            "model": model,
                            "messages": formatted_messages,
                            "temperature": temperature,
                            "max_tokens": max_tokens,
                        },
                        timeout=4
                    )
                    if res.status_code == 200:
                        data = res.json()
                        return data["choices"][0]["message"]["content"]
                    elif res.status_code in (401, 402, 403):
                        _disabled_providers.add("xai")
                except Exception as e:
                    logger.debug(f"[{self.name}] Grok call error: {e}")

        # 5. Qwen / DashScope
        if "qwen" not in _disabled_providers:
            qwen_key = os.environ.get("QWEN_API_KEY") or os.environ.get("DASHSCOPE_API_KEY") or getattr(settings, "QWEN_API_KEY", None)
            if qwen_key:
                try:
                    model = os.environ.get("QWEN_MODEL", "qwen-plus")
                    res = requests.post(
                        "https://dashscope-intl.aliyuncs.com/compatible-mode/v1/chat/completions",
                        headers={"Authorization": f"Bearer {qwen_key}", "Content-Type": "application/json"},
                        json={
                            "model": model,
                            "messages": formatted_messages,
                            "temperature": temperature,
                            "max_tokens": max_tokens,
                        },
                        timeout=4
                    )
                    if res.status_code == 200:
                        data = res.json()
                        return data["choices"][0]["message"]["content"]
                    elif res.status_code in (401, 402, 403):
                        _disabled_providers.add("qwen")
                except Exception as e:
                    logger.debug(f"[{self.name}] Qwen call error: {e}")

        # 6. Google Gemini REST API
        if "gemini" not in _disabled_providers:
            gemini_key = os.environ.get("GEMINI_API_KEY") or getattr(settings, "GEMINI_API_KEY", None)
            if gemini_key and not gemini_key.startswith("AQ."):
                for model_name in ["gemini-2.0-flash", "gemini-1.5-flash-latest"]:
                    try:
                        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={gemini_key}"
                        contents = []
                        for m in formatted_messages:
                            role = "user" if m["role"] in ("user", "system") else "model"
                            contents.append({"role": role, "parts": [{"text": m["content"]}]})

                        res = requests.post(
                            url,
                            headers={"Content-Type": "application/json"},
                            json={
                                "contents": contents,
                                "generationConfig": {"temperature": temperature, "maxOutputTokens": max_tokens}
                            },
                            timeout=4
                        )
                        if res.status_code == 200:
                            data = res.json()
                            candidates = data.get("candidates", [])
                            if candidates:
                                parts = candidates[0].get("content", {}).get("parts", [])
                                if parts:
                                    return parts[0].get("text", "")
                    except Exception as e:
                        logger.debug(f"[{self.name}] Gemini call error: {e}")

        # 7. OpenAI
        if "openai" not in _disabled_providers:
            openai_key = os.environ.get("OPENAI_API_KEY") or getattr(settings, "OPENAI_API_KEY", None)
            if openai_key:
                try:
                    model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
                    res = requests.post(
                        "https://api.openai.com/v1/chat/completions",
                        headers={"Authorization": f"Bearer {openai_key}", "Content-Type": "application/json"},
                        json={
                            "model": model,
                            "messages": formatted_messages,
                            "temperature": temperature,
                            "max_tokens": max_tokens,
                        },
                        timeout=4
                    )
                    if res.status_code == 200:
                        data = res.json()
                        return data["choices"][0]["message"]["content"]
                    elif res.status_code in (401, 402, 403):
                        _disabled_providers.add("openai")
                except Exception as e:
                    logger.debug(f"[{self.name}] OpenAI call error: {e}")

        raise RuntimeError("No working LLM provider available or all requests timed out.")


    def call_gemini(self, messages: list[dict], context: dict,
                    temperature: float = 0.7, max_tokens: int = 2048) -> str:
        """Backwards-compatible alias for _call_llm."""
        return self._call_llm(messages, context, temperature=temperature, max_tokens=max_tokens)

    def call_gemini_json(self, messages: list[dict], context: dict,
                         temperature: float = 0.3) -> dict:
        """
        Call LLM and parse the response as clean JSON.
        """
        raw = self._call_llm(messages, context, temperature=temperature)

        cleaned = raw.strip()
        if cleaned.startswith("```"):
            lines = cleaned.split("\n")
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            cleaned = "\n".join(lines).strip()

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            logger.warning(f"[{self.name}] Failed to parse JSON from LLM: {raw[:200]}")
            return {"error": "Failed to parse agent response", "raw": raw}

    def execute(self, messages: list[dict], context: dict) -> dict:
        """
        Run this agent's logic. Override in subclasses.
        Returns a dict with at least {"content": str}.
        """
        raise NotImplementedError
