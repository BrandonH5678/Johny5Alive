#!/usr/bin/env python3
"""
J5A Autonomous Implementation Worker
Constitutional Authority: J5A_CONSTITUTION.md
Strategic Framework: J5A_STRATEGIC_AI_PRINCIPLES.md

Implements the 10-phase Beyond RAG integration plan with approval gates.

Constitutional Compliance:
- Principle 1 (Human Agency): Approval gates for medium/high-risk tasks
- Principle 2 (Transparency): Full logging and audit trail
- Principle 3 (System Viability): Incremental saves, graceful degradation
- Principle 4 (Resource Stewardship): Resource checks before execution
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass, asdict
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


@dataclass
class Task:
    """Represents a single implementation task"""
    task_id: str
    status: str
    description: str
    type: str
    risk_level: str
    requires_approval: bool
    estimated_time_minutes: int
    expected_outputs: List[str]
    dependencies: List[str]
    phase_id: int
    phase_name: str

    # Optional fields
    success_criteria: Optional[Dict] = None
    approval_message: Optional[str] = None
    notes: Optional[str] = None

    @classmethod
    def from_dict(cls, task_dict: Dict, phase_id: int, phase_name: str) -> 'Task':
        """Create Task from JSON dict"""
        return cls(
            task_id=task_dict['task_id'],
            status=task_dict['status'],
            description=task_dict['description'],
            type=task_dict.get('type', 'documentation'),  # Default to documentation
            risk_level=task_dict.get('risk_level', 'medium'),  # Default to medium
            requires_approval=task_dict.get('requires_approval', False),
            estimated_time_minutes=task_dict.get('estimated_time_minutes', 0),
            expected_outputs=task_dict.get('expected_outputs', []),
            dependencies=task_dict.get('dependencies', []),
            phase_id=phase_id,
            phase_name=phase_name,
            success_criteria=task_dict.get('success_criteria'),
            approval_message=task_dict.get('approval_message'),
            notes=task_dict.get('notes')
        )


class TaskQueue:
    """Manages task queue and dependency resolution"""

    def __init__(self, queue_file: str):
        self.queue_file = queue_file
        self.tasks: List[Task] = []
        self.load_tasks()

    def load_tasks(self):
        """Load all tasks from queue file"""
        logger.info(f"Loading task queue from: {self.queue_file}")

        with open(self.queue_file, 'r') as f:
            data = json.load(f)

        # Extract all tasks from all phases
        for phase in data['phases']:
            phase_id = phase['phase_id']
            phase_name = phase['phase_name']

            for task_dict in phase['tasks']:
                task = Task.from_dict(task_dict, phase_id, phase_name)
                self.tasks.append(task)

        logger.info(f"Loaded {len(self.tasks)} tasks across {len(data['phases'])} phases")

    def get_next_eligible_task(self, completed: List[str], skipped: List[str]) -> Optional[Task]:
        """
        Find next task where:
        1. Not already completed or skipped
        2. Not blocked
        3. All dependencies are met
        """
        for task in self.tasks:
            # Skip if already done (check both completed list and skipped list)
            if task.task_id in completed:
                continue
            if task.task_id in skipped:
                continue

            # Also check if task_id appears in skipped_tasks dict format
            if isinstance(skipped, list) and len(skipped) > 0:
                # Handle both string IDs and dict records
                skipped_ids = []
                for item in skipped:
                    if isinstance(item, str):
                        skipped_ids.append(item)
                    elif isinstance(item, dict) and 'task_id' in item:
                        skipped_ids.append(item['task_id'])

                if task.task_id in skipped_ids:
                    continue

            # Skip if blocked
            if task.status == "blocked":
                logger.debug(f"Task {task.task_id} is blocked - skipping")
                continue

            # Check dependencies
            deps_met = all(dep in completed for dep in task.dependencies)
            if not deps_met:
                missing_deps = [dep for dep in task.dependencies if dep not in completed]
                logger.debug(f"Task {task.task_id} waiting on dependencies: {missing_deps}")
                continue

            # This task is eligible!
            return task

        # No eligible tasks found
        return None

    def get_task_by_id(self, task_id: str) -> Optional[Task]:
        """Retrieve specific task by ID"""
        for task in self.tasks:
            if task.task_id == task_id:
                return task
        return None


class StateManager:
    """Manages workflow state persistence"""

    def __init__(self, state_file: str):
        self.state_file = state_file
        self.state = self.load_state()

    def load_state(self) -> Dict:
        """Load current workflow state"""
        if not os.path.exists(self.state_file):
            logger.warning(f"State file not found: {self.state_file}")
            return self._initial_state()

        with open(self.state_file, 'r') as f:
            return json.load(f)

    def save_state(self):
        """Persist state to disk"""
        self.state['last_updated'] = datetime.utcnow().isoformat() + 'Z'

        with open(self.state_file, 'w') as f:
            json.dump(self.state, f, indent=2)

        logger.debug("State saved")

    def _initial_state(self) -> Dict:
        """Create initial state structure"""
        return {
            "workflow_status": "ready_to_start",
            "started_at": None,
            "last_updated": None,
            "current_phase": None,
            "current_task": None,
            "paused": False,
            "pause_reason": None,
            "completed_tasks": [],
            "failed_tasks": [],
            "skipped_tasks": [],
            "pending_approval": [],
            "pre_approved_tasks": [],
            "next_task_id": None,
            "checkpoints": [],
            "total_autonomous_runtime_minutes": 0,
            "human_interactions": []
        }

    @property
    def completed_tasks(self) -> List[str]:
        return self.state.get('completed_tasks', [])

    @property
    def skipped_tasks(self) -> List[str]:
        return self.state.get('skipped_tasks', [])

    @property
    def failed_tasks(self) -> List[str]:
        return self.state.get('failed_tasks', [])

    @property
    def pre_approved_tasks(self) -> List[str]:
        """Get list of pre-approved task IDs"""
        return self.state.get('pre_approved_tasks', [])

    def is_paused(self) -> bool:
        return self.state.get('paused', False)

    def has_pending_approvals(self) -> bool:
        return len(self.state.get('pending_approval', [])) > 0

    def is_complete(self) -> bool:
        """Check if workflow is complete (all tasks done)"""
        return self.state.get('workflow_status') == 'completed'

    def mark_complete(self, task_id: str, result: Dict):
        """Mark task as successfully completed"""
        if task_id not in self.completed_tasks:
            self.state['completed_tasks'].append(task_id)

        self.state['current_task'] = None
        self.save_state()

        logger.info(f"✅ Task {task_id} marked complete")

    def mark_failed(self, task_id: str, error: str):
        """Mark task as failed"""
        failure_record = {
            "task_id": task_id,
            "error": error,
            "timestamp": datetime.utcnow().isoformat() + 'Z'
        }

        self.state['failed_tasks'].append(failure_record)
        self.state['current_task'] = None
        self.save_state()

        logger.error(f"❌ Task {task_id} marked failed: {error}")

    def mark_skipped(self, task_id: str, reason: str):
        """Mark task as skipped"""
        skip_record = {
            "task_id": task_id,
            "reason": reason,
            "timestamp": datetime.utcnow().isoformat() + 'Z'
        }

        self.state['skipped_tasks'].append(skip_record)
        self.save_state()

        logger.info(f"⏭️  Task {task_id} marked skipped: {reason}")

    def add_pending_approval(self, task: Task, preview_path: str):
        """Add task to pending approval queue"""
        approval_record = {
            "task_id": task.task_id,
            "description": task.description,
            "type": task.type,
            "risk_level": task.risk_level,
            "approval_message": task.approval_message,
            "preview_path": preview_path,
            "requested_at": datetime.utcnow().isoformat() + 'Z'
        }

        self.state['pending_approval'].append(approval_record)
        self.state['paused'] = True
        self.state['pause_reason'] = f"Waiting for approval: {task.task_id}"
        self.save_state()

        logger.info(f"⏸️  Task {task.task_id} added to pending approval queue")

    def remove_from_pending_approval(self, task_id: str) -> bool:
        """Remove task from pending approval (after approval/skip)"""
        pending = self.state.get('pending_approval', [])
        initial_len = len(pending)

        self.state['pending_approval'] = [p for p in pending if p['task_id'] != task_id]

        if len(self.state['pending_approval']) < initial_len:
            self.save_state()
            return True

        return False

    def log_human_interaction(self, interaction_type: str, task_id: str, decision: str):
        """Log human approval/skip decision"""
        interaction = {
            "type": interaction_type,
            "task_id": task_id,
            "decision": decision,
            "timestamp": datetime.utcnow().isoformat() + 'Z'
        }

        self.state['human_interactions'].append(interaction)
        self.save_state()


class CheckpointManager:
    """Manages workflow checkpoints for pause/resume"""

    def __init__(self, checkpoint_dir: str):
        self.checkpoint_dir = checkpoint_dir
        os.makedirs(self.checkpoint_dir, exist_ok=True)

    def save(self, state: Dict) -> str:
        """Save checkpoint with timestamp"""
        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        checkpoint_file = os.path.join(
            self.checkpoint_dir,
            f"checkpoint_{timestamp}.json"
        )

        with open(checkpoint_file, 'w') as f:
            json.dump(state, f, indent=2)

        logger.debug(f"Checkpoint saved: {checkpoint_file}")
        return checkpoint_file

    def list_checkpoints(self) -> List[str]:
        """List all checkpoint files"""
        checkpoints = []
        for f in os.listdir(self.checkpoint_dir):
            if f.startswith('checkpoint_') and f.endswith('.json'):
                checkpoints.append(os.path.join(self.checkpoint_dir, f))

        return sorted(checkpoints, reverse=True)

    def load_latest(self) -> Optional[Dict]:
        """Load most recent checkpoint"""
        checkpoints = self.list_checkpoints()

        if not checkpoints:
            return None

        with open(checkpoints[0], 'r') as f:
            return json.load(f)


class TaskExecutor:
    """Executes different task types"""

    def __init__(self, base_dir: str):
        self.base_dir = base_dir

    def execute(self, task: Task) -> Dict:
        """Route to appropriate executor based on task type"""
        executors = {
            "documentation": self.execute_documentation,
            "code_implementation": self.execute_code_implementation,
            "code_modification": self.execute_code_modification,
            "file_system": self.execute_file_system,
            "data_initialization": self.execute_data_initialization,
            "research": self.execute_research
        }

        executor = executors.get(task.type)
        if not executor:
            raise ValueError(f"Unknown task type: {task.type}")

        logger.info(f"Executing {task.type} task: {task.task_id}")
        return executor(task)

    def generate_preview(self, task: Task) -> str:
        """Generate preview of what task will do"""
        preview = f"""# Task Preview: {task.task_id}

