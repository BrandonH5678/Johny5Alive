#!/usr/bin/env python3
"""
Qwen2.5-7B Validator Client for J5A Night Shift

Provides a simple interface for Night Shift jobs to use Qwen for validation tasks.
Based on benchmark results: 81% overall accuracy, 304ms avg response time.

Constitutional Basis:
- Principle 2 (Transparency): Validation results are logged and auditable
- Principle 9 (Local LLM Optimization): Efficient use of j5a-server resources

Usage:
    from qwen_validator import QwenValidator

    validator = QwenValidator()

    # Classify a log entry
    result = validator.classify_error(log_entry, ["network", "auth", "database"])

    # Validate JSON format
    is_valid = validator.validate_json(json_string)

    # Check code syntax
    is_valid = validator.check_python_syntax(code_string)
"""

import json
import logging
import time
from dataclasses import dataclass
from typing import Optional, List, Dict, Any, Union
from enum import Enum

# Try to use requests, fall back to urllib if not available
try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    import urllib.request
    import urllib.error
    HAS_REQUESTS = False


logger = logging.getLogger(__name__)


class TaskType(Enum):
    """Supported validation task types"""
    CLASSIFICATION = "classification"
    FORMAT_VALIDATION = "format_validation"
    LOG_ANALYSIS = "log_analysis"
    SIMPLE_EXTRACTION = "simple_extraction"
    JSON_VALIDATION = "json_validation"
    CODE_SYNTAX_CHECK = "code_syntax_check"


@dataclass
class ValidationResult:
    """Result of a validation task"""
    success: bool
    result: Any
    confidence: str  # "high", "medium", "low" based on task type accuracy
    response_time_ms: float
    raw_response: str
    error: Optional[str] = None


