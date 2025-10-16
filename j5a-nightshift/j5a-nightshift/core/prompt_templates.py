#!/usr/bin/env python3
"""
Prompt Template System

Provides constitutional and principle-aligned prompt templates.
"""

from typing import Dict, Any
from pathlib import Path


class PromptTemplateManager:
    """
    Manage prompt templates with constitutional alignment
    """

    def __init__(self, template_dir: str = "templates"):
        self.template_dir = Path(template_dir)
        self.template_dir.mkdir(parents=True, exist_ok=True)

    def get_template(self, template_name: str) -> str:
        """Load template by name"""
        template_file = self.template_dir / f"{template_name}.md"

        if not template_file.exists():
            return self._get_default_template()

        with open(template_file, 'r') as f:
            return f.read()

    def render_template(self, template_name: str,
                       variables: Dict[str, Any]) -> str:
        """Render template with variables"""
        template = self.get_template(template_name)

        # Simple variable substitution
        for key, value in variables.items():
            template = template.replace(f"{{{key}}}", str(value))

        return template

    def _get_default_template(self) -> str:
        """Default template"""
        return """# Task

## Context
{context}

## Instructions
{instructions}

## Output Requirements
{output_requirements}
"""
