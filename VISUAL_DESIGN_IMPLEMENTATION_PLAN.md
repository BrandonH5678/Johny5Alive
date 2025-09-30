# Squirt Visual Design Extension - 4-Phase Implementation Plan

**Date:** 2025-09-30
**Status:** Ready for J5A Queue Management
**Priority:** NORMAL (incremental, non-blocking)
**Dependencies:** Phase 3 blocked until 16GB RAM upgrade completed

---

## Overview

Extend Squirt with visual media workflows (concept renders, CAD/STL outputs, AR mockups) while maintaining system stability and integrating with existing validation frameworks. Implementation proceeds in 4 phases with Phase 3 deferred until RAM upgrade.

---

## Phase 1: Foundation & Data Models (Week 1)

**Status:** Ready to begin
**Risk Level:** LOW
**Blocking Issues:** None

### Goals
- Create folder structure and stub modules
- Define data schemas and models
- Set up vector DB for design memory
- Establish validation framework
- Zero impact on existing systems

### Tasks

#### Task 1.1: Create Folder Structure
```bash
mkdir -p visual/prompts visual/schemas visual/sd visual/cad visual/ar
mkdir -p memory/index
touch visual/__init__.py memory/__init__.py
```

**Expected Outputs:**
- `visual/` folder with subfolders
- `memory/` folder with index subfolder
- Empty `__init__.py` files

**Success Criteria:**
- All folders exist
- No impact on existing Squirt functionality
- Folder structure matches design spec

**Validation:**
- Directory structure check: `ls -la visual/ memory/`
- No existing files overwritten

#### Task 1.2: Define Data Schemas
**File:** `visual/schemas/tasks.py`

```python
from pydantic import BaseModel, Field
from typing import Optional, Dict, List
from datetime import datetime

class VisualTask(BaseModel):
    """Visual processing task definition"""
    project_id: str = Field(..., description="Client project identifier")
    task_type: str = Field(..., description="Type: concept, cad, ar")
    params: Dict = Field(default_factory=dict, description="Task-specific parameters")
    context: Optional[str] = Field(None, description="Additional context from memory")
    created_at: datetime = Field(default_factory=datetime.now)

class DesignMemory(BaseModel):
    """Design registry entry"""
    project_id: str
    task_type: str
    version: int
    inputs: Dict
    outputs: Dict
    constraints_honored: List[str]
    hash: str
    timestamp: datetime = Field(default_factory=datetime.now)
```

**Expected Outputs:**
- `visual/schemas/tasks.py` with complete Pydantic models

**Success Criteria:**
- Models instantiate without errors
- All fields properly typed
- Validation working (try invalid data)

**Test Oracle:**
```python
# Should succeed
task = VisualTask(project_id="test", task_type="cad", params={})

# Should fail validation
invalid = VisualTask(project_id="", task_type="invalid")
```

#### Task 1.3: Vector DB Setup
**File:** `memory/vector_store.py`

```python
import chromadb
from chromadb.config import Settings
from pathlib import Path
import json
from typing import List, Dict, Optional

class DesignMemoryStore:
    """Vector database for design context and history"""

    def __init__(self, persist_dir: str = "./memory/index"):
        self.persist_dir = Path(persist_dir)
        self.persist_dir.mkdir(parents=True, exist_ok=True)

        self.client = chromadb.Client(Settings(
            persist_directory=str(self.persist_dir),
            anonymized_telemetry=False
        ))

        self.collection = self.client.get_or_create_collection(
            name="squirt_designs",
            metadata={"description": "Design context and history"}
        )

        self.registry_path = Path("memory/design_registry.jsonl")
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)
        self.registry_path.touch(exist_ok=True)

    def add_design(self, design: Dict, embedding_text: str):
        """Add design to vector DB and registry"""
        design_id = f"{design['project_id']}_v{design['version']}"

        # Add to vector DB
        self.collection.add(
            documents=[embedding_text],
            metadatas=[design],
            ids=[design_id]
        )

        # Append to registry
        with open(self.registry_path, 'a') as f:
            f.write(json.dumps(design) + '\n')

    def find_similar(self, query: str, n_results: int = 5) -> List[Dict]:
        """Find similar designs by query"""
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results
        )
        return results['metadatas'][0] if results['metadatas'] else []

    def get_project_history(self, project_id: str) -> List[Dict]:
        """Get all versions for a project"""
        results = self.collection.get(
            where={"project_id": project_id}
        )
        return results['metadatas'] if results else []
```

