#!/usr/bin/env python3
"""
Context Engineer - Strategic Principle 3

Optimizes context window usage for efficient token consumption
and improved accuracy.
"""

from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)


class ContextEngineer:
    """
    Strategic Principle 3: Context Engineering

    Make every token count - feed only what matters.
    """

    def __init__(self, max_tokens: int = 8000):
        self.max_tokens = max_tokens

    def build_context(self, task: Dict[str, Any],
                     available_docs: List[Dict]) -> str:
        """
        Build optimized context for task

        Args:
            task: Task definition
            available_docs: Available documentation

        Returns:
            Optimized context string
        """
        # Layer 1: System instructions (cached)
        context_parts = [self._get_system_instructions()]

        # Layer 2: Mission context
        context_parts.append(self._format_mission(task))

        # Layer 3: Relevant data only
        relevant_docs = self._filter_relevant(task, available_docs)
        context_parts.append(self._format_docs(relevant_docs))

        # Layer 4: Processing instructions
        context_parts.append(self._format_instructions(task))

        return "\n\n".join(context_parts)

    def _get_system_instructions(self) -> str:
        """Get cached system instructions"""
        return "## System Instructions\n[From CLAUDE.md - J5A principles]"

    def _format_mission(self, task: Dict) -> str:
        """Format mission context"""
        return f"""## Mission
Task: {task.get('name')}
Purpose: {task.get('purpose')}
Human Goal: {task.get('goal')}
"""

    def _filter_relevant(self, task: Dict, docs: List[Dict]) -> List[Dict]:
        """Filter to only relevant documents"""
        # TODO: Implement relevance scoring
        return docs[:5]  # Placeholder

    def _format_docs(self, docs: List[Dict]) -> str:
        """Format documents for context"""
        return "## Input Data\n" + "\n".join(str(d) for d in docs)

    def _format_instructions(self, task: Dict) -> str:
        """Format processing instructions"""
        return f"""## Processing Instructions
{task.get('instructions', 'Process the provided data')}
"""

    def optimize_context(self, context: Any, max_tokens: int = None) -> Any:
        """
        Optimize context to fit within token limits

        Args:
            context: Context to optimize (dict, list, or string)
            max_tokens: Maximum tokens allowed

        Returns:
            Optimized context
        """
        if max_tokens is None:
            max_tokens = self.max_tokens

        # Simple optimization: truncate if needed
        if isinstance(context, dict):
            # Keep only essential keys and optimize their values
            essential_keys = ['data', 'metadata', 'task']
            optimized = {}
            for key in essential_keys:
                if key in context:
                    value = context[key]
                    # Recursively optimize nested structures
                    if isinstance(value, list):
                        # Limit list size
                        max_items = max_tokens // 100
                        optimized[key] = value[:max_items]
                    elif isinstance(value, dict):
                        # Keep dict but limit number of keys
                        items = list(value.items())[:5]
                        optimized[key] = dict(items)
                    else:
                        optimized[key] = value
            return optimized
        elif isinstance(context, list):
            # Keep only first N items
            max_items = max_tokens // 100  # Rough estimate
            return context[:max_items]
        elif isinstance(context, str):
            # Truncate string
            max_chars = max_tokens * 4  # Rough estimate (4 chars per token)
            return context[:max_chars]
        else:
            return context
