#!/usr/bin/env python3
"""
J5A Universe Memory Manager

Unified Active Memory and Adaptive Feedback Loop implementation for J5A universe.

This module provides a centralized memory management system for:
- Squirt: Business document automation with learning from invoice/estimate outcomes
- J5A: Overnight queue/batch management with cross-system coordination learning
- Sherlock: Intelligence analysis with evidence extraction and timeline construction
- Jeeves: Future system integration

Constitutional Compliance:
- Principle 2 (Transparency): All decisions tracked with full provenance
- Principle 3 (System Viability): Persistent memory ensures reliable operation
- Principle 4 (Resource Stewardship): Efficient SQLite storage
- Principle 6 (AI Sentience): Acknowledges AI learning and adaptation

Strategic Implementation:
- Strategic Principle 4 (Active Memory): Bridges transient and long-term knowledge
- Strategic Principle 5 (Adaptive Feedback): Continuous refinement with human oversight
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from contextlib import contextmanager
from dataclasses import dataclass, asdict
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Database path
DB_PATH = Path("/home/johnny5/j5a_universe_memory.db")

@dataclass
class Entity:
    """Represents a cross-system entity (client, source, speaker, person, org, concept, project, job_site)"""
    entity_id: str
    entity_type: str
    entity_name: str
    system_origin: str
    attributes: Dict[str, Any]
    created_timestamp: str
    last_updated_timestamp: str
    usage_count: int = 0
    related_entities: Optional[List[str]] = None
    aliases: Optional[List[str]] = None

@dataclass
class PerformanceMetric:
    """System performance metric"""
    system_name: str
    subsystem_name: str
    metric_name: str
    metric_value: float
    metric_unit: str
    measurement_timestamp: str
    context: Optional[Dict[str, Any]] = None

@dataclass
class SessionEvent:
    """Significant event or learning from a session"""
    system_name: str
    session_id: str
    event_type: str
    event_summary: str
    importance_score: float
    event_timestamp: str
    full_context: Optional[Dict[str, Any]] = None
    related_entities: Optional[List[str]] = None

@dataclass
class Decision:
    """Recorded decision with full provenance"""
    system_name: str
    decision_type: str
    decision_summary: str
    decision_rationale: str
    constitutional_compliance: Dict[str, str]
    strategic_alignment: Dict[str, str]
    decision_timestamp: str
    decided_by: str
    outcome_expected: str
    outcome_actual: Optional[str] = None
    parameters_used: Optional[Dict[str, Any]] = None

@dataclass
class AdaptiveParameter:
    """Learned system parameter"""
    system_name: str
    parameter_name: str
    parameter_value: float
    parameter_context: str
    learning_source: str
    confidence_score: float
    last_updated_timestamp: str
    update_count: int = 1

@dataclass
class SiteModifier:
    """WaterWizard job site characteristics with learned multipliers"""
    job_site_entity_id: str
    job_site_name: str
    soil_type: Optional[str] = None
    soil_quality_rating: Optional[float] = None
    soil_drainage: Optional[str] = None
    slope_type: Optional[str] = None
    slope_percentage: Optional[float] = None
    slope_stability: Optional[str] = None
    vegetation_type: Optional[str] = None
    vegetation_density: Optional[float] = None
    vegetation_removal_difficulty: Optional[float] = None
    space_type: Optional[str] = None
    access_difficulty: Optional[float] = None
    equipment_restrictions: Optional[str] = None
    labor_rate_multiplier: float = 1.0
    material_waste_multiplier: float = 1.0
    time_multiplier: float = 1.0
    jobs_completed_count: int = 0
    total_variance_labor_hours: float = 0.0
    total_variance_material_cost: float = 0.0

@dataclass
class EstimateActual:
    """WaterWizard estimate vs. actual comparison with satisfaction metrics"""
    job_id: str
    client_entity_id: str
    job_type: str
    estimate_timestamp: str
    estimate_labor_hours: float
    estimate_labor_cost: float
    estimate_materials_cost: float
    estimate_total_cost: float
    job_site_entity_id: Optional[str] = None
    estimate_generation_time_seconds: Optional[float] = None
    estimate_human_input_time_seconds: Optional[float] = None
    estimate_template_usage_percent: Optional[float] = None
    estimate_custom_scopes_count: Optional[int] = None
    estimate_custom_scopes_total_chars: Optional[int] = None
    actual_timestamp: Optional[str] = None
    actual_labor_hours: Optional[float] = None
    actual_labor_cost: Optional[float] = None
    actual_materials_cost: Optional[float] = None
    actual_total_cost: Optional[float] = None
    labor_hours_variance: Optional[float] = None
    labor_cost_variance: Optional[float] = None
    materials_cost_variance: Optional[float] = None
    total_cost_variance: Optional[float] = None
    labor_hours_variance_percent: Optional[float] = None
    labor_cost_variance_percent: Optional[float] = None
    materials_cost_variance_percent: Optional[float] = None
    customer_satisfaction_score: Optional[float] = None
    employee_satisfaction_score: Optional[float] = None
    management_satisfaction_score: Optional[float] = None
    site_conditions: Optional[Dict[str, Any]] = None
    weather_conditions: Optional[Dict[str, Any]] = None
    complications_encountered: Optional[List[str]] = None


class UniverseMemoryManager:
    """
    Unified memory management for J5A universe systems.

    Provides persistent storage and retrieval of:
    - Cross-system entities and relationships
    - System performance metrics and trends
    - Session memory (significant events and learnings)
    - Context refresh (evergreen knowledge)
    - Decision history with full constitutional compliance tracking
    - Adaptive parameters (learned settings)
    - Quality benchmarks
    - Learning outcomes and cross-system transfers
    - WaterWizard-specific site modifiers and estimate tracking
    """

    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        if not self.db_path.exists():
            raise FileNotFoundError(f"Database not found at {self.db_path}. Run create_universe_memory_db.sql first.")
        logger.info(f"UniverseMemoryManager initialized with database: {self.db_path}")

    @contextmanager
    def _get_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            conn.close()

    # ========== ENTITY MANAGEMENT ==========

    def create_entity(self, entity: Entity) -> str:
        """Create or update an entity in the cross-system registry"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO entities (
                    entity_id, entity_type, entity_name, system_origin, attributes,
                    created_timestamp, last_updated_timestamp, usage_count,
                    related_entities, aliases
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                entity.entity_id, entity.entity_type, entity.entity_name,
                entity.system_origin, json.dumps(entity.attributes),
                entity.created_timestamp, entity.last_updated_timestamp,
                entity.usage_count,
                json.dumps(entity.related_entities) if entity.related_entities else None,
                json.dumps(entity.aliases) if entity.aliases else None
            ))
            logger.info(f"Created/updated entity: {entity.entity_id} ({entity.entity_type})")
            return entity.entity_id

    def get_entity(self, entity_id: str) -> Optional[Entity]:
        """Retrieve an entity by ID"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM entities WHERE entity_id = ?", (entity_id,))
            row = cursor.fetchone()
            if row:
                return Entity(
                    entity_id=row['entity_id'],
                    entity_type=row['entity_type'],
                    entity_name=row['entity_name'],
                    system_origin=row['system_origin'],
                    attributes=json.loads(row['attributes']),
                    created_timestamp=row['created_timestamp'],
                    last_updated_timestamp=row['last_updated_timestamp'],
                    usage_count=row['usage_count'],
                    related_entities=json.loads(row['related_entities']) if row['related_entities'] else None,
                    aliases=json.loads(row['aliases']) if row['aliases'] else None
                )
            return None

    def search_entities(self, entity_type: Optional[str] = None,
                       system_origin: Optional[str] = None,
                       name_pattern: Optional[str] = None) -> List[Entity]:
        """Search for entities by type, system, or name pattern"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            query = "SELECT * FROM entities WHERE 1=1"
            params = []

            if entity_type:
                query += " AND entity_type = ?"
                params.append(entity_type)
            if system_origin:
                query += " AND system_origin = ?"
                params.append(system_origin)
            if name_pattern:
                query += " AND entity_name LIKE ?"
                params.append(f"%{name_pattern}%")

            query += " ORDER BY usage_count DESC, entity_name ASC"
            cursor.execute(query, params)

            entities = []
            for row in cursor.fetchall():
                entities.append(Entity(
                    entity_id=row['entity_id'],
                    entity_type=row['entity_type'],
                    entity_name=row['entity_name'],
                    system_origin=row['system_origin'],
                    attributes=json.loads(row['attributes']),
                    created_timestamp=row['created_timestamp'],
                    last_updated_timestamp=row['last_updated_timestamp'],
                    usage_count=row['usage_count'],
                    related_entities=json.loads(row['related_entities']) if row['related_entities'] else None,
                    aliases=json.loads(row['aliases']) if row['aliases'] else None
                ))
            return entities

    def increment_entity_usage(self, entity_id: str) -> None:
        """Increment usage counter for an entity"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE entities
                SET usage_count = usage_count + 1,
                    last_updated_timestamp = ?
                WHERE entity_id = ?
            """, (datetime.now().isoformat(), entity_id))

    # ========== PERFORMANCE TRACKING ==========

    def record_performance(self, metric: PerformanceMetric) -> None:
        """Record a system performance metric"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO system_performance (
                    system_name, subsystem_name, metric_name, metric_value,
                    metric_unit, measurement_timestamp, context
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                metric.system_name, metric.subsystem_name, metric.metric_name,
                metric.metric_value, metric.metric_unit, metric.measurement_timestamp,
                json.dumps(metric.context) if metric.context else None
            ))
            logger.info(f"Recorded performance: {metric.system_name}.{metric.subsystem_name}.{metric.metric_name} = {metric.metric_value} {metric.metric_unit}")

    def get_performance_trend(self, system_name: str, subsystem_name: str,
                            metric_name: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent performance metrics for trend analysis"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT metric_value, metric_unit, measurement_timestamp, context
                FROM system_performance
                WHERE system_name = ? AND subsystem_name = ? AND metric_name = ?
                ORDER BY measurement_timestamp DESC
                LIMIT ?
            """, (system_name, subsystem_name, metric_name, limit))

            results = []
            for row in cursor.fetchall():
                results.append({
                    'value': row['metric_value'],
                    'unit': row['metric_unit'],
                    'timestamp': row['measurement_timestamp'],
                    'context': json.loads(row['context']) if row['context'] else None
                })
            return results

    def get_latest_performance(self, system_name: str, subsystem_name: str) -> Dict[str, Any]:
        """Get latest performance metrics for a subsystem"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT metric_name, metric_value, metric_unit, measurement_timestamp
                FROM system_performance
                WHERE system_name = ? AND subsystem_name = ?
                AND measurement_timestamp IN (
                    SELECT MAX(measurement_timestamp)
                    FROM system_performance
                    WHERE system_name = ? AND subsystem_name = ?
                    GROUP BY metric_name
                )
                ORDER BY metric_name
            """, (system_name, subsystem_name, system_name, subsystem_name))

            metrics = {}
            for row in cursor.fetchall():
                metrics[row['metric_name']] = {
                    'value': row['metric_value'],
                    'unit': row['metric_unit'],
                    'timestamp': row['measurement_timestamp']
                }
            return metrics

    # ========== SESSION MEMORY ==========

    def record_session_event(self, event: SessionEvent) -> None:
        """Record a significant event from a session"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO session_memory (
                    system_name, session_id, event_type, event_summary,
                    importance_score, event_timestamp, full_context, related_entities
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                event.system_name, event.session_id, event.event_type,
                event.event_summary, event.importance_score, event.event_timestamp,
                json.dumps(event.full_context) if event.full_context else None,
                json.dumps(event.related_entities) if event.related_entities else None
            ))
            logger.info(f"Recorded session event: {event.system_name} - {event.event_type} (importance: {event.importance_score})")

    def get_session_context(self, system_name: str, min_importance: float = 0.5,
                           limit: int = 50) -> List[Dict[str, Any]]:
        """Retrieve relevant session context for a system"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT session_id, event_type, event_summary, importance_score,
                       event_timestamp, full_context, related_entities
                FROM session_memory
                WHERE system_name = ? AND importance_score >= ?
                ORDER BY importance_score DESC, event_timestamp DESC
                LIMIT ?
            """, (system_name, min_importance, limit))

            context = []
            for row in cursor.fetchall():
                context.append({
                    'session_id': row['session_id'],
                    'event_type': row['event_type'],
                    'summary': row['event_summary'],
                    'importance': row['importance_score'],
                    'timestamp': row['event_timestamp'],
                    'context': json.loads(row['full_context']) if row['full_context'] else None,
                    'related_entities': json.loads(row['related_entities']) if row['related_entities'] else None
                })
            return context

    # ========== CONTEXT REFRESH (EVERGREEN KNOWLEDGE) ==========

    def set_context_refresh(self, system_name: str, knowledge_key: str,
                           knowledge_summary: str, full_content: str,
                           refresh_priority: float = 0.5) -> None:
        """Set or update evergreen knowledge for context refresh"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            timestamp = datetime.now().isoformat()
            cursor.execute("""
                INSERT OR REPLACE INTO context_refresh (
                    system_name, knowledge_key, knowledge_summary, full_content,
                    last_refreshed_timestamp, refresh_priority, usage_count
                ) VALUES (?, ?, ?, ?, ?, ?, COALESCE(
                    (SELECT usage_count FROM context_refresh WHERE system_name = ? AND knowledge_key = ?),
                    0
                ))
            """, (system_name, knowledge_key, knowledge_summary, full_content,
                 timestamp, refresh_priority, system_name, knowledge_key))
            logger.info(f"Set context refresh: {system_name}.{knowledge_key}")

    def get_context_refresh(self, system_name: str, min_priority: float = 0.3) -> List[Dict[str, Any]]:
        """Get evergreen knowledge for context refresh"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT knowledge_key, knowledge_summary, full_content, refresh_priority,
                       last_refreshed_timestamp, usage_count
                FROM context_refresh
                WHERE system_name = ? AND refresh_priority >= ?
                ORDER BY refresh_priority DESC, usage_count DESC
            """, (system_name, min_priority))

            knowledge = []
            for row in cursor.fetchall():
                knowledge.append({
                    'key': row['knowledge_key'],
                    'summary': row['knowledge_summary'],
                    'content': row['full_content'],
                    'priority': row['refresh_priority'],
                    'last_refreshed': row['last_refreshed_timestamp'],
                    'usage_count': row['usage_count']
                })

            # Increment usage counts
            cursor.execute("""
                UPDATE context_refresh
                SET usage_count = usage_count + 1,
                    last_refreshed_timestamp = ?
                WHERE system_name = ? AND refresh_priority >= ?
            """, (datetime.now().isoformat(), system_name, min_priority))

            return knowledge

    # ========== DECISION HISTORY ==========

    def record_decision(self, decision: Decision) -> None:
        """Record a decision with full provenance and constitutional compliance"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO decision_history (
                    system_name, decision_type, decision_summary, decision_rationale,
                    constitutional_compliance, strategic_alignment, decision_timestamp,
                    decided_by, outcome_expected, outcome_actual, parameters_used
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                decision.system_name, decision.decision_type, decision.decision_summary,
                decision.decision_rationale, json.dumps(decision.constitutional_compliance),
                json.dumps(decision.strategic_alignment), decision.decision_timestamp,
                decision.decided_by, decision.outcome_expected, decision.outcome_actual,
                json.dumps(decision.parameters_used) if decision.parameters_used else None
            ))
            logger.info(f"Recorded decision: {decision.system_name} - {decision.decision_type}")

    def update_decision_outcome(self, decision_summary: str, outcome_actual: str) -> None:
        """Update the actual outcome of a decision"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE decision_history
                SET outcome_actual = ?
                WHERE decision_summary = ?
                ORDER BY decision_timestamp DESC
                LIMIT 1
            """, (outcome_actual, decision_summary))

    def get_decision_history(self, system_name: str, decision_type: Optional[str] = None,
                            limit: int = 50) -> List[Dict[str, Any]]:
        """Retrieve decision history for audit and learning"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            query = """
                SELECT decision_type, decision_summary, decision_rationale,
                       constitutional_compliance, strategic_alignment, decision_timestamp,
                       decided_by, outcome_expected, outcome_actual, parameters_used
                FROM decision_history
                WHERE system_name = ?
            """
            params = [system_name]

            if decision_type:
                query += " AND decision_type = ?"
                params.append(decision_type)

            query += " ORDER BY decision_timestamp DESC LIMIT ?"
            params.append(limit)

            cursor.execute(query, params)

            decisions = []
            for row in cursor.fetchall():
                decisions.append({
                    'type': row['decision_type'],
                    'summary': row['decision_summary'],
                    'rationale': row['decision_rationale'],
                    'constitutional_compliance': json.loads(row['constitutional_compliance']),
                    'strategic_alignment': json.loads(row['strategic_alignment']),
                    'timestamp': row['decision_timestamp'],
                    'decided_by': row['decided_by'],
                    'outcome_expected': row['outcome_expected'],
                    'outcome_actual': row['outcome_actual'],
                    'parameters': json.loads(row['parameters_used']) if row['parameters_used'] else None
                })
            return decisions

    # ========== ADAPTIVE PARAMETERS ==========

    def set_adaptive_parameter(self, param: AdaptiveParameter) -> None:
        """Set or update an adaptive parameter"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            # Check if parameter exists
            cursor.execute("""
                SELECT update_count FROM adaptive_parameters
                WHERE system_name = ? AND parameter_name = ? AND parameter_context = ?
            """, (param.system_name, param.parameter_name, param.parameter_context))

            existing = cursor.fetchone()
            update_count = existing['update_count'] + 1 if existing else 1

            cursor.execute("""
                INSERT OR REPLACE INTO adaptive_parameters (
                    system_name, parameter_name, parameter_value, parameter_context,
                    learning_source, confidence_score, last_updated_timestamp, update_count
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                param.system_name, param.parameter_name, param.parameter_value,
                param.parameter_context, param.learning_source, param.confidence_score,
                param.last_updated_timestamp, update_count
            ))
            logger.info(f"Set adaptive parameter: {param.system_name}.{param.parameter_name} = {param.parameter_value} (confidence: {param.confidence_score})")

    def get_adaptive_parameter(self, system_name: str, parameter_name: str,
                              parameter_context: str) -> Optional[AdaptiveParameter]:
        """Get a specific adaptive parameter"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM adaptive_parameters
                WHERE system_name = ? AND parameter_name = ? AND parameter_context = ?
            """, (system_name, parameter_name, parameter_context))

            row = cursor.fetchone()
            if row:
                return AdaptiveParameter(
                    system_name=row['system_name'],
                    parameter_name=row['parameter_name'],
                    parameter_value=row['parameter_value'],
                    parameter_context=row['parameter_context'],
                    learning_source=row['learning_source'],
                    confidence_score=row['confidence_score'],
                    last_updated_timestamp=row['last_updated_timestamp'],
                    update_count=row['update_count']
                )
            return None

    def get_all_adaptive_parameters(self, system_name: str,
                                    min_confidence: float = 0.3) -> List[AdaptiveParameter]:
        """Get all adaptive parameters for a system above confidence threshold"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM adaptive_parameters
                WHERE system_name = ? AND confidence_score >= ?
                ORDER BY confidence_score DESC, update_count DESC
            """, (system_name, min_confidence))

            parameters = []
            for row in cursor.fetchall():
                parameters.append(AdaptiveParameter(
                    system_name=row['system_name'],
                    parameter_name=row['parameter_name'],
                    parameter_value=row['parameter_value'],
                    parameter_context=row['parameter_context'],
                    learning_source=row['learning_source'],
                    confidence_score=row['confidence_score'],
                    last_updated_timestamp=row['last_updated_timestamp'],
                    update_count=row['update_count']
                ))
            return parameters

    # ========== QUALITY BENCHMARKS ==========

    def set_quality_benchmark(self, system_name: str, subsystem_name: str,
                             metric_name: str, benchmark_type: str,
                             benchmark_value: float, set_by: str,
                             reasoning: str) -> None:
        """Set a quality benchmark"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            timestamp = datetime.now().isoformat()
            cursor.execute("""
                INSERT OR REPLACE INTO quality_benchmarks (
                    system_name, subsystem_name, metric_name, benchmark_type,
                    benchmark_value, set_timestamp, set_by, reasoning
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (system_name, subsystem_name, metric_name, benchmark_type,
                 benchmark_value, timestamp, set_by, reasoning))
            logger.info(f"Set quality benchmark: {system_name}.{subsystem_name}.{metric_name} {benchmark_type} = {benchmark_value}")

    def get_quality_benchmarks(self, system_name: str,
                              subsystem_name: Optional[str] = None) -> Dict[str, Any]:
        """Get quality benchmarks for a system or subsystem"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            query = """
                SELECT subsystem_name, metric_name, benchmark_type, benchmark_value,
                       set_timestamp, set_by, reasoning
                FROM quality_benchmarks
                WHERE system_name = ?
            """
            params = [system_name]

            if subsystem_name:
                query += " AND subsystem_name = ?"
                params.append(subsystem_name)

            query += " ORDER BY subsystem_name, metric_name"
            cursor.execute(query, params)

            benchmarks = {}
            for row in cursor.fetchall():
                subsys = row['subsystem_name']
                if subsys not in benchmarks:
                    benchmarks[subsys] = {}

                metric = row['metric_name']
                if metric not in benchmarks[subsys]:
                    benchmarks[subsys][metric] = {}

                benchmarks[subsys][metric][row['benchmark_type']] = {
                    'value': row['benchmark_value'],
                    'set_timestamp': row['set_timestamp'],
                    'set_by': row['set_by'],
                    'reasoning': row['reasoning']
                }

            return benchmarks

    # ========== LEARNING OUTCOMES ==========

    def record_learning_outcome(self, system_name: str, learning_category: str,
                               insight_summary: str, insight_detail: str,
                               evidence: Dict[str, Any], confidence_score: float,
                               applies_to_systems: List[str],
                               human_validated: bool = False) -> int:
        """Record a learning outcome"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            timestamp = datetime.now().isoformat()
            cursor.execute("""
                INSERT INTO learning_outcomes (
                    system_name, learning_category, insight_summary, insight_detail,
                    evidence, confidence_score, learned_timestamp, applies_to_systems,
                    human_validated
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                system_name, learning_category, insight_summary, insight_detail,
                json.dumps(evidence), confidence_score, timestamp,
                json.dumps(applies_to_systems), human_validated
            ))
            learning_id = cursor.lastrowid
            logger.info(f"Recorded learning outcome #{learning_id}: {system_name} - {learning_category}")
            return learning_id

    def get_learning_outcomes(self, system_name: Optional[str] = None,
                             learning_category: Optional[str] = None,
                             min_confidence: float = 0.5,
                             human_validated_only: bool = False) -> List[Dict[str, Any]]:
        """Get learning outcomes"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            query = """
                SELECT learning_id, system_name, learning_category, insight_summary,
                       insight_detail, evidence, confidence_score, learned_timestamp,
                       applies_to_systems, human_validated
                FROM learning_outcomes
                WHERE confidence_score >= ?
            """
            params = [min_confidence]

            if system_name:
                query += " AND system_name = ?"
                params.append(system_name)

            if learning_category:
                query += " AND learning_category = ?"
                params.append(learning_category)

            if human_validated_only:
                query += " AND human_validated = 1"

            query += " ORDER BY confidence_score DESC, learned_timestamp DESC"
            cursor.execute(query, params)

            outcomes = []
            for row in cursor.fetchall():
                outcomes.append({
                    'id': row['learning_id'],
                    'system': row['system_name'],
                    'category': row['learning_category'],
                    'summary': row['insight_summary'],
                    'detail': row['insight_detail'],
                    'evidence': json.loads(row['evidence']),
                    'confidence': row['confidence_score'],
                    'timestamp': row['learned_timestamp'],
                    'applies_to': json.loads(row['applies_to_systems']),
                    'human_validated': bool(row['human_validated'])
                })
            return outcomes

    def validate_learning_outcome(self, learning_id: int, validated: bool = True) -> None:
        """Mark a learning outcome as human-validated"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE learning_outcomes
                SET human_validated = ?
                WHERE learning_id = ?
            """, (validated, learning_id))
            logger.info(f"Learning outcome #{learning_id} validation set to: {validated}")

    # ========== LEARNING TRANSFERS ==========

    def record_learning_transfer(self, learning_id: int, source_system: str,
                                target_system: str, transfer_method: str,
                                adaptation_required: str, transfer_success: bool,
                                impact_summary: Optional[str] = None) -> None:
        """Record cross-system learning transfer"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            timestamp = datetime.now().isoformat()
            cursor.execute("""
                INSERT INTO learning_transfers (
                    learning_id, source_system, target_system, transfer_method,
                    adaptation_required, transfer_timestamp, transfer_success,
                    impact_summary
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                learning_id, source_system, target_system, transfer_method,
                adaptation_required, timestamp, transfer_success, impact_summary
            ))
            logger.info(f"Recorded learning transfer: {source_system} -> {target_system} (learning #{learning_id})")

    def get_learning_transfers(self, source_system: Optional[str] = None,
                              target_system: Optional[str] = None,
                              successful_only: bool = False) -> List[Dict[str, Any]]:
        """Get learning transfer history"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            query = """
                SELECT lt.transfer_id, lt.learning_id, lt.source_system, lt.target_system,
                       lt.transfer_method, lt.adaptation_required, lt.transfer_timestamp,
                       lt.transfer_success, lt.impact_summary,
                       lo.learning_category, lo.insight_summary
                FROM learning_transfers lt
                JOIN learning_outcomes lo ON lt.learning_id = lo.learning_id
                WHERE 1=1
            """
            params = []

            if source_system:
                query += " AND lt.source_system = ?"
                params.append(source_system)

            if target_system:
                query += " AND lt.target_system = ?"
                params.append(target_system)

            if successful_only:
                query += " AND lt.transfer_success = 1"

            query += " ORDER BY lt.transfer_timestamp DESC"
            cursor.execute(query, params)

            transfers = []
            for row in cursor.fetchall():
                transfers.append({
                    'transfer_id': row['transfer_id'],
                    'learning_id': row['learning_id'],
                    'source': row['source_system'],
                    'target': row['target_system'],
                    'method': row['transfer_method'],
                    'adaptation': row['adaptation_required'],
                    'timestamp': row['transfer_timestamp'],
                    'success': bool(row['transfer_success']),
                    'impact': row['impact_summary'],
                    'category': row['learning_category'],
                    'insight': row['insight_summary']
                })
            return transfers

    # ========== WATERWIZARD: SITE MODIFIERS ==========

    def create_site_modifier(self, modifier: SiteModifier) -> int:
        """Create or update site modifier for a WaterWizard job site"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO site_modifiers (
                    job_site_entity_id, job_site_name, soil_type, soil_quality_rating,
                    soil_drainage, slope_type, slope_percentage, slope_stability,
                    vegetation_type, vegetation_density, vegetation_removal_difficulty,
                    space_type, access_difficulty, equipment_restrictions,
                    labor_rate_multiplier, material_waste_multiplier, time_multiplier,
                    jobs_completed_count, total_variance_labor_hours, total_variance_material_cost
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                         COALESCE((SELECT jobs_completed_count FROM site_modifiers WHERE job_site_entity_id = ?), 0),
                         COALESCE((SELECT total_variance_labor_hours FROM site_modifiers WHERE job_site_entity_id = ?), 0.0),
                         COALESCE((SELECT total_variance_material_cost FROM site_modifiers WHERE job_site_entity_id = ?), 0.0))
            """, (
                modifier.job_site_entity_id, modifier.job_site_name,
                modifier.soil_type, modifier.soil_quality_rating, modifier.soil_drainage,
                modifier.slope_type, modifier.slope_percentage, modifier.slope_stability,
                modifier.vegetation_type, modifier.vegetation_density, modifier.vegetation_removal_difficulty,
                modifier.space_type, modifier.access_difficulty, modifier.equipment_restrictions,
                modifier.labor_rate_multiplier, modifier.material_waste_multiplier, modifier.time_multiplier,
                modifier.job_site_entity_id, modifier.job_site_entity_id, modifier.job_site_entity_id
            ))
            modifier_id = cursor.lastrowid
            logger.info(f"Created/updated site modifier for: {modifier.job_site_name}")
            return modifier_id

    def get_site_modifier(self, job_site_entity_id: str) -> Optional[SiteModifier]:
        """Get site modifier for a job site"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM site_modifiers WHERE job_site_entity_id = ?",
                         (job_site_entity_id,))
            row = cursor.fetchone()

            if row:
                return SiteModifier(
                    job_site_entity_id=row['job_site_entity_id'],
                    job_site_name=row['job_site_name'],
                    soil_type=row['soil_type'],
                    soil_quality_rating=row['soil_quality_rating'],
                    soil_drainage=row['soil_drainage'],
                    slope_type=row['slope_type'],
                    slope_percentage=row['slope_percentage'],
                    slope_stability=row['slope_stability'],
                    vegetation_type=row['vegetation_type'],
                    vegetation_density=row['vegetation_density'],
                    vegetation_removal_difficulty=row['vegetation_removal_difficulty'],
                    space_type=row['space_type'],
                    access_difficulty=row['access_difficulty'],
                    equipment_restrictions=row['equipment_restrictions'],
                    labor_rate_multiplier=row['labor_rate_multiplier'],
                    material_waste_multiplier=row['material_waste_multiplier'],
                    time_multiplier=row['time_multiplier'],
                    jobs_completed_count=row['jobs_completed_count'],
                    total_variance_labor_hours=row['total_variance_labor_hours'],
                    total_variance_material_cost=row['total_variance_material_cost']
                )
            return None

    def _update_site_modifier_multipliers_internal(self, cursor, job_site_entity_id: str,
                                                   labor_hours_variance: float,
                                                   material_cost_variance: float) -> None:
        """Internal method to update site modifier multipliers within existing transaction"""
        # Get current values
        cursor.execute("""
            SELECT jobs_completed_count, total_variance_labor_hours,
                   total_variance_material_cost, labor_rate_multiplier,
                   material_waste_multiplier
            FROM site_modifiers
            WHERE job_site_entity_id = ?
        """, (job_site_entity_id,))
        row = cursor.fetchone()

        if row:
            jobs_count = row['jobs_completed_count'] + 1
            total_labor_variance = row['total_variance_labor_hours'] + labor_hours_variance
            total_material_variance = row['total_variance_material_cost'] + material_cost_variance

            # Calculate new multipliers (moving average)
            # Positive variance = took longer/cost more than expected
            new_labor_multiplier = 1.0 + (total_labor_variance / jobs_count)
            new_material_multiplier = 1.0 + (total_material_variance / jobs_count)

            cursor.execute("""
                UPDATE site_modifiers
                SET jobs_completed_count = ?,
                    total_variance_labor_hours = ?,
                    total_variance_material_cost = ?,
                    labor_rate_multiplier = ?,
                    material_waste_multiplier = ?
                WHERE job_site_entity_id = ?
            """, (jobs_count, total_labor_variance, total_material_variance,
                 new_labor_multiplier, new_material_multiplier, job_site_entity_id))

            logger.info(f"Updated site modifiers for {job_site_entity_id}: labor={new_labor_multiplier:.3f}, material={new_material_multiplier:.3f}")

    def update_site_modifier_multipliers(self, job_site_entity_id: str,
                                        labor_hours_variance: float,
                                        material_cost_variance: float) -> None:
        """Update site modifier multipliers based on actual job variance"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            self._update_site_modifier_multipliers_internal(cursor, job_site_entity_id,
                                                           labor_hours_variance, material_cost_variance)

    # ========== WATERWIZARD: ESTIMATE ACTUALS ==========

    def record_estimate(self, estimate: EstimateActual) -> int:
        """Record a new estimate"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO estimate_actuals (
                    job_id, client_entity_id, job_site_entity_id, job_type,
                    estimate_timestamp, estimate_labor_hours, estimate_labor_cost,
                    estimate_materials_cost, estimate_total_cost,
                    estimate_generation_time_seconds, estimate_human_input_time_seconds,
                    estimate_template_usage_percent, estimate_custom_scopes_count,
                    estimate_custom_scopes_total_chars
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                estimate.job_id, estimate.client_entity_id, estimate.job_site_entity_id,
                estimate.job_type, estimate.estimate_timestamp, estimate.estimate_labor_hours,
                estimate.estimate_labor_cost, estimate.estimate_materials_cost,
                estimate.estimate_total_cost, estimate.estimate_generation_time_seconds,
                estimate.estimate_human_input_time_seconds, estimate.estimate_template_usage_percent,
                estimate.estimate_custom_scopes_count, estimate.estimate_custom_scopes_total_chars
            ))
            comparison_id = cursor.lastrowid
            logger.info(f"Recorded estimate for job {estimate.job_id}: ${estimate.estimate_total_cost:.2f}")
            return comparison_id

    def update_estimate_actuals(self, job_id: str, actual_labor_hours: float,
                               actual_labor_cost: float, actual_materials_cost: float,
                               customer_satisfaction: Optional[float] = None,
                               employee_satisfaction: Optional[float] = None,
                               management_satisfaction: Optional[float] = None,
                               site_conditions: Optional[Dict[str, Any]] = None,
                               weather_conditions: Optional[Dict[str, Any]] = None,
                               complications: Optional[List[str]] = None) -> None:
        """Update estimate with actual values and calculate variances"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Get estimate values
            cursor.execute("""
                SELECT estimate_labor_hours, estimate_labor_cost, estimate_materials_cost,
                       estimate_total_cost, job_site_entity_id
                FROM estimate_actuals
                WHERE job_id = ?
            """, (job_id,))
            row = cursor.fetchone()

            if not row:
                logger.error(f"No estimate found for job {job_id}")
                return

            est_labor_hours = row['estimate_labor_hours']
            est_labor_cost = row['estimate_labor_cost']
            est_materials_cost = row['estimate_materials_cost']
            est_total = row['estimate_total_cost']
            job_site_id = row['job_site_entity_id']

            actual_total_cost = actual_labor_cost + actual_materials_cost

            # Calculate variances
            labor_hours_var = actual_labor_hours - est_labor_hours
            labor_cost_var = actual_labor_cost - est_labor_cost
            materials_var = actual_materials_cost - est_materials_cost
            total_var = actual_total_cost - est_total

            labor_hours_var_pct = (labor_hours_var / est_labor_hours) if est_labor_hours > 0 else 0.0
            labor_cost_var_pct = (labor_cost_var / est_labor_cost) if est_labor_cost > 0 else 0.0
            materials_var_pct = (materials_var / est_materials_cost) if est_materials_cost > 0 else 0.0

            # Update estimate actuals
            cursor.execute("""
                UPDATE estimate_actuals
                SET actual_timestamp = ?,
                    actual_labor_hours = ?,
                    actual_labor_cost = ?,
                    actual_materials_cost = ?,
                    actual_total_cost = ?,
                    labor_hours_variance = ?,
                    labor_cost_variance = ?,
                    materials_cost_variance = ?,
                    total_cost_variance = ?,
                    labor_hours_variance_percent = ?,
                    labor_cost_variance_percent = ?,
                    materials_cost_variance_percent = ?,
                    customer_satisfaction_score = ?,
                    employee_satisfaction_score = ?,
                    management_satisfaction_score = ?,
                    site_conditions = ?,
                    weather_conditions = ?,
                    complications_encountered = ?
                WHERE job_id = ?
            """, (
                datetime.now().isoformat(),
                actual_labor_hours, actual_labor_cost, actual_materials_cost, actual_total_cost,
                labor_hours_var, labor_cost_var, materials_var, total_var,
                labor_hours_var_pct, labor_cost_var_pct, materials_var_pct,
                customer_satisfaction, employee_satisfaction, management_satisfaction,
                json.dumps(site_conditions) if site_conditions else None,
                json.dumps(weather_conditions) if weather_conditions else None,
                json.dumps(complications) if complications else None,
                job_id
            ))

            logger.info(f"Updated actuals for job {job_id}: ${actual_total_cost:.2f} (variance: ${total_var:+.2f})")

            # Update site modifiers if job site is known (use internal method to avoid nested transaction)
            if job_site_id:
                self._update_site_modifier_multipliers_internal(cursor, job_site_id, labor_hours_var_pct, materials_var_pct)

    def get_estimate_variance_analysis(self, job_type: Optional[str] = None,
                                      min_sample_size: int = 5) -> Dict[str, Any]:
        """Get variance analysis for estimate accuracy"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            query = """
                SELECT
                    job_type,
                    COUNT(*) as job_count,
                    AVG(labor_hours_variance_percent) as avg_labor_hours_var_pct,
                    AVG(labor_cost_variance_percent) as avg_labor_cost_var_pct,
                    AVG(materials_cost_variance_percent) as avg_materials_var_pct,
                    AVG(customer_satisfaction_score) as avg_customer_satisfaction,
                    AVG(employee_satisfaction_score) as avg_employee_satisfaction,
                    AVG(management_satisfaction_score) as avg_management_satisfaction,
                    AVG(estimate_generation_time_seconds) as avg_generation_time,
                    AVG(estimate_template_usage_percent) as avg_template_usage
                FROM estimate_actuals
                WHERE actual_timestamp IS NOT NULL
            """
            params = []

            if job_type:
                query += " AND job_type = ?"
                params.append(job_type)

            query += " GROUP BY job_type HAVING COUNT(*) >= ?"
            params.append(min_sample_size)

            cursor.execute(query, params)

            analysis = {}
            for row in cursor.fetchall():
                analysis[row['job_type']] = {
                    'sample_size': row['job_count'],
                    'avg_labor_hours_variance_pct': row['avg_labor_hours_var_pct'],
                    'avg_labor_cost_variance_pct': row['avg_labor_cost_var_pct'],
                    'avg_materials_variance_pct': row['avg_materials_var_pct'],
                    'avg_customer_satisfaction': row['avg_customer_satisfaction'],
                    'avg_employee_satisfaction': row['avg_employee_satisfaction'],
                    'avg_management_satisfaction': row['avg_management_satisfaction'],
                    'avg_generation_time_seconds': row['avg_generation_time'],
                    'avg_template_usage_pct': row['avg_template_usage']
                }

            return analysis

    # ========== DATABASE INFO ==========

    def get_database_version(self) -> str:
        """Get database schema version"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT version_number FROM database_version ORDER BY applied_timestamp DESC LIMIT 1")
            row = cursor.fetchone()
            return row['version_number'] if row else "unknown"

    def get_statistics(self) -> Dict[str, int]:
        """Get database statistics"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            stats = {}

            tables = [
                'entities', 'system_performance', 'session_memory', 'context_refresh',
                'decision_history', 'adaptive_parameters', 'quality_benchmarks',
                'learning_outcomes', 'learning_transfers', 'site_modifiers', 'estimate_actuals'
            ]

            for table in tables:
                cursor.execute(f"SELECT COUNT(*) as count FROM {table}")
                stats[table] = cursor.fetchone()['count']

            return stats


# ========== CLI FOR TESTING ==========

if __name__ == "__main__":
    import sys

    manager = UniverseMemoryManager()

    print(f"✅ UniverseMemoryManager initialized")
    print(f"📁 Database: {manager.db_path}")
    print(f"🔖 Version: {manager.get_database_version()}")
    print(f"\n📊 Database Statistics:")

    stats = manager.get_statistics()
    for table, count in stats.items():
        print(f"  {table}: {count} records")

    print(f"\n✅ UniverseMemoryManager operational")