**Expected Outputs:**
- `memory/vector_store.py` with complete implementation
- `memory/design_registry.jsonl` created
- Vector DB initialized in `memory/index/`

**Success Criteria:**
- Can add design to DB
- Can query similar designs
- Can retrieve project history
- Persistence working (survives restart)

**Test Oracle:**
```python
store = DesignMemoryStore()
design = {
    "project_id": "test",
    "task_type": "cad",
    "version": 1,
    "inputs": {},
    "outputs": {},
    "constraints_honored": [],
    "hash": "abc123"
}
store.add_design(design, "test design for irrigation system")
results = store.find_similar("irrigation")
assert len(results) > 0
```

#### Task 1.4: Validation Framework
**File:** `visual/validators.py`

```python
from pathlib import Path
from PIL import Image
import trimesh
from typing import Dict, Optional, Tuple

class ValidationResult:
    """Validation result with pass/fail and details"""
    def __init__(self, passed: bool, message: str, details: Dict = None):
        self.passed = passed
        self.message = message
        self.details = details or {}

def validate_image(
    path: str,
    min_dpi: int = 150,
    min_width: int = 800,
    min_height: int = 600,
    max_size_mb: float = 50.0
) -> ValidationResult:
    """
    Validate image file

    Checks:
    - File exists and readable
    - Resolution meets minimums
    - File size within limits
    - Valid image format
    """
    file_path = Path(path)

    # Existence check
    if not file_path.exists():
        return ValidationResult(False, f"File not found: {path}")

    try:
        img = Image.open(file_path)

        # Resolution check
        width, height = img.size
        if width < min_width or height < min_height:
            return ValidationResult(
                False,
                f"Resolution too low: {width}x{height} < {min_width}x{min_height}"
            )

        # DPI check (if available)
        dpi = img.info.get('dpi')
        if dpi and min(dpi) < min_dpi:
            return ValidationResult(
                False,
                f"DPI too low: {min(dpi)} < {min_dpi}"
            )

        # File size check
        size_mb = file_path.stat().st_size / (1024 * 1024)
        if size_mb > max_size_mb:
            return ValidationResult(
                False,
                f"File too large: {size_mb:.1f}MB > {max_size_mb}MB"
            )

        return ValidationResult(
            True,
            "Image validation passed",
            {"width": width, "height": height, "format": img.format, "size_mb": size_mb}
        )

    except Exception as e:
        return ValidationResult(False, f"Image validation error: {e}")

def validate_stl(
    path: str,
    expected_dims: Optional[Dict[str, float]] = None,
    max_triangles: int = 1000000,
    check_watertight: bool = True
) -> ValidationResult:
    """
    Validate STL file

    Checks:
    - File exists and readable
    - Valid STL format
    - Geometry validity (watertight, manifold)
    - Triangle count within limits
    - Bounding box dimensions (if specified)
    """
    file_path = Path(path)

    # Existence check
    if not file_path.exists():
        return ValidationResult(False, f"File not found: {path}")

    try:
        mesh = trimesh.load(file_path)

        # Triangle count check
        if len(mesh.faces) > max_triangles:
            return ValidationResult(
                False,
                f"Too many triangles: {len(mesh.faces)} > {max_triangles}"
            )

        # Geometry validity
        if check_watertight and not mesh.is_watertight:
            return ValidationResult(False, "Mesh is not watertight")

        # Bounding box check
        bounds = mesh.bounds
        bbox = {
            'min': bounds[0].tolist(),
            'max': bounds[1].tolist(),
            'dimensions': (bounds[1] - bounds[0]).tolist()
        }

        if expected_dims:
            actual_dims = bounds[1] - bounds[0]
            for axis, expected in expected_dims.items():
                axis_idx = {'x': 0, 'y': 1, 'z': 2}[axis.lower()]
                if abs(actual_dims[axis_idx] - expected) > expected * 0.1:  # 10% tolerance
                    return ValidationResult(
                        False,
                        f"Dimension mismatch on {axis}: {actual_dims[axis_idx]:.2f} != {expected:.2f}"
                    )

        return ValidationResult(
            True,
            "STL validation passed",
            {
                "triangles": len(mesh.faces),
                "vertices": len(mesh.vertices),
                "watertight": mesh.is_watertight,
                "bounds": bbox
            }
        )

    except Exception as e:
        return ValidationResult(False, f"STL validation error: {e}")
```

