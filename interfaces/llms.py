"""
This module contains the interfaces to external LLMs;
There's an abstract base class LLM that can be subclassed to provide an interface to a model.
The class method LLM.for_model_name creates an instance of a subclass to interact with the API
This module should have no knowledge of the game itself.
"""

import json
import os
import urllib.request
from abc import ABC
from typing import Any, Dict, Self, List, Type
from openai import OpenAI
import anthropic
from groq import Groq


ANTHROPIC_BASE_URL = "https://api.anthropic.com/v1/"
DEEPSEEK_BASE_URL = "https://api.deepseek.com/v1"
GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"
GROK_BASE_URL = "https://api.x.ai/v1"
GROQ_BASE_URL = "https://api.groq.com/openai/v1"
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
OLLAMA_BASE_URL = "http://localhost:11434/v1"


class LLM(ABC):
    """
    An abstract base class for LLMs
    Use LLM.for_model_name() to instantiate the appropriate subclass, then communicate with send()
    """

    model_names = []
    env_key: str | None = None
    provider_name: str = ""
    model_prefixes: List[str] = []
    supports_custom_input: bool = False
    model_name: str
    temperature: float
    client: Any

    def __init__(self, model_name, temperature=1.0):
        self.model_name = model_name
        self.temperature = temperature
        self.setup_client()

    def setup_client(self):
        """
        Implemented by subclasses
        """
        pass

    def send(self, system_prompt: str, user_prompt: str, max_tokens: int) -> str:
        """
        Implemented by subclasses
        :param system_prompt: The system prompt passed to the LLM
        :param user_prompt: The user prompt passed to the LLM
        :param max_tokens: Maximum number of tokens
        :return: the response from the LLM
        """
        pass

    def __repr__(self) -> str:
        """
        :return: A string version of the receiver
        """
        return f"<LLM {self.model_name} with temnp={self.temperature}>"

    @classmethod
    def model_map(cls) -> Dict[str, Type[Self]]:
        """
        Generate a mapping of Model Names to LLM classes, filtered to providers whose API key is set.
        :return: a mapping dictionary from model name to LLM subclass
        """
        mapping = {}
        for llm in cls.__subclasses__():
            if llm.env_key is None or os.getenv(llm.env_key):
                for model_name in llm.model_names:
                    mapping[model_name] = llm
        return mapping

    @classmethod
    def missing_keys(cls) -> List[str]:
        """
        :return: env var names that are required by known providers but not currently set
        """
        return [
            llm.env_key
            for llm in cls.__subclasses__()
            if llm.env_key and not os.getenv(llm.env_key)
        ]

    @classmethod
    def available_providers(cls) -> List[Type[Self]]:
        """
        :return: provider classes whose API key is set and that have models (or support free input)
        """
        result = []
        for llm in cls.__subclasses__():
            key_ok = llm.env_key is None or os.getenv(llm.env_key)
            has_models = bool(llm.model_names) or llm.supports_custom_input
            if key_ok and has_models:
                result.append(llm)
        return result

    @classmethod
    def for_model_name(cls, model_name: str, temperature=0.7) -> Self:
        """
        Given a particular model name, instantiate the right subclass.
        Falls back to prefix matching for custom model names not in the static list.
        """
        mapping = cls.model_map()
        if model_name in mapping:
            llm_class = mapping[model_name]
        else:
            llm_class = None
            for llm in cls.__subclasses__():
                key_ok = llm.env_key is None or os.getenv(llm.env_key)
                if key_ok and any(model_name.startswith(p) for p in llm.model_prefixes):
                    llm_class = llm
                    break
            if llm_class is None:
                raise KeyError(f"No LLM provider found for model: {model_name}")
        return llm_class(model_name, temperature)

    @classmethod
    def all_model_names(cls) -> List[str]:
        """
        :return: a list of names of all the models supported
        """
        return list(cls.model_map().keys())


class GPT(LLM):
    provider_name = "OpenAI"
    env_key = "OPENAI_API_KEY"
    model_names = ["gpt-5", "gpt-5-nano", "gpt-5-mini"]
    model_prefixes = ["gpt-", "o1", "o3", "o4", "chatgpt-"]

    def setup_client(self):
        self.client = OpenAI()

    def send(self, system_prompt: str, user_prompt: str, max_tokens: int) -> str:
        """
        Implementation for OpenAI / GPT
        :param system_prompt: The system prompt passed to the LLM
        :param user_prompt: The user prompt passed to the LLM
        :param max_tokens: Maximum number of tokens
        :return: the response from the LLM
        """
        effort = "low" if "gpt-5" in self.model_name else None
        completion = self.client.chat.completions.create(
            model=self.model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            response_format={"type": "json_object"},
            reasoning_effort=effort,
        )
        return completion.choices[0].message.content


class Claude(LLM):
    provider_name = "Anthropic"
    env_key = "ANTHROPIC_API_KEY"
    model_names = ["claude-sonnet-4-5", "claude-haiku-4-5"]
    model_prefixes = ["claude-"]

    def setup_client(self):
        self.client = anthropic.Anthropic()

    def send(self, system_prompt: str, user_prompt: str, max_tokens: int) -> str:
        """
        Implementation for Anthropic / Claude
        :param system_prompt: The system prompt passed to the LLM
        :param user_prompt: The user prompt passed to the LLM
        :param max_tokens: Maximum number of tokens
        :return: the response from the LLM
        """
        message = self.client.messages.create(
            model=self.model_name,
            max_tokens=max_tokens,
            temperature=0.5,
            system=system_prompt,
            messages=[
                {"role": "user", "content": user_prompt},
            ],
        )
        return message.content[0].text