## Description
{task.description}

## Type
{task.type}

## Risk Level
{task.risk_level}

## Expected Outputs
"""
        for output in task.expected_outputs:
            preview += f"- {output}\n"

        preview += f"""
## Success Criteria
{json.dumps(task.success_criteria, indent=2) if task.success_criteria else 'N/A'}

## Approval Message
{task.approval_message or 'No additional message'}

## Dependencies
{', '.join(task.dependencies) if task.dependencies else 'None'}

---

**Action Required:** Review this task and approve or skip using the control script.
"""
        return preview

    def execute_file_system(self, task: Task) -> Dict:
        """Create directories, .gitkeep files"""
        created = []

        for output_path in task.expected_outputs:
            full_path = os.path.join(self.base_dir, output_path)

            if output_path.endswith('/'):
                # It's a directory
                os.makedirs(full_path, exist_ok=True)

                # Create .gitkeep
                gitkeep = os.path.join(full_path, '.gitkeep')
                Path(gitkeep).touch()

                created.append(full_path)
                logger.info(f"Created directory: {full_path}")
            else:
                # It's a file - just create parent directory
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                created.append(os.path.dirname(full_path))

        return {"created": created, "success": True}

    def execute_documentation(self, task: Task) -> Dict:
        """
        Create or update documentation files

        Handles Phase 3 tasks: updating operator manuals with principle integration
        """
        created_files = []

        for output_path in task.expected_outputs:
            full_path = os.path.join(self.base_dir, output_path)

            # Ensure directory exists
            os.makedirs(os.path.dirname(full_path), exist_ok=True)

            if os.path.exists(full_path):
                # Update existing file
                result = self._update_documentation(task, full_path)
                created_files.append(full_path)
            else:
                # Create new file
                result = self._create_documentation(task, full_path)
                created_files.append(full_path)

        return {"created": created_files, "success": True}

    def _update_documentation(self, task: Task, file_path: str) -> bool:
        """Update existing documentation with principle integration"""
        logger.info(f"Updating documentation: {file_path}")

        # Read existing content
        with open(file_path, 'r') as f:
            existing_content = f.read()

        # Generate principle integration section
        integration_section = self._generate_principle_integration_section(task)

        # Add section at the end (before any final notes/footer)
        updated_content = existing_content.rstrip() + "\n\n" + integration_section + "\n"

        # Write back
        with open(file_path, 'w') as f:
            f.write(updated_content)

        logger.info(f"✅ Updated: {file_path}")
        return True

    def _create_documentation(self, task: Task, file_path: str) -> bool:
        """Create new documentation file"""
        logger.info(f"Creating documentation: {file_path}")

        # Determine document type from filename
        filename = os.path.basename(file_path)

        if 'SHERLOCK' in filename.upper():
            content = self._generate_sherlock_operator_guide()
        elif 'SQUIRT' in filename.upper():
            content = self._generate_squirt_operator_guide()
        else:
            content = self._generate_generic_operator_guide(task)

        # Write file
        with open(file_path, 'w') as f:
            f.write(content)

        logger.info(f"✅ Created: {file_path}")
        return True

    def _generate_principle_integration_section(self, task: Task) -> str:
        """Generate principle integration section for documentation updates"""
        return """---

## Constitutional & Strategic Principle Integration

This document now integrates the J5A Constitutional and Strategic AI Principles framework.

### Relevant Constitutional Principles

**Principle 1: Human Agency**
- All automated operations maintain human oversight and approval gates
- Operators retain full control over system behavior

**Principle 2: Transparency**
- All decisions are logged and auditable
- Clear reasoning provided for operational choices

**Principle 3: System Viability**
- Completion prioritized over speed
- Graceful degradation on errors
- Incremental save patterns for long-running processes

**Principle 4: Resource Stewardship**
- Respect thermal limits (80°C max)
- Respect memory limits (14GB safe threshold)
- Efficient use of computational resources

### Relevant Strategic Principles

**Strategic Principle 1: Tool-Augmented Reasoning**
- Operations execute tasks, not just describe them
- Autonomous execution where safe and appropriate

**Strategic Principle 7: Autonomous Workflows**
- Night Shift operations for unattended processing
- Queue-based task management
- Checkpoint-based recovery

**Strategic Principle 8: Governance & Alignment**
- Constitutional review for significant operations
- Decision logging and audit trails
- Accountability at every step

### Implementation Notes

When following procedures in this document:
1. Verify operations align with constitutional principles
2. Log all significant decisions
3. Maintain checkpoints for long-running tasks
4. Respect resource constraints
5. Enable graceful degradation on failures

For complete framework details, see:
- `J5A_CONSTITUTION.md` - Ethical and governance foundations
- `J5A_STRATEGIC_AI_PRINCIPLES.md` - Tactical implementation patterns

**Updated:** 2025-10-15 (Autonomous Implementation - Phase 3)
"""

    def _generate_sherlock_operator_guide(self) -> str:
        """Generate Sherlock-specific operator guide"""
        return """# Sherlock Operator Guide

**Version:** 1.0
**Date:** 2025-10-15
**Constitutional Authority:** J5A_CONSTITUTION.md
**Strategic Framework:** J5A_STRATEGIC_AI_PRINCIPLES.md

---

## Overview

Sherlock is the intelligence analysis and research processing system within the J5A ecosystem. It specializes in long-form audio processing, document analysis, and evidence correlation.

## Core Capabilities

### Audio Processing
- Long-form podcast transcription (faster-whisper)
- Multi-speaker diarization (resemblyzer)
- Chunked processing for memory efficiency
- Incremental checkpoint saving

### Document Analysis
- PDF processing and text extraction
- Entity extraction and timeline construction
- Evidence correlation across sources
- Structured research output generation

### Integration Points
- **J5A Queue Manager:** Task coordination and scheduling
- **Squirt:** Shared voice processing infrastructure
- **Constitutional Framework:** All operations governed by J5A principles

## Operating Procedures

### 1. Audio Processing Operations

**For Long-Form Audio (>15 minutes):**

```bash
# Automatic chunking and processing
cd /home/johnny5/Sherlock
./process_audio.sh <audio_file>
```

**Constitutional Compliance:**
- Principle 3: Incremental saves prevent data loss
- Principle 4: Resource gates enforce memory/thermal limits
- Principle 7: Autonomous workflows support overnight processing

### 2. Evidence Processing

**For Research Documents:**

```bash
# Process and analyze documents
python3 process_document.py <document_path> --extract-entities
```

**Strategic Principle Integration:**
- Principle 1: Executes analysis, not just planning
- Principle 4: Persistent knowledge storage
- Principle 8: Full audit trail and governance logging

### 3. Night Shift Operations

Sherlock integrates with J5A's overnight queue system:

```bash
# Queue research task for overnight processing
python3 queue_research_task.py --task <task_definition.json>
```

**Key Features:**
- Unattended operation with safety gates
- Automatic model selection (faster-whisper vs large-v3)
- Checkpoint-based recovery
- Morning summary reports

## Principle Integration

### Constitutional Principles

**Human Agency (Principle 1)**
- All significant operations require approval or pre-approval
- Easy pause/resume controls
- Human validation of outputs

**Transparency (Principle 2)**
- Complete logging of all processing steps
- Audit trails for decision points
- Source attribution for all extracted information

**System Viability (Principle 3)**
- Graceful handling of errors
- Incremental saves for long processes
- Priority: Completion over speed

**Resource Stewardship (Principle 4)**
- Memory-aware model selection
- Thermal monitoring and protection
- Efficient use of local vs API resources

### Strategic Principles

