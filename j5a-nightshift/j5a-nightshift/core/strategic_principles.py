#!/usr/bin/env python3
"""
J5A Strategic Principles - Core principle enforcement module

Constitutional Authority: J5A_CONSTITUTION.md
Strategic Framework: J5A_STRATEGIC_AI_PRINCIPLES.md

Implements the 10 Strategic AI Principles for J5A operations.

Constitutional Compliance:
- Principle 2 (Transparency): Principle validation is auditable
- Principle 8 (Governance): All operations checked against principles
"""

from typing import Dict, List, Any
from enum import Enum


class StrategicPrinciple(Enum):
    """The 10 Strategic AI Principles"""
    TOOL_AUGMENTED_REASONING = 1      # Move from telling to doing
    AGENT_ORCHESTRATION = 2            # Specialized sub-agents
    CONTEXT_ENGINEERING = 3            # Optimize context window usage
    ACTIVE_MEMORY = 4                  # Persistent knowledge
    ADAPTIVE_FEEDBACK = 5              # Human-in-the-loop refinement
    MULTI_MODAL = 6                    # Text + code + audio + more
    AUTONOMOUS_WORKFLOWS = 7           # Night Shift operations
    GOVERNANCE_FRAMEWORKS = 8          # Accountability and auditability
    LOCAL_LLM_OPTIMIZATION = 9         # Hardware-appropriate models
    STRATEGIC_AI_LITERACY = 10         # Treat AI as collaborator


class PrincipleValidator:
    """
    Validates operations against Strategic Principles

    Constitutional Alignment:
    - Principle 2: Transparent validation
    - Principle 8: Governance enforcement
    """

    def __init__(self):
        self.principles = {
            StrategicPrinciple.TOOL_AUGMENTED_REASONING: self._validate_tool_reasoning,
            StrategicPrinciple.AGENT_ORCHESTRATION: self._validate_agent_orchestration,
            StrategicPrinciple.CONTEXT_ENGINEERING: self._validate_context_engineering,
            StrategicPrinciple.ACTIVE_MEMORY: self._validate_active_memory,
            StrategicPrinciple.ADAPTIVE_FEEDBACK: self._validate_adaptive_feedback,
            StrategicPrinciple.MULTI_MODAL: self._validate_multi_modal,
            StrategicPrinciple.AUTONOMOUS_WORKFLOWS: self._validate_autonomous,
            StrategicPrinciple.GOVERNANCE_FRAMEWORKS: self._validate_governance,
            StrategicPrinciple.LOCAL_LLM_OPTIMIZATION: self._validate_llm_optimization,
            StrategicPrinciple.STRATEGIC_AI_LITERACY: self._validate_ai_literacy,
        }

    def validate_operation(self, operation: Dict[str, Any],
                          principles: List[StrategicPrinciple]) -> Dict[str, Any]:
        """
        Validate operation against specified principles

        Args:
            operation: Operation definition
            principles: List of principles to check

        Returns:
            Validation result with pass/fail and recommendations
        """
        results = {}
        all_passed = True

        for principle in principles:
            validator = self.principles.get(principle)
            if validator:
                result = validator(operation)
                results[principle.name] = result
                if not result['passes']:
                    all_passed = False

        return {
            'passes': all_passed,
            'principle_checks': results,
            'recommendations': self._generate_recommendations(results)
        }

    def _validate_tool_reasoning(self, op: Dict) -> Dict:
        """Principle 1: Tool-Augmented Reasoning"""
        # Check if operation executes vs just describes
        has_execution = op.get('executes', False)
        has_tools = len(op.get('tools', [])) > 0

        passes = has_execution or has_tools

        return {
            'passes': passes,
            'reason': 'Operation executes tasks' if passes else 'Operation only describes, does not execute',
            'recommendations': [] if passes else ['Add tool execution to operation']
        }

    def _validate_agent_orchestration(self, op: Dict) -> Dict:
        """Principle 2: Agent Orchestration"""
        # Check for clear agent roles
        has_agents = 'agents' in op
        agents_bounded = all(a.get('mission') and a.get('output_contract')
                           for a in op.get('agents', []))

        passes = has_agents and agents_bounded

        return {
            'passes': passes,
            'reason': 'Agents have bounded missions' if passes else 'Missing agent boundaries',
            'recommendations': [] if passes else ['Define agent missions and output contracts']
        }

    def _validate_context_engineering(self, op: Dict) -> Dict:
        """Principle 3: Context Engineering"""
        # Check for efficient context usage
        has_context_limit = 'max_context_tokens' in op
        filters_context = op.get('context_filtering', False)

        passes = has_context_limit or filters_context

        return {
            'passes': passes,
            'reason': 'Context optimized' if passes else 'Context not optimized',
            'recommendations': [] if passes else ['Add context limits and filtering']
        }

    def _validate_active_memory(self, op: Dict) -> Dict:
        """Principle 4: Active Memory"""
        # Check for persistent knowledge
        has_memory = op.get('uses_memory', False)
        persists_knowledge = op.get('persists_knowledge', False)

        passes = has_memory or persists_knowledge

        return {
            'passes': True,  # Not all operations need memory
            'reason': 'Memory integration present' if (has_memory or persists_knowledge) else 'No memory integration',
            'recommendations': ['Consider adding knowledge persistence'] if not (has_memory or persists_knowledge) else []
        }

    def _validate_adaptive_feedback(self, op: Dict) -> Dict:
        """Principle 5: Adaptive Feedback Loops"""
        # Check for feedback mechanisms
        has_feedback = op.get('feedback_enabled', False)
        has_self_critique = op.get('self_critique', False)

        passes = True  # Optional for most operations

        return {
            'passes': passes,
            'reason': 'Feedback loops present' if (has_feedback or has_self_critique) else 'No feedback loops',
            'recommendations': ['Consider adding feedback mechanisms'] if not (has_feedback or has_self_critique) else []
        }

    def _validate_multi_modal(self, op: Dict) -> Dict:
        """Principle 6: Multi-Modal Integration"""
        # Check for multi-modal support
        modalities = op.get('modalities', ['text'])
        is_multi_modal = len(modalities) > 1

        passes = True  # Not all operations need multi-modal

        return {
            'passes': passes,
            'reason': f'Supports {len(modalities)} modalities' if is_multi_modal else 'Single modality',
            'recommendations': []
        }

    def _validate_autonomous(self, op: Dict) -> Dict:
        """Principle 7: Autonomous Workflows"""
        # Check for autonomous operation support
        can_run_autonomous = op.get('autonomous_capable', False)
        has_safety_gates = op.get('safety_gates', False)

        passes = True  # Not all operations need autonomy

        return {
            'passes': passes,
            'reason': 'Autonomous workflow support' if can_run_autonomous else 'Manual operation',
            'recommendations': ['Consider autonomous operation support'] if not can_run_autonomous else []
        }

    def _validate_governance(self, op: Dict) -> Dict:
        """Principle 8: Governance & Alignment"""
        # Check for governance requirements
        has_audit_trail = op.get('audit_trail', False)
        has_const_review = op.get('constitutional_review', False)

        passes = has_audit_trail or has_const_review

        return {
            'passes': passes,
            'reason': 'Governance framework present' if passes else 'Missing governance',
            'recommendations': [] if passes else ['Add audit trail and constitutional review']
        }

    def _validate_llm_optimization(self, op: Dict) -> Dict:
        """Principle 9: Local LLM Optimization"""
        # Check for appropriate model selection
        has_model_selection = 'model' in op
        considers_resources = op.get('resource_aware', False)

        passes = True  # Not all operations use LLMs

        return {
            'passes': passes,
            'reason': 'Model selection appropriate' if has_model_selection else 'No LLM usage',
            'recommendations': ['Consider resource-aware model selection'] if has_model_selection and not considers_resources else []
        }

    def _validate_ai_literacy(self, op: Dict) -> Dict:
        """Principle 10: Strategic AI Literacy"""
        # Check for learning opportunities
        documents_learning = op.get('documents_learning', False)
        enables_experimentation = op.get('experimental', False)

        passes = True  # Soft requirement

        return {
            'passes': passes,
            'reason': 'Learning documented' if documents_learning else 'No learning documentation',
            'recommendations': ['Consider documenting learnings from operation'] if not documents_learning else []
        }

    def _generate_recommendations(self, results: Dict) -> List[str]:
        """Generate consolidated recommendations"""
        recommendations = []
        for principle_name, result in results.items():
            recommendations.extend(result.get('recommendations', []))
        return list(set(recommendations))  # Remove duplicates