**Expected Outputs:**
- `visual/validators.py` with complete validation functions
- ValidationResult class for structured results

**Success Criteria:**
- Image validation catches invalid images
- STL validation catches invalid geometry
- Proper error messages for each failure type
- Details provided on success

**Test Oracle:**
Create test images/STLs with known properties and verify validation results.

---

## Phase 2: Integration & Coordination (Week 2-3)

**Status:** Waiting for Phase 1 completion
**Risk Level:** MEDIUM
**Blocking Issues:** Requires Phase 1 complete

### Goals
- Integrate with existing Squirt systems
- Add thermal safety and business hours coordination
- Wire into voice input and queue management
- Create comprehensive test suite
- Maintain system stability

### Tasks

#### Task 2.1: Thermal Safety Integration
**File:** `visual/thermal_coordinator.py`

```python
import sys
sys.path.append('/home/johnny5/Squirt')
from src.thermal_safety_manager import ThermalSafetyManager

class VisualThermalCoordinator:
    """Thermal safety for visual processing tasks"""

    def __init__(self):
        self.thermal_manager = ThermalSafetyManager()

    def check_safe_for_visual_task(self, task_type: str) -> bool:
        """Check if thermal conditions allow visual processing"""

        # Different thresholds for different tasks
        thresholds = {
            "concept": 75.0,  # Light work (cloud API calls)
            "cad": 78.0,      # Medium work (OpenSCAD rendering)
            "ar": 75.0        # Light work (cloud compositing)
        }

        max_temp = thresholds.get(task_type, 75.0)
        return self.thermal_manager.is_safe_to_proceed(max_temp)

    def monitor_during_processing(self, callback=None):
        """Monitor temperature during long visual tasks"""
        return self.thermal_manager.monitor_continuous(callback)
```

**Expected Outputs:**
- `visual/thermal_coordinator.py` with thermal integration
- Pre-flight thermal checks for all visual tasks

**Success Criteria:**
- Thermal checks block tasks when CPU too hot
- Integration with existing thermal_safety_manager working
- Different thresholds for different task types

#### Task 2.2: Business Hours Coordination
**File:** `visual/business_coordinator.py`

```python
import sys
sys.path.append('/home/johnny5/Squirt')
from src.libreoffice_coordinator import LibreOfficeCoordinator
from datetime import datetime

class VisualBusinessCoordinator:
    """Coordinate visual tasks with business operations"""

    def __init__(self):
        self.lo_coordinator = LibreOfficeCoordinator()

    def is_visual_task_allowed(self, task_type: str, priority: str = "normal") -> bool:
        """Check if visual task can run now"""

        # High priority visual tasks (client requests) can run during business hours
        if priority == "high":
            return True

        # Normal/low priority visual tasks should wait for off-hours
        if self.lo_coordinator.is_business_hours():
            return False

        return True

    def get_next_available_slot(self) -> datetime:
        """Get next time slot when visual processing can run"""
        return self.lo_coordinator.get_next_off_hours_window()
```