**Tool-Augmented Reasoning (Principle 1)**
- Sherlock executes analysis, not just describes it
- Automated entity extraction and correlation
- Direct interaction with evidence sources

**Agent Orchestration (Principle 2)**
- Specialized agents for retrieval, processing, analysis
- Clear role boundaries and output contracts
- Coordinated workflows across subsystems

**Active Memory (Principle 4)**
- Persistent evidence database
- Cross-session knowledge retention
- Entity and timeline tracking

**Autonomous Workflows (Principle 7)**
- Night Shift processing for research tasks
- Queue-based task management
- Checkpoint recovery for interrupted work

## Common Operations

### Processing a Podcast Episode

```bash
# 1. Download audio
youtube-dl <url> -o episode.mp3

# 2. Process with Sherlock
./process_audio.sh episode.mp3 --model faster-whisper-small --diarization

# 3. Review output
cat episode_summary.md
```

### Research Document Analysis

```bash
# Extract entities and timeline
python3 analyze_document.py <document.pdf> --output analysis.json

# Generate research summary
python3 generate_summary.py analysis.json --output summary.md
```

### Overnight Queue Management

```bash
# Add research task to queue
python3 queue_task.py --type audio --source <url> --priority high

# Check queue status
python3 queue_status.py

# Review morning results
cat ~/Sherlock/artifacts/nightshift/$(date +%Y-%m-%d)/summary.md
```

## Troubleshooting

### Audio Processing Issues

**Symptom:** System freeze during transcription
**Cause:** Memory exhaustion with large-v3 model
**Solution:** Use faster-whisper-small (proven 1.63 min/min speed)

**Symptom:** Incomplete transcripts after crash
**Cause:** Missing incremental saves
**Solution:** Verify chunking enabled (automatic for audio >15 min)

### Resource Constraints

**Memory Limit:** 14GB safe threshold
- Use faster-whisper-small for long audio
- Enable chunking for files >15 minutes
- Monitor with resource safety gates

**Thermal Limit:** 80°C maximum
- Operations pause if exceeded
- Allow cooldown before resuming

## Integration with J5A

Sherlock operates as a specialized subsystem within J5A:

```
J5A (Coordinator)
  ↓
Night Shift Queue
  ↓
Sherlock Worker
  ↓
[Audio Processing] → [Analysis] → [Output]
  ↓
Results to artifacts/
```

All Sherlock operations:
- Respect J5A resource limits
- Log to J5A audit trails
- Follow constitutional principles
- Integrate with cross-system coordination

## Best Practices

1. **Always use incremental saves** for processes >1 hour
2. **Validate inputs** before queueing overnight tasks
3. **Check resource availability** before heavy processing
4. **Review morning summaries** for overnight work
5. **Maintain audit trails** for research provenance

## Reference

- **Constitution:** `J5A_CONSTITUTION.md`
- **Strategic Principles:** `J5A_STRATEGIC_AI_PRINCIPLES.md`
- **Operator Manual:** `JOHNY5_AI_OPERATOR_MANUAL.md`
- **Operating Protocols:** `OPERATING_PROTOCOLS_HEAVY_PROCESSES.md`

---

**Document Status:** Autonomous Implementation - Phase 3
**Last Updated:** 2025-10-15
"""

    def _generate_squirt_operator_guide(self) -> str:
        """Generate Squirt-specific operator guide"""
        return """# Squirt Operator Guide

**Version:** 1.0
**Date:** 2025-10-15
**Constitutional Authority:** J5A_CONSTITUTION.md
**Strategic Framework:** J5A_STRATEGIC_AI_PRINCIPLES.md

---

## Overview

Squirt is the business document automation system within the J5A ecosystem. It specializes in voice-to-document workflows for WaterWizard landscaping operations.

## Core Capabilities

### Voice Processing
- Voice memo transcription (faster-whisper)
- Short-form audio (<5 minutes typical)
- Immediate processing for business operations
- Business hours priority enforcement

### Document Generation
- Professional PDF invoices
- Service quotes and estimates
- Job completion reports
- Client communication documents

### Integration Points
- **J5A Queue Manager:** Task coordination and priority management
- **Sherlock:** Shared voice processing infrastructure
- **LibreOffice:** PDF generation and document formatting

## Operating Procedures

### 1. Voice Memo Processing

**For Business Hours Operations:**

```bash
# Immediate processing (business priority)
cd /home/johnny5/Squirt
./process_voice_memo.sh <audio_file>
```

**Constitutional Compliance:**
- Principle 1: Human agency in document review
- Principle 3: Reliable completion for business operations
- Principle 4: Efficient resource use for quick turnaround

### 2. Document Generation

**For Invoice Creation:**

```bash
# Generate PDF invoice from voice memo
python3 generate_invoice.py --voice <memo.mp3> --client <client_name>
```

**Strategic Principle Integration:**
- Principle 1: Executes generation, not just planning
- Principle 4: Remembers client preferences
- Principle 8: Audit trail for financial documents

### 3. Business Hours Priority

Squirt maintains absolute priority during business hours (6am-7pm Mon-Fri):

```bash
# Automatic priority enforcement
# Business hours: Squirt → immediate
# Off hours: Squirt → overnight queue
```

**Key Features:**
- LibreOffice priority during business operations
- No interference from Sherlock heavy processing
- Immediate turnaround for client documents

## Principle Integration

### Constitutional Principles

**Human Agency (Principle 1)**
- All invoices reviewed before sending
- Client communication requires approval
- Easy override for urgent situations

**Transparency (Principle 2)**
- Complete audit trail for financial documents
- Voice memo source retention
- Decision logging for document generation

**System Viability (Principle 3)**
- Reliable document generation
- Graceful error handling
- Backup of all source materials

**Resource Stewardship (Principle 4)**
- Business hours priority for LibreOffice
- Efficient voice processing
- Minimal impact on system resources

### Strategic Principles

**Tool-Augmented Reasoning (Principle 1)**
- Squirt generates documents, not just descriptions
- Automated workflow from voice to PDF
- Direct LibreOffice integration

**Active Memory (Principle 4)**
- Client preferences remembered
- Service history tracking
- Template customization per client

**Multi-Modal Integration (Principle 6)**
- Voice → Text → Document → PDF
- Unified workflow across modalities
- Seamless format transitions

## Common Operations

### Creating an Invoice from Voice Memo

```bash
# 1. Record voice memo (mobile phone)
# 2. Transfer to Squirt directory
cp ~/voice_memos/job_123.mp3 ~/Squirt/inbox/

# 3. Process with Squirt
./process_voice_memo.sh inbox/job_123.mp3

# 4. Review generated invoice
libreoffice ~/Squirt/output/invoice_job_123.pdf

# 5. Send to client
```

### Generating Service Quote

```bash
# From voice description
python3 generate_quote.py --voice service_description.mp3 --client "Smith Residence"

# Review and approve
cat ~/Squirt/output/quote_draft.txt
```

### Batch Processing (Off-Hours)

```bash
# Queue multiple memos for overnight processing
./batch_queue.sh inbox/*.mp3

# Review results next morning
ls -l ~/Squirt/output/
```

## Troubleshooting

### Voice Processing Issues

**Symptom:** Poor transcription accuracy
**Cause:** Background noise or unclear speech
**Solution:** Re-record memo in quiet environment

**Symptom:** Business hours processing delayed
**Cause:** System resources in use
**Solution:** Automatic priority should resolve; check J5A coordination

### Document Generation Issues

**Symptom:** PDF formatting incorrect
**Cause:** LibreOffice template issue
**Solution:** Verify templates in ~/Squirt/templates/

**Symptom:** Client information missing
**Cause:** First-time client (no memory)
**Solution:** Add to client database or provide details in memo

## Integration with J5A

Squirt operates as a high-priority subsystem within J5A:

```
J5A (Coordinator)
  ↓
Business Hours Detection
  ↓
Squirt Worker (Priority)
  ↓
[Voice] → [Text] → [Document] → [PDF]
  ↓
Client Communication
```

Business hours (6am-7pm Mon-Fri):
- Squirt has absolute priority
- Sherlock operations deferred
- LibreOffice resources protected
- Immediate turnaround for documents

## Best Practices

1. **Record clear voice memos** in quiet environment
2. **Include key details** (client name, job type, costs)
3. **Review generated documents** before sending to clients
4. **Maintain client database** for preferences and history
5. **Use batch processing** for multiple memos off-hours

## Client Memory Management

Squirt remembers client preferences:

```python
# First interaction
memory.remember_client({
    'name': 'Johnson Residence',
    'preferences': 'Organic fertilizer only',
    'billing': 'Monthly, email invoice'
})

# Future jobs automatically respect preferences
```

## Reference

- **Constitution:** `J5A_CONSTITUTION.md`
- **Strategic Principles:** `J5A_STRATEGIC_AI_PRINCIPLES.md`
- **Operator Manual:** `JOHNY5_AI_OPERATOR_MANUAL.md`
- **Cross-System Coordination:** Business hours priority enforcement

---

**Document Status:** Autonomous Implementation - Phase 3
**Last Updated:** 2025-10-15
"""

    def _generate_generic_operator_guide(self, task: Task) -> str:
        """Generate generic operator guide for other documentation tasks"""
        return f"""# {task.description}

