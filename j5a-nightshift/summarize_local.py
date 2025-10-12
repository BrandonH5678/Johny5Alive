#!/usr/bin/env python3
"""
Local LLM Summarization - Evidence-based synthesis with excerpt citation
Uses llm_gateway for unified local/remote/API LLM access
"""

import os
import json
import yaml
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

# Import nightshift components
from llm_gateway import LLMGateway, LLMMode, retry_with_backoff
from sherlock_chunk import select_excerpts

logger = logging.getLogger(__name__)


def summarize(
    excerpts_path: str,
    output_path: Optional[str] = None,
    mode: LLMMode = LLMMode.LOCAL,
    max_excerpts: int = 10,
    max_tokens_input: int = 3000
) -> str:
    """
    Generate summary from excerpts using local LLM

    Args:
        excerpts_path: Path to chunks.json file from sherlock_chunk.py
        output_path: Path to save summary.md (default: ops/outputs/)
        mode: LLM mode (local/remote/api)
        max_excerpts: Maximum excerpts to include
        max_tokens_input: Maximum input tokens for LLM context

    Returns:
        Path to generated summary.md file

    Raises:
        ValueError: If INSUFFICIENT_EVIDENCE or validation fails
    """
    # Load config
    config_path = "/home/johnny5/Johny5Alive/j5a-nightshift/rules.yaml"
    with open(config_path) as f:
        config = yaml.safe_load(f)

    # Load contract
    contract_path = "/home/johnny5/Johny5Alive/j5a-nightshift/contracts/summary_contract.txt"
    with open(contract_path) as f:
        contract = f.read()

    # Select excerpts
    excerpts = select_excerpts(excerpts_path, max_excerpts=max_excerpts, max_tokens=max_tokens_input)

    if not excerpts:
        raise ValueError("No excerpts available for summarization")

    logger.info(f"Summarizing {len(excerpts)} excerpts via {mode.value} LLM")

    # Initialize gateway
    gateway = LLMGateway(mode=mode, config=config)

    # Generate summary with retry
    def generate():
        return gateway.complete(
            instructions=contract,
            excerpts=excerpts,
            limits={"max_output": config["llm"]["max_output"]}
        )

    summary_text = retry_with_backoff(generate, retries=config["processing"]["retries"])

    # Validate output
    if summary_text.strip() == "INSUFFICIENT_EVIDENCE":
        raise ValueError("LLM determined evidence is insufficient for summarization")

    # Count excerpt citations
    cited_excerpts = _count_citations(summary_text, excerpts)

    if cited_excerpts < 3:
        logger.warning(f"Only {cited_excerpts} excerpts cited (minimum: 3)")
        # In Phase 1, we allow this but log it
        # In Phase 2, could fail validation

    # Save output
    if output_path is None:
        output_dir = "/home/johnny5/Johny5Alive/j5a-nightshift/ops/outputs"
        os.makedirs(output_dir, exist_ok=True)

        # Generate filename from source
        with open(excerpts_path) as f:
            data = json.load(f)
        source_name = Path(data["source"]).stem

        output_path = os.path.join(output_dir, f"{source_name}_summary.md")

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(summary_text)

    logger.info(f"Summary saved to {output_path} ({cited_excerpts} excerpts cited)")
    return output_path


def _count_citations(text: str, excerpts: List[Dict[str, Any]]) -> int:
    """
    Count how many distinct excerpts are cited in the summary

    Simple check: look for quoted phrases from excerpts in the summary text
    """
    cited = 0

    for excerpt in excerpts:
        # Check if any substantial phrase from excerpt appears quoted in summary
        excerpt_text = excerpt["text"]

        # Extract sentences from excerpt
        sentences = [s.strip() for s in excerpt_text.split('.') if len(s.strip()) > 20]

        # Check if any sentence appears quoted in summary
        for sentence in sentences[:3]:  # Check first 3 sentences
            # Look for quotes of 10+ words from this sentence
            words = sentence.split()
            for i in range(len(words) - 10):
                phrase = ' '.join(words[i:i+10])
                if phrase.lower() in text.lower():
                    cited += 1
                    break  # This excerpt is cited, move to next
            if cited > 0:
                break

    return min(cited, len(excerpts))  # Cap at number of excerpts


# Example usage and testing
if __name__ == "__main__":
    import sys

    logging.basicConfig(level=logging.INFO)

    # Check for test mode
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        print("Running in test mode (mock data)...")

        # Create test chunks file
        test_dir = "/home/johnny5/Johny5Alive/j5a-nightshift/ops/processed"
        os.makedirs(test_dir, exist_ok=True)

        chunks_path = os.path.join(test_dir, "test_chunks.json")
        with open(chunks_path, 'w') as f:
            json.dump({
                "source": "test_document.txt",
                "total_chunks": 3,
                "chunks": [
                    {
                        "id": 0,
                        "start": 0,
                        "end": 200,
                        "text": "Python is a high-level interpreted programming language created by Guido van Rossum. It emphasizes code readability.",
                        "score": 0.95,
                        "tokens_estimate": 50
                    },
                    {
                        "id": 1,
                        "start": 200,
                        "end": 400,
                        "text": "Python supports multiple programming paradigms including procedural, object-oriented, and functional programming.",
                        "score": 0.88,
                        "tokens_estimate": 50
                    },
                    {
                        "id": 2,
                        "start": 400,
                        "end": 600,
                        "text": "Python is widely used in web development, data science, machine learning, and automation.",
                        "score": 0.82,
                        "tokens_estimate": 50
                    }
                ]
            }, f)

        print(f"Test chunks created: {chunks_path}")

        # Try to generate summary
        try:
            summary_path = summarize(chunks_path, mode=LLMMode.LOCAL)
            print(f"\nSummary generated: {summary_path}")

            # Display summary
            with open(summary_path) as f:
                print("\n" + "="*60)
                print("SUMMARY:")
                print("="*60)
                print(f.read())
                print("="*60)

        except Exception as e:
            print(f"\nSummarization failed: {e}")
            print("\nThis is expected if Ollama is not running yet.")
            print("Once model download completes, run:")
            print("  ollama serve &")
            print("  python3 summarize_local.py --test")

    else:
        print("Usage: python3 summarize_local.py --test")
        print("\nOr import and use programmatically:")
        print("  from summarize_local import summarize")
        print("  summary_path = summarize('chunks.json')")
