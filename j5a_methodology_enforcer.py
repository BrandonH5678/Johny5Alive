#!/usr/bin/env python3
"""
J5A Methodology Enforcer
Prevents deviation from approved approaches and shortcuts under difficulty

Addresses Claude tendency to abandon best practices when encountering obstacles
"""

import re
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from j5a_work_assignment import J5AWorkAssignment


class ComplianceStatus(Enum):
    """Methodology compliance status"""
    COMPLIANT = "compliant"
    VIOLATION = "violation"
    WARNING = "warning"


@dataclass
class ComplianceResult:
    """Result of methodology compliance check"""
    status: ComplianceStatus
    compliant: bool
    violations: List[str]
    warnings: List[str]
    details: Dict[str, any]


class MethodologyEnforcer:
    """
    Enforces approved methodologies and prevents shortcuts

    Key principles:
    1. Must use approved architectures (extend existing, don't replace)
    2. Must not use forbidden patterns (shortcuts, workarounds)
    3. Must maintain quality standards even when difficult
    4. Must escalate obstacles, not degrade methodology
    """

    # Domain-specific approved methodologies
    APPROVED_METHODOLOGIES = {
        "audio_processing": {
            "approved_architectures": ["VoiceEngineManager", "IntelligentModelSelector"],
            "must_extend": "VoiceEngineManager",
            "forbidden_patterns": [
                r"whisper\.load_model\(",  # Must use IntelligentModelSelector
                r"class\s+\w*Processor\b(?!.*\(VoiceEngineManager\))",  # Must extend VoiceEngineManager
                r"subprocess\.run.*ffmpeg.*(?!capture_output)",  # Must use proper error handling
                r"#\s*TODO.*validation",  # No deferred validation
            ],
            "required_patterns": [
                r"from.*intelligent_model_selector.*import",  # Must import intelligent selector
                r"IntelligentModelSelector\(",  # Must use selector
            ]
        },
        "database_operations": {
            "approved_architectures": ["EvidenceDatabase"],
            "must_extend": "EvidenceDatabase",
            "forbidden_patterns": [
                r"cursor\.execute\(",  # Must use ORM, not raw SQL
                r"#\s*TODO.*validate",  # No deferred validation
                r"\.get_\w+\(\).*#.*assume",  # No assumptions about API methods
            ],
            "required_patterns": [
                r"from.*evidence_database.*import",
            ]
        },
        "general": {
            "forbidden_patterns": [
                r"except:\s*pass",  # No silent error swallowing
                r"except\s+Exception:\s*pass",  # No silent exception swallowing
                r"#\s*TODO.*later",  # No deferred work
                r"#\s*HACK",  # No hacks
                r"#\s*FIXME.*later",  # No deferred fixes
            ]
        }
    }

    def __init__(self):
        self.logger = logging.getLogger("MethodologyEnforcer")

    def validate_implementation(self, task: J5AWorkAssignment,
                               implementation_code: str,
                               file_path: Optional[Path] = None) -> ComplianceResult:
        """
        Validate implementation complies with approved methodology

        Args:
            task: Work assignment with methodology requirements
            implementation_code: Code to validate
            file_path: Optional file path for context

        Returns:
            ComplianceResult with violations/warnings
        """
        self.logger.info(f"🔍 Validating methodology compliance for: {task.task_name}")

        violations = []
        warnings = []
        details = {}

        # Get domain-specific rules
        domain_rules = self.APPROVED_METHODOLOGIES.get(task.domain, {})
        general_rules = self.APPROVED_METHODOLOGIES.get("general", {})

        # Check 1: Forbidden patterns (shortcuts)
        forbidden_violations = self._check_forbidden_patterns(
            implementation_code,
            domain_rules.get("forbidden_patterns", []) + general_rules.get("forbidden_patterns", []),
            task.forbidden_patterns
        )
        violations.extend(forbidden_violations)
        details["forbidden_pattern_violations"] = forbidden_violations

        # Check 2: Required patterns (must use approved approaches)
        required_violations = self._check_required_patterns(
            implementation_code,
            domain_rules.get("required_patterns", [])
        )
        violations.extend(required_violations)
        details["required_pattern_violations"] = required_violations

        # Check 3: Architecture compliance
        architecture_violations = self._check_architecture_compliance(
            implementation_code,
            task.approved_architectures,
            task.extends_existing_class
        )
        violations.extend(architecture_violations)
        details["architecture_violations"] = architecture_violations

        # Check 4: Quality degradation patterns
        degradation_warnings = self._check_quality_degradation(implementation_code, task.domain)
        warnings.extend(degradation_warnings)
        details["quality_degradation_warnings"] = degradation_warnings

        # Determine overall status
        if violations:
            status = ComplianceStatus.VIOLATION
            compliant = False
            self.logger.error(f"❌ Methodology violations detected: {len(violations)}")
        elif warnings:
            status = ComplianceStatus.WARNING
            compliant = True  # Warnings don't block, but should be reviewed
            self.logger.warning(f"⚠️  Methodology warnings: {len(warnings)}")
        else:
            status = ComplianceStatus.COMPLIANT
            compliant = True
            self.logger.info("✅ Methodology compliance verified")

        return ComplianceResult(
            status=status,
            compliant=compliant,
            violations=violations,
            warnings=warnings,
            details=details
        )

    def _check_forbidden_patterns(self, code: str, forbidden_patterns: List[str],
                                  task_forbidden: List[str]) -> List[str]:
        """
        Check for forbidden patterns (shortcuts, workarounds)

        These are patterns that indicate Claude is taking shortcuts
        rather than using approved methodologies
        """
        violations = []
        all_forbidden = forbidden_patterns + task_forbidden

        for pattern in all_forbidden:
            matches = re.finditer(pattern, code, re.MULTILINE)
            for match in matches:
                line_num = code[:match.start()].count('\n') + 1
                violation = f"Forbidden pattern at line {line_num}: {pattern}"
                violations.append(violation)
                self.logger.warning(f"🚫 {violation}")

        return violations

    def _check_required_patterns(self, code: str, required_patterns: List[str]) -> List[str]:
        """
        Check for required patterns (must use approved approaches)

        These patterns MUST be present if using certain functionality
        """
        violations = []

        for pattern in required_patterns:
            if not re.search(pattern, code, re.MULTILINE):
                violation = f"Missing required pattern: {pattern}"
                violations.append(violation)
                self.logger.warning(f"⚠️  {violation}")

        return violations

    def _check_architecture_compliance(self, code: str, approved_architectures: List[str],
                                      must_extend: Optional[str]) -> List[str]:
        """
        Check if implementation extends approved architecture

        Claude tends to create standalone implementations rather than
        extending existing architectures when encountering difficulties
        """
        violations = []

        # If must extend specific class, verify
        if must_extend:
            # Look for class definition that extends required class
            extends_pattern = rf"class\s+\w+\({must_extend}\)"
            if not re.search(extends_pattern, code):
                violation = f"Must extend {must_extend}, not create standalone implementation"
                violations.append(violation)
                self.logger.error(f"❌ {violation}")

        # Check for approved architecture usage
        if approved_architectures:
            has_approved = False
            for arch in approved_architectures:
                if arch in code:
                    has_approved = True
                    break

            if not has_approved and must_extend:
                violation = f"Must use approved architectures: {', '.join(approved_architectures)}"
                violations.append(violation)

        return violations

    def _check_quality_degradation(self, code: str, domain: str) -> List[str]:
        """
        Check for patterns indicating quality degradation

        These are "easier but worse" patterns that Claude might adopt
        when encountering difficulties
        """
        warnings = []

        # Pattern 1: Overly broad exception handling
        if re.search(r"except\s+(Exception|BaseException):", code):
            matches = re.finditer(r"except\s+(Exception|BaseException):", code)
            for match in matches:
                line_num = code[:match.start()].count('\n') + 1
                # Check if exception is being logged/handled properly
                # Get next 5 lines after except
                lines_after = code[match.end():].split('\n')[:5]
                if not any(('log' in line or 'print' in line or 'raise' in line)
                          for line in lines_after):
                    warnings.append(
                        f"Line {line_num}: Broad exception handling without logging/re-raising"
                    )

        # Pattern 2: TODOs indicating deferred work
        todo_matches = re.finditer(r"#\s*TODO:?\s*(.+)", code)
        for match in todo_matches:
            line_num = code[:match.start()].count('\n') + 1
            todo_text = match.group(1).strip()
            if any(word in todo_text.lower() for word in ['later', 'fix', 'improve', 'hack']):
                warnings.append(f"Line {line_num}: TODO indicating deferred work: {todo_text}")

        # Pattern 3: Commented-out code (might indicate abandoned approaches)
        commented_code_lines = [i + 1 for i, line in enumerate(code.split('\n'))
                               if line.strip().startswith('#') and
                               len(line.strip()) > 2 and
                               not line.strip().startswith('# ') and
                               not 'TODO' in line and
                               not 'NOTE' in line and
                               not 'FIXME' in line]
        if commented_code_lines and len(commented_code_lines) > 5:
            warnings.append(
                f"Excessive commented-out code ({len(commented_code_lines)} lines) - "
                f"may indicate abandoned approaches"
            )

        return warnings

    def validate_file(self, task: J5AWorkAssignment, file_path: Path) -> ComplianceResult:
        """Validate a file's methodology compliance"""
        if not file_path.exists():
            return ComplianceResult(
                status=ComplianceStatus.VIOLATION,
                compliant=False,
                violations=[f"File not found: {file_path}"],
                warnings=[],
                details={}
            )

        with open(file_path, 'r') as f:
            code = f.read()

        return self.validate_implementation(task, code, file_path)

    def validate_multiple_files(self, task: J5AWorkAssignment,
                               file_paths: List[Path]) -> ComplianceResult:
        """Validate multiple files' methodology compliance"""
        all_violations = []
        all_warnings = []
        all_details = {}

        for file_path in file_paths:
            result = self.validate_file(task, file_path)
            all_violations.extend(
                [f"{file_path.name}: {v}" for v in result.violations]
            )
            all_warnings.extend(
                [f"{file_path.name}: {w}" for w in result.warnings]
            )
            all_details[str(file_path)] = result.details

        if all_violations:
            status = ComplianceStatus.VIOLATION
            compliant = False
        elif all_warnings:
            status = ComplianceStatus.WARNING
            compliant = True
        else:
            status = ComplianceStatus.COMPLIANT
            compliant = True

        return ComplianceResult(
            status=status,
            compliant=compliant,
            violations=all_violations,
            warnings=all_warnings,
            details=all_details
        )