class QwenValidator:
    """
    Qwen-based validator for Night Shift operations.

    Benchmark Results (2025-11-29):
    - Overall Accuracy: 81%
    - Average Response Time: 304ms

    Best for:
    - Code syntax checking (100% accuracy)
    - Simple extraction (100% accuracy)
    - Classification (80% accuracy)
    - Format validation (75% accuracy)

    Use with care:
    - Log analysis (66.7% - edge cases)
    - JSON schema validation (66.7% - missing field detection)
    """

    # Confidence levels based on benchmark accuracy
    CONFIDENCE_MAP = {
        TaskType.CODE_SYNTAX_CHECK: "high",      # 100%
        TaskType.SIMPLE_EXTRACTION: "high",       # 100%
        TaskType.CLASSIFICATION: "medium",        # 80%
        TaskType.FORMAT_VALIDATION: "medium",     # 75%
        TaskType.LOG_ANALYSIS: "low",            # 66.7%
        TaskType.JSON_VALIDATION: "low",         # 66.7%
    }

    def __init__(self,
                 ollama_url: str = "http://localhost:11434",
                 model: str = "qwen2.5:7b",
                 timeout: int = 60):
        """
        Initialize Qwen validator.

        Args:
            ollama_url: Ollama API endpoint (default: localhost for j5a-server)
            model: Model to use (default: qwen2.5:7b)
            timeout: Request timeout in seconds
        """
        self.ollama_url = ollama_url
        self.model = model
        self.timeout = timeout
        self._verified = False

    def verify_connection(self) -> bool:
        """Verify Ollama is accessible and model is loaded"""
        try:
            if HAS_REQUESTS:
                response = requests.get(
                    f"{self.ollama_url}/api/tags",
                    timeout=5
                )
                models = response.json().get("models", [])
            else:
                req = urllib.request.Request(f"{self.ollama_url}/api/tags")
                with urllib.request.urlopen(req, timeout=5) as resp:
                    models = json.loads(resp.read()).get("models", [])

            model_names = [m.get("name", "") for m in models]
            self._verified = any(self.model in name for name in model_names)
            return self._verified
        except Exception as e:
            logger.error(f"Failed to verify Ollama connection: {e}")
            return False

    def _query(self, prompt: str, max_tokens: int = 100) -> tuple[str, float]:
        """
        Query Qwen model.

        Returns:
            Tuple of (response_text, response_time_ms)
        """
        start = time.time()

        payload = json.dumps({
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "num_predict": max_tokens,
                "temperature": 0.1  # Low temp for consistent validation
            }
        }).encode('utf-8')

        try:
            if HAS_REQUESTS:
                response = requests.post(
                    f"{self.ollama_url}/api/generate",
                    json=json.loads(payload),
                    timeout=self.timeout
                )
                data = response.json()
            else:
                req = urllib.request.Request(
                    f"{self.ollama_url}/api/generate",
                    data=payload,
                    headers={'Content-Type': 'application/json'}
                )
                with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                    data = json.loads(resp.read())

            elapsed_ms = (time.time() - start) * 1000
            return data.get("response", "").strip(), elapsed_ms

        except Exception as e:
            elapsed_ms = (time.time() - start) * 1000
            raise RuntimeError(f"Qwen query failed: {e}") from e

    # === HIGH CONFIDENCE METHODS (100% accuracy) ===

    def check_python_syntax(self, code: str) -> ValidationResult:
        """
        Check if Python code has valid syntax.

        Confidence: HIGH (100% accuracy in benchmarks)
        """
        prompt = f"""Is this valid Python syntax? Answer only YES or NO.

{code}"""

        try:
            response, time_ms = self._query(prompt)
            is_valid = response.upper().startswith("YES")

            return ValidationResult(
                success=True,
                result=is_valid,
                confidence=self.CONFIDENCE_MAP[TaskType.CODE_SYNTAX_CHECK],
                response_time_ms=time_ms,
                raw_response=response
            )
        except Exception as e:
            return ValidationResult(
                success=False,
                result=None,
                confidence="none",
                response_time_ms=0,
                raw_response="",
                error=str(e)
            )

    def check_json_syntax(self, json_str: str) -> ValidationResult:
        """
        Check if string is valid JSON syntax.

        Confidence: HIGH (uses code_syntax_check pattern)
        """
        prompt = f"""Is this valid JSON syntax? Answer only YES or NO.

{json_str}"""

        try:
            response, time_ms = self._query(prompt)
            is_valid = response.upper().startswith("YES")

            return ValidationResult(
                success=True,
                result=is_valid,
                confidence=self.CONFIDENCE_MAP[TaskType.CODE_SYNTAX_CHECK],
                response_time_ms=time_ms,
                raw_response=response
            )
        except Exception as e:
            return ValidationResult(
                success=False,
                result=None,
                confidence="none",
                response_time_ms=0,
                raw_response="",
                error=str(e)
            )

    def extract_structured_data(self, text: str, fields: List[str]) -> ValidationResult:
        """
        Extract structured data from text as JSON.

        Confidence: HIGH (100% accuracy in benchmarks)

        Args:
            text: Source text to extract from
            fields: List of field names to extract
        """
        fields_str = ", ".join(fields)
        prompt = f"""Extract these fields as JSON: {fields_str}

Text: "{text}"

Return ONLY valid JSON with the requested fields."""

        try:
            response, time_ms = self._query(prompt, max_tokens=200)

            # Parse JSON from response
            extracted = None
            if "{" in response:
                try:
                    start = response.index("{")
                    end = response.rindex("}") + 1
                    extracted = json.loads(response[start:end])
                except json.JSONDecodeError:
                    pass

            return ValidationResult(
                success=extracted is not None,
                result=extracted,
                confidence=self.CONFIDENCE_MAP[TaskType.SIMPLE_EXTRACTION],
                response_time_ms=time_ms,
                raw_response=response
            )
        except Exception as e:
            return ValidationResult(
                success=False,
                result=None,
                confidence="none",
                response_time_ms=0,
                raw_response="",
                error=str(e)
            )

    # === MEDIUM CONFIDENCE METHODS (75-80% accuracy) ===

    def classify_error(self, log_entry: str, categories: List[str]) -> ValidationResult:
        """
        Classify a log entry into one of the given categories.

        Confidence: MEDIUM (80% accuracy in benchmarks)

        Args:
            log_entry: The log entry to classify
            categories: List of valid category names
        """
        categories_str = ", ".join(categories)
        prompt = f"""Classify this log entry into exactly one category: {categories_str}.

Log: "{log_entry}"

Respond with ONLY the category name, nothing else."""

        try:
            response, time_ms = self._query(prompt)

            # Normalize response
            result = response.lower().strip()
            # Check if response matches a category
            matched = None
            for cat in categories:
                if cat.lower() in result:
                    matched = cat
                    break

            return ValidationResult(
                success=matched is not None,
                result=matched or result,
                confidence=self.CONFIDENCE_MAP[TaskType.CLASSIFICATION],
                response_time_ms=time_ms,
                raw_response=response
            )
        except Exception as e:
            return ValidationResult(
                success=False,
                result=None,
                confidence="none",
                response_time_ms=0,
                raw_response="",
                error=str(e)
            )

    def classify_job_status(self, output: str) -> ValidationResult:
        """
        Classify Night Shift job output as SUCCESS, PARTIAL, or FAILED.

        Confidence: MEDIUM (80% accuracy in benchmarks)
        """
        return self.classify_error(
            f"Job output: {output}",
            ["SUCCESS", "PARTIAL", "FAILED"]
        )

    def validate_format(self, content: str, format_type: str) -> ValidationResult:
        """
        Validate content matches expected format.

        Confidence: MEDIUM (75% accuracy in benchmarks)

        Args:
            content: Content to validate
            format_type: Expected format (e.g., "email", "phone", "url")
        """
        prompt = f"""Is this a valid {format_type} format? Answer only YES or NO.

{content}"""

        try:
            response, time_ms = self._query(prompt)
            is_valid = response.upper().startswith("YES")

            return ValidationResult(
                success=True,
                result=is_valid,
                confidence=self.CONFIDENCE_MAP[TaskType.FORMAT_VALIDATION],
                response_time_ms=time_ms,
                raw_response=response
            )
        except Exception as e:
            return ValidationResult(
                success=False,
                result=None,
                confidence="none",
                response_time_ms=0,
                raw_response="",
                error=str(e)
            )

    # === LOW CONFIDENCE METHODS (66.7% accuracy - use with human review) ===

    def extract_timestamp(self, log_entry: str) -> ValidationResult:
        """
        Extract timestamp from log entry.

        Confidence: LOW (66.7% accuracy - recommend human review)
        """
        prompt = f"""Extract the timestamp from this log entry. Return ONLY the timestamp.

{log_entry}"""

        try:
            response, time_ms = self._query(prompt)

            return ValidationResult(
                success=True,
                result=response,
                confidence=self.CONFIDENCE_MAP[TaskType.LOG_ANALYSIS],
                response_time_ms=time_ms,
                raw_response=response
            )
        except Exception as e:
            return ValidationResult(
                success=False,
                result=None,
                confidence="none",
                response_time_ms=0,
                raw_response="",
                error=str(e)
            )

    def validate_json_schema(self, json_str: str, required_fields: List[str]) -> ValidationResult:
        """
        Validate JSON has required fields.

        Confidence: LOW (66.7% accuracy - recommend programmatic check as backup)

        Note: For critical validation, combine with programmatic JSON parsing.
        """
        fields_str = ", ".join([f"{f} (required)" for f in required_fields])
        prompt = f"""Does this JSON have all required fields: {fields_str}?
Answer only YES or NO.

{json_str}"""

        try:
            response, time_ms = self._query(prompt)
            is_valid = response.upper().startswith("YES")

            # Backup: Also check programmatically
            try:
                data = json.loads(json_str)
                programmatic_valid = all(f in data for f in required_fields)
            except:
                programmatic_valid = False

            return ValidationResult(
                success=True,
                result={
                    "qwen_says": is_valid,
                    "programmatic_check": programmatic_valid,
                    "combined": is_valid and programmatic_valid
                },
                confidence=self.CONFIDENCE_MAP[TaskType.JSON_VALIDATION],
                response_time_ms=time_ms,
                raw_response=response
            )
        except Exception as e:
            return ValidationResult(
                success=False,
                result=None,
                confidence="none",
                response_time_ms=0,
                raw_response="",
                error=str(e)
            )


