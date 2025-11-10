# J5A Universe Active Memory & Adaptive Feedback Loop Architecture
## Unified Continuous Improvement Across Squirt, J5A, and Sherlock Systems

**Version:** 1.0
**Last Updated:** 2025-10-16
**Previous Version:** N/A (Initial Release)
**Constitutional Basis:** J5A Constitution Principles 1-7
**Strategic Basis:** Strategic Principles 4 (Active Memory) & 5 (Adaptive Feedback Loops)
**Scope:** Cross-system learning and adaptation for entire J5A ecosystem
**Excludes:** Sherlock podcast processing (already implemented in `PODCAST_CONTINUOUS_IMPROVEMENT_ARCHITECTURE.md`)

## Recent Changes (Since Initial Release)

**Version 1.0 (2025-10-16) - Initial Release**
- Established: Cross-system entity memory (`j5a_universe_memory.py`)
- Defined: 4-Phase Implementation (Unified Memory, Squirt Learning, J5A Learning, Sherlock Extended)
- Integrated: AAR (After Action Review) database schema
- Provided: Learning synthesizer for pattern detection and improvement proposals

**⚠️ CRITICAL CHANGES:** N/A (Initial Release)

---

## TABLE OF CONTENTS

1. [Executive Summary](#executive-summary)
2. [Architectural Overview](#architectural-overview)
3. [Phase 1: Unified Memory Foundation](#phase-1-unified-memory-foundation)
4. [Phase 2: Squirt Learning Systems](#phase-2-squirt-learning-systems)
5. [Phase 3: J5A Queue Management Learning](#phase-3-j5a-queue-management-learning)
6. [Phase 4: Sherlock Extended Learning](#phase-4-sherlock-extended-learning)
7. [Phase 5: Human Oversight Integration](#phase-5-human-oversight-integration)
8. [Phase 6: Cross-System Synthesis](#phase-6-cross-system-synthesis)
9. [Implementation Roadmap](#implementation-roadmap)
10. [Constitutional Alignment](#constitutional-alignment)
11. [Success Metrics](#success-metrics)

---

## EXECUTIVE SUMMARY

### Purpose

This architecture implements **Strategic Principles 4 (Active Memory) and 5 (Adaptive Feedback Loops)** across the entire J5A universe, creating a unified continuous improvement system where every subsystem learns, adapts, and improves through operation.

### Core Design Principles

1. **Unified, Not Siloed:** Single memory store and learning infrastructure shared across all systems
2. **Domain-Specific Adaptation:** Each system (Squirt, J5A, Sherlock) learns in its specialized domain
3. **Constitutional Alignment:** Every adaptation respects human agency, transparency, and resource stewardship
4. **No Duplication:** Leverages existing Sherlock podcast architecture pattern, extends to new domains
5. **Cross-System Learning:** Systems learn from each other's adaptations

### Scope

**High Priority Systems:**
- **Squirt:** Invoice, estimate, contract generation + image generation learning
- **J5A:** Claude Queue and Night Shift Queue operational learning
- **Sherlock:** Intelligence extraction, cross-reference analysis, timeline construction, Sherlock Exchange Format (SEF) evidence sharing

**Explicitly Excluded:** Sherlock podcast processing pipeline (comprehensive implementation already exists)

### Key Outcomes

- **Active Memory:** Every system remembers past performance, decisions, and outcomes
- **Adaptive Feedback Loops:** Systems automatically refine parameters, strategies, and models
- **Human Governance:** All significant adaptations require human approval
- **Cross-System Synthesis:** Learnings transfer between systems (e.g., Squirt voice corrections inform Sherlock diarization)

---

## ARCHITECTURAL OVERVIEW

### The Unified Loop

```
┌─────────────────────────────────────────────────────────────┐
│                    UNIFIED MEMORY LAYER                      │
│  (Shared by Squirt, J5A, Sherlock)                          │
│  - Entity Memory (clients, sources, speakers, people)        │
│  - Performance History (metrics, decisions, outcomes)        │
│  - Context Refresh (priorities, patterns, benchmarks)        │
│  - Decision Provenance (reasoning, alternatives, results)    │
└─────────────────────────────────────────────────────────────┘
                           ↕
        ┌──────────────────┼──────────────────┐
        ↓                  ↓                   ↓
┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│   SQUIRT     │   │     J5A      │   │   SHERLOCK   │
│   Learning   │   │   Learning   │   │   Learning   │
│              │   │              │   │              │
│ • Invoice    │   │ • Claude Q   │   │ • Intel Extr │
│ • Contract   │   │ • Night Q    │   │ • Cross-Ref  │
│ • Estimate   │   │ • Resource   │   │ • Timeline   │
│ • Image Gen  │   │ • Priority   │   │ • SEF Share  │
└──────────────┘   └──────────────┘   └──────────────┘
        ↓                  ↓                   ↓
        └──────────────────┼──────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│           CROSS-SYSTEM LEARNING SYNTHESIS                    │
│  - Pattern Transfer (voice corrections → diarization)        │
│  - Resource Optimization (thermal/memory across systems)     │
│  - Quality Benchmarks (unified standards)                    │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│              HUMAN OVERSIGHT & GOVERNANCE                    │
│  - Constitutional Compliance Checker                         │
│  - Refinement Approval Dashboard                             │
│  - Performance Monitoring                                    │
└─────────────────────────────────────────────────────────────┘
```

### Core Components

**1. Unified Memory Manager (`j5a_universe_memory.py`)**
- Central SQLite database at `/home/johnny5/j5a_universe_memory.db`
- Single source of truth for all systems
- Fast retrieval (<100ms queries)
- Cross-system entity resolution

**2. Domain-Specific Learners**
- `squirt_learner.py` - Business document and image generation learning
- `j5a_learner.py` - Queue management and resource optimization learning
- `sherlock_learner.py` - Intelligence analysis and evidence sharing learning

**3. Cross-System Synthesizer (`learning_synthesizer.py`)**
- Identifies transferable patterns
- Propagates adaptations across systems
- Manages learning conflicts

**4. Human Oversight Interface (`j5a_oversight_cli.py`)**
- Review pending adaptations
- Approve/reject refinements
- Monitor system health
- Set quality benchmarks

### Integration with Existing Architecture

**Leverages:**
- Sherlock podcast continuous improvement architecture (extend pattern, don't duplicate)
- J5A Constitution (7 principles govern all adaptations)
- Strategic Principles (10 patterns guide implementation)
- Existing IntelligentModelSelector (enhance with learned parameters)
- Current queue systems (add learning layer)

---

## PHASE 1: UNIFIED MEMORY FOUNDATION

### 1.1 Database Schema

**File:** `/home/johnny5/j5a_universe_memory.db`

```sql
-- ================================================================
-- UNIFIED ENTITY REGISTRY
-- Cross-system entity tracking
-- ================================================================

CREATE TABLE IF NOT EXISTS entities (
    entity_id TEXT PRIMARY KEY,  -- UUID or system-specific ID
    entity_type TEXT NOT NULL,   -- client, source, speaker, person, organization, concept
    entity_name TEXT NOT NULL,
    system_origin TEXT NOT NULL,  -- squirt, j5a, sherlock
    attributes JSON NOT NULL,     -- Flexible schema per entity type

    -- Metadata
    created_timestamp TEXT NOT NULL,
    last_updated_timestamp TEXT NOT NULL,
    usage_count INTEGER DEFAULT 0,

    -- Cross-references
    related_entities JSON,        -- Links to other entity_ids
    aliases JSON                  -- Alternative names/spellings
);

CREATE INDEX idx_entities_type ON entities(entity_type);
CREATE INDEX idx_entities_system ON entities(system_origin);
CREATE INDEX idx_entities_name ON entities(entity_name);

-- ================================================================
-- SYSTEM PERFORMANCE TRACKING
-- Unified metrics across all systems
-- ================================================================

CREATE TABLE IF NOT EXISTS system_performance (
    performance_id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Identification
    system_name TEXT NOT NULL,    -- squirt, j5a, sherlock
    subsystem_name TEXT,          -- invoice, contract, claude_queue, intelligence_extraction, etc.
    task_type TEXT NOT NULL,      -- specific operation type
    task_id TEXT,                 -- Optional reference to specific task

    -- Timing
    timestamp TEXT NOT NULL,
    duration_seconds REAL,

    -- Outcome
    success BOOLEAN NOT NULL,
    failure_reason TEXT,

    -- Quality
    quality_score REAL,           -- 0.0-1.0 normalized quality
    quality_dimensions JSON,      -- Detailed quality breakdown

    -- Metrics (system-specific)
    metrics JSON NOT NULL,

    -- Context (what conditions existed)
    context JSON NOT NULL,

    -- Resources
    memory_usage_gb REAL,
    cpu_temperature REAL,
    thermal_constraint_hit BOOLEAN DEFAULT FALSE
);

CREATE INDEX idx_performance_system ON system_performance(system_name, subsystem_name);
CREATE INDEX idx_performance_timestamp ON system_performance(timestamp);
CREATE INDEX idx_performance_success ON system_performance(success);

-- ================================================================
-- SESSION MEMORY
-- Significant events, incidents, learnings
-- ================================================================

CREATE TABLE IF NOT EXISTS session_memory (
    session_id TEXT PRIMARY KEY,
    timestamp TEXT NOT NULL,
    system_name TEXT NOT NULL,

    -- Event classification
    event_type TEXT NOT NULL,     -- success, failure, anomaly, breakthrough, pattern_discovered
    event_description TEXT NOT NULL,
    impact_assessment TEXT,       -- high, medium, low

    -- Learning
    learnings JSON,               -- Structured learnings from this session
    patterns_discovered JSON,     -- New patterns identified

    -- Context
    related_performance_ids JSON,  -- Links to performance records
    related_entity_ids JSON,      -- Links to involved entities

    -- Human oversight
    human_validated BOOLEAN DEFAULT FALSE,
    human_validation_timestamp TEXT,
    human_notes TEXT
);

CREATE INDEX idx_session_memory_system ON session_memory(system_name);
CREATE INDEX idx_session_memory_type ON session_memory(event_type);

-- ================================================================
-- CONTEXT REFRESH
-- Evergreen knowledge that guides operations
-- ================================================================

CREATE TABLE IF NOT EXISTS context_refresh (
    context_id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Classification
    category TEXT NOT NULL,       -- priorities, active_projects, learned_patterns, quality_standards
    system_name TEXT,             -- NULL for cross-system context

    -- Content
    content TEXT NOT NULL,        -- Markdown-formatted context
    content_type TEXT DEFAULT 'markdown',  -- markdown, json, yaml

    -- Lifecycle
    effective_timestamp TEXT NOT NULL,
    expires_timestamp TEXT,       -- NULL if permanent
    currently_active BOOLEAN DEFAULT TRUE,
    superseded_by INTEGER,        -- References another context_id

    -- Metadata
    author TEXT,                  -- human or system
    update_frequency TEXT,        -- daily, weekly, monthly, as_needed

    FOREIGN KEY (superseded_by) REFERENCES context_refresh(context_id)
);

CREATE INDEX idx_context_category ON context_refresh(category);
CREATE INDEX idx_context_system ON context_refresh(system_name);
CREATE INDEX idx_context_active ON context_refresh(currently_active);

-- ================================================================
-- DECISION PROVENANCE
-- Track all significant decisions with reasoning
-- ================================================================

CREATE TABLE IF NOT EXISTS decision_history (
    decision_id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Identification
    timestamp TEXT NOT NULL,
    system_name TEXT NOT NULL,
    subsystem_name TEXT,
    decision_point TEXT NOT NULL,  -- What decision was made

    -- Decision details
    decision_made TEXT NOT NULL,
    alternatives_considered JSON NOT NULL,

    -- Reasoning (CRITICAL for transparency)
    reasoning TEXT NOT NULL,
    retrieve_inputs JSON,          -- What data was retrieved
    reason_factors JSON,           -- Factors considered

    -- Constitutional alignment
    constitutional_principles JSON NOT NULL,  -- Which principles guided decision
    human_agency_preserved BOOLEAN DEFAULT TRUE,

    -- Outcome tracking
    outcome_measured BOOLEAN DEFAULT FALSE,
    outcome_quality REAL,
    outcome_notes TEXT,

    -- Human oversight
    human_overridden BOOLEAN DEFAULT FALSE,
    override_reason TEXT,
    override_timestamp TEXT,

    -- Links
    related_performance_id INTEGER,
    related_session_id TEXT,

    FOREIGN KEY (related_performance_id) REFERENCES system_performance(performance_id),
    FOREIGN KEY (related_session_id) REFERENCES session_memory(session_id)
);

CREATE INDEX idx_decision_system ON decision_history(system_name);
CREATE INDEX idx_decision_timestamp ON decision_history(timestamp);
CREATE INDEX idx_decision_point ON decision_history(decision_point);

-- ================================================================
-- ADAPTIVE PARAMETERS
-- System parameters that adapt based on learning
-- ================================================================

CREATE TABLE IF NOT EXISTS adaptive_parameters (
    parameter_id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Identification
    parameter_name TEXT NOT NULL,
    parameter_category TEXT NOT NULL,  -- model_selection, threshold, timeout, etc.
    system_name TEXT NOT NULL,
    subsystem_name TEXT,

    -- Value
    parameter_value JSON NOT NULL,    -- Serialized value (can be any type)
    parameter_type TEXT NOT NULL,     -- float, int, string, bool, dict, list

    -- Lifecycle
    effective_timestamp TEXT NOT NULL,
    superseded_timestamp TEXT,
    superseded_by INTEGER,
    currently_active BOOLEAN DEFAULT TRUE,

    -- Adaptation reasoning
    adaptation_reason TEXT NOT NULL,
    supporting_evidence JSON,         -- Performance IDs or other evidence
    confidence REAL NOT NULL,         -- 0.0-1.0 confidence in adaptation

    -- Human oversight
    human_approved BOOLEAN DEFAULT FALSE,
    human_approval_timestamp TEXT,
    human_notes TEXT,

    -- Effectiveness tracking
    effectiveness_measured BOOLEAN DEFAULT FALSE,
    effectiveness_score REAL,
    measurement_period_days INTEGER,
    measurement_sample_size INTEGER,

    FOREIGN KEY (superseded_by) REFERENCES adaptive_parameters(parameter_id)
);

CREATE INDEX idx_adaptive_system ON adaptive_parameters(system_name, subsystem_name);
CREATE INDEX idx_adaptive_active ON adaptive_parameters(currently_active);
CREATE INDEX idx_adaptive_category ON adaptive_parameters(parameter_category);

-- ================================================================
-- QUALITY BENCHMARKS
-- Target quality levels per system/task
-- ================================================================

CREATE TABLE IF NOT EXISTS quality_benchmarks (
    benchmark_id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Scope
    system_name TEXT NOT NULL,
    subsystem_name TEXT,
    metric_name TEXT NOT NULL,

    -- Benchmark levels
    benchmark_type TEXT NOT NULL,  -- minimum, target, excellent
    benchmark_value REAL NOT NULL,

    -- Context
    set_timestamp TEXT NOT NULL,
    set_by TEXT NOT NULL,          -- human or system
    reasoning TEXT,

    -- Lifecycle
    currently_active BOOLEAN DEFAULT TRUE,
    superseded_by INTEGER,
    superseded_timestamp TEXT,

    FOREIGN KEY (superseded_by) REFERENCES quality_benchmarks(benchmark_id)
);

CREATE INDEX idx_benchmark_system ON quality_benchmarks(system_name, subsystem_name);
CREATE INDEX idx_benchmark_metric ON quality_benchmarks(metric_name);
CREATE INDEX idx_benchmark_active ON quality_benchmarks(currently_active);

-- ================================================================
-- LEARNING OUTCOMES
-- Captured insights and their impact
-- ================================================================

CREATE TABLE IF NOT EXISTS learning_outcomes (
    outcome_id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,

    -- Learning classification
    learning_category TEXT NOT NULL,  -- model_selection, parameter_tuning, error_pattern, workflow_optimization
    system_name TEXT NOT NULL,
    subsystem_name TEXT,

    -- Learning description
    learning_description TEXT NOT NULL,
    evidence_performance_ids JSON,   -- Supporting performance records
    evidence_decision_ids JSON,      -- Supporting decisions
    confidence_score REAL NOT NULL,  -- 0.0-1.0

    -- Action taken
    system_refinement_applied BOOLEAN DEFAULT FALSE,
    refinement_description TEXT,
    refinement_code_path TEXT,       -- Path to code implementing refinement

    -- Validation
    human_validated BOOLEAN DEFAULT FALSE,
    human_validation_timestamp TEXT,
    validation_notes TEXT,

    -- Effectiveness tracking
    effectiveness_measured BOOLEAN DEFAULT FALSE,
    effectiveness_score REAL,
    measurement_episode_count INTEGER,

    -- Transfer potential
    cross_system_applicable BOOLEAN DEFAULT FALSE,
    target_systems JSON              -- Systems that might benefit from this learning
);

CREATE INDEX idx_learning_system ON learning_outcomes(system_name, subsystem_name);
CREATE INDEX idx_learning_category ON learning_outcomes(learning_category);
CREATE INDEX idx_learning_validated ON learning_outcomes(human_validated);

-- ================================================================
-- CROSS-SYSTEM LEARNING TRANSFERS
-- Track when learnings move between systems
-- ================================================================

CREATE TABLE IF NOT EXISTS learning_transfers (
    transfer_id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,

    -- Source and target
    source_learning_id INTEGER NOT NULL,
    source_system TEXT NOT NULL,
    target_system TEXT NOT NULL,

    -- Transfer details
    transfer_type TEXT NOT NULL,  -- pattern, parameter, strategy, template
    adaptation_description TEXT NOT NULL,

    -- Effectiveness
    transfer_success BOOLEAN,
    effectiveness_score REAL,
    notes TEXT,

    FOREIGN KEY (source_learning_id) REFERENCES learning_outcomes(outcome_id)
);

CREATE INDEX idx_transfer_source ON learning_transfers(source_system);
CREATE INDEX idx_transfer_target ON learning_transfers(target_system);
```

### 1.2 Unified Memory Manager Implementation

**File:** `/home/johnny5/j5a_universe_memory.py`

```python
"""
J5A Universe Memory Manager
Unified Active Memory layer for Squirt, J5A, and Sherlock systems

Constitutional Basis: Principles 2 (Transparency), 4 (Resource Stewardship), 6 (AI Sentience)
Strategic Basis: Principle 4 (Active Memory)
"""

import sqlite3
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import uuid

# Database path
J5A_MEMORY_DB = Path("/home/johnny5/j5a_universe_memory.db")


class SystemName(Enum):
    """J5A systems"""
    SQUIRT = "squirt"
    J5A = "j5a"
    SHERLOCK = "sherlock"


class EntityType(Enum):
    """Entity types in memory"""
    CLIENT = "client"
    SOURCE = "source"
    SPEAKER = "speaker"
    PERSON = "person"
    ORGANIZATION = "organization"
    CONCEPT = "concept"
    PROJECT = "project"


@dataclass
class Entity:
    """Unified entity representation"""
    entity_id: str
    entity_type: EntityType
    entity_name: str
    system_origin: SystemName
    attributes: Dict[str, Any]
    created_timestamp: datetime
    last_updated_timestamp: datetime
    usage_count: int = 0
    related_entities: Optional[List[str]] = None
    aliases: Optional[List[str]] = None


@dataclass
class PerformanceRecord:
    """Performance tracking record"""
    system_name: SystemName
    subsystem_name: Optional[str]
    task_type: str
    timestamp: datetime
    success: bool
    duration_seconds: Optional[float] = None
    quality_score: Optional[float] = None
    quality_dimensions: Optional[Dict] = None
    metrics: Optional[Dict] = None
    context: Optional[Dict] = None
    memory_usage_gb: Optional[float] = None
    cpu_temperature: Optional[float] = None
    thermal_constraint_hit: bool = False
    task_id: Optional[str] = None
    failure_reason: Optional[str] = None


@dataclass
class Decision:
    """Decision provenance record"""
    timestamp: datetime
    system_name: SystemName
    subsystem_name: Optional[str]
    decision_point: str
    decision_made: str
    alternatives_considered: List[str]
    reasoning: str
    retrieve_inputs: Optional[Dict] = None
    reason_factors: Optional[Dict] = None
    constitutional_principles: Optional[List[str]] = None
    human_agency_preserved: bool = True
    outcome_measured: bool = False
    outcome_quality: Optional[float] = None
    outcome_notes: Optional[str] = None


class UniverseMemoryManager:
    """
    Unified memory manager for J5A universe

    Provides:
    - Entity management (clients, sources, speakers, etc.)
    - Performance tracking (metrics, outcomes, quality)
    - Decision provenance (reasoning, alternatives, outcomes)
    - Context refresh (evergreen knowledge)
    - Adaptive parameters (learned settings)
    """

    def __init__(self, db_path: Path = J5A_MEMORY_DB):
        self.db_path = db_path
        self._ensure_database()
        self._cache = {}  # In-memory cache for frequent queries

    def _ensure_database(self):
        """Ensure database exists with correct schema"""
        if not self.db_path.exists():
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            self._create_schema()

    def _create_schema(self):
        """Create database schema"""
        # Schema SQL would go here (from above)
        # For brevity, assume schema is created
        pass

    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection"""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row  # Access columns by name
        return conn

    # ================================================================
    # ENTITY MANAGEMENT
    # ================================================================

    def add_entity(
        self,
        entity_type: EntityType,
        entity_name: str,
        system_origin: SystemName,
        attributes: Dict[str, Any],
        entity_id: Optional[str] = None,
        related_entities: Optional[List[str]] = None,
        aliases: Optional[List[str]] = None
    ) -> str:
        """
        Add or update entity in memory

        Returns entity_id
        """
        if entity_id is None:
            entity_id = str(uuid.uuid4())

        now = datetime.now().isoformat()

        # Check if entity exists
        existing = self.get_entity(entity_id)

        conn = self._get_connection()
        cursor = conn.cursor()

        if existing:
            # Update existing
            cursor.execute("""
                UPDATE entities
                SET entity_name = ?,
                    attributes = ?,
                    last_updated_timestamp = ?,
                    usage_count = usage_count + 1,
                    related_entities = ?,
                    aliases = ?
                WHERE entity_id = ?
            """, (
                entity_name,
                json.dumps(attributes),
                now,
                json.dumps(related_entities) if related_entities else None,
                json.dumps(aliases) if aliases else None,
                entity_id
            ))
        else:
            # Insert new
            cursor.execute("""
                INSERT INTO entities (
                    entity_id, entity_type, entity_name, system_origin,
                    attributes, created_timestamp, last_updated_timestamp,
                    usage_count, related_entities, aliases
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                entity_id,
                entity_type.value,
                entity_name,
                system_origin.value,
                json.dumps(attributes),
                now,
                now,
                1,
                json.dumps(related_entities) if related_entities else None,
                json.dumps(aliases) if aliases else None
            ))

        conn.commit()
        conn.close()

        return entity_id

    def get_entity(self, entity_id: str) -> Optional[Entity]:
        """Retrieve entity by ID"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM entities WHERE entity_id = ?
        """, (entity_id,))

        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        return Entity(
            entity_id=row['entity_id'],
            entity_type=EntityType(row['entity_type']),
            entity_name=row['entity_name'],
            system_origin=SystemName(row['system_origin']),
            attributes=json.loads(row['attributes']),
            created_timestamp=datetime.fromisoformat(row['created_timestamp']),
            last_updated_timestamp=datetime.fromisoformat(row['last_updated_timestamp']),
            usage_count=row['usage_count'],
            related_entities=json.loads(row['related_entities']) if row['related_entities'] else None,
            aliases=json.loads(row['aliases']) if row['aliases'] else None
        )

    def find_entities(
        self,
        entity_type: Optional[EntityType] = None,
        system_origin: Optional[SystemName] = None,
        name_pattern: Optional[str] = None,
        limit: int = 50
    ) -> List[Entity]:
        """Find entities matching criteria"""
        conn = self._get_connection()
        cursor = conn.cursor()

        query = "SELECT * FROM entities WHERE 1=1"
        params = []

        if entity_type:
            query += " AND entity_type = ?"
            params.append(entity_type.value)

        if system_origin:
            query += " AND system_origin = ?"
            params.append(system_origin.value)

        if name_pattern:
            query += " AND entity_name LIKE ?"
            params.append(f"%{name_pattern}%")

        query += " ORDER BY usage_count DESC, last_updated_timestamp DESC LIMIT ?"
        params.append(limit)

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        return [
            Entity(
                entity_id=row['entity_id'],
                entity_type=EntityType(row['entity_type']),
                entity_name=row['entity_name'],
                system_origin=SystemName(row['system_origin']),
                attributes=json.loads(row['attributes']),
                created_timestamp=datetime.fromisoformat(row['created_timestamp']),
                last_updated_timestamp=datetime.fromisoformat(row['last_updated_timestamp']),
                usage_count=row['usage_count'],
                related_entities=json.loads(row['related_entities']) if row['related_entities'] else None,
                aliases=json.loads(row['aliases']) if row['aliases'] else None
            )
            for row in rows
        ]

    # ================================================================
    # PERFORMANCE TRACKING
    # ================================================================

    def record_performance(
        self,
        record: PerformanceRecord
    ) -> int:
        """
        Record performance metrics

        Returns performance_id
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO system_performance (
                system_name, subsystem_name, task_type, task_id,
                timestamp, duration_seconds, success, failure_reason,
                quality_score, quality_dimensions, metrics, context,
                memory_usage_gb, cpu_temperature, thermal_constraint_hit
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            record.system_name.value,
            record.subsystem_name,
            record.task_type,
            record.task_id,
            record.timestamp.isoformat(),
            record.duration_seconds,
            record.success,
            record.failure_reason,
            record.quality_score,
            json.dumps(record.quality_dimensions) if record.quality_dimensions else None,
            json.dumps(record.metrics) if record.metrics else None,
            json.dumps(record.context) if record.context else None,
            record.memory_usage_gb,
            record.cpu_temperature,
            record.thermal_constraint_hit
        ))

        performance_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return performance_id

    def get_performance_history(
        self,
        system_name: SystemName,
        subsystem_name: Optional[str] = None,
        task_type: Optional[str] = None,
        success_only: bool = False,
        limit: int = 50,
        days_back: int = 30
    ) -> List[Dict]:
        """Retrieve performance history"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cutoff = (datetime.now() - timedelta(days=days_back)).isoformat()

        query = """
            SELECT * FROM system_performance
            WHERE system_name = ?
            AND timestamp > ?
        """
        params = [system_name.value, cutoff]

        if subsystem_name:
            query += " AND subsystem_name = ?"
            params.append(subsystem_name)

        if task_type:
            query += " AND task_type = ?"
            params.append(task_type)

        if success_only:
            query += " AND success = 1"

        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    def get_performance_statistics(
        self,
        system_name: SystemName,
        subsystem_name: Optional[str] = None,
        days_back: int = 30
    ) -> Dict[str, Any]:
        """Get aggregate performance statistics"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cutoff = (datetime.now() - timedelta(days=days_back)).isoformat()

        query = """
            SELECT
                COUNT(*) as total_count,
                SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as success_count,
                AVG(duration_seconds) as avg_duration,
                AVG(quality_score) as avg_quality,
                AVG(memory_usage_gb) as avg_memory,
                MAX(cpu_temperature) as max_temperature,
                SUM(CASE WHEN thermal_constraint_hit = 1 THEN 1 ELSE 0 END) as thermal_hits
            FROM system_performance
            WHERE system_name = ?
            AND timestamp > ?
        """
        params = [system_name.value, cutoff]

        if subsystem_name:
            query += " AND subsystem_name = ?"
            params.append(subsystem_name)

        cursor.execute(query, params)
        row = cursor.fetchone()
        conn.close()

        return dict(row) if row else {}

    # ================================================================
    # DECISION PROVENANCE
    # ================================================================

    def record_decision(
        self,
        decision: Decision
    ) -> int:
        """
        Record decision with full provenance

        Returns decision_id
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO decision_history (
                timestamp, system_name, subsystem_name, decision_point,
                decision_made, alternatives_considered, reasoning,
                retrieve_inputs, reason_factors, constitutional_principles,
                human_agency_preserved, outcome_measured, outcome_quality,
                outcome_notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            decision.timestamp.isoformat(),
            decision.system_name.value,
            decision.subsystem_name,
            decision.decision_point,
            decision.decision_made,
            json.dumps(decision.alternatives_considered),
            decision.reasoning,
            json.dumps(decision.retrieve_inputs) if decision.retrieve_inputs else None,
            json.dumps(decision.reason_factors) if decision.reason_factors else None,
            json.dumps(decision.constitutional_principles) if decision.constitutional_principles else None,
            decision.human_agency_preserved,
            decision.outcome_measured,
            decision.outcome_quality,
            decision.outcome_notes
        ))

        decision_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return decision_id

    def get_decision_history(
        self,
        system_name: SystemName,
        decision_point: Optional[str] = None,
        days_back: int = 30,
        limit: int = 50
    ) -> List[Dict]:
        """Retrieve decision history"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cutoff = (datetime.now() - timedelta(days=days_back)).isoformat()

        query = """
            SELECT * FROM decision_history
            WHERE system_name = ?
            AND timestamp > ?
        """
        params = [system_name.value, cutoff]

        if decision_point:
            query += " AND decision_point = ?"
            params.append(decision_point)

        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    # ================================================================
    # ADAPTIVE PARAMETERS
    # ================================================================

    def get_adaptive_parameters(
        self,
        system_name: SystemName,
        parameter_category: Optional[str] = None,
        subsystem_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get currently active adaptive parameters

        Returns dict of parameter_name -> value
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        query = """
            SELECT parameter_name, parameter_value, parameter_type,
                   adaptation_reason, confidence
            FROM adaptive_parameters
            WHERE system_name = ?
            AND currently_active = 1
            AND superseded_timestamp IS NULL
        """
        params = [system_name.value]

        if parameter_category:
            query += " AND parameter_category = ?"
            params.append(parameter_category)

        if subsystem_name:
            query += " AND subsystem_name = ?"
            params.append(subsystem_name)

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        params_dict = {}
        for row in rows:
            params_dict[row['parameter_name']] = {
                'value': json.loads(row['parameter_value']),
                'type': row['parameter_type'],
                'reason': row['adaptation_reason'],
                'confidence': row['confidence']
            }

        return params_dict

    def update_adaptive_parameter(
        self,
        system_name: SystemName,
        parameter_name: str,
        parameter_category: str,
        new_value: Any,
        adaptation_reason: str,
        confidence: float,
        subsystem_name: Optional[str] = None,
        supporting_evidence: Optional[Dict] = None
    ) -> int:
        """
        Update an adaptive parameter

        Supersedes old value, creates new record
        Returns new parameter_id
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        # Determine parameter type
        param_type = type(new_value).__name__
        if isinstance(new_value, (dict, list)):
            param_type = 'dict' if isinstance(new_value, dict) else 'list'

        # Supersede current parameter
        cursor.execute("""
            UPDATE adaptive_parameters
            SET superseded_timestamp = ?,
                currently_active = 0
            WHERE system_name = ?
            AND parameter_name = ?
            AND parameter_category = ?
            AND currently_active = 1
        """, (
            datetime.now().isoformat(),
            system_name.value,
            parameter_name,
            parameter_category
        ))

        # Insert new parameter
        cursor.execute("""
            INSERT INTO adaptive_parameters (
                parameter_name, parameter_category, system_name, subsystem_name,
                parameter_value, parameter_type, effective_timestamp,
                adaptation_reason, supporting_evidence, confidence,
                human_approved, currently_active
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            parameter_name,
            parameter_category,
            system_name.value,
            subsystem_name,
            json.dumps(new_value),
            param_type,
            datetime.now().isoformat(),
            adaptation_reason,
            json.dumps(supporting_evidence) if supporting_evidence else None,
            confidence,
            False,  # Requires human approval
            True
        ))

        parameter_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return parameter_id

    # ================================================================
    # QUALITY BENCHMARKS
    # ================================================================

    def get_quality_benchmarks(
        self,
        system_name: SystemName,
        subsystem_name: Optional[str] = None
    ) -> Dict[str, Dict[str, float]]:
        """
        Get quality benchmarks for a system

        Returns dict: metric_name -> {minimum, target, excellent}
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        query = """
            SELECT metric_name, benchmark_type, benchmark_value
            FROM quality_benchmarks
            WHERE system_name = ?
            AND currently_active = 1
        """
        params = [system_name.value]

        if subsystem_name:
            query += " AND subsystem_name = ?"
            params.append(subsystem_name)

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        benchmarks = {}
        for row in rows:
            metric = row['metric_name']
            if metric not in benchmarks:
                benchmarks[metric] = {}
            benchmarks[metric][row['benchmark_type']] = row['benchmark_value']

        return benchmarks

    # ================================================================
    # CONTEXT REFRESH
    # ================================================================

    def get_active_context(
        self,
        category: str,
        system_name: Optional[SystemName] = None
    ) -> List[str]:
        """Get active context for a category"""
        conn = self._get_connection()
        cursor = conn.cursor()

        query = """
            SELECT content FROM context_refresh
            WHERE category = ?
            AND currently_active = 1
        """
        params = [category]

        if system_name:
            query += " AND (system_name = ? OR system_name IS NULL)"
            params.append(system_name.value)
        else:
            query += " AND system_name IS NULL"

        query += " ORDER BY effective_timestamp DESC"

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        return [row['content'] for row in rows]

    def update_context(
        self,
        category: str,
        content: str,
        system_name: Optional[SystemName] = None,
        expires_in_days: Optional[int] = None
    ):
        """Update context for a category"""
        conn = self._get_connection()
        cursor = conn.cursor()

        now = datetime.now()
        expires = (now + timedelta(days=expires_in_days)).isoformat() if expires_in_days else None

        cursor.execute("""
            INSERT INTO context_refresh (
                category, system_name, content, content_type,
                effective_timestamp, expires_timestamp, currently_active,
                author, update_frequency
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            category,
            system_name.value if system_name else None,
            content,
            'markdown',
            now.isoformat(),
            expires,
            True,
            'system',
            'as_needed'
        ))

        conn.commit()
        conn.close()


# Convenience singleton
_memory_manager = None

def get_memory() -> UniverseMemoryManager:
    """Get singleton memory manager"""
    global _memory_manager
    if _memory_manager is None:
        _memory_manager = UniverseMemoryManager()
    return _memory_manager
```

### 1.3 Integration Tests

**File:** `/home/johnny5/tests/test_universe_memory.py`

```python
"""
Tests for Universe Memory Manager
"""

import pytest
from pathlib import Path
from datetime import datetime
from j5a_universe_memory import (
    UniverseMemoryManager,
    SystemName,
    EntityType,
    Entity,
    PerformanceRecord,
    Decision
)

@pytest.fixture
def memory_manager(tmp_path):
    """Test memory manager with temporary database"""
    db_path = tmp_path / "test_memory.db"
    return UniverseMemoryManager(db_path)

def test_add_and_get_entity(memory_manager):
    """Test entity storage and retrieval"""
    entity_id = memory_manager.add_entity(
        entity_type=EntityType.CLIENT,
        entity_name="Johnson Residence",
        system_origin=SystemName.SQUIRT,
        attributes={
            'address': '123 Main St',
            'phone': '555-1234',
            'preferences': 'organic fertilizer only'
        }
    )

    entity = memory_manager.get_entity(entity_id)

    assert entity is not None
    assert entity.entity_name == "Johnson Residence"
    assert entity.entity_type == EntityType.CLIENT
    assert entity.attributes['address'] == '123 Main St'

def test_record_and_retrieve_performance(memory_manager):
    """Test performance tracking"""
    record = PerformanceRecord(
        system_name=SystemName.SQUIRT,
        subsystem_name='invoice',
        task_type='generate_invoice',
        timestamp=datetime.now(),
        success=True,
        duration_seconds=25.3,
        quality_score=0.95,
        metrics={'client_approval': True}
    )

    perf_id = memory_manager.record_performance(record)

    history = memory_manager.get_performance_history(
        system_name=SystemName.SQUIRT,
        subsystem_name='invoice'
    )

    assert len(history) == 1
    assert history[0]['success'] == True
    assert history[0]['duration_seconds'] == 25.3

def test_adaptive_parameters(memory_manager):
    """Test adaptive parameter management"""
    # Update parameter
    param_id = memory_manager.update_adaptive_parameter(
        system_name=SystemName.SQUIRT,
        parameter_name='default_tax_rate',
        parameter_category='pricing',
        new_value=0.08,
        adaptation_reason='State tax change',
        confidence=1.0
    )

    # Retrieve active parameters
    params = memory_manager.get_adaptive_parameters(
        system_name=SystemName.SQUIRT,
        parameter_category='pricing'
    )

    assert 'default_tax_rate' in params
    assert params['default_tax_rate']['value'] == 0.08
    assert params['default_tax_rate']['confidence'] == 1.0
```

---

*(Architecture document continues with Phase 2-6 in next sections...)*

**[Document continues with detailed implementations of Squirt, J5A, Sherlock learning systems, human oversight, and cross-system synthesis - would you like me to continue with those sections?]**