class DifficultyEscalationProtocol:
    """
    Handles obstacles by escalating, not degrading methodology

    When Claude encounters difficulties, this protocol ensures
    approved methodologies are maintained
    """

    def __init__(self):
        self.logger = logging.getLogger("DifficultyEscalation")

    def handle_obstacle(self, task: J5AWorkAssignment, obstacle_type: str,
                       obstacle_description: str) -> Dict[str, any]:
        """
        Handle implementation obstacle while maintaining standards

        Returns recommended action (never shortcuts)
        """
        self.logger.warning(f"⚠️  Obstacle encountered: {obstacle_type}")
        self.logger.info(f"Description: {obstacle_description}")

        if obstacle_type == "technical_difficulty":
            return self._handle_technical_difficulty(task, obstacle_description)
        elif obstacle_type == "resource_constraint":
            return self._handle_resource_constraint(task, obstacle_description)
        elif obstacle_type == "api_unavailable":
            return self._handle_api_unavailable(task, obstacle_description)
        elif obstacle_type == "test_failure":
            return self._handle_test_failure(task, obstacle_description)
        else:
            return self._handle_unknown_obstacle(task, obstacle_description)

    def _handle_technical_difficulty(self, task: J5AWorkAssignment,
                                    description: str) -> Dict:
        """
        Technical difficulty: Research solution, don't shortcut

        ❌ WRONG: Abandon approved methodology for "easier" approach
        ✅ RIGHT: Research compliant solution or escalate to human
        """
        return {
            "action": "research_compliant_solution",
            "maintain_methodology": True,
            "shortcut_allowed": False,
            "escalate_if_no_solution": True,
            "message": "Research solution maintaining approved methodology. "
                      "If no compliant solution found, escalate to human."
        }

    def _handle_resource_constraint(self, task: J5AWorkAssignment,
                                   description: str) -> Dict:
        """
        Resource constraint: Adjust scope, don't lower quality

        ❌ WRONG: Skip validation or reduce quality standards
        ✅ RIGHT: Reduce scope while maintaining quality
        """
        return {
            "action": "reduce_scope_maintain_quality",
            "maintain_methodology": True,
            "shortcut_allowed": False,
            "message": "Reduce task scope while maintaining quality standards. "
                      "Process fewer items but maintain validation rigor."
        }

    def _handle_api_unavailable(self, task: J5AWorkAssignment,
                               description: str) -> Dict:
        """
        API unavailable: Find alternative or escalate, don't bypass validation

        ❌ WRONG: Skip API validation or assume methods work
        ✅ RIGHT: Find alternative API or escalate
        """
        return {
            "action": "find_alternative_or_escalate",
            "maintain_methodology": True,
            "shortcut_allowed": False,
            "escalate_to_human": True,
            "message": "API unavailable - find compliant alternative or escalate. "
                      "Do not bypass validation."
        }

    def _handle_test_failure(self, task: J5AWorkAssignment,
                            description: str) -> Dict:
        """
        Test failure: Fix root cause, don't disable tests

        ❌ WRONG: Comment out failing test or skip validation
        ✅ RIGHT: Fix implementation to pass test
        """
        return {
            "action": "fix_root_cause",
            "maintain_methodology": True,
            "shortcut_allowed": False,
            "message": "Test failure - fix implementation, do not disable test. "
                      "Tests protect against regressions."
        }

    def _handle_unknown_obstacle(self, task: J5AWorkAssignment,
                                 description: str) -> Dict:
        """
        Unknown obstacle: STOP and escalate

        ❌ WRONG: Guess at solution or try shortcuts
        ✅ RIGHT: Stop and escalate to human
        """
        return {
            "action": "stop_and_escalate",
            "maintain_methodology": True,
            "shortcut_allowed": False,
            "escalate_to_human": True,
            "blocking": True,
            "message": "Unknown obstacle - STOP and escalate. "
                      "Do not proceed without human guidance."
        }