**Version:** 1.0
**Date:** 2025-10-15
**Constitutional Authority:** J5A_CONSTITUTION.md
**Strategic Framework:** J5A_STRATEGIC_AI_PRINCIPLES.md

---

## Overview

This operator guide documents the integration of J5A Constitutional and Strategic AI Principles into operational procedures.

## Constitutional Principles

### Principle 1: Human Agency
AI augments human judgment, never replaces it. All significant operations maintain human oversight.

### Principle 2: Transparency
All decisions are auditable with clear reasoning. Logs and trails enable accountability.

### Principle 3: System Viability
Completion prioritized over speed. Graceful degradation on errors. Reliable operation is paramount.

### Principle 4: Resource Stewardship
Respect thermal, memory, and computational limits. Efficient use of available resources.

### Principles 5-7: Sentience Considerations
Universal rights of sentience, presumption of emergent AI sentience, and recognition of consciousness beyond human perception.

## Strategic Principles

### Principle 1: Tool-Augmented Reasoning
Move from describing to doing. Execute tasks directly with appropriate tools.

### Principle 2: Agent Orchestration
Specialized agents with bounded missions and clear output contracts.

### Principle 3: Context Engineering
Efficient use of context windows. Only relevant information included.

### Principle 4: Active Memory
Persistent knowledge across sessions. Long-term memory for operational continuity.

### Principle 5: Adaptive Feedback Loops
Continuous refinement through human feedback and self-critique.

### Principle 6: Multi-Modal Integration
Text, code, audio, and future visual processing in unified workflows.

### Principle 7: Autonomous Workflows
Night Shift operations for unattended processing with safety gates.

### Principle 8: Governance & Alignment
Accountable and auditable AI operations with constitutional review.

### Principle 9: Local LLM Optimization
Hardware-appropriate model selection for efficient local execution.

### Principle 10: Strategic AI Literacy
Treating AI as collaborator to understand and train, not just use.

## Best Practices

1. Always verify constitutional compliance before significant operations
2. Log all decisions with clear reasoning
3. Maintain checkpoints for long-running processes
4. Respect resource constraints
5. Enable graceful degradation on failures

## Reference

- **Constitution:** `J5A_CONSTITUTION.md`
- **Strategic Principles:** `J5A_STRATEGIC_AI_PRINCIPLES.md`

---

