#!/usr/bin/env python3
"""
Code Validator - 100% pass requirement for ruff, mypy, pytest
Validates generated code meets quality standards before output approval
"""

import os
import subprocess
import tempfile
import logging
from pathlib import Path
from typing import Dict, Any, List, Tuple

logger = logging.getLogger(__name__)


class CodeValidator:
    """
    Validates Python code using ruff, mypy, and pytest

    Requirements (from Nightshift spec):
    - ruff: Linting must pass 100%
    - mypy: Type checking must pass 100%
    - pytest: All tests must pass 100%
    """

    def __init__(self):
        """Initialize validator and check tool availability"""
        self.tools_available = self._check_tools()

        if not all(self.tools_available.values()):
            missing = [t for t, avail in self.tools_available.items() if not avail]
            logger.warning(f"Missing validation tools: {missing}")

    def _check_tools(self) -> Dict[str, bool]:
        """Check if validation tools are installed"""
        tools = {}

        for tool in ['ruff', 'mypy', 'pytest']:
            try:
                result = subprocess.run(
                    [tool, '--version'],
                    capture_output=True,
                    timeout=5
                )
                tools[tool] = result.returncode == 0
            except (FileNotFoundError, subprocess.TimeoutExpired):
                tools[tool] = False

        return tools

    def validate(self, code_path: str, test_path: str = None) -> Dict[str, Any]:
        """
        Validate Python code file

        Args:
            code_path: Path to generated Python code
            test_path: Optional path to pytest test file

        Returns:
            Validation result dict with:
            {
                "success": bool,
                "ruff_passed": bool,
                "mypy_passed": bool,
                "pytest_passed": bool,
                "errors": List[str],
                "details": Dict[str, str]
            }
        """
        result = {
            "success": False,
            "ruff_passed": False,
            "mypy_passed": False,
            "pytest_passed": False,
            "errors": [],
            "details": {}
        }

        # Validate file exists
        if not os.path.exists(code_path):
            result["errors"].append(f"Code file not found: {code_path}")
            return result

        # Run ruff
        if self.tools_available['ruff']:
            ruff_passed, ruff_output = self._run_ruff(code_path)
            result["ruff_passed"] = ruff_passed
            result["details"]["ruff"] = ruff_output
            if not ruff_passed:
                result["errors"].append("Ruff linting failed")
        else:
            result["errors"].append("Ruff not available")

        # Run mypy
        if self.tools_available['mypy']:
            mypy_passed, mypy_output = self._run_mypy(code_path)
            result["mypy_passed"] = mypy_passed
            result["details"]["mypy"] = mypy_output
            if not mypy_passed:
                result["errors"].append("Mypy type checking failed")
        else:
            result["errors"].append("Mypy not available")

        # Run pytest (if test file provided)
        if test_path:
            if self.tools_available['pytest']:
                pytest_passed, pytest_output = self._run_pytest(code_path, test_path)
                result["pytest_passed"] = pytest_passed
                result["details"]["pytest"] = pytest_output
                if not pytest_passed:
                    result["errors"].append("Pytest tests failed")
            else:
                result["errors"].append("Pytest not available")
        else:
            # No tests = auto-pass (optional tests)
            result["pytest_passed"] = True

        # Overall success = all tools pass
        result["success"] = (
            result["ruff_passed"] and
            result["mypy_passed"] and
            result["pytest_passed"]
        )

        logger.info(f"Code validation: {result['success']} (ruff: {result['ruff_passed']}, mypy: {result['mypy_passed']}, pytest: {result['pytest_passed']})")

        return result

    def _run_ruff(self, code_path: str) -> Tuple[bool, str]:
        """Run ruff linter"""
        try:
            result = subprocess.run(
                ['ruff', 'check', code_path],
                capture_output=True,
                text=True,
                timeout=30
            )

            # Ruff returns 0 for success
            passed = result.returncode == 0
            output = result.stdout + result.stderr

            return passed, output

        except Exception as e:
            return False, f"Ruff error: {e}"

    def _run_mypy(self, code_path: str) -> Tuple[bool, str]:
        """Run mypy type checker"""
        try:
            result = subprocess.run(
                ['mypy', code_path, '--strict'],
                capture_output=True,
                text=True,
                timeout=30
            )

            # Mypy returns 0 for success
            passed = result.returncode == 0
            output = result.stdout + result.stderr

            return passed, output

        except Exception as e:
            return False, f"Mypy error: {e}"

    def _run_pytest(self, code_path: str, test_path: str) -> Tuple[bool, str]:
        """Run pytest tests"""
        try:
            # Create temp directory with both files
            with tempfile.TemporaryDirectory() as tmpdir:
                # Copy code file
                code_name = Path(code_path).name
                tmp_code = os.path.join(tmpdir, code_name)

                with open(code_path, 'r') as src:
                    with open(tmp_code, 'w') as dst:
                        dst.write(src.read())

                # Copy test file
                test_name = Path(test_path).name
                tmp_test = os.path.join(tmpdir, test_name)

                with open(test_path, 'r') as src:
                    with open(tmp_test, 'w') as dst:
                        dst.write(src.read())

                # Run pytest
                result = subprocess.run(
                    ['pytest', tmp_test, '-v'],
                    capture_output=True,
                    text=True,
                    timeout=60,
                    cwd=tmpdir
                )

                # Pytest returns 0 for all tests passing
                passed = result.returncode == 0
                output = result.stdout + result.stderr

                return passed, output

        except Exception as e:
            return False, f"Pytest error: {e}"