**Expected Outputs:**
- `visual/business_coordinator.py` with business hours logic
- Integration with LibreOffice coordinator

**Success Criteria:**
- Visual tasks respect business hours (6am-7pm Mon-Fri)
- High priority tasks can override during business hours
- Queue system defers low priority tasks to off-hours

#### Task 2.3: Queue Integration
**File:** `visual/visual_queue_manager.py`

```python
import sys
sys.path.append('/home/johnny5/Squirt')
from src.voice_queue_manager import VoiceQueueManager
from visual.schemas.tasks import VisualTask
from visual.thermal_coordinator import VisualThermalCoordinator
from visual.business_coordinator import VisualBusinessCoordinator
from typing import Optional
import json
from pathlib import Path

class VisualQueueManager:
    """Queue manager for visual processing tasks"""

    def __init__(self):
        self.queue_file = Path("visual_queue.json")
        self.thermal = VisualThermalCoordinator()
        self.business = VisualBusinessCoordinator()
        self.queue = self._load_queue()

    def enqueue(self, task: VisualTask, priority: str = "normal") -> str:
        """Add visual task to queue"""

        # Check if can run now
        can_run_now = (
            self.thermal.check_safe_for_visual_task(task.task_type) and
            self.business.is_visual_task_allowed(task.task_type, priority)
        )

        task_entry = {
            "task": task.dict(),
            "priority": priority,
            "status": "ready" if can_run_now else "queued",
            "enqueued_at": task.created_at.isoformat()
        }

        self.queue.append(task_entry)
        self._save_queue()

        return task.project_id

    def get_next_task(self) -> Optional[VisualTask]:
        """Get next ready task from queue"""

        for entry in self.queue:
            if entry["status"] == "ready":
                # Double-check thermal and business hours
                task = VisualTask(**entry["task"])
                if (self.thermal.check_safe_for_visual_task(task.task_type) and
                    self.business.is_visual_task_allowed(task.task_type, entry["priority"])):
                    entry["status"] = "processing"
                    self._save_queue()
                    return task

        return None

    def mark_complete(self, project_id: str):
        """Mark task as complete"""
        for entry in self.queue:
            if entry["task"]["project_id"] == project_id:
                entry["status"] = "complete"
                break
        self._save_queue()

    def _load_queue(self):
        if self.queue_file.exists():
            with open(self.queue_file) as f:
                return json.load(f)
        return []

    def _save_queue(self):
        with open(self.queue_file, 'w') as f:
            json.dump(self.queue, f, indent=2)
```

**Expected Outputs:**
- `visual/visual_queue_manager.py` with queue management
- Integration with thermal and business coordinators
- Persistent queue storage

**Success Criteria:**
- Tasks can be enqueued
- Thermal/business checks enforced
- Queue persists across restarts
- Tasks retrieved in priority order

#### Task 2.4: Voice Input Integration
**File:** `visual/voice_visual_commands.py`