# === CONVENIENCE FUNCTIONS ===

def get_validator(ollama_url: str = "http://localhost:11434") -> Optional[QwenValidator]:
    """
    Get a validated QwenValidator instance.

    Returns None if Ollama is not accessible.
    """
    validator = QwenValidator(ollama_url=ollama_url)
    if validator.verify_connection():
        return validator
    return None


if __name__ == "__main__":
    # Quick test
    import sys

    url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:11434"

    validator = QwenValidator(ollama_url=url)

    if not validator.verify_connection():
        print(f"Could not connect to Ollama at {url}")
        sys.exit(1)

    print("Qwen Validator Quick Test")
    print("=" * 40)

    # Test code syntax (HIGH confidence)
    result = validator.check_python_syntax("def hello(): print('hi')")
    print(f"Python syntax check: {result.result} ({result.confidence} confidence, {result.response_time_ms:.0f}ms)")

    # Test classification (MEDIUM confidence)
    result = validator.classify_job_status("Transcription complete. Output saved to file.txt")
    print(f"Job classification: {result.result} ({result.confidence} confidence, {result.response_time_ms:.0f}ms)")

    # Test extraction (HIGH confidence)
    result = validator.extract_structured_data(
        "Meeting with Bob at 2pm on Friday",
        ["person", "time", "day"]
    )
    print(f"Data extraction: {result.result} ({result.confidence} confidence, {result.response_time_ms:.0f}ms)")

    print("\nAll tests complete!")