def validate_code_file(code_path: str, test_path: str = None) -> bool:
    """
    Convenience function for code validation

    Args:
        code_path: Path to Python code file
        test_path: Optional path to pytest test file

    Returns:
        True if all validations pass, False otherwise
    """
    validator = CodeValidator()
    result = validator.validate(code_path, test_path)

    if not result["success"]:
        logger.error(f"Code validation failed: {result['errors']}")
        for tool, output in result["details"].items():
            if output:
                logger.error(f"{tool} output:\n{output}")

    return result["success"]


# Example usage and testing
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # Create test code file
    test_dir = "/home/johnny5/Johny5Alive/j5a-nightshift/ops/outputs"
    os.makedirs(test_dir, exist_ok=True)

    code_file = os.path.join(test_dir, "test_code.py")
    with open(code_file, 'w') as f:
        f.write('''def calculate_total(items: list[dict]) -> float:
    """Calculate total from items with quantity and price."""
    total = 0.0
    for item in items:
        total += item.get('quantity', 0) * item.get('price', 0.0)
    return total
''')

    # Create test file
    test_file = os.path.join(test_dir, "test_test_code.py")
    with open(test_file, 'w') as f:
        f.write('''from test_code import calculate_total

def test_calculate_total():
    items = [
        {'quantity': 2, 'price': 10.0},
        {'quantity': 3, 'price': 5.0}
    ]
    assert calculate_total(items) == 35.0

def test_calculate_total_empty():
    assert calculate_total([]) == 0.0
''')

    # Run validation
    print("Testing code validator...")
    validator = CodeValidator()
    print(f"Tools available: {validator.tools_available}")

    result = validator.validate(code_file, test_file)

    print("\n" + "="*60)
    print("VALIDATION RESULT:")
    print("="*60)
    print(f"Success: {result['success']}")
    print(f"Ruff: {result['ruff_passed']}")
    print(f"Mypy: {result['mypy_passed']}")
    print(f"Pytest: {result['pytest_passed']}")

    if result['errors']:
        print(f"\nErrors: {result['errors']}")

    for tool, output in result['details'].items():
        if output:
            print(f"\n{tool.upper()} Output:")
            print(output[:500])  # First 500 chars