# class Gemini(LLM):
#     model_names = ["gemini-1.0-pro", "gemini-1.5-flash", "gemini-2.0-flash", "gemini-2.5-flash"]

#     def setup_client(self):
#         google.generativeai.configure()
#         self.client = google.generativeai.GenerativeModel(self.model_name)

#     def send(self, system_prompt: str, user_prompt: str, max_tokens: int) -> str:
#         """
#         Implementation for Google / Gemini
#         :param system_prompt: The system prompt passed to the LLM
#         :param user_prompt: The user prompt passed to the LLM
#         :param max_tokens: Maximum number of tokens
#         :return: the response from the LLM
#         """
#         words = int(max_tokens * 0.75)
#         message = "First, here is a System Message to set context and instructions:\n\n"
#         message += system_prompt + "\n\n"
#         message += f"Now here is the User's Request - please respond in under {words} words:\n\n"
#         message += user_prompt + "\n"
#         response = self.client.generate_content(message)
#         first_candidate = response.candidates[0]

#         if first_candidate.content.parts:
#             myanswer1 = response.candidates[0].content.parts[0].text
#             return myanswer1
#         raise ValueError("Could not parse response from Gemini")


class Grok(LLM):
    provider_name = "xAI Grok"
    env_key = "GROK_API_KEY"
    model_names = ["grok-4", "grok-4-fast"]
    model_prefixes = ["grok-"]

    def setup_client(self):
        self.client = OpenAI(api_key=os.getenv("GROK_API_KEY"), base_url=GROK_BASE_URL)

    def send(self, system_prompt: str, user_prompt: str, max_tokens: int) -> str:
        """
        Implementation for OpenAI / GPT
        :param system_prompt: The system prompt passed to the LLM
        :param user_prompt: The user prompt passed to the LLM
        :param max_tokens: Maximum number of tokens
        :return: the response from the LLM
        """
        completion = self.client.chat.completions.create(
            model=self.model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        return completion.choices[0].message.content


class Gemini(LLM):
    provider_name = "Google Gemini"
    env_key = "GOOGLE_API_KEY"
    model_names = ["gemini-2.5-flash", "gemini-2.5-pro"]
    model_prefixes = ["gemini-"]

    def setup_client(self):
        self.client = OpenAI(api_key=os.getenv("GOOGLE_API_KEY"), base_url=GEMINI_BASE_URL)

    def send(self, system_prompt: str, user_prompt: str, max_tokens: int) -> str:
        """
        Implementation for OpenAI / GPT
        :param system_prompt: The system prompt passed to the LLM
        :param user_prompt: The user prompt passed to the LLM
        :param max_tokens: Maximum number of tokens
        :return: the response from the LLM
        """
        completion = self.client.chat.completions.create(
            model=self.model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.5,
            response_format={"type": "json_object"},
        )
        return completion.choices[0].message.content


class GroqAPI(LLM):
    provider_name = "Groq"
    env_key = "GROQ_API_KEY"
    model_names = ["openai/gpt-oss-120b"]
    model_prefixes = ["openai/gpt-oss"]

    def setup_client(self):
        self.client = Groq()

    def send(self, system_prompt: str, user_prompt: str, max_tokens: int) -> str:
        """
        Implementation for Groq
        :param system_prompt: The system prompt passed to the LLM
        :param user_prompt: The user prompt passed to the LLM
        :param max_tokens: Maximum number of tokens
        :return: the response from the LLM
        """
        completion = self.client.chat.completions.create(
            model=self.model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.5,
            response_format={"type": "json_object"},
        )
        return completion.choices[0].message.content


def _discover_ollama_models() -> List[str]:
    try:
        with urllib.request.urlopen("http://localhost:11434/api/tags", timeout=2) as resp:
            data = json.loads(resp.read())
        return [
            "ollama/" + (e["name"][:-7] if e["name"].endswith(":latest") else e["name"])
            for e in data.get("models", [])
        ]
    except Exception:
        return []


class Ollama(LLM):
    provider_name = "Ollama (local)"
    env_key = None
    model_names = _discover_ollama_models()
    model_prefixes = ["ollama/"]

    def setup_client(self):
        self.client = OpenAI(api_key="ollama", base_url=OLLAMA_BASE_URL)

    def send(self, system_prompt: str, user_prompt: str, max_tokens: int) -> str:
        completion = self.client.chat.completions.create(
            model=self.model_name.removeprefix("ollama/"),
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            response_format={"type": "json_object"},
        )
        return completion.choices[0].message.content


class OpenRouter(LLM):
    provider_name = "OpenRouter"
    env_key = "OPENROUTER_API_KEY"
    model_names = []
    model_prefixes = ["openrouter/"]
    supports_custom_input = True

    def setup_client(self):
        self.client = OpenAI(
            api_key=os.getenv("OPENROUTER_API_KEY"),
            base_url=OPENROUTER_BASE_URL,
        )

    def send(self, system_prompt: str, user_prompt: str, max_tokens: int) -> str:
        completion = self.client.chat.completions.create(
            model=self.model_name.removeprefix("openrouter/"),
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        return completion.choices[0].message.content
