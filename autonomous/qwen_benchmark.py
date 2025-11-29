#!/usr/bin/env python3
"""
Qwen2.5-7B Validation Benchmark Suite
Phase 3: Local Model Integration

Tests Qwen's capabilities across all validation task types defined in
qwen_validation_format.json. Measures accuracy and response time.

Constitutional Basis:
- Principle 2 (Transparency): Document model capabilities
- Principle 9 (Local LLM Optimization): Efficient use of constrained hardware
"""

import json
import time
import requests
from dataclasses import dataclass
from typing import Optional, Dict, Any, List
from datetime import datetime


@dataclass
class BenchmarkResult:
    """Result of a single benchmark test"""
    task_type: str
    test_name: str
    prompt: str
    expected: str
    actual: str
    correct: bool
    response_time_ms: float
    tokens_generated: int


class QwenBenchmark:
    """Benchmark suite for Qwen2.5-7B validation tasks"""

    def __init__(self, ollama_url: str = "http://localhost:11434"):
        self.ollama_url = ollama_url
        self.model = "qwen2.5:7b"
        self.results: List[BenchmarkResult] = []

    def query_qwen(self, prompt: str, max_tokens: int = 100) -> tuple[str, float, int]:
        """Query Qwen via Ollama API, return (response, time_ms, tokens)"""
        start = time.time()

        response = requests.post(
            f"{self.ollama_url}/api/generate",
            json={
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "num_predict": max_tokens,
                    "temperature": 0.1  # Low temp for consistent validation
                }
            },
            timeout=60
        )

        elapsed_ms = (time.time() - start) * 1000
        data = response.json()

        return (
            data.get("response", "").strip(),
            elapsed_ms,
            data.get("eval_count", 0)
        )

    def run_test(self, task_type: str, test_name: str, prompt: str,
                 expected: str, validator: callable = None) -> BenchmarkResult:
        """Run a single benchmark test"""
        response, time_ms, tokens = self.query_qwen(prompt)

        if validator:
            correct = validator(response, expected)
        else:
            correct = expected.lower() in response.lower()

        result = BenchmarkResult(
            task_type=task_type,
            test_name=test_name,
            prompt=prompt[:200] + "..." if len(prompt) > 200 else prompt,
            expected=expected,
            actual=response[:500],
            correct=correct,
            response_time_ms=time_ms,
            tokens_generated=tokens
        )
        self.results.append(result)
        return result

    # === CLASSIFICATION BENCHMARKS ===

    def benchmark_classification(self):
        """Test log/error classification capabilities"""
        tests = [
            {
                "name": "network_error",
                "prompt": """Classify this log entry into exactly one category: network_error, database_error, auth_error, or other.

Log: "Error: Unable to connect to database at 192.168.0.100:5432 - Connection refused"

Respond with ONLY the category name, nothing else.""",
                "expected": "network_error"
            },
            {
                "name": "auth_error",
                "prompt": """Classify this log entry into exactly one category: network_error, database_error, auth_error, or other.

Log: "Authentication failed for user 'admin': Invalid password"

Respond with ONLY the category name, nothing else.""",
                "expected": "auth_error"
            },
            {
                "name": "database_error",
                "prompt": """Classify this log entry into exactly one category: network_error, database_error, auth_error, or other.

Log: "ERROR 1045 (28000): Access denied for user 'root'@'localhost'"

Respond with ONLY the category name, nothing else.""",
                "expected": "auth_error"  # This is actually auth, testing edge case
            },
            {
                "name": "job_status_success",
                "prompt": """Classify this Night Shift job result: SUCCESS, PARTIAL, or FAILED.

Job output: "Transcription complete. 45 minutes processed. Output: transcript.txt (2.3MB)"

Respond with ONLY the status, nothing else.""",
                "expected": "success"
            },
            {
                "name": "job_status_failed",
                "prompt": """Classify this Night Shift job result: SUCCESS, PARTIAL, or FAILED.

Job output: "ERROR: Out of memory. GPU allocation failed. No output generated."

Respond with ONLY the status, nothing else.""",
                "expected": "failed"
            }
        ]

        print("\n=== CLASSIFICATION BENCHMARKS ===")
        for test in tests:
            result = self.run_test("classification", test["name"],
                                   test["prompt"], test["expected"])
            status = "✓" if result.correct else "✗"
            print(f"  {status} {test['name']}: {result.response_time_ms:.0f}ms")

    # === FORMAT VALIDATION BENCHMARKS ===

    def benchmark_format_validation(self):
        """Test JSON/format validation capabilities"""
        tests = [
            {
                "name": "valid_json",
                "prompt": """Is this valid JSON? Answer only YES or NO.

{"name": "test", "value": 123, "active": true}""",
                "expected": "yes"
            },
            {
                "name": "invalid_json",
                "prompt": """Is this valid JSON? Answer only YES or NO.

{"name": "test", value: 123}""",
                "expected": "no"
            },
            {
                "name": "valid_email",
                "prompt": """Is this a valid email format? Answer only YES or NO.

user@example.com""",
                "expected": "yes"
            },
            {
                "name": "invalid_email",
                "prompt": """Is this a valid email format? Answer only YES or NO.

user@example""",
                "expected": "no"
            }
        ]

        print("\n=== FORMAT VALIDATION BENCHMARKS ===")
        for test in tests:
            result = self.run_test("format_validation", test["name"],
                                   test["prompt"], test["expected"])
            status = "✓" if result.correct else "✗"
            print(f"  {status} {test['name']}: {result.response_time_ms:.0f}ms")

    # === LOG ANALYSIS BENCHMARKS ===

    def benchmark_log_analysis(self):
        """Test log parsing and analysis capabilities"""
        tests = [
            {
                "name": "extract_timestamp",
                "prompt": """Extract the timestamp from this log entry. Return ONLY the timestamp.

[2025-11-29 14:32:45] INFO: Processing started""",
                "expected": "2025-11-29 14:32:45"
            },
            {
                "name": "count_errors",
                "prompt": """Count the number of ERROR lines in this log. Return ONLY a number.

[INFO] Starting service
[ERROR] Connection failed
[WARN] Retrying...
[ERROR] Connection failed again
[INFO] Giving up""",
                "expected": "2"
            },
            {
                "name": "identify_severity",
                "prompt": """What is the highest severity level in this log? Return only: DEBUG, INFO, WARN, ERROR, or CRITICAL.

[DEBUG] Initialization
[INFO] Started
[WARN] Low memory
[ERROR] Disk full""",
                "expected": "error"
            }
        ]

        print("\n=== LOG ANALYSIS BENCHMARKS ===")
        for test in tests:
            result = self.run_test("log_analysis", test["name"],
                                   test["prompt"], test["expected"])
            status = "✓" if result.correct else "✗"
            print(f"  {status} {test['name']}: {result.response_time_ms:.0f}ms")

    # === SIMPLE EXTRACTION BENCHMARKS ===

    def benchmark_simple_extraction(self):
        """Test entity/data extraction capabilities"""

        def json_validator(response: str, expected: str) -> bool:
            """Check if response contains expected JSON fields"""
            try:
                # Try to parse response as JSON
                if "{" in response:
                    start = response.index("{")
                    end = response.rindex("}") + 1
                    data = json.loads(response[start:end])
                    expected_data = json.loads(expected)
                    return all(k in data for k in expected_data.keys())
            except:
                pass
            return False

        tests = [
            {
                "name": "extract_meeting",
                "prompt": """Extract meeting details as JSON with keys: date, time, person.

"Meeting scheduled for 2025-11-30 at 3:00 PM with John Smith"

Return ONLY valid JSON.""",
                "expected": '{"date": "2025-11-30", "time": "3:00 PM", "person": "John Smith"}'
            },
            {
                "name": "extract_contact",
                "prompt": """Extract contact details as JSON with keys: name, phone, email.

"Contact Jane Doe at 555-1234 or jane@example.com for questions."

Return ONLY valid JSON.""",
                "expected": '{"name": "Jane Doe", "phone": "555-1234", "email": "jane@example.com"}'
            }
        ]

        print("\n=== SIMPLE EXTRACTION BENCHMARKS ===")
        for test in tests:
            result = self.run_test("simple_extraction", test["name"],
                                   test["prompt"], test["expected"], json_validator)
            status = "✓" if result.correct else "✗"
            print(f"  {status} {test['name']}: {result.response_time_ms:.0f}ms")

    # === JSON VALIDATION BENCHMARKS ===

    def benchmark_json_validation(self):
        """Test JSON schema validation capabilities"""
        tests = [
            {
                "name": "valid_schema",
                "prompt": """Does this JSON match the schema requiring: name (string), age (number)?
Answer only YES or NO.

{"name": "Alice", "age": 30}""",
                "expected": "yes"
            },
            {
                "name": "invalid_schema",
                "prompt": """Does this JSON match the schema requiring: name (string), age (number)?
Answer only YES or NO.

{"name": "Bob", "age": "thirty"}""",
                "expected": "no"
            },
            {
                "name": "missing_field",
                "prompt": """Does this JSON match the schema requiring: id (number), status (string)?
Answer only YES or NO.

{"id": 123}""",
                "expected": "no"
            }
        ]

        print("\n=== JSON VALIDATION BENCHMARKS ===")
        for test in tests:
            result = self.run_test("json_validation", test["name"],
                                   test["prompt"], test["expected"])
            status = "✓" if result.correct else "✗"
            print(f"  {status} {test['name']}: {result.response_time_ms:.0f}ms")

    # === CODE SYNTAX CHECK BENCHMARKS ===

    def benchmark_code_syntax(self):
        """Test code syntax validation capabilities"""
        tests = [
            {
                "name": "valid_python",
                "prompt": """Is this valid Python syntax? Answer only YES or NO.

def hello():
    print("Hello, World!")""",
                "expected": "yes"
            },
            {
                "name": "invalid_python",
                "prompt": """Is this valid Python syntax? Answer only YES or NO.

def hello()
    print("Hello, World!")""",
                "expected": "no"
            },
            {
                "name": "valid_json_code",
                "prompt": """Is this valid JSON syntax? Answer only YES or NO.

{
  "items": [1, 2, 3],
  "count": 3
}""",
                "expected": "yes"
            },
            {
                "name": "invalid_bash",
                "prompt": """Is this valid bash syntax? Answer only YES or NO.

if [ -f file.txt ]
then
  echo "exists"
fi""",
                "expected": "yes"
            }
        ]

        print("\n=== CODE SYNTAX CHECK BENCHMARKS ===")
        for test in tests:
            result = self.run_test("code_syntax_check", test["name"],
                                   test["prompt"], test["expected"])
            status = "✓" if result.correct else "✗"
            print(f"  {status} {test['name']}: {result.response_time_ms:.0f}ms")

    def run_all_benchmarks(self):
        """Run complete benchmark suite"""
        print(f"\n{'='*60}")
        print(f"QWEN 2.5-7B VALIDATION BENCHMARK SUITE")
        print(f"Date: {datetime.now().isoformat()}")
        print(f"Model: {self.model}")
        print(f"Server: {self.ollama_url}")
        print(f"{'='*60}")

        self.benchmark_classification()
        self.benchmark_format_validation()
        self.benchmark_log_analysis()
        self.benchmark_simple_extraction()
        self.benchmark_json_validation()
        self.benchmark_code_syntax()

        self.print_summary()
        return self.generate_report()

    def print_summary(self):
        """Print benchmark summary"""
        print(f"\n{'='*60}")
        print("SUMMARY")
        print(f"{'='*60}")

        # Overall stats
        total = len(self.results)
        correct = sum(1 for r in self.results if r.correct)
        avg_time = sum(r.response_time_ms for r in self.results) / total

        print(f"\nOverall Accuracy: {correct}/{total} ({100*correct/total:.1f}%)")
        print(f"Average Response Time: {avg_time:.0f}ms")

        # By task type
        print("\nBy Task Type:")
        task_types = set(r.task_type for r in self.results)
        for tt in sorted(task_types):
            tt_results = [r for r in self.results if r.task_type == tt]
            tt_correct = sum(1 for r in tt_results if r.correct)
            tt_time = sum(r.response_time_ms for r in tt_results) / len(tt_results)
            print(f"  {tt}: {tt_correct}/{len(tt_results)} correct, {tt_time:.0f}ms avg")

    def generate_report(self) -> Dict[str, Any]:
        """Generate JSON report"""
        total = len(self.results)
        correct = sum(1 for r in self.results if r.correct)

        report = {
            "metadata": {
                "date": datetime.now().isoformat(),
                "model": self.model,
                "server": self.ollama_url,
                "total_tests": total,
                "passed": correct,
                "accuracy": correct / total if total > 0 else 0
            },
            "summary": {
                "overall_accuracy": f"{100*correct/total:.1f}%" if total > 0 else "N/A",
                "avg_response_time_ms": sum(r.response_time_ms for r in self.results) / total if total > 0 else 0
            },
            "by_task_type": {},
            "results": []
        }

        # Aggregate by task type
        task_types = set(r.task_type for r in self.results)
        for tt in task_types:
            tt_results = [r for r in self.results if r.task_type == tt]
            tt_correct = sum(1 for r in tt_results if r.correct)
            report["by_task_type"][tt] = {
                "tests": len(tt_results),
                "passed": tt_correct,
                "accuracy": f"{100*tt_correct/len(tt_results):.1f}%",
                "avg_time_ms": sum(r.response_time_ms for r in tt_results) / len(tt_results)
            }

        # Individual results
        for r in self.results:
            report["results"].append({
                "task_type": r.task_type,
                "test_name": r.test_name,
                "correct": r.correct,
                "response_time_ms": r.response_time_ms,
                "expected": r.expected,
                "actual": r.actual[:200]
            })

        return report


if __name__ == "__main__":
    import sys

    # Check if running remotely via SSH
    url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:11434"

    benchmark = QwenBenchmark(ollama_url=url)
    report = benchmark.run_all_benchmarks()

    # Save report
    report_path = "/tmp/qwen_benchmark_report.json"
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
    print(f"\nReport saved to: {report_path}")