```python
from visual.schemas.tasks import VisualTask
from visual.visual_queue_manager import VisualQueueManager
import re

class VisualVoiceCommands:
    """Parse voice commands for visual tasks"""

    def __init__(self):
        self.queue = VisualQueueManager()

    def parse_visual_command(self, transcription: str, project_id: str) -> Optional[VisualTask]:
        """Extract visual task from voice transcription"""

        text = transcription.lower()

        # CAD generation patterns
        cad_patterns = [
            r"generate (?:a )?cad (?:model|file)",
            r"create (?:a )?stl",
            r"design (?:a )?(?:pipe|fitting|component)",
        ]

        # Concept render patterns
        concept_patterns = [
            r"show (?:me )?(?:a )?concept",
            r"visualize",
            r"render (?:a )?layout",
        ]

        # AR mockup patterns
        ar_patterns = [
            r"add (?:a )?(?:pergola|fence|deck) to (?:the )?(?:photo|picture)",
            r"place (?:a )?(?:structure|object) in",
        ]

        # Determine task type
        task_type = None
        if any(re.search(p, text) for p in cad_patterns):
            task_type = "cad"
        elif any(re.search(p, text) for p in concept_patterns):
            task_type = "concept"
        elif any(re.search(p, text) for p in ar_patterns):
            task_type = "ar"

        if not task_type:
            return None

        # Create task
        task = VisualTask(
            project_id=project_id,
            task_type=task_type,
            params={"source": "voice", "transcription": transcription}
        )

        return task

    def enqueue_from_voice(self, transcription: str, project_id: str, priority: str = "normal") -> Optional[str]:
        """Parse voice command and enqueue if visual task detected"""
        task = self.parse_visual_command(transcription, project_id)
        if task:
            return self.queue.enqueue(task, priority)
        return None
```

**Expected Outputs:**
- `visual/voice_visual_commands.py` with voice parsing
- Pattern matching for visual commands
- Integration with queue manager

**Success Criteria:**
- Voice commands like "generate a CAD model" detected
- Tasks automatically enqueued from voice input
- Works with existing voice processing pipeline

#### Task 2.5: Comprehensive Testing
**File:** `tests/test_visual_foundation.py`

```python
import pytest
from visual.schemas.tasks import VisualTask
from memory.vector_store import DesignMemoryStore
from visual.validators import validate_image, validate_stl
from visual.visual_queue_manager import VisualQueueManager

class TestVisualSchemas:
    def test_visual_task_creation(self):
        task = VisualTask(
            project_id="test",
            task_type="cad",
            params={"units": "mm"}
        )
        assert task.project_id == "test"
        assert task.task_type == "cad"

    def test_invalid_task_fails(self):
        with pytest.raises(Exception):
            VisualTask(project_id="", task_type="invalid")

class TestMemoryStore:
    def test_add_and_retrieve(self):
        store = DesignMemoryStore(persist_dir="./test_memory")
        design = {
            "project_id": "test",
            "task_type": "cad",
            "version": 1,
            "inputs": {},
            "outputs": {},
            "constraints_honored": [],
            "hash": "test123"
        }
        store.add_design(design, "test irrigation CAD model")
        results = store.find_similar("irrigation")
        assert len(results) > 0

class TestValidators:
    def test_image_validation_missing_file(self):
        result = validate_image("nonexistent.png")
        assert not result.passed

    def test_stl_validation_missing_file(self):
        result = validate_stl("nonexistent.stl")
        assert not result.passed

class TestQueueIntegration:
    def test_enqueue_task(self):
        queue = VisualQueueManager()
        task = VisualTask(
            project_id="test_queue",
            task_type="concept",
            params={}
        )
        task_id = queue.enqueue(task, priority="normal")
        assert task_id == "test_queue"
```

**Expected Outputs:**
- `tests/test_visual_foundation.py` with comprehensive tests
- All Phase 1 and 2 components tested

**Success Criteria:**
- All tests pass
- 80%+ code coverage
- Integration tests verify cross-component functionality

---

## Phase 3: Processing Engines (BLOCKED - Waiting for 16GB RAM)

**Status:** BLOCKED until RAM upgrade
**Risk Level:** HIGH (until RAM upgraded, then MEDIUM)
**Blocking Issues:** 3.7GB RAM insufficient for local Stable Diffusion

### Goals
- Implement CAD generation (OpenSCAD, FreeCAD)
- Implement cloud-based image generation
- Implement AR compositing
- Add local Stable Diffusion AFTER RAM upgrade
- Maintain thermal safety throughout

### Tasks

#### Task 3.1: CAD Engine - OpenSCAD
**File:** `visual/cad/openscad_engine.py`