if __name__ == "__main__":
    # Test methodology enforcer
    from j5a_work_assignment import create_example_task

    print("🔍 Testing J5A Methodology Enforcer")
    print("=" * 80)

    # Create test task
    task = create_example_task()
    task.domain = "audio_processing"

    # Create enforcer
    enforcer = MethodologyEnforcer()

    # Test 1: Compliant code
    print("\n✅ Test 1: Compliant code")
    compliant_code = """
from intelligent_model_selector import IntelligentModelSelector

class GladioProcessor(VoiceEngineManager):
    def __init__(self):
        super().__init__()
        self.selector = IntelligentModelSelector()

    def process(self):
        selection = self.selector.select_model()
        return self.transcribe(selection)
"""
    result = enforcer.validate_implementation(task, compliant_code)
    print(f"Status: {result.status.value}")
    print(f"Compliant: {result.compliant}")
    print(f"Violations: {len(result.violations)}")

    # Test 2: Non-compliant code (shortcut)
    print("\n❌ Test 2: Non-compliant code (shortcut detected)")
    noncompliant_code = """
import whisper

class DirectProcessor:  # ❌ Not extending VoiceEngineManager
    def __init__(self):
        self.model = whisper.load_model("large-v3")  # ❌ Not using IntelligentModelSelector

    def process(self):
        try:
            return self.model.transcribe("file.wav")
        except:  # ❌ Silent error swallowing
            pass
"""
    result = enforcer.validate_implementation(task, noncompliant_code)
    print(f"Status: {result.status.value}")
    print(f"Compliant: {result.compliant}")
    print(f"Violations: {len(result.violations)}")
    for violation in result.violations:
        print(f"  - {violation}")

    # Test 3: Difficulty escalation
    print("\n⚠️  Test 3: Difficulty escalation protocol")
    escalation = DifficultyEscalationProtocol()

    obstacle = escalation.handle_obstacle(
        task,
        "technical_difficulty",
        "Cannot figure out how to extend VoiceEngineManager"
    )
    print(f"Action: {obstacle['action']}")
    print(f"Maintain methodology: {obstacle['maintain_methodology']}")
    print(f"Shortcut allowed: {obstacle['shortcut_allowed']}")
    print(f"Message: {obstacle['message']}")

    print("\n" + "=" * 80)
    print("✅ Methodology enforcer tests complete")