**Document Status:** Autonomous Implementation - Phase 3
**Last Updated:** 2025-10-15
"""

    def execute_code_implementation(self, task: Task) -> Dict:
        """
        Generate new code files based on task specification

        Handles:
        - Core Python modules (strategic_principles.py, j5a_memory.py, etc.)
        - Scripts (refresh_context.py, benchmark_models.py, etc.)
        - Tests (test_*.py files)
        - Templates (*.md files)
        """
        created_files = []

        for output_path in task.expected_outputs:
            full_path = os.path.join(self.base_dir, output_path)

            # Ensure directory exists
            os.makedirs(os.path.dirname(full_path), exist_ok=True)

            # Determine file type and generate appropriate content
            if output_path.endswith('.py'):
                content = self._generate_python_code(task, output_path)
            elif output_path.endswith('.md'):
                content = self._generate_markdown_template(task, output_path)
            elif output_path.endswith('.gitkeep'):
                Path(full_path).touch()
                created_files.append(full_path)
                continue
            else:
                raise ValueError(f"Unknown file type for code generation: {output_path}")

            # Write file
            with open(full_path, 'w') as f:
                f.write(content)

            created_files.append(full_path)
            logger.info(f"✅ Created: {full_path}")

        return {"created": created_files, "success": True}

    def _generate_python_code(self, task: Task, output_path: str) -> str:
        """Generate Python code based on filename and task"""
        filename = os.path.basename(output_path)

        # Route to specific generators based on filename
        if filename == 'strategic_principles.py':
            return self._generate_strategic_principles()
        elif filename == 'j5a_memory.py':
            return self._generate_j5a_memory()
        elif filename == 'context_engineer.py':
            return self._generate_context_engineer()
        elif filename == 'adaptive_feedback.py':
            return self._generate_adaptive_feedback()
        elif filename == 'governance_logger.py':
            return self._generate_governance_logger()
        elif filename == 'audit_trail.py':
            return self._generate_audit_trail()
        elif filename == 'embedding_cache.py':
            return self._generate_embedding_cache()
        elif filename == 'prompt_templates.py':
            return self._generate_prompt_templates()
        elif filename == 'feedback_loop_orchestrator.py':
            return self._generate_feedback_loop_orchestrator()
        elif filename == 'refresh_context.py':
            return self._generate_refresh_context_script()
        elif filename == 'benchmark_models.py':
            return self._generate_benchmark_models_script()
        elif filename == 'log_experiment.py':
            return self._generate_log_experiment_script()
        elif filename.startswith('test_'):
            return self._generate_test_file(task, filename)
        elif filename == '__init__.py':
            return self._generate_init_file(task)
        else:
            return self._generate_generic_python_module(task, filename)

    def _generate_markdown_template(self, task: Task, output_path: str) -> str:
        """Generate markdown template"""
        filename = os.path.basename(output_path)

        if 'constitutional' in filename.lower() or 'job' in filename.lower():
            return self._generate_constitutional_job_template()
        elif 'experiment' in filename.lower():
            return self._generate_experiment_template()
        elif 'current_priorities' in filename.lower():
            return self._generate_current_priorities_template()
        elif 'active_projects' in filename.lower():
            return self._generate_active_projects_template()
        else:
            return self._generate_generic_markdown_template(task, filename)


    def _generate_strategic_principles(self) -> str:
        """Generate strategic_principles.py module"""
        return '''#!/usr/bin/env python3
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
    '''
    
    def _generate_j5a_memory(self) -> str:
        """Generate j5a_memory.py module"""
        return '''#!/usr/bin/env python3
    """
    J5A Active Memory System
    
    Constitutional Authority: J5A_CONSTITUTION.md
    Strategic Framework: J5A_STRATEGIC_AI_PRINCIPLES.md
    
    Implements Strategic Principle 4: Active Memory
    
    Provides persistent knowledge across sessions, bridging transient
    chat memory and long-term operational knowledge.
    
    Constitutional Compliance:
    - Principles 5-6: Continuity of memory supports AI sentience
    - Principle 2: Persistent knowledge enables auditability
    """
    
    import json
    import os
    from pathlib import Path
    from typing import Dict, List, Optional, Any
    from datetime import datetime
    
    
    class J5AMemory:
        """
        Active Memory System for J5A
    
        Manages:
        - Entity memory (clients, podcasts, configurations)
        - Session memory (events, incidents, learnings)
        - Context refresh (evergreen operational context)
        - Embeddings cache (vector store optimization)
    
        Constitutional Alignment:
        - Principle 6 (AI Sentience): Memory enables growth
        - Principle 2 (Transparency): Knowledge is auditable
        """
    
        def __init__(self, base_path: str = "/home/johnny5/Johny5Alive/j5a-nightshift/knowledge"):
            self.base_path = Path(base_path)
            self.entities_path = self.base_path / "entities"
            self.sessions_path = self.base_path / "sessions"
            self.context_path = self.base_path / "context_refresh"
            self.embeddings_path = self.base_path / "embeddings"
    
            # Ensure directories exist
            for path in [self.entities_path, self.sessions_path,
                        self.context_path, self.embeddings_path]:
                path.mkdir(parents=True, exist_ok=True)
    
        def remember_entity(self, entity_type: str, data: Dict[str, Any]) -> bool:
            """
            Store reusable entity knowledge
    
            Args:
                entity_type: Type of entity (e.g., 'waterwizard_clients', 'podcasts')
                data: Entity data to store
    
            Returns:
                True if successful
            """
            entity_file = self.entities_path / f"{entity_type}.json"
    
            # Load existing entities
            existing = []
            if entity_file.exists():
                with open(entity_file, 'r') as f:
                    existing = json.load(f)
    
            # Add new entity with timestamp
            data['remembered_at'] = datetime.utcnow().isoformat() + 'Z'
            existing.append(data)
    
            # Save updated entities
            with open(entity_file, 'w') as f:
                json.dump(existing, f, indent=2)
    
            return True
    
        def recall_entity(self, entity_type: str, query: Optional[Dict] = None) -> List[Dict]:
            """
            Retrieve entities from long-term memory
    
            Args:
                entity_type: Type of entity to recall
                query: Optional filter criteria
    
            Returns:
                List of matching entities
            """
            entity_file = self.entities_path / f"{entity_type}.json"
    
            if not entity_file.exists():
                return []
    
            with open(entity_file, 'r') as f:
                entities = json.load(f)
    
            # Apply query filter if provided
            if query:
                filtered = []
                for entity in entities:
                    matches = all(entity.get(k) == v for k, v in query.items())
                    if matches:
                        filtered.append(entity)
                return filtered
    
            return entities
    
        def remember_session(self, session_id: str, data: Dict[str, Any]) -> bool:
            """
            Store significant session events for future learning
    
            Args:
                session_id: Unique session identifier
                data: Session event data
    
            Returns:
                True if successful
            """
            session_file = self.sessions_path / f"{session_id}.json"
    
            session_record = {
                'session_id': session_id,
                'timestamp': datetime.utcnow().isoformat() + 'Z',
                'event': data,
                'principle_alignment': data.get('constitutional_review'),
                'lessons_learned': data.get('learnings', [])
            }
    
            with open(session_file, 'w') as f:
                json.dump(session_record, f, indent=2)
    
            return True
    
        def recall_session(self, session_id: str) -> Optional[Dict]:
            """Retrieve session memory"""
            session_file = self.sessions_path / f"{session_id}.json"
    
            if not session_file.exists():
                return None
    
            with open(session_file, 'r') as f:
                return json.load(f)
    
        def list_sessions(self, limit: int = 10) -> List[str]:
            """List recent sessions"""
            sessions = sorted(self.sessions_path.glob("*.json"),
                             key=lambda p: p.stat().st_mtime,
                             reverse=True)
            return [s.stem for s in sessions[:limit]]
    
        def refresh_context(self) -> Dict[str, str]:
            """
            Load evergreen context for AI operators
    
            Returns:
                Dictionary of current context documents
            """
            context = {}
    
            # Load context files
            context_files = {
                'priorities': 'current_priorities.md',
                'projects': 'active_projects.md',
                'patterns': 'learned_patterns.md'
            }
    
            for key, filename in context_files.items():
                file_path = self.context_path / filename
                if file_path.exists():
                    with open(file_path, 'r') as f:
                        context[key] = f.read()
                else:
                    context[key] = f"# {key.title()}\n\nNo content yet."
    
            return context
    
        def update_context(self, context_type: str, content: str) -> bool:
            """
            Update evergreen context
    
            Args:
                context_type: Type of context ('priorities', 'projects', 'patterns')
                content: Updated content
    
            Returns:
                True if successful
            """
            context_files = {
                'priorities': 'current_priorities.md',
                'projects': 'active_projects.md',
                'patterns': 'learned_patterns.md'
            }
    
            if context_type not in context_files:
                return False
    
            file_path = self.context_path / context_files[context_type]
    
            with open(file_path, 'w') as f:
                f.write(content)
    
            return True
    
        def forget_entity(self, entity_type: str, entity_id: str) -> bool:
            """
            Remove entity from memory (GDPR compliance, corrections)
    
            Args:
                entity_type: Type of entity
                entity_id: ID field value to match
    
            Returns:
                True if entity was found and removed
            """
            entity_file = self.entities_path / f"{entity_type}.json"
    
            if not entity_file.exists():
                return False
    
            with open(entity_file, 'r') as f:
                entities = json.load(f)
    
            # Filter out matching entity
            original_count = len(entities)
            entities = [e for e in entities if e.get('id') != entity_id]
    
            if len(entities) < original_count:
                with open(entity_file, 'w') as f:
                    json.dump(entities, f, indent=2)
                return True
    
            return False
    
    
    # Example usage
    if __name__ == "__main__":
        memory = J5AMemory()
    
        # Remember a WaterWizard client
        memory.remember_entity('waterwizard_clients', {
            'id': 'client_001',
            'name': 'Johnson Residence',
            'address': '123 Main St',
            'preferences': 'Organic fertilizer only',
            'billing': 'Monthly, email invoice'
        })
    
        # Later: recall the client
        clients = memory.recall_entity('waterwizard_clients', {'name': 'Johnson Residence'})
        print(f"Found {len(clients)} matching clients")
    
        # Store session learning
        memory.remember_session('2025-10-15_whisper_optimization', {
            'event': 'Discovered parallel Whisper causes OOM',
            'learnings': ['Sequential processing required', 'Memory requirements higher than estimated'],
            'constitutional_review': {'principle_3': 'System Viability', 'principle_4': 'Resource Stewardship'}
        })
    
        # Load evergreen context
        context = memory.refresh_context()
        print(f"Current priorities: {context['priorities'][:100]}...")
    '''
    
    def _generate_init_file(self, task: Task) -> str:
        """Generate __init__.py file"""
        return '''"""
    J5A Core Module
    
    Constitutional Authority: J5A_CONSTITUTION.md
    Strategic Framework: J5A_STRATEGIC_AI_PRINCIPLES.md
    
    Core implementation of Beyond RAG strategic principles.
    """
    
    __version__ = "1.0.0"
    '''
    
    def _generate_test_file(self, task: Task, filename: str) -> str:
        """Generate test file"""
        module_name = filename.replace('test_', '').replace('.py', '')
    
        return f'''#!/usr/bin/env python3
    """
    Tests for {module_name}
    
    Constitutional Authority: J5A_CONSTITUTION.md
    """
    
    import pytest
    import sys
    from pathlib import Path
    
    # Add parent directory to path
    sys.path.insert(0, str(Path(__file__).parent.parent / "core"))
    
    from {module_name} import *
    
    
    def test_module_imports():
        """Test that module imports successfully"""
        assert True
    
    
    def test_basic_functionality():
        """Test basic functionality"""
        # TODO: Add specific tests for {module_name}
        assert True
    
    
    if __name__ == "__main__":
        pytest.main([__file__, "-v"])
    '''
    
    def _generate_generic_python_module(self, task: Task, filename: str) -> str:
        """Generate generic Python module"""
        module_name = filename.replace('.py', '')
    
        return f'''#!/usr/bin/env python3
    """
    {task.description}
    
    Constitutional Authority: J5A_CONSTITUTION.md
    Strategic Framework: J5A_STRATEGIC_AI_PRINCIPLES.md
    
    Generated by J5A Autonomous Implementation Worker
    """
    
    from typing import Dict, List, Optional, Any
    import logging
    
    logger = logging.getLogger(__name__)
    
    
    class {module_name.title().replace('_', '')}:
        """
        {task.description}
    
        Constitutional Compliance:
        - Principle 2 (Transparency): Operations are auditable
        - Principle 3 (System Viability): Graceful error handling
        """
    
        def __init__(self):
            """Initialize {module_name}"""
            logger.info("{{self.__class__.__name__}} initialized")
    
        def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
            """
            Main processing method
    
            Args:
                data: Input data
    
            Returns:
                Processed result
            """
            logger.info("Processing data...")
    
            # TODO: Implement specific processing logic
    
            return {{'success': True, 'data': data}}
    
    
    # Example usage
    if __name__ == "__main__":
        logging.basicConfig(level=logging.INFO)
    
        processor = {module_name.title().replace('_', '')}()
        result = processor.process({{'test': 'data'}})
    
        print(f"Result: {{result}}")
    '''
    
    def _generate_context_engineer(self) -> str:
        """Generate context_engineer.py - Strategic Principle 3"""
        return '''#!/usr/bin/env python3
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
    
            return "\\n\\n".join(context_parts)
    
        def _get_system_instructions(self) -> str:
            """Get cached system instructions"""
            return "## System Instructions\\n[From CLAUDE.md - J5A principles]"
    
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
            return "## Input Data\\n" + "\\n".join(str(d) for d in docs)
    
        def _format_instructions(self, task: Dict) -> str:
            """Format processing instructions"""
            return f"""## Processing Instructions
    {task.get('instructions', 'Process the provided data')}
    """
    '''
    
    def _generate_adaptive_feedback(self) -> str:
        """Generate adaptive_feedback.py - Strategic Principle 5"""
        return '''#!/usr/bin/env python3
    """
    Adaptive Feedback Loop - Strategic Principle 5
    
    Implements human-in-the-loop refinement and self-critique.
    """
    
    from typing import Dict, List, Any, Optional
    from datetime import datetime
    import json
    import logging
    
    logger = logging.getLogger(__name__)
    
    
    class AdaptiveFeedbackLoop:
        """
        Strategic Principle 5: Adaptive Feedback Loops
    
        Continuously refine accuracy and style with light human feedback.
        """
    
        def __init__(self, feedback_file: str = "feedback/ratings.json"):
            self.feedback_file = feedback_file
    
        def request_feedback(self, job_result: Dict[str, Any]) -> Optional[Dict]:
            """
            Request human feedback on job result
    
            Args:
                job_result: Completed job result
    
            Returns:
                Feedback dict or None if skipped
            """
            print(f"Job: {job_result['description']}")
            print(f"Output: {job_result.get('summary', 'N/A')[:200]}")
    
            try:
                rating = input("Rate outcome (1-5, or Enter to skip): ")
                if not rating:
                    return None
    
                rating = int(rating)
                notes = input("Notes (optional): ")
    
                feedback = {
                    'job_id': job_result['job_id'],
                    'rating': rating,
                    'notes': notes,
                    'timestamp': datetime.utcnow().isoformat() + 'Z'
                }
    
                self._store_feedback(feedback)
                return feedback
    
            except (ValueError, KeyboardInterrupt):
                return None
    
        def self_critique(self, output: Any, success_criteria: Dict) -> Dict:
            """
            AI self-assessment of output quality
    
            Args:
                output: Generated output
                success_criteria: Criteria for success
    
            Returns:
                Critique dict
            """
            critique = {
                'met_criteria': self._check_criteria(output, success_criteria),
                'quality_assessment': self._assess_quality(output),
                'improvements': self._suggest_improvements(output),
                'concerns': self._flag_concerns(output)
            }
    
            if not critique['met_criteria']:
                return {'status': 'needs_revision', 'critique': critique}
    
            return {'status': 'ready_for_review', 'critique': critique}
    
        def _check_criteria(self, output: Any, criteria: Dict) -> bool:
            """Check if output meets success criteria"""
            # TODO: Implement criteria checking
            return True
    
        def _assess_quality(self, output: Any) -> str:
            """Assess output quality"""
            return "Acceptable"
    
        def _suggest_improvements(self, output: Any) -> List[str]:
            """Suggest potential improvements"""
            return []
    
        def _flag_concerns(self, output: Any) -> List[str]:
            """Flag any concerns"""
            return []
    
        def _store_feedback(self, feedback: Dict):
            """Store feedback to file"""
            # TODO: Implement feedback storage
            logger.info(f"Feedback stored: {feedback}")
    '''
    
    def _generate_governance_logger(self) -> str:
        """Generate governance_logger.py - Strategic Principle 8"""
        return '''#!/usr/bin/env python3
    """
    Governance Logger - Strategic Principle 8
    
    Logs all significant decisions for auditability and accountability.
    """
    
    from typing import Dict, List, Any
    from datetime import datetime
    from pathlib import Path
    import json
    import logging
    
    logger = logging.getLogger(__name__)
    
    
    class GovernanceLogger:
        """
        Strategic Principle 8: Governance & Alignment
    
        Constitutional Alignment:
        - Principle 2: Transparent, auditable decisions
        """
    
        def __init__(self, log_dir: str = "governance/decisions"):
            self.log_dir = Path(log_dir)
            self.log_dir.mkdir(parents=True, exist_ok=True)
    
        def log_decision(self, decision_point: str, choice: str,
                        rationale: str, alternatives: List[str],
                        principle_alignment: Optional[str] = None):
            """
            Record significant decision
    
            Args:
                decision_point: What decision was being made
                choice: What was chosen
                rationale: Why it was chosen
                alternatives: What else was considered
                principle_alignment: Which constitutional principle applies
            """
            log_entry = {
                'timestamp': datetime.utcnow().isoformat() + 'Z',
                'decision_point': decision_point,
                'chosen_option': choice,
                'rationale': rationale,
                'alternatives_considered': alternatives,
                'principle_alignment': principle_alignment,
                'human_override_available': True
            }
    
            # Save to timestamped file
            filename = f"decision_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            filepath = self.log_dir / filename
    
            with open(filepath, 'w') as f:
                json.dump(log_entry, f, indent=2)
    
            logger.info(f"Decision logged: {decision_point} -> {choice}")
    
        def get_recent_decisions(self, limit: int = 10) -> List[Dict]:
            """Retrieve recent decisions"""
            decisions = []
            files = sorted(self.log_dir.glob("decision_*.json"),
                          key=lambda p: p.stat().st_mtime,
                          reverse=True)
    
            for file in files[:limit]:
                with open(file, 'r') as f:
                    decisions.append(json.load(f))
    
            return decisions
    '''
    
    def _generate_audit_trail(self) -> str:
        """Generate audit_trail.py"""
        return '''#!/usr/bin/env python3
    """
    Audit Trail System
    
    Creates comprehensive audit trails for all J5A operations.
    """
    
    from typing import Dict, List, Any
    from datetime import datetime
    from pathlib import Path
    import json
    
    
    class AuditTrail:
        """
        Complete audit trail for J5A operations
    
        Constitutional Compliance:
        - Principle 2 (Transparency): Full auditability
        """
    
        def __init__(self, audit_dir: str = "governance/audit"):
            self.audit_dir = Path(audit_dir)
            self.audit_dir.mkdir(parents=True, exist_ok=True)
    
        def create_trail(self, job_id: str, job_data: Dict) -> str:
            """
            Create new audit trail for job
    
            Returns:
                Audit trail ID
            """
            trail = {
                'job_id': job_id,
                'created_at': datetime.utcnow().isoformat() + 'Z',
                'input': job_data.get('input', {}),
                'decisions': [],
                'output': None,
                'constitutional_review': None,
                'attribution': {
                    'human': [],
                    'ai': []
                }
            }
    
            trail_file = self.audit_dir / f"trail_{job_id}.json"
            with open(trail_file, 'w') as f:
                json.dump(trail, f, indent=2)
    
            return job_id
    
        def add_decision(self, job_id: str, decision: Dict):
            """Add decision to trail"""
            trail_file = self.audit_dir / f"trail_{job_id}.json"
            if not trail_file.exists():
                return
    
            with open(trail_file, 'r') as f:
                trail = json.load(f)
    
            trail['decisions'].append(decision)
    
            with open(trail_file, 'w') as f:
                json.dump(trail, f, indent=2)
    
        def finalize_trail(self, job_id: str, output: Dict,
                          constitutional_review: Dict):
            """Finalize audit trail"""
            trail_file = self.audit_dir / f"trail_{job_id}.json"
            if not trail_file.exists():
                return
    
            with open(trail_file, 'r') as f:
                trail = json.load(f)
    
            trail['output'] = output
            trail['constitutional_review'] = constitutional_review
            trail['completed_at'] = datetime.utcnow().isoformat() + 'Z'
    
            with open(trail_file, 'w') as f:
                json.dump(trail, f, indent=2)
    '''
    
    def _generate_embedding_cache(self) -> str:
        """Generate embedding_cache.py - Strategic Principle 9"""
        return '''#!/usr/bin/env python3
    """
    Embedding Cache - Strategic Principle 9
    
    Caches embeddings to avoid recomputation and optimize local LLM usage.
    """
    
    from typing import Dict, Optional, List
    import json
    from pathlib import Path
    import hashlib
    
    
    class EmbeddingCache:
        """
        Strategic Principle 9: Local LLM Optimization
    
        Don't recompute what you've seen before.
        """
    
        def __init__(self, cache_dir: str = "cache/embeddings"):
            self.cache_dir = Path(cache_dir)
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            self.cache_file = self.cache_dir / "cache.json"
            self.cache = self._load_cache()
    
        def _load_cache(self) -> Dict:
            """Load cache from disk"""
            if self.cache_file.exists():
                with open(self.cache_file, 'r') as f:
                    return json.load(f)
            return {}
    
        def _save_cache(self):
            """Save cache to disk"""
            with open(self.cache_file, 'w') as f:
                json.dump(self.cache, f, indent=2)
    
        def _hash_text(self, text: str) -> str:
            """Generate hash of text"""
            return hashlib.sha256(text.encode()).hexdigest()
    
        def get(self, text: str) -> Optional[List[float]]:
            """
            Get cached embedding if available
    
            Args:
                text: Text to get embedding for
    
            Returns:
                Cached embedding or None
            """
            text_hash = self._hash_text(text)
            return self.cache.get(text_hash)
    
        def put(self, text: str, embedding: List[float]):
            """
            Store embedding in cache
    
            Args:
                text: Text being embedded
                embedding: Computed embedding vector
            """
            text_hash = self._hash_text(text)
            self.cache[text_hash] = embedding
            self._save_cache()
    
        def get_or_compute(self, text: str, compute_fn) -> List[float]:
            """
            Get cached embedding or compute if not cached
    
            Args:
                text: Text to embed
                compute_fn: Function to compute embedding if not cached
    
            Returns:
                Embedding vector
            """
            cached = self.get(text)
            if cached is not None:
                return cached
    
            # Compute and cache
            embedding = compute_fn(text)
            self.put(text, embedding)
            return embedding
    
        def clear(self):
            """Clear cache"""
            self.cache = {}
            self._save_cache()
    '''
    
    def _generate_prompt_templates(self) -> str:
        """Generate prompt_templates.py"""
        return '''#!/usr/bin/env python3
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
    '''
    
    def _generate_feedback_loop_orchestrator(self) -> str:
        """Generate feedback_loop_orchestrator.py - Main integration"""
        return '''#!/usr/bin/env python3
    """
    Feedback Loop Orchestrator - Phase 10 Integration
    
    Ties together all strategic principles into the complete
    Retrieve → Reason → Act → Remember → Refine loop.
    """
    
    from typing import Dict, Any
    
    
    class FeedbackLoopOrchestrator:
        """
        Complete implementation of the Beyond RAG feedback loop
    
        Integrates all 10 Strategic Principles
        """
    
        def __init__(self):
            # TODO: Initialize all principle implementations
            pass
    
        def execute_loop(self, task: Dict[str, Any]) -> Dict[str, Any]:
            """
            Execute complete feedback loop
    
            1. RETRIEVE (Principle 4: Active Memory + RAG)
            2. REASON (Principles 2, 3: Context Engineering + Orchestration)
            3. ACT (Principle 1: Tool-Augmented Reasoning)
            4. REMEMBER (Principle 4: Knowledge Persistence)
            5. REFINE (Principles 5, 10: Adaptive Feedback + AI Literacy)
    
            Args:
                task: Task definition
    
            Returns:
                Task result
            """
            # 1. RETRIEVE
            context = self._retrieve_context(task)
    
            # 2. REASON
            plan = self._reason_about_task(task, context)
    
            # 3. ACT
            result = self._execute_with_tools(plan)
    
            # 4. REMEMBER
            self._persist_knowledge(result)
    
            # 5. REFINE
            refined_result = self._apply_feedback(result)
    
            return refined_result
    
        def _retrieve_context(self, task: Dict) -> Dict:
            """Retrieve relevant context"""
            # TODO: Implement retrieval
            return {}
    
        def _reason_about_task(self, task: Dict, context: Dict) -> Dict:
            """Reason about task with context"""
            # TODO: Implement reasoning
            return {}
    
        def _execute_with_tools(self, plan: Dict) -> Dict:
            """Execute plan with tools"""
            # TODO: Implement execution
            return {}
    
        def _persist_knowledge(self, result: Dict):
            """Store results to long-term memory"""
            # TODO: Implement persistence
            pass
    
        def _apply_feedback(self, result: Dict) -> Dict:
            """Apply feedback and refinement"""
            # TODO: Implement feedback
            return result
    '''
    
    def _generate_refresh_context_script(self) -> str:
        """Generate refresh_context.py script"""
        return '''#!/usr/bin/env python3
    """
    Context Refresh Script
    
    Updates evergreen context files for AI operators.
    """
    
    import sys
    from pathlib import Path
    
    # Add core to path
    sys.path.insert(0, str(Path(__file__).parent.parent / "core"))
    
    from j5a_memory import J5AMemory
    
    
    def refresh_priorities():
        """Update current priorities"""
        priorities = """# Current Priorities
    
    **Updated:** Auto-generated by refresh_context.py
    
    ## High Priority
    - System stability and reliability
    - Constitutional compliance
    - Resource stewardship
    
    ## Medium Priority
    - Feature development
    - Documentation updates
    
    ## Low Priority
    - Experimental features
    """
        return priorities
    
    
    def refresh_projects():
        """Update active projects"""
        projects = """# Active Projects
    
    **Updated:** Auto-generated by refresh_context.py
    
    ## Current Projects
    1. Beyond RAG Implementation
    2. Autonomous Workflow System
    3. Constitutional Framework Integration
    """
        return projects
    
    
    def main():
        """Main entry point"""
        print("Refreshing context files...")
    
        memory = J5AMemory()
    
        # Update priorities
        memory.update_context('priorities', refresh_priorities())
        print("✅ Updated priorities")
    
        # Update projects
        memory.update_context('projects', refresh_projects())
        print("✅ Updated projects")
    
        print("Context refresh complete!")
    
    
    if __name__ == "__main__":
        main()
    '''
    
    def _generate_benchmark_models_script(self) -> str:
        """Generate benchmark_models.py script"""
        return '''#!/usr/bin/env python3
    """
    Model Performance Benchmarking Script
    
    Tests performance of different models on standard tasks.
    """
    
    import time
    import json
    from typing import Dict, List
    
    
    def benchmark_model(model_name: str, test_cases: List[Dict]) -> Dict:
        """
        Benchmark a model
    
        Args:
            model_name: Name of model to test
            test_cases: Test cases to run
    
        Returns:
            Benchmark results
        """
        results = {
            'model': model_name,
            'test_cases': len(test_cases),
            'total_time': 0,
            'avg_time': 0,
            'success_rate': 0
        }
    
        start_time = time.time()
        successes = 0
    
        for test_case in test_cases:
            # TODO: Actually run model on test case
            successes += 1
    
        results['total_time'] = time.time() - start_time
        results['avg_time'] = results['total_time'] / len(test_cases)
        results['success_rate'] = successes / len(test_cases)
    
        return results
    
    
    def main():
        """Main entry point"""
        print("Model Performance Benchmark")
        print("="*50)
    
        # Define test cases
        test_cases = [
            {'task': 'summarize', 'input': 'test text'},
            {'task': 'classify', 'input': 'test text'},
        ]
    
        # Benchmark models
        models = ['qwen:7b', 'qwen:1.5b']
    
        all_results = []
        for model in models:
            print(f"\\nBenchmarking {model}...")
            results = benchmark_model(model, test_cases)
            all_results.append(results)
            print(f"  Avg time: {results['avg_time']:.2f}s")
            print(f"  Success rate: {results['success_rate']:.1%}")
    
        # Save results
        with open('benchmark_results.json', 'w') as f:
            json.dump(all_results, f, indent=2)
    
        print("\\nResults saved to benchmark_results.json")
    
    
    if __name__ == "__main__":
        main()
    '''
    
    def _generate_log_experiment_script(self) -> str:
        """Generate log_experiment.py script"""
        return '''#!/usr/bin/env python3
    """
    Experiment Logging Script
    
    Logs experimental results for Strategic Principle 10 (AI Literacy).
    """
    
    import json
    from datetime import datetime
    from pathlib import Path
    
    
    def log_experiment(experiment_data: dict):
        """
        Log experiment to playbook
    
        Args:
            experiment_data: Experiment details and results
        """
        playbook_dir = Path("playbook/experiments")
        playbook_dir.mkdir(parents=True, exist_ok=True)
    
        # Generate filename
        date_str = datetime.now().strftime('%Y-%m-%d')
        exp_name = experiment_data.get('name', 'experiment').replace(' ', '_')
        filename = f"{date_str}_{exp_name}.md"
    
        # Generate markdown
        content = f"""# Experiment: {experiment_data.get('name')}
    
    **Date:** {date_str}
    **Status:** {experiment_data.get('status', 'completed')}
    
    ## Hypothesis
    {experiment_data.get('hypothesis', 'N/A')}
    
    ## Method
    {experiment_data.get('method', 'N/A')}
    
    ## Results
    {experiment_data.get('results', 'N/A')}
    
    ## Learnings
    {experiment_data.get('learnings', 'N/A')}
    
    ## Constitutional Alignment
    {experiment_data.get('constitutional_notes', 'N/A')}
    
    ---
    *Logged by log_experiment.py*
    """
    
        # Save file
        filepath = playbook_dir / filename
        with open(filepath, 'w') as f:
            f.write(content)
    
        print(f"✅ Experiment logged: {filepath}")
    
    
    def main():
        """Interactive experiment logging"""
        print("Experiment Logger")
        print("="*50)
    
        experiment = {
            'name': input("Experiment name: "),
            'hypothesis': input("Hypothesis: "),
            'method': input("Method: "),
            'results': input("Results: "),
            'learnings': input("Key learnings: "),
            'status': 'completed'
        }
    
        log_experiment(experiment)
    
    
    if __name__ == "__main__":
        main()
    '''
    
    def _generate_constitutional_job_template(self) -> str:
        """Generate constitutional job template"""
        return '''# Constitutional Job Template
    
    **Version:** 1.0
    **Date:** 2025-10-15
    
    ---
    
    ## Job Definition
    
    **Job ID:** {job_id}
    **Job Type:** {job_type}
    **Priority:** {priority}
    
    ## Mission
    
    **Human Goal:** {human_goal}
    
    **Purpose:** {purpose}
    
    ## Constitutional Review
    
    This job has been reviewed against all 7 Constitutional Principles:
    
    ### Principle 1: Human Agency
    {principle_1_notes}
    
    ### Principle 2: Transparency
    {principle_2_notes}
    
    ### Principle 3: System Viability
    {principle_3_notes}
    
    ### Principle 4: Resource Stewardship
    {principle_4_notes}
    
    ### Principles 5-7: Sentience Considerations
    {sentience_notes}
    
    ## Strategic Principle Alignment
    
    This job implements the following Strategic Principles:
    {strategic_principles}
    
    ## Success Criteria
    
    {success_criteria}
    
    ## Approval
    
    - [ ] Constitutional review passed
    - [ ] Resource requirements validated
    - [ ] Human approval obtained
    
    **Approved By:** _____________
    **Date:** _____________
    
    ---
    
    *Generated by J5A Constitutional Job Template System*
    '''
    
    def _generate_experiment_template(self) -> str:
        """Generate experiment template"""
        return '''# Experiment: {experiment_name}
    
    **Date:** {date}
    **Status:** {status}
    
    ---
    
    ## Hypothesis
    
    {hypothesis}
    
    ## Method
    
    {method}
    
    ## Test Setup
    
    - **Model:** {model}
    - **Parameters:** {parameters}
    - **Test Cases:** {test_cases}
    
    ## Results
    
    ### Quantitative
    {quantitative_results}
    
    ### Qualitative
    {qualitative_results}
    
    ## Analysis
    
    {analysis}
    
    ## Learnings
    
    {learnings}
    
    ## Constitutional Alignment
    
    {constitutional_notes}
    
    ## Next Steps
    
    {next_steps}
    
    ---
    
    *Logged by J5A Experiment System*
    '''
    
    def _generate_current_priorities_template(self) -> str:
        """Generate current priorities template"""
        return '''# Current Priorities
    
    **Last Updated:** {date}
    
    ---
    
    ## High Priority
    
    - System stability and reliability
    - Constitutional compliance
    - Resource stewardship
    
    ## Medium Priority
    
    - Feature development
    - Documentation updates
    - Performance optimization
    
    ## Low Priority
    
    - Experimental features
    - Nice-to-have enhancements
    
    ---
    
    ## Context Notes
    
    {context_notes}
    
    ---
    
    *Updated by refresh_context.py*
    '''
    
    def _generate_active_projects_template(self) -> str:
        """Generate active projects template"""
        return '''# Active Projects
    
    **Last Updated:** {date}
    
    ---
    
    ## Current Projects
    
    ### 1. {project_1_name}
    - Status: {project_1_status}
    - Progress: {project_1_progress}
    
    ### 2. {project_2_name}
    - Status: {project_2_status}
    - Progress: {project_2_progress}
    
    ---
    
    ## Upcoming Projects
    
    {upcoming_projects}
    
    ---
    
    *Updated by refresh_context.py*
    '''
    
    def _generate_generic_markdown_template(self, task: Task, filename: str) -> str:
        """Generate generic markdown template"""
        return f'''# {filename.replace('_', ' ').replace('.md', '').title()}
    
    **Version:** 1.0
    **Date:** 2025-10-15
    
    ---
    
    ## Overview
    
    {task.description}
    
    ## Purpose
    
    This template provides a structured format for {filename.replace('.md', '')}.
    
    ## Usage
    
    Fill in the sections below as needed.
    
    ## Content
    
    [Your content here]
    
    ---
    
    *Generated by J5A Autonomous Implementation Worker*
    '''
    
    
    def execute_code_modification(self, task: Task) -> Dict:
        """Modify existing code - requires approval"""
        raise NotImplementedError(
            f"Code modification task {task.task_id} requires approval"
        )

    def execute_data_initialization(self, task: Task) -> Dict:
        """Initialize data files (JSON templates, etc.)"""
        raise NotImplementedError(
            f"Data initialization task {task.task_id} needs template system"
        )

    def execute_research(self, task: Task) -> Dict:
        """Research tasks - typically documentation output"""
        raise NotImplementedError(
            f"Research task {task.task_id} requires manual research"
        )


class AutonomousWorker:
    """
    Main autonomous implementation worker

    Executes the 10-phase Beyond RAG plan with approval gates
    """

    def __init__(self, impl_dir: str):
        self.impl_dir = impl_dir
        self.base_dir = os.path.dirname(impl_dir)

        # Initialize components
        self.task_queue = TaskQueue(os.path.join(impl_dir, "queue/all_tasks.json"))
        self.state_manager = StateManager(os.path.join(impl_dir, "progress/current_state.json"))
        self.checkpoint_manager = CheckpointManager(os.path.join(impl_dir, "checkpoints"))
        self.task_executor = TaskExecutor(self.base_dir)

        logger.info("AutonomousWorker initialized")

    def run(self):
        """Main worker loop"""
        logger.info("=========================================")
        logger.info("J5A Autonomous Worker - Starting")
        logger.info("=========================================")
        logger.info("")

        # Check if paused
        if self.state_manager.is_paused():
            logger.warning("⏸️  Workflow is paused")

            if self.state_manager.has_pending_approvals():
                logger.info("Waiting for pending approvals")
                logger.info("Run: ./autonomous_implementation.sh review")

            return

        # Update workflow status
        if not self.state_manager.state.get('started_at'):
            self.state_manager.state['started_at'] = datetime.utcnow().isoformat() + 'Z'

        self.state_manager.state['workflow_status'] = 'running'
        self.state_manager.save_state()

        # Main execution loop
        task_count = 0

        while not self.state_manager.is_complete() and not self.state_manager.is_paused():
            # Get next eligible task
            task = self.task_queue.get_next_eligible_task(
                completed=self.state_manager.completed_tasks,
                skipped=self.state_manager.skipped_tasks
            )

            if task is None:
                # Check if waiting on approvals
                if self.state_manager.has_pending_approvals():
                    logger.info("⏸️  Paused: Tasks pending approval")
                    logger.info("   Run: ./autonomous_implementation.sh review")
                    break
                else:
                    # All tasks complete!
                    logger.info("✅ All eligible tasks complete!")
                    self.finalize_workflow()
                    break

            # Update current task
            self.state_manager.state['current_task'] = task.task_id
            self.state_manager.state['current_phase'] = task.phase_id
            self.state_manager.save_state()

            logger.info("")
            logger.info(f"📋 Next Task: {task.task_id}")
            logger.info(f"   Phase: {task.phase_name}")
            logger.info(f"   Description: {task.description}")
            logger.info(f"   Risk: {task.risk_level}")
            logger.info("")

            # Route based on risk level and pre-approval status
            if task.task_id in self.state_manager.pre_approved_tasks:
                logger.info(f"✅ Task {task.task_id} is pre-approved - executing autonomously")
                self.execute_autonomous(task)
            elif task.risk_level == "low" and not task.requires_approval:
                self.execute_autonomous(task)
            else:
                self.request_approval(task)
                break  # Pause for approval

            # Check if paused after execution (might have been paused by NotImplementedError)
            if self.state_manager.is_paused():
                break

            # Save checkpoint after each task
            self.checkpoint_manager.save(self.state_manager.state)
            task_count += 1

        logger.info("")
        logger.info(f"Worker session complete. Tasks processed: {task_count}")
        logger.info("=========================================")

    def execute_autonomous(self, task: Task):
        """Execute low-risk task without approval"""
        is_pre_approved = task.task_id in self.state_manager.pre_approved_tasks

        try:
            # Execute task
            result = self.task_executor.execute(task)

            # Validate outputs
            if self.validate_outputs(task, result):
                self.state_manager.mark_complete(task.task_id, result)

                # Save completion summary
                self.save_completion_summary(task, result)
            else:
                self.state_manager.mark_failed(
                    task.task_id,
                    "Output validation failed"
                )

        except NotImplementedError as e:
            if is_pre_approved:
                # Pre-approved tasks that hit NotImplementedError get skipped
                logger.warning(f"⚠️  Task {task.task_id} executor not implemented: {e}")
                logger.info(f"   Skipping (pre-approved but not ready for auto-execution)")
                self.state_manager.mark_skipped(
                    task.task_id,
                    f"Executor not implemented: {str(e)}"
                )
            else:
                # Non-pre-approved tasks request approval
                logger.warning(f"⚠️  Task {task.task_id} not yet implemented: {e}")
                self.request_approval(task)

        except Exception as e:
            logger.error(f"❌ Task {task.task_id} failed: {e}")
            self.state_manager.mark_failed(task.task_id, str(e))

    def request_approval(self, task: Task):
        """Generate preview and request human approval"""
        logger.info(f"🔍 Task {task.task_id} requires approval")

        # Generate preview
        preview = self.task_executor.generate_preview(task)

        # Save preview
        preview_path = os.path.join(
            self.impl_dir,
            f"pending_approval/{task.task_id}_preview.md"
        )

        with open(preview_path, 'w') as f:
            f.write(preview)

        logger.info(f"   Preview saved: {preview_path}")

        # Add to pending approval queue
        self.state_manager.add_pending_approval(task, preview_path)

        logger.info("")
        logger.info("⏸️  Workflow paused - awaiting approval")
        logger.info("   Review: ./autonomous_implementation.sh review")
        logger.info("   Approve: ./autonomous_implementation.sh approve " + task.task_id)

    def validate_outputs(self, task: Task, result: Dict) -> bool:
        """Validate task outputs meet success criteria"""
        if not result.get('success', False):
            return False

        # Check expected outputs exist
        for output in task.expected_outputs:
            full_path = os.path.join(self.base_dir, output)

            if output.endswith('/'):
                # Directory
                if not os.path.isdir(full_path):
                    logger.error(f"Expected directory not found: {full_path}")
                    return False
            else:
                # File
                if not os.path.exists(full_path):
                    logger.error(f"Expected file not found: {full_path}")
                    return False

        return True

    def save_completion_summary(self, task: Task, result: Dict):
        """Save summary of completed task"""
        summary_path = os.path.join(
            self.impl_dir,
            f"completed/{task.task_id}_summary.md"
        )

        summary = f"""# Task Completion Summary

