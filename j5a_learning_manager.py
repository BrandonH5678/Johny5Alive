#!/usr/bin/env python3
"""
J5A Learning Manager - Phase 3 Implementation

Integrates J5A Universe Memory with J5A Queue Management workflows.

Phase 3 Focus Areas:
1. Claude Queue operations learning
2. Night Shift Queue operations learning
3. Resource allocation optimization
4. Thermal safety decision tracking
5. Cross-system coordination improvements

Constitutional Compliance:
- Principle 2 (Transparency): All resource decisions tracked with reasoning
- Principle 3 (System Viability): Learning prevents crashes and ensures completion
- Principle 4 (Resource Stewardship): Optimal resource allocation based on history
"""

import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
import logging

# Add current directory for memory manager import
sys.path.insert(0, str(Path(__file__).parent))

from j5a_universe_memory import (
    UniverseMemoryManager,
    Entity, PerformanceMetric, SessionEvent, Decision,
    AdaptiveParameter
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class J5ALearningManager:
    """
    Manages active memory and adaptive feedback loops for J5A queue operations.

    Integrates with J5A Universe Memory to:
    - Track Claude Queue task performance
    - Learn from Night Shift batch operations
    - Optimize resource allocation decisions
    - Improve thermal safety gates
    - Enhance cross-system coordination
    """

    def __init__(self, memory_manager: Optional[UniverseMemoryManager] = None):
        """Initialize J5A learning manager"""
        self.memory = memory_manager if memory_manager else UniverseMemoryManager()
        logger.info("J5ALearningManager initialized")

        # Load current knowledge
        self._load_evergreen_knowledge()
        self._load_adaptive_parameters()
        self._load_quality_benchmarks()

    def _load_evergreen_knowledge(self):
        """Load evergreen knowledge from memory"""
        knowledge = self.memory.get_context_refresh("j5a", min_priority=0.7)
        self.evergreen = {k['key']: k['content'] for k in knowledge}
        logger.info(f"Loaded {len(self.evergreen)} pieces of evergreen knowledge")

    def _load_adaptive_parameters(self):
        """Load learned adaptive parameters"""
        params = self.memory.get_all_adaptive_parameters("j5a", min_confidence=0.5)
        self.adaptive_params = {
            f"{p.parameter_name}_{p.parameter_context}": p.parameter_value
            for p in params
        }
        logger.info(f"Loaded {len(self.adaptive_params)} adaptive parameters")

    def _load_quality_benchmarks(self):
        """Load quality benchmarks"""
        self.benchmarks = self.memory.get_quality_benchmarks("j5a")
        logger.info(f"Loaded quality benchmarks for {len(self.benchmarks)} subsystems")

    # ========== CLAUDE QUEUE LEARNING ==========

    def track_claude_queue_task(self,
                                task_id: str,
                                task_type: str,
                                priority: str,
                                duration_seconds: float,
                                success: bool,
                                failure_reason: Optional[str] = None,
                                resources_used: Optional[Dict[str, Any]] = None,
                                context: Optional[Dict[str, Any]] = None) -> None:
        """
        Track Claude Queue task execution for learning.

        Args:
            task_id: Unique task identifier
            task_type: Type of task (development, throughput, maintenance)
            priority: Priority level (high, medium, low)
            duration_seconds: Task execution time
            success: True if task completed successfully
            failure_reason: Reason for failure (if applicable)
            resources_used: Resource usage (memory, CPU, etc.)
            context: Additional context
        """
        # Track performance
        self.memory.record_performance(PerformanceMetric(
            system_name="j5a",
            subsystem_name="claude_queue",
            metric_name="task_duration_seconds",
            metric_value=duration_seconds,
            metric_unit="seconds",
            measurement_timestamp=datetime.now().isoformat(),
            context={
                "task_type": task_type,
                "priority": priority,
                "success": success,
                "resources": resources_used
            }
        ))

        # Track success rate
        self.memory.record_performance(PerformanceMetric(
            system_name="j5a",
            subsystem_name="claude_queue",
            metric_name="task_success_rate",
            metric_value=1.0 if success else 0.0,
            metric_unit="boolean",
            measurement_timestamp=datetime.now().isoformat(),
            context={"task_type": task_type, "priority": priority}
        ))

        # Check against benchmarks
        if "claude_queue" in self.benchmarks:
            bench = self.benchmarks["claude_queue"]

            # Check completion rate target
            if "task_completion_rate" in bench and "target" in bench["task_completion_rate"]:
                target_rate = bench["task_completion_rate"]["target"]["value"]

                if not success:
                    logger.warning(f"⚠️ Task {task_id} failed: {failure_reason}")

                    # Record session event for failures
                    self.memory.record_session_event(SessionEvent(
                        system_name="j5a",
                        session_id=f"claude_queue_{task_id}",
                        event_type="task_failure",
                        event_summary=f"Task {task_id} ({task_type}) failed: {failure_reason}",
                        importance_score=0.7,
                        event_timestamp=datetime.now().isoformat(),
                        full_context={
                            "task_type": task_type,
                            "priority": priority,
                            "failure_reason": failure_reason,
                            "resources_used": resources_used,
                            "context": context
                        }
                    ))

        logger.info(f"Tracked Claude Queue task: {task_id} ({task_type}) - {'✅ Success' if success else '❌ Failed'} in {duration_seconds:.1f}s")

    def analyze_claude_queue_performance(self, days: int = 30) -> Dict[str, Any]:
        """
        Analyze Claude Queue performance trends.

        Args:
            days: Number of days to analyze

        Returns:
            Performance analysis with recommendations
        """
        # Get recent performance
        duration_trend = self.memory.get_performance_trend(
            "j5a", "claude_queue", "task_duration_seconds", limit=100
        )
        success_trend = self.memory.get_performance_trend(
            "j5a", "claude_queue", "task_success_rate", limit=100
        )

        if not duration_trend:
            return {"status": "no_data", "message": "No Claude Queue task data available"}

        # Calculate statistics
        avg_duration = sum(t['value'] for t in duration_trend) / len(duration_trend)
        success_rate = sum(s['value'] for s in success_trend) / len(success_trend) if success_trend else 0.0

        # Analyze by task type
        by_type = {}
        for metric in duration_trend:
            if metric['context']:
                task_type = metric['context'].get('task_type', 'unknown')
                if task_type not in by_type:
                    by_type[task_type] = []
                by_type[task_type].append(metric['value'])

        type_analysis = {
            task_type: {
                "avg_duration": sum(durations) / len(durations),
                "count": len(durations)
            }
            for task_type, durations in by_type.items()
        }

        # Get benchmarks
        target_rate = 0.85  # Default 85% target
        if "claude_queue" in self.benchmarks:
            bench = self.benchmarks["claude_queue"]
            if "task_completion_rate" in bench and "target" in bench["task_completion_rate"]:
                target_rate = bench["task_completion_rate"]["target"]["value"]

        analysis = {
            "period_days": days,
            "sample_size": len(duration_trend),
            "avg_task_duration_seconds": avg_duration,
            "task_success_rate": success_rate,
            "target_success_rate": target_rate,
            "meets_success_target": success_rate >= target_rate,
            "by_task_type": type_analysis,
            "recommendations": []
        }

        # Generate recommendations
        if success_rate < target_rate:
            analysis["recommendations"].append({
                "priority": "high",
                "issue": "Success rate below target",
                "recommendation": f"Investigate task failures. Current: {success_rate:.0%}, Target: {target_rate:.0%}"
            })

        # Identify slow task types
        for task_type, stats in type_analysis.items():
            if stats['avg_duration'] > avg_duration * 1.5:
                analysis["recommendations"].append({
                    "priority": "medium",
                    "issue": f"{task_type} tasks significantly slower",
                    "recommendation": f"Optimize {task_type} tasks: {stats['avg_duration']:.1f}s vs. avg {avg_duration:.1f}s"
                })

        return analysis

    # ========== NIGHT SHIFT QUEUE LEARNING ==========

    def track_nightshift_batch(self,
                               batch_id: str,
                               tasks_queued: int,
                               tasks_completed: int,
                               tasks_failed: int,
                               total_duration_seconds: float,
                               thermal_issues: bool,
                               resource_constraints_hit: bool,
                               context: Optional[Dict[str, Any]] = None) -> None:
        """
        Track Night Shift batch execution for learning.

        Args:
            batch_id: Unique batch identifier
            tasks_queued: Total tasks in batch
            tasks_completed: Successfully completed tasks
            tasks_failed: Failed tasks
            total_duration_seconds: Total batch execution time
            thermal_issues: True if thermal constraints hit
            resource_constraints_hit: True if memory/CPU constraints hit
            context: Additional context (system states, conditions)
        """
        completion_rate = tasks_completed / tasks_queued if tasks_queued > 0 else 0.0

        # Track batch performance
        metrics = [
            PerformanceMetric(
                system_name="j5a",
                subsystem_name="nightshift_queue",
                metric_name="batch_completion_rate",
                metric_value=completion_rate,
                metric_unit="proportion",
                measurement_timestamp=datetime.now().isoformat(),
                context={
                    "tasks_queued": tasks_queued,
                    "tasks_completed": tasks_completed,
                    "tasks_failed": tasks_failed
                }
            ),
            PerformanceMetric(
                system_name="j5a",
                subsystem_name="nightshift_queue",
                metric_name="batch_duration_seconds",
                metric_value=total_duration_seconds,
                metric_unit="seconds",
                measurement_timestamp=datetime.now().isoformat(),
                context={"tasks_count": tasks_queued}
            ),
            PerformanceMetric(
                system_name="j5a",
                subsystem_name="nightshift_queue",
                metric_name="thermal_constraint_hit",
                metric_value=1.0 if thermal_issues else 0.0,
                metric_unit="boolean",
                measurement_timestamp=datetime.now().isoformat(),
                context=context
            )
        ]

        for metric in metrics:
            self.memory.record_performance(metric)

        # Record significant events
        if completion_rate < 0.8:
            self.memory.record_session_event(SessionEvent(
                system_name="j5a",
                session_id=f"nightshift_{batch_id}",
                event_type="low_completion_rate",
                event_summary=f"Night Shift batch {batch_id} only completed {completion_rate:.0%} of tasks",
                importance_score=0.8,
                event_timestamp=datetime.now().isoformat(),
                full_context={
                    "batch_id": batch_id,
                    "tasks_queued": tasks_queued,
                    "tasks_completed": tasks_completed,
                    "tasks_failed": tasks_failed,
                    "thermal_issues": thermal_issues,
                    "resource_constraints": resource_constraints_hit,
                    "context": context
                }
            ))

        logger.info(f"Tracked Night Shift batch: {batch_id} - {completion_rate:.0%} completion ({tasks_completed}/{tasks_queued})")

    def analyze_nightshift_performance(self) -> Dict[str, Any]:
        """
        Analyze Night Shift batch performance.

        Returns:
            Performance analysis with recommendations
        """
        # Get recent performance
        completion_trend = self.memory.get_performance_trend(
            "j5a", "nightshift_queue", "batch_completion_rate", limit=50
        )
        thermal_trend = self.memory.get_performance_trend(
            "j5a", "nightshift_queue", "thermal_constraint_hit", limit=50
        )

        if not completion_trend:
            return {"status": "no_data", "message": "No Night Shift batch data available"}

        # Calculate statistics
        avg_completion = sum(c['value'] for c in completion_trend) / len(completion_trend)
        thermal_frequency = sum(t['value'] for t in thermal_trend) / len(thermal_trend) if thermal_trend else 0.0

        analysis = {
            "sample_size": len(completion_trend),
            "avg_completion_rate": avg_completion,
            "thermal_constraint_frequency": thermal_frequency,
            "meets_target": avg_completion >= 0.85,
            "recommendations": []
        }

        # Generate recommendations
        if avg_completion < 0.85:
            analysis["recommendations"].append({
                "priority": "high",
                "issue": "Night Shift completion rate below 85%",
                "recommendation": f"Investigate failures. Current: {avg_completion:.0%}"
            })

        if thermal_frequency > 0.2:
            analysis["recommendations"].append({
                "priority": "high",
                "issue": "Frequent thermal constraints",
                "recommendation": f"Thermal issues in {thermal_frequency:.0%} of batches. Consider task scheduling adjustments."
            })

        return analysis

    # ========== RESOURCE ALLOCATION & THERMAL SAFETY ==========

    def track_resource_allocation_decision(self,
                                          decision_id: str,
                                          task_description: str,
                                          decision_made: str,
                                          reasoning: str,
                                          current_cpu_temp: float,
                                          current_memory_gb: float,
                                          thermal_limit: float,
                                          memory_limit: float,
                                          alternatives_considered: List[str],
                                          outcome: Optional[str] = None) -> None:
        """
        Track resource allocation decision with constitutional compliance.

        Args:
            decision_id: Unique decision identifier
            task_description: What task needed resources
            decision_made: The decision (defer, proceed, adjust)
            reasoning: Why this decision was made
            current_cpu_temp: Current CPU temperature
            current_memory_gb: Current memory usage
            thermal_limit: Thermal safety limit
            memory_limit: Memory safety limit
            alternatives_considered: Other options considered
            outcome: Actual outcome (to be updated later)
        """
        # Determine constitutional principles
        constitutional_compliance = {}

        if decision_made == "defer":
            constitutional_compliance["principle_3_system_viability"] = \
                "Preventing resource exhaustion ensures system availability"
            constitutional_compliance["principle_4_resource_stewardship"] = \
                "Respecting resource limits protects hardware and data integrity"
        elif decision_made == "proceed":
            constitutional_compliance["principle_3_system_viability"] = \
                "Task can complete safely within resource constraints"

        # Strategic alignment
        strategic_alignment = {
            "principle_7_autonomous_workflows": "Automatic resource gate operates without human intervention",
            "principle_9_local_llm_optimization": "Constraint-aware task scheduling"
        }

        # Record decision
        decision = Decision(
            system_name="j5a",
            decision_type="resource_allocation",
            decision_summary=f"{decision_made}: {task_description}",
            decision_rationale=reasoning,
            constitutional_compliance=constitutional_compliance,
            strategic_alignment=strategic_alignment,
            decision_timestamp=datetime.now().isoformat(),
            decided_by="j5a_resource_gate",
            outcome_expected=f"Task {'deferred until resources available' if decision_made == 'defer' else 'completes successfully'}",
            outcome_actual=outcome,
            parameters_used={
                "cpu_temp": current_cpu_temp,
                "memory_gb": current_memory_gb,
                "thermal_limit": thermal_limit,
                "memory_limit": memory_limit,
                "alternatives": alternatives_considered
            }
        )

        self.memory.record_decision(decision)
        logger.info(f"Tracked resource allocation decision: {decision_id} - {decision_made}")

    def update_resource_decision_outcome(self, decision_summary: str, outcome: str) -> None:
        """Update resource allocation decision with actual outcome"""
        self.memory.update_decision_outcome(decision_summary, outcome)
        logger.info(f"Updated decision outcome: {decision_summary[:50]}...")

    def get_thermal_safety_recommendation(self,
                                         current_cpu_temp: float,
                                         task_estimated_duration_seconds: float,
                                         task_cpu_intensive: bool) -> Dict[str, Any]:
        """
        Get recommendation for thermal safety based on current conditions and history.

        Args:
            current_cpu_temp: Current CPU temperature
            task_estimated_duration_seconds: Estimated task duration
            task_cpu_intensive: True if task is CPU-intensive

        Returns:
            Recommendation with reasoning
        """
        # Get thermal constraint history
        thermal_decisions = self.memory.get_decision_history("j5a", "resource_allocation", limit=50)
        thermal_issues = [d for d in thermal_decisions if "thermal" in d['rationale'].lower()]

        # Default thermal limit
        thermal_limit = 80.0

        # Get learned thermal threshold if available
        thermal_param = self.memory.get_adaptive_parameter(
            "j5a", "thermal_safety_threshold", "cpu_intensive_tasks"
        )
        if thermal_param:
            thermal_limit = thermal_param.parameter_value

        # Estimate peak temperature
        if task_cpu_intensive:
            # Learned or default: CPU intensive tasks add 5-8°C
            temp_increase = 7.0
        else:
            temp_increase = 3.0

        projected_peak = current_cpu_temp + temp_increase

        # Make recommendation
        if projected_peak > thermal_limit:
            recommendation = "defer"
            reasoning = f"Projected peak {projected_peak:.1f}°C exceeds limit {thermal_limit:.1f}°C"
            safe_threshold = thermal_limit - temp_increase - 2.0  # Safety margin
        else:
            recommendation = "proceed"
            reasoning = f"Projected peak {projected_peak:.1f}°C within limit {thermal_limit:.1f}°C"
            safe_threshold = None

        return {
            "recommendation": recommendation,
            "reasoning": reasoning,
            "current_temp": current_cpu_temp,
            "projected_peak": projected_peak,
            "thermal_limit": thermal_limit,
            "safe_threshold": safe_threshold,
            "thermal_issues_in_history": len(thermal_issues)
        }

    # ========== CROSS-SYSTEM COORDINATION ==========

    def track_cross_system_coordination(self,
                                       coordination_id: str,
                                       systems_involved: List[str],
                                       coordination_type: str,
                                       success: bool,
                                       conflicts_resolved: int,
                                       duration_seconds: float,
                                       context: Optional[Dict[str, Any]] = None) -> None:
        """
        Track cross-system coordination events.

        Args:
            coordination_id: Unique coordination identifier
            systems_involved: List of systems (squirt, j5a, sherlock)
            coordination_type: Type (resource_sharing, task_ordering, conflict_resolution)
            success: True if coordination successful
            conflicts_resolved: Number of conflicts resolved
            duration_seconds: Coordination time
            context: Additional context
        """
        self.memory.record_performance(PerformanceMetric(
            system_name="j5a",
            subsystem_name="cross_system_coordination",
            metric_name="coordination_success_rate",
            metric_value=1.0 if success else 0.0,
            metric_unit="boolean",
            measurement_timestamp=datetime.now().isoformat(),
            context={
                "systems": systems_involved,
                "type": coordination_type,
                "conflicts_resolved": conflicts_resolved
            }
        ))

        if conflicts_resolved > 0:
            self.memory.record_session_event(SessionEvent(
                system_name="j5a",
                session_id=f"coordination_{coordination_id}",
                event_type="coordination_success",
                event_summary=f"Resolved {conflicts_resolved} conflicts between {', '.join(systems_involved)}",
                importance_score=0.6,
                event_timestamp=datetime.now().isoformat(),
                full_context={
                    "coordination_id": coordination_id,
                    "systems": systems_involved,
                    "type": coordination_type,
                    "conflicts_resolved": conflicts_resolved,
                    "context": context
                }
            ))

        logger.info(f"Tracked cross-system coordination: {coordination_id} - {'✅ Success' if success else '❌ Failed'}")

    # ========== ADAPTIVE PARAMETER LEARNING ==========

    def learn_optimal_batch_size(self, observed_data: List[Dict[str, Any]]) -> None:
        """
        Learn optimal batch size from observed performance.

        Args:
            observed_data: List of {batch_size, completion_rate, duration} dicts
        """
        if len(observed_data) < 3:
            logger.warning("Insufficient data for batch size learning")
            return

        # Find batch size with best completion rate
        best = max(observed_data, key=lambda x: x['completion_rate'])

        param = AdaptiveParameter(
            system_name="j5a",
            parameter_name="optimal_batch_size",
            parameter_value=float(best['batch_size']),
            parameter_context="nightshift_queue",
            learning_source=f"analysis of {len(observed_data)} batches",
            confidence_score=min(0.5 + (len(observed_data) * 0.1), 0.95),
            last_updated_timestamp=datetime.now().isoformat()
        )

        self.memory.set_adaptive_parameter(param)
        logger.info(f"Learned optimal batch size: {best['batch_size']} (confidence: {param.confidence_score:.0%})")

    # ========== REPORTS ==========

    def generate_learning_report(self) -> Dict[str, Any]:
        """Generate comprehensive learning report for J5A"""
        report = {
            "generated_at": datetime.now().isoformat(),
            "system": "j5a",
            "sections": {}
        }

        # Claude Queue analysis
        claude_queue_analysis = self.analyze_claude_queue_performance(days=30)
        report["sections"]["claude_queue"] = claude_queue_analysis

        # Night Shift analysis
        nightshift_analysis = self.analyze_nightshift_performance()
        report["sections"]["nightshift_queue"] = nightshift_analysis

        # Decision history
        decisions = self.memory.get_decision_history("j5a", limit=20)
        report["sections"]["recent_decisions"] = {
            "count": len(decisions),
            "decisions": decisions[:5]  # Top 5
        }

        # Learning outcomes
        outcomes = self.memory.get_learning_outcomes(system_name="j5a", min_confidence=0.5)
        report["sections"]["learning_outcomes"] = {
            "count": len(outcomes),
            "outcomes": outcomes
        }

        # Adaptive parameters
        params = self.memory.get_all_adaptive_parameters("j5a", min_confidence=0.5)
        report["sections"]["adaptive_parameters"] = {
            "count": len(params),
            "parameters": [
                {
                    "name": p.parameter_name,
                    "value": p.parameter_value,
                    "context": p.parameter_context,
                    "confidence": p.confidence_score
                }
                for p in params
            ]
        }

        return report


# ========== CLI FOR TESTING ==========

if __name__ == "__main__":
    print("="*60)
    print("J5A Learning Manager - Test Mode")
    print("="*60)

    manager = J5ALearningManager()

    print(f"\n✅ J5A Learning Manager initialized")
    print(f"📊 Loaded {len(manager.evergreen)} evergreen knowledge items")
    print(f"📊 Loaded {len(manager.adaptive_params)} adaptive parameters")
    print(f"📊 Loaded benchmarks for {len(manager.benchmarks)} subsystems")

    print(f"\n📋 Generating learning report...")
    report = manager.generate_learning_report()

    print(f"\n✅ Learning Report Generated:")
    print(f"   Claude Queue: {report['sections']['claude_queue'].get('status', 'ready')}")
    print(f"   Night Shift Queue: {report['sections']['nightshift_queue'].get('status', 'ready')}")
    print(f"   Recent decisions: {report['sections']['recent_decisions']['count']}")
    print(f"   Learning outcomes: {report['sections']['learning_outcomes']['count']}")
    print(f"   Adaptive parameters: {report['sections']['adaptive_parameters']['count']}")

    print(f"\n✅ J5A Learning Manager ready for integration")