```python
import subprocess
import tempfile
from pathlib import Path
from visual.thermal_coordinator import VisualThermalCoordinator
from typing import Optional

class OpenSCADEngine:
    """OpenSCAD CAD generation with thermal monitoring"""

    def __init__(self):
        self.thermal = VisualThermalCoordinator()

    def generate_stl(
        self,
        scad_code: str,
        output_file: str,
        timeout: int = 300
    ) -> Optional[str]:
        """
        Generate STL from OpenSCAD code

        Args:
            scad_code: OpenSCAD code string
            output_file: Output STL file path
            timeout: Max seconds for rendering

        Returns:
            Path to generated STL or None if failed
        """

        # Pre-flight thermal check
        if not self.thermal.check_safe_for_visual_task("cad"):
            raise Exception("System too hot for CAD generation")

        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Write SCAD code to temp file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.scad', delete=False) as f:
            f.write(scad_code)
            scad_file = f.name

        try:
            # Run OpenSCAD
            result = subprocess.run(
                ['openscad', '-o', str(output_path), scad_file],
                timeout=timeout,
                capture_output=True,
                text=True
            )

            if result.returncode != 0:
                raise Exception(f"OpenSCAD failed: {result.stderr}")

            if not output_path.exists():
                raise Exception("STL file not generated")

            return str(output_path)

        finally:
            # Cleanup temp file
            Path(scad_file).unlink(missing_ok=True)
```

**Expected Outputs:**
- `visual/cad/openscad_engine.py` with OpenSCAD integration
- Thermal safety checks before rendering
- Error handling and cleanup

**Success Criteria:**
- Can generate STL from SCAD code
- Thermal checks prevent overheating
- Timeout prevents hung processes
- Clean error messages on failure

**Test Oracle:**
```python
engine = OpenSCADEngine()
code = "cube([50,50,50]);"
output = engine.generate_stl(code, "./test_cube.stl")
assert Path(output).exists()
assert validate_stl(output).passed
```

#### Task 3.2: Cloud Image Generation (Stability API)
**File:** `visual/sd/cloud_engine.py`

```python
import requests
from pathlib import Path
from typing import Optional, Dict
import os

class StabilityCloudEngine:
    """Cloud-based image generation via Stability API"""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('STABILITY_API_KEY')
        if not self.api_key:
            raise ValueError("STABILITY_API_KEY required")

        self.base_url = "https://api.stability.ai/v1/generation"

    def generate_image(
        self,
        prompt: str,
        output_file: str,
        width: int = 1024,
        height: int = 1024,
        steps: int = 30,
        cfg_scale: float = 7.0
    ) -> Optional[str]:
        """
        Generate image via Stability API

        Args:
            prompt: Text description
            output_file: Output image path
            width: Image width
            height: Image height
            steps: Inference steps (quality)
            cfg_scale: How closely to follow prompt

        Returns:
            Path to generated image or None
        """

        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # API request
        response = requests.post(
            f"{self.base_url}/stable-diffusion-xl-1024-v1-0/text-to-image",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            },
            json={
                "text_prompts": [{"text": prompt}],
                "width": width,
                "height": height,
                "steps": steps,
                "cfg_scale": cfg_scale
            }
        )

        if response.status_code != 200:
            raise Exception(f"Stability API error: {response.text}")

        # Save image
        for artifact in response.json()["artifacts"]:
            if artifact["finishReason"] == "SUCCESS":
                import base64
                image_data = base64.b64decode(artifact["base64"])
                with open(output_path, 'wb') as f:
                    f.write(image_data)
                return str(output_path)

        return None
```

**Expected Outputs:**
- `visual/sd/cloud_engine.py` with Stability API integration
- Cloud-based image generation
- No local resource requirements

**Success Criteria:**
- Can generate images via API
- API key management working
- Error handling for API failures
- Images saved correctly