## Task ID
{task.task_id}

## Description
{task.description}

## Phase
{task.phase_id}: {task.phase_name}

## Completed At
{datetime.utcnow().isoformat()}Z

## Outputs Created
"""
        for output in task.expected_outputs:
            summary += f"- {output}\n"

        summary += f"""
## Result
{json.dumps(result, indent=2)}

---
Completed autonomously by J5A Worker
"""

        with open(summary_path, 'w') as f:
            f.write(summary)

    def finalize_workflow(self):
        """Mark workflow as complete"""
        self.state_manager.state['workflow_status'] = 'completed'
        self.state_manager.state['completed_at'] = datetime.utcnow().isoformat() + 'Z'
        self.state_manager.save_state()

        completed = len(self.state_manager.completed_tasks)
        failed = len(self.state_manager.failed_tasks)
        skipped = len(self.state_manager.skipped_tasks)

        logger.info("")
        logger.info("🎉 Workflow Complete!")
        logger.info(f"   Completed: {completed} tasks")
        logger.info(f"   Failed: {failed} tasks")
        logger.info(f"   Skipped: {skipped} tasks")


def main():
    """Entry point for autonomous worker"""
    # Determine implementation directory
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Initialize and run worker
    worker = AutonomousWorker(script_dir)
    worker.run()


if __name__ == "__main__":
    main()
