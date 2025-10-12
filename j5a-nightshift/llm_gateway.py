#!/usr/bin/env python3
"""
LLM Gateway - Unified interface for local/remote/API LLM access
Provides consistent complete(instructions, excerpts, limits) interface across all model types
"""

import os
import json
import logging
import requests
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class LLMMode(Enum):
    """LLM execution modes"""
    LOCAL = "local"      # Local Ollama instance
    REMOTE = "remote"    # Remote Ollama server (VPN)
    API = "api"          # Claude Code API


@dataclass
class LLMRequest:
    """Standardized LLM request"""
    instructions: str
    excerpts: List[Dict[str, Any]]
    max_tokens: int = 600
    temperature: float = 0.7
    top_p: float = 0.9


@dataclass
class LLMResponse:
    """Standardized LLM response"""
    text: str
    mode: LLMMode
    model: str
    tokens_input: int = 0
    tokens_output: int = 0
    success: bool = True
    error: Optional[str] = None


class LLMGateway:
    """
    Unified LLM interface supporting local, remote, and API modes

    Usage:
        gateway = LLMGateway(mode=LLMMode.LOCAL, config=config)
        response = gateway.complete(
            instructions="Summarize the excerpts",
            excerpts=[{"text": "...", "source": "file.txt"}],
            limits={"max_tokens": 600}
        )
    """

    def __init__(self, mode: LLMMode, config: Dict[str, Any]):
        """
        Initialize LLM gateway

        Args:
            mode: Execution mode (local/remote/api)
            config: Configuration dict from rules.yaml
        """
        self.mode = mode
        self.config = config
        self.llm_config = config.get("llm", {})
        self.api_config = config.get("api", {})

        # Validate configuration
        if mode == LLMMode.API and not self.api_config.get("enabled", False):
            raise ValueError("API mode requested but api.enabled=false in config")

        if mode == LLMMode.API and os.getenv(self.api_config.get("kill_env", "J5A_API_DISABLED")):
            raise ValueError(f"API mode blocked by {self.api_config.get('kill_env')} environment variable")

        logger.info(f"LLM Gateway initialized in {mode.value} mode")

    def complete(
        self,
        instructions: str,
        excerpts: List[Dict[str, Any]],
        limits: Optional[Dict[str, int]] = None
    ) -> str:
        """
        Unified completion interface across all LLM modes

        Args:
            instructions: System/user instructions for the LLM
            excerpts: List of text excerpts with metadata
            limits: Token limits and other constraints

        Returns:
            Generated text response

        Raises:
            RuntimeError: If LLM call fails
        """
        limits = limits or {}
        max_tokens = limits.get("max_output", self.llm_config.get("max_output", 600))

        # Build request
        request = LLMRequest(
            instructions=instructions,
            excerpts=excerpts,
            max_tokens=max_tokens,
            temperature=self.llm_config.get("temperature", 0.7),
            top_p=self.llm_config.get("top_p", 0.9)
        )

        # Route to appropriate backend
        if self.mode == LLMMode.LOCAL:
            response = self._complete_local(request)
        elif self.mode == LLMMode.REMOTE:
            response = self._complete_remote(request)
        elif self.mode == LLMMode.API:
            response = self._complete_api(request)
        else:
            raise ValueError(f"Unknown LLM mode: {self.mode}")

        if not response.success:
            raise RuntimeError(f"LLM completion failed: {response.error}")

        logger.info(f"LLM completion: {response.tokens_input} in, {response.tokens_output} out")
        return response.text

    def _complete_local(self, request: LLMRequest) -> LLMResponse:
        """Execute LLM request via local Ollama"""
        endpoint = self.llm_config.get("local_endpoint", "http://localhost:11434")
        model = self.llm_config.get("model", "qwen2.5:7b-instruct")

        try:
            # Build prompt with excerpts
            prompt = self._build_prompt(request.instructions, request.excerpts)

            # Call Ollama API
            response = requests.post(
                f"{endpoint}/api/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": request.temperature,
                        "top_p": request.top_p,
                        "num_predict": request.max_tokens
                    }
                },
                timeout=600  # 10 minute timeout for local generation (CPU-only inference is slow)
            )
            response.raise_for_status()

            result = response.json()

            return LLMResponse(
                text=result["response"],
                mode=LLMMode.LOCAL,
                model=model,
                tokens_input=result.get("prompt_eval_count", 0),
                tokens_output=result.get("eval_count", 0),
                success=True
            )

        except Exception as e:
            logger.error(f"Local LLM error: {e}")
            return LLMResponse(
                text="",
                mode=LLMMode.LOCAL,
                model=model,
                success=False,
                error=str(e)
            )

    def _complete_remote(self, request: LLMRequest) -> LLMResponse:
        """Execute LLM request via remote Ollama server"""
        endpoint = self.llm_config.get("remote_endpoint", "http://10.8.0.2:11434")
        model = self.llm_config.get("model", "qwen2.5:7b-instruct")

        try:
            # Build prompt
            prompt = self._build_prompt(request.instructions, request.excerpts)

            # Call remote Ollama API
            response = requests.post(
                f"{endpoint}/api/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": request.temperature,
                        "top_p": request.top_p,
                        "num_predict": request.max_tokens
                    }
                },
                timeout=600  # 10 minute timeout for remote generation
            )
            response.raise_for_status()

            result = response.json()

            return LLMResponse(
                text=result["response"],
                mode=LLMMode.REMOTE,
                model=model,
                tokens_input=result.get("prompt_eval_count", 0),
                tokens_output=result.get("eval_count", 0),
                success=True
            )

        except Exception as e:
            logger.error(f"Remote LLM error: {e}")
            return LLMResponse(
                text="",
                mode=LLMMode.REMOTE,
                model=model,
                success=False,
                error=str(e)
            )

    def _complete_api(self, request: LLMRequest) -> LLMResponse:
        """Execute LLM request via Claude API"""
        try:
            import anthropic
        except ImportError:
            return LLMResponse(
                text="",
                mode=LLMMode.API,
                model="claude",
                success=False,
                error="anthropic package not installed"
            )

        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            return LLMResponse(
                text="",
                mode=LLMMode.API,
                model="claude",
                success=False,
                error="ANTHROPIC_API_KEY environment variable not set"
            )

        try:
            client = anthropic.Anthropic(api_key=api_key)
            model = self.api_config.get("model", "claude-sonnet-4-5")

            # Build messages
            prompt = self._build_prompt(request.instructions, request.excerpts)

            # Call Claude API
            response = client.messages.create(
                model=model,
                max_tokens=request.max_tokens,
                temperature=request.temperature,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            return LLMResponse(
                text=response.content[0].text,
                mode=LLMMode.API,
                model=model,
                tokens_input=response.usage.input_tokens,
                tokens_output=response.usage.output_tokens,
                success=True
            )

        except Exception as e:
            logger.error(f"API LLM error: {e}")
            return LLMResponse(
                text="",
                mode=LLMMode.API,
                model="claude",
                success=False,
                error=str(e)
            )

    def _build_prompt(self, instructions: str, excerpts: List[Dict[str, Any]]) -> str:
        """
        Build prompt from instructions and excerpts

        Args:
            instructions: System instructions
            excerpts: List of excerpt dicts with 'text', 'source', etc.

        Returns:
            Formatted prompt string
        """
        prompt_parts = [instructions, "\n\n# Source Excerpts\n"]

        for i, excerpt in enumerate(excerpts, 1):
            text = excerpt.get("text", "")
            source = excerpt.get("source", "unknown")
            score = excerpt.get("score", 0.0)

            prompt_parts.append(f"\n## Excerpt {i} (source: {source}, relevance: {score:.2f})\n{text}\n")

        return "\n".join(prompt_parts)


def retry_with_backoff(fn, retries=1, delay=10):
    """
    Retry a function with linear backoff

    Args:
        fn: Function to execute
        retries: Number of retries (default 1)
        delay: Base delay in seconds (default 10)

    Returns:
        Function result

    Raises:
        Last exception if all retries fail
    """
    import time

    for i in range(retries + 1):
        try:
            return fn()
        except Exception as e:
            if i == retries:
                raise
            logger.warning(f"Retry {i+1}/{retries}: {e}")
            time.sleep(delay * (i + 1))


# Example usage and testing
if __name__ == "__main__":
    import yaml

    logging.basicConfig(level=logging.INFO)

    # Load config
    config_path = "/home/johnny5/Johny5Alive/j5a-nightshift/rules.yaml"
    with open(config_path) as f:
        config = yaml.safe_load(f)

    # Test local mode (requires Ollama running)
    try:
        gateway = LLMGateway(mode=LLMMode.LOCAL, config=config)

        response = gateway.complete(
            instructions="Summarize the following excerpts in 3 bullet points.",
            excerpts=[
                {"text": "Python is a high-level programming language.", "source": "intro.txt", "score": 0.95},
                {"text": "It emphasizes code readability with significant whitespace.", "source": "intro.txt", "score": 0.88}
            ]
        )

        print("=" * 60)
        print("LLM RESPONSE:")
        print("=" * 60)
        print(response)
        print("=" * 60)

    except Exception as e:
        print(f"Test failed: {e}")
        print("This is expected if Ollama is not yet installed.")
        print("\nTo install Ollama:")
        print("  curl -fsSL https://ollama.com/install.sh | sh")
        print("  ollama pull qwen2.5:7b-instruct-q4_K_M")