**Prerequisites:**
- Stability API key (requires sign-up and billing)
- Alternative: Use Replicate or HuggingFace Inference API

#### Task 3.3: Local Stable Diffusion (DEFERRED)
**File:** `visual/sd/local_engine.py`

**Status:** DEFERRED until 16GB RAM upgrade completed

**Implementation Notes:**
- Use `diffusers` library
- Quantized models only (<=2GB)
- CPU inference with INT8 optimization
- Strict memory monitoring
- Thermal safety integration
- Fall back to cloud if local fails

**Memory Requirements:**
- Model: ~2GB (quantized SD 1.5)
- Runtime: ~2-3GB
- Total: ~5GB minimum
- **Current system: 3.7GB - INSUFFICIENT**
- **After upgrade: 16GB - SUFFICIENT**

---

## Phase 4: Advanced Features (Week 4+)

**Status:** Future work
**Risk Level:** LOW
**Blocking Issues:** Requires Phase 1-3 complete

### Goals
- Enhance prompt template system
- Add advanced metadata embedding
- Implement ControlNet for guided generation
- Create comprehensive operator manual
- Performance optimization

### Tasks

#### Task 4.1: Prompt Template System
**File:** `visual/prompts/template_engine.py`

Create YAML-based prompt templates with constraint injection:

```yaml
# visual/prompts/irrigation_layout.yml
name: "Irrigation Layout Concept"
description: "Generate overhead view of irrigation system"
base_prompt: |
  Professional landscape architecture rendering, overhead view,
  {num_zones} irrigation zones, {spacing} spacing between heads,
  {coverage} coverage pattern, {style} style
constraints:
  - units: ["feet", "meters"]
  - num_zones: [1, 20]
  - spacing: ["5ft", "10ft", "15ft", "20ft"]
  - coverage: ["full", "partial", "corners"]
  - style: ["technical", "artistic", "photorealistic"]
validation:
  - check_units_consistent
  - verify_zone_count
```

#### Task 4.2: Metadata Enhancement
**File:** `visual/metadata.py`

Implement comprehensive metadata tracking:
- Embed generation params in image EXIF
- Link to design registry
- Track constraint provenance
- Version control for iterative designs
- JSON sidecar files with full context

#### Task 4.3: ControlNet Integration
**File:** `visual/sd/controlnet_engine.py`

Add guided generation with ControlNet:
- Depth-based composition for AR
- Sketch-to-render for concept development
- Segmentation for site photo integration
- Edge detection for CAD-to-render

#### Task 4.4: Visual Operator Manual
**File:** `VISUAL_WORKFLOWS_OPERATOR_MANUAL.md`

Document:
- Visual workflow protocols
- Thermal safety for visual tasks
- Business hours coordination
- Validation requirements
- Prompt engineering guidelines
- Memory system usage
- Troubleshooting guide

---

## Dependencies Installation

### Phase 1 Dependencies
```bash
# Core dependencies (lightweight)
pip install pydantic chromadb pillow trimesh

# Optional for enhanced validation
pip install python-magic  # File type detection
```

### Phase 2 Dependencies
```bash
# No new dependencies - uses existing Squirt components
```

### Phase 3 Dependencies
```bash
# OpenSCAD (system package)
sudo apt-get install openscad

# Cloud API client
pip install requests

# For local SD (AFTER RAM upgrade only)
pip install diffusers transformers accelerate safetensors torch torchvision
```

### Phase 4 Dependencies
```bash
# Enhanced image processing
pip install opencv-python
pip install controlnet_aux  # For ControlNet preprocessing
```

---

## Risk Mitigation

### Critical Risks

1. **RAM Constraints**
   - **Mitigation:** Cloud-only approach until RAM upgrade
   - **Status:** Phase 3 blocked until hardware upgrade

2. **Thermal Safety**
   - **Mitigation:** Integrated thermal checks, monitoring during processing
   - **Status:** Addressed in Phase 2