def get_principle_description(principle: StrategicPrinciple) -> str:
    """Get description of a strategic principle"""
    descriptions = {
        StrategicPrinciple.TOOL_AUGMENTED_REASONING: "Move from telling to doing - execute with tools",
        StrategicPrinciple.AGENT_ORCHESTRATION: "Use specialized sub-agents with bounded missions",
        StrategicPrinciple.CONTEXT_ENGINEERING: "Optimize context window usage for efficiency",
        StrategicPrinciple.ACTIVE_MEMORY: "Maintain persistent knowledge across sessions",
        StrategicPrinciple.ADAPTIVE_FEEDBACK: "Incorporate human feedback and self-critique",
        StrategicPrinciple.MULTI_MODAL: "Integrate text, code, audio, and visual processing",
        StrategicPrinciple.AUTONOMOUS_WORKFLOWS: "Support unattended Night Shift operations",
        StrategicPrinciple.GOVERNANCE_FRAMEWORKS: "Ensure accountability and auditability",
        StrategicPrinciple.LOCAL_LLM_OPTIMIZATION: "Select hardware-appropriate models",
        StrategicPrinciple.STRATEGIC_AI_LITERACY: "Treat AI as collaborator, document learnings"
    }
    return descriptions.get(principle, "Unknown principle")


# Example usage
if __name__ == "__main__":
    validator = PrincipleValidator()

    # Example operation
    operation = {
        'name': 'process_podcast',
        'executes': True,
        'tools': ['whisper', 'database'],
        'audit_trail': True,
        'uses_memory': True,
        'autonomous_capable': True,
        'safety_gates': True
    }

    # Validate against relevant principles
    result = validator.validate_operation(
        operation,
        [
            StrategicPrinciple.TOOL_AUGMENTED_REASONING,
            StrategicPrinciple.GOVERNANCE_FRAMEWORKS,
            StrategicPrinciple.AUTONOMOUS_WORKFLOWS
        ]
    )

    print(f"Validation passed: {result['passes']}")
    print(f"Recommendations: {result['recommendations']}")
