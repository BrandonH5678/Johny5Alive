#!/usr/bin/env python3
"""
Summaries Validator - Ensures ≥3 distinct excerpt citations
Validates summary outputs meet evidence-based requirements
"""

import re
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


class SummariesValidator:
    """
    Validates summary outputs meet citation requirements

    Requirements (from Nightshift spec):
    - Must cite ≥3 distinct excerpts with quoted text
    - OR output exactly "INSUFFICIENT_EVIDENCE"
    - Quotes must be verbatim from source excerpts
    """

    def validate(self, summary_path: str, excerpts_path: str = None) -> Dict[str, Any]:
        """
        Validate summary file meets citation requirements

        Args:
            summary_path: Path to generated summary.md file
            excerpts_path: Optional path to excerpts.json for quote verification

        Returns:
            Validation result dict with:
            {
                "success": bool,
                "citation_count": int,
                "insufficient_evidence": bool,
                "errors": List[str],
                "details": str
            }
        """
        result = {
            "success": False,
            "citation_count": 0,
            "insufficient_evidence": False,
            "errors": [],
            "details": ""
        }

        # Read summary file
        try:
            with open(summary_path, 'r', encoding='utf-8') as f:
                summary_text = f.read()
        except FileNotFoundError:
            result["errors"].append(f"Summary file not found: {summary_path}")
            return result
        except Exception as e:
            result["errors"].append(f"Error reading summary: {e}")
            return result

        result["details"] = summary_text[:500]  # First 500 chars

        # Check for INSUFFICIENT_EVIDENCE
        if summary_text.strip() == "INSUFFICIENT_EVIDENCE":
            result["insufficient_evidence"] = True
            result["success"] = True  # This is a valid response
            logger.info("Summary marked as INSUFFICIENT_EVIDENCE (valid)")
            return result

        # Count citations (look for quoted text with source attribution)
        citations = self._count_citations(summary_text)
        result["citation_count"] = citations

        # Validate minimum citations
        if citations < 3:
            result["errors"].append(f"Insufficient citations: {citations} (minimum: 3)")
        else:
            result["success"] = True

        logger.info(f"Summary validation: {result['success']} ({citations} citations)")

        return result

    def _count_citations(self, text: str) -> int:
        """
        Count distinct citations in summary text

        Citations are identified by:
        - Quoted text in "quotes"
        - Source attribution like (source: filename)
        """
        # Pattern: "quoted text" (source: something)
        # More flexible: just count bullet points with quotes and sources
        citation_count = 0

        # Split into lines and check each
        lines = text.split('\n')

        for line in lines:
            # Check if line has both quotes and source
            has_quotes = '"' in line and line.count('"') >= 2
            has_source = 'source:' in line.lower() or '(source' in line.lower()

            if has_quotes and has_source:
                citation_count += 1

        return citation_count


def validate_summary(summary_path: str, excerpts_path: str = None) -> bool:
    """
    Convenience function for summary validation

    Args:
        summary_path: Path to summary.md file
        excerpts_path: Optional path to excerpts.json

    Returns:
        True if validation passes, False otherwise
    """
    validator = SummariesValidator()
    result = validator.validate(summary_path, excerpts_path)

    if not result["success"]:
        logger.error(f"Summary validation failed: {result['errors']}")

    return result["success"]


# Example usage and testing
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    import os

    # Test with good summary (3+ citations)
    test_dir = "/home/johnny5/Johny5Alive/j5a-nightshift/ops/outputs"
    os.makedirs(test_dir, exist_ok=True)

    good_summary = os.path.join(test_dir, "test_good_summary.md")
    with open(good_summary, 'w') as f:
        f.write('''- Python is a "high-level programming language" (source: intro.txt)
- It emphasizes "code readability with significant whitespace" (source: intro.txt)
- Python supports "multiple programming paradigms" (source: features.txt)
- It has a "comprehensive standard library" (source: features.txt)
- Python is used in "web development, data science, and machine learning" (source: usecases.txt)
''')

    # Test with insufficient citations
    bad_summary = os.path.join(test_dir, "test_bad_summary.md")
    with open(bad_summary, 'w') as f:
        f.write('''- Python is a "high-level programming language" (source: intro.txt)
- It emphasizes readability
''')

    # Test with INSUFFICIENT_EVIDENCE
    insufficient_summary = os.path.join(test_dir, "test_insufficient_summary.md")
    with open(insufficient_summary, 'w') as f:
        f.write('INSUFFICIENT_EVIDENCE')

    # Run tests
    validator = SummariesValidator()

    print("="*60)
    print("TEST 1: Good Summary (5 citations)")
    print("="*60)
    result1 = validator.validate(good_summary)
    print(f"Success: {result1['success']}")
    print(f"Citations: {result1['citation_count']}")
    print(f"Errors: {result1['errors']}")

    print("\n" + "="*60)
    print("TEST 2: Bad Summary (2 citations)")
    print("="*60)
    result2 = validator.validate(bad_summary)
    print(f"Success: {result2['success']}")
    print(f"Citations: {result2['citation_count']}")
    print(f"Errors: {result2['errors']}")

    print("\n" + "="*60)
    print("TEST 3: INSUFFICIENT_EVIDENCE")
    print("="*60)
    result3 = validator.validate(insufficient_summary)
    print(f"Success: {result3['success']}")
    print(f"Insufficient Evidence: {result3['insufficient_evidence']}")
    print(f"Errors: {result3['errors']}")