3. **Business Operations Interference**
   - **Mitigation:** Business hours coordination, off-hours queuing
   - **Status:** Addressed in Phase 2

4. **System Stability**
   - **Mitigation:** Incremental implementation, comprehensive testing
   - **Status:** Phased approach ensures stability

### Medium Risks

5. **Cloud API Costs**
   - **Mitigation:** Budget monitoring, local fallback after RAM upgrade
   - **Consideration:** Stability API ~$0.01-0.02 per image

6. **Dependency Conflicts**
   - **Mitigation:** Test in isolated environment first
   - **Status:** Phase 1 uses minimal dependencies

7. **Integration Complexity**
   - **Mitigation:** Reuse existing patterns (queue, validation, coordination)
   - **Status:** Phase 2 focuses on integration

---

## J5A Integration

This implementation plan is designed for J5A queue management:

### Task Queueing
```python
from j5a_work_assignment import J5AWorkAssignment, Priority, OutputSpecification
from visual_implementation_tasks import PHASE_1_TASKS

for task in PHASE_1_TASKS:
    j5a_task = J5AWorkAssignment(
        task_id=task.id,
        task_name=task.name,
        domain="system_development",
        description=task.description,
        priority=Priority.NORMAL,
        expected_outputs=task.expected_outputs,
        success_criteria=task.success_criteria,
        test_oracle=task.test_oracle,
        requires_poc=True
    )
    queue.add_task(j5a_task)
```

### Validation Integration
- All tasks use J5A outcome validator (3-layer validation)
- Quality gates enforced (PreFlight, POC, Implementation, Delivery)
- Methodology compliance checked (no shortcuts)

### Execution Scheduling
- Phase 1: Can execute immediately (low risk, no blocking)
- Phase 2: Queued after Phase 1 complete
- Phase 3: BLOCKED until RAM upgrade notification received
- Phase 4: Queued after Phase 3 complete

---

## Success Metrics

### Phase 1
- ✅ All folders and stubs created without errors
- ✅ Vector DB operational and persistent
- ✅ Validators catching invalid inputs
- ✅ 100% test pass rate

### Phase 2
- ✅ Thermal safety integrated and blocking correctly
- ✅ Business hours coordination working
- ✅ Tasks successfully queued and dequeued
- ✅ Voice commands parsed and enqueued
- ✅ No interference with existing Squirt operations

### Phase 3
- ✅ CAD generation producing valid STL files
- ✅ Cloud image generation working
- ✅ All outputs validated before delivery
- ✅ Thermal monitoring preventing overheating
- ⏸️  Local SD deferred until RAM upgrade

### Phase 4
- ✅ Prompt templates functional
- ✅ Metadata system complete
- ✅ Advanced features operational
- ✅ Documentation comprehensive

---

## Timeline

- **Phase 1:** Week 1 (5-7 days)
- **Phase 2:** Week 2-3 (7-10 days)
- **Phase 3:** BLOCKED - Waiting for RAM upgrade (ETA: Monday/Tuesday)
- **Phase 4:** Week 4+ (ongoing, as needed)

**Total Time (excluding Phase 3 block):** 2-3 weeks of incremental implementation

---

## Approval and Execution

**Ready for J5A Queue:** YES
**Blocking Issues:** Phase 3 only (RAM upgrade required)
**Risk Assessment:** LOW (Phase 1-2), MEDIUM (Phase 3 after upgrade), LOW (Phase 4)

**Execution Strategy:**
1. Load Phase 1 tasks into J5A queue
2. Execute Phase 1 with full validation
3. Review Phase 1 results before Phase 2
4. Load Phase 2 tasks upon Phase 1 success
5. HOLD Phase 3 until RAM upgrade notification
6. Phase 4 as enhancement backlog

---

**Document Status:** Ready for J5A ingestion
**Last Updated:** 2025-09-30
**Maintained By:** Squirt Development Team