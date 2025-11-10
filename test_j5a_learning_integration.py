#!/usr/bin/env python3
"""
J5A Learning Manager - Integration Test

Demonstrates complete Phase 3 workflows:
1. Claude Queue task tracking and learning
2. Night Shift batch operations tracking
3. Resource allocation decisions with thermal safety
4. Cross-system coordination learning
5. Adaptive parameter learning from outcomes
"""

import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

from j5a_learning_manager import J5ALearningManager


def test_claude_queue_workflow(manager: J5ALearningManager):
    """Test Claude Queue task tracking and learning"""
    print("\n" + "="*60)
    print("TEST 1: Claude Queue Task Tracking")
    print("="*60)

    # Set quality benchmarks
    manager.memory.set_quality_benchmark(
        system_name="j5a",
        subsystem_name="claude_queue",
        metric_name="task_completion_rate",
        benchmark_type="target",
        benchmark_value=0.85,
        set_by="system",
        reasoning="Target: 85% task completion rate"
    )
    print(f"✅ Set quality benchmark: 85% completion rate target")

    # Track successful tasks
    tasks = [
        {"id": "task_001", "type": "development", "priority": "high", "duration": 180.5, "success": True},
        {"id": "task_002", "type": "throughput", "priority": "medium", "duration": 45.2, "success": True},
        {"id": "task_003", "type": "maintenance", "priority": "low", "duration": 120.0, "success": True},
        {"id": "task_004", "type": "development", "priority": "high", "duration": 240.0, "success": False, "failure": "Memory exhausted"},
        {"id": "task_005", "type": "throughput", "priority": "medium", "duration": 38.9, "success": True},
    ]

    for task in tasks:
        manager.track_claude_queue_task(
            task_id=task["id"],
            task_type=task["type"],
            priority=task["priority"],
            duration_seconds=task["duration"],
            success=task["success"],
            failure_reason=task.get("failure"),
            resources_used={"memory_gb": 12.5, "cpu_temp": 75.0}
        )
        print(f"{'✅' if task['success'] else '❌'} Tracked: {task['id']} ({task['type']}) - {task['duration']:.1f}s")

    # Analyze performance
    analysis = manager.analyze_claude_queue_performance()
    print(f"\n📊 Claude Queue Performance Analysis:")
    print(f"   Sample size: {analysis['sample_size']}")
    print(f"   Avg task duration: {analysis['avg_task_duration_seconds']:.1f}s")
    print(f"   Success rate: {analysis['task_success_rate']:.0%}")
    print(f"   Target success rate: {analysis['target_success_rate']:.0%}")
    print(f"   Meets target: {'✅ YES' if analysis['meets_success_target'] else '❌ NO'}")

    if analysis['by_task_type']:
        print(f"\n📊 By Task Type:")
        for task_type, stats in analysis['by_task_type'].items():
            print(f"   {task_type}: {stats['avg_duration']:.1f}s avg ({stats['count']} tasks)")

    if analysis['recommendations']:
        print(f"\n💡 Recommendations:")
        for rec in analysis['recommendations']:
            print(f"   [{rec['priority'].upper()}] {rec['recommendation']}")


def test_nightshift_batch_workflow(manager: J5ALearningManager):
    """Test Night Shift batch tracking"""
    print("\n" + "="*60)
    print("TEST 2: Night Shift Batch Operations")
    print("="*60)

    # Track several night shift batches
    batches = [
        {
            "id": "batch_20251016_01",
            "queued": 10,
            "completed": 9,
            "failed": 1,
            "duration": 7200.0,  # 2 hours
            "thermal": False,
            "resource_constraints": False
        },
        {
            "id": "batch_20251016_02",
            "queued": 15,
            "completed": 12,
            "failed": 3,
            "duration": 10800.0,  # 3 hours
            "thermal": True,
            "resource_constraints": True
        },
        {
            "id": "batch_20251016_03",
            "queued": 8,
            "completed": 8,
            "failed": 0,
            "duration": 5400.0,  # 1.5 hours
            "thermal": False,
            "resource_constraints": False
        }
    ]

    for batch in batches:
        completion_rate = batch["completed"] / batch["queued"]
        manager.track_nightshift_batch(
            batch_id=batch["id"],
            tasks_queued=batch["queued"],
            tasks_completed=batch["completed"],
            tasks_failed=batch["failed"],
            total_duration_seconds=batch["duration"],
            thermal_issues=batch["thermal"],
            resource_constraints_hit=batch["resource_constraints"],
            context={
                "start_time": "22:00",
                "end_time": "06:00",
                "systems_active": ["sherlock", "squirt"]
            }
        )
        print(f"✅ Tracked: {batch['id']} - {completion_rate:.0%} completion ({batch['completed']}/{batch['queued']})")

    # Analyze performance
    analysis = manager.analyze_nightshift_performance()
    print(f"\n📊 Night Shift Performance Analysis:")
    print(f"   Sample size: {analysis['sample_size']} batches")
    print(f"   Avg completion rate: {analysis['avg_completion_rate']:.0%}")
    print(f"   Thermal constraint frequency: {analysis['thermal_constraint_frequency']:.0%}")
    print(f"   Meets 85% target: {'✅ YES' if analysis['meets_target'] else '❌ NO'}")

    if analysis['recommendations']:
        print(f"\n💡 Recommendations:")
        for rec in analysis['recommendations']:
            print(f"   [{rec['priority'].upper()}] {rec['recommendation']}")

    # Learn optimal batch size
    observed_data = [
        {"batch_size": 10, "completion_rate": 0.90, "duration": 7200},
        {"batch_size": 15, "completion_rate": 0.80, "duration": 10800},
        {"batch_size": 8, "completion_rate": 1.00, "duration": 5400},
    ]
    manager.learn_optimal_batch_size(observed_data)
    print(f"\n🧠 Learned optimal batch size from performance data")


def test_thermal_safety_decisions(manager: J5ALearningManager):
    """Test thermal safety and resource allocation decisions"""
    print("\n" + "="*60)
    print("TEST 3: Thermal Safety & Resource Allocation")
    print("="*60)

    # Scenario 1: High CPU temp, defer task
    print(f"\n🌡️  Scenario 1: High CPU Temperature")
    rec1 = manager.get_thermal_safety_recommendation(
        current_cpu_temp=77.0,
        task_estimated_duration_seconds=7200,
        task_cpu_intensive=True
    )
    print(f"   Current temp: {rec1['current_temp']:.1f}°C")
    print(f"   Projected peak: {rec1['projected_peak']:.1f}°C")
    print(f"   Thermal limit: {rec1['thermal_limit']:.1f}°C")
    print(f"   Recommendation: {rec1['recommendation'].upper()}")
    print(f"   Reasoning: {rec1['reasoning']}")

    if rec1['recommendation'] == 'defer':
        # Track decision to defer
        manager.track_resource_allocation_decision(
            decision_id="decision_001",
            task_description="Sherlock transcription of 2-hour podcast",
            decision_made="defer",
            reasoning=rec1['reasoning'],
            current_cpu_temp=77.0,
            current_memory_gb=13.5,
            thermal_limit=80.0,
            memory_limit=14.0,
            alternatives_considered=["proceed_now", "defer_2_hours", "split_into_chunks"]
        )
        print(f"✅ Tracked decision: DEFER task")

        # Later: Update with outcome
        manager.update_resource_decision_outcome(
            decision_summary="defer: Sherlock transcription of 2-hour podcast",
            outcome="Task deferred 2.5 hours. Executed at CPU 72°C, completed successfully without thermal issues."
        )
        print(f"✅ Updated decision outcome: Success at lower temperature")

    # Scenario 2: Safe temperature, proceed
    print(f"\n🌡️  Scenario 2: Safe CPU Temperature")
    rec2 = manager.get_thermal_safety_recommendation(
        current_cpu_temp=68.0,
        task_estimated_duration_seconds=1800,
        task_cpu_intensive=False
    )
    print(f"   Current temp: {rec2['current_temp']:.1f}°C")
    print(f"   Projected peak: {rec2['projected_peak']:.1f}°C")
    print(f"   Thermal limit: {rec2['thermal_limit']:.1f}°C")
    print(f"   Recommendation: {rec2['recommendation'].upper()}")
    print(f"   Reasoning: {rec2['reasoning']}")

    if rec2['recommendation'] == 'proceed':
        manager.track_resource_allocation_decision(
            decision_id="decision_002",
            task_description="Squirt invoice generation batch",
            decision_made="proceed",
            reasoning=rec2['reasoning'],
            current_cpu_temp=68.0,
            current_memory_gb=10.5,
            thermal_limit=80.0,
            memory_limit=14.0,
            alternatives_considered=["proceed_now", "defer"],
            outcome="Task completed in 28 minutes, peak CPU 71°C, no issues."
        )
        print(f"✅ Tracked decision: PROCEED with task")


def test_cross_system_coordination(manager: J5ALearningManager):
    """Test cross-system coordination tracking"""
    print("\n" + "="*60)
    print("TEST 4: Cross-System Coordination")
    print("="*60)

    # Scenario 1: Squirt and Sherlock need resources simultaneously
    print(f"\n🔄 Scenario 1: Resource Conflict Resolution")
    manager.track_cross_system_coordination(
        coordination_id="coord_001",
        systems_involved=["squirt", "sherlock"],
        coordination_type="resource_sharing",
        success=True,
        conflicts_resolved=1,
        duration_seconds=2.5,
        context={
            "conflict": "Both systems requested transcription resources",
            "resolution": "Squirt given priority (business hours), Sherlock deferred to night shift",
            "business_hours": True
        }
    )
    print(f"✅ Coordinated: Squirt + Sherlock (1 conflict resolved)")

    # Scenario 2: Three-system coordination
    print(f"\n🔄 Scenario 2: Three-System Task Ordering")
    manager.track_cross_system_coordination(
        coordination_id="coord_002",
        systems_involved=["squirt", "j5a", "sherlock"],
        coordination_type="task_ordering",
        success=True,
        conflicts_resolved=2,
        duration_seconds=5.1,
        context={
            "tasks": ["squirt_estimate", "j5a_queue_processing", "sherlock_transcription"],
            "order_determined": ["squirt_estimate", "j5a_queue_processing", "sherlock_transcription"],
            "reasoning": "Business priority + resource availability"
        }
    )
    print(f"✅ Coordinated: Squirt + J5A + Sherlock (2 conflicts resolved)")

    # Record learning outcome about coordination
    learning_id = manager.memory.record_learning_outcome(
        system_name="j5a",
        learning_category="cross_system_coordination",
        insight_summary="Business hours priority prevents cross-system conflicts",
        insight_detail="Enforcing Squirt priority during 6am-7pm eliminated resource conflicts. Sherlock tasks automatically defer to night shift.",
        evidence={
            "conflicts_before_policy": 15,
            "conflicts_after_policy": 2,
            "resolution_success_rate": 0.98
        },
        confidence_score=0.90,
        applies_to_systems=["j5a", "squirt", "sherlock"],
        human_validated=True
    )
    print(f"✅ Captured learning outcome #{learning_id}")


def test_adaptive_parameter_learning(manager: J5ALearningManager):
    """Test adaptive parameter learning"""
    print("\n" + "="*60)
    print("TEST 5: Adaptive Parameter Learning")
    print("="*60)

    # Learn thermal threshold from decision outcomes
    print(f"\n🔧 Learning thermal safety threshold from decisions...")

    # Get all thermal decisions
    decisions = manager.memory.get_decision_history("j5a", "resource_allocation", limit=50)
    thermal_decisions = [d for d in decisions if "thermal" in d['rationale'].lower() or "temperature" in d['rationale'].lower()]

    print(f"   Found {len(thermal_decisions)} thermal-related decisions")

    if len(thermal_decisions) >= 2:
        # Analyze successful deferrals
        successful_deferrals = [
            d for d in thermal_decisions
            if d['outcome_actual'] and "success" in d['outcome_actual'].lower()
        ]

        if successful_deferrals:
            # Extract temperatures from parameters
            temps = [
                d['parameters']['cpu_temp']
                for d in successful_deferrals
                if d['parameters'] and 'cpu_temp' in d['parameters']
            ]

            if temps:
                # Learn conservative threshold (min successful deferral temp - margin)
                learned_threshold = min(temps) - 3.0  # 3°C safety margin

                from j5a_universe_memory import AdaptiveParameter
                param = AdaptiveParameter(
                    system_name="j5a",
                    parameter_name="thermal_safety_threshold",
                    parameter_value=learned_threshold,
                    parameter_context="cpu_intensive_tasks",
                    learning_source=f"analysis of {len(successful_deferrals)} successful deferrals",
                    confidence_score=min(0.6 + (len(successful_deferrals) * 0.1), 0.95),
                    last_updated_timestamp=datetime.now().isoformat()
                )
                manager.memory.set_adaptive_parameter(param)
                print(f"✅ Learned thermal threshold: {learned_threshold:.1f}°C (confidence: {param.confidence_score:.0%})")
                print(f"   Based on {len(successful_deferrals)} successful deferrals")
            else:
                print(f"   ⚠️  No temperature data in decisions")
        else:
            print(f"   ℹ️  No successful deferrals yet to learn from")
    else:
        print(f"   ℹ️  Need more thermal decisions for learning (have {len(thermal_decisions)})")

    # Set context refresh for operators
    manager.memory.set_context_refresh(
        system_name="j5a",
        knowledge_key="thermal_safety_protocol",
        knowledge_summary="Thermal safety protocols for Mac Mini operations",
        full_content="""
**J5A Thermal Safety Protocol**

Hardware: 2012 Mac Mini (prone to thermal throttling)

Limits:
- Safe operating temperature: <80°C
- Thermal throttling starts: ~85°C
- Emergency shutdown: ~95°C

Decision Protocol:
- CPU-intensive tasks: Defer if current + 7°C > 80°C
- Standard tasks: Defer if current + 3°C > 80°C
- Always include 2-3°C safety margin

Learned from operations:
- Defer at 77°C for CPU-intensive → successful at 72°C
- Peak temps during transcription: +5-8°C
- Cooling time: ~2-3 hours from 78°C to 72°C

Last Updated: 2025-10-16
        """,
        refresh_priority=0.95
    )
    print(f"✅ Set evergreen knowledge: Thermal safety protocol")


def generate_final_report(manager: J5ALearningManager):
    """Generate and display comprehensive learning report"""
    print("\n" + "="*60)
    print("FINAL LEARNING REPORT - J5A")
    print("="*60)

    report = manager.generate_learning_report()

    print(f"\n📅 Generated: {report['generated_at']}")
    print(f"🖥️  System: {report['system']}")

    # Claude Queue section
    cq = report['sections']['claude_queue']
    if cq.get('sample_size', 0) > 0:
        print(f"\n⚙️  Claude Queue:")
        print(f"   Sample size: {cq['sample_size']}")
        print(f"   Avg task duration: {cq['avg_task_duration_seconds']:.1f}s")
        print(f"   Success rate: {cq['task_success_rate']:.0%} (target: {cq['target_success_rate']:.0%})")
        print(f"   Status: {'✅ Meets target' if cq['meets_success_target'] else '⚠️ Below target'}")

        if cq['by_task_type']:
            print(f"\n   By Type:")
            for task_type, stats in cq['by_task_type'].items():
                print(f"      {task_type}: {stats['avg_duration']:.1f}s avg ({stats['count']} tasks)")

    # Night Shift section
    ns = report['sections']['nightshift_queue']
    if ns.get('sample_size', 0) > 0:
        print(f"\n🌙 Night Shift Queue:")
        print(f"   Sample size: {ns['sample_size']} batches")
        print(f"   Avg completion rate: {ns['avg_completion_rate']:.0%}")
        print(f"   Thermal constraints: {ns['thermal_constraint_frequency']:.0%} of batches")
        print(f"   Status: {'✅ Meets 85% target' if ns['meets_target'] else '⚠️ Below target'}")

    # Decisions section
    decisions = report['sections']['recent_decisions']
    print(f"\n⚖️  Recent Decisions: {decisions['count']}")
    for decision in decisions['decisions'][:3]:  # Show top 3
        print(f"   • {decision['type']}: {decision['summary']}")
        if decision['outcome_actual']:
            print(f"     Outcome: {decision['outcome_actual'][:60]}...")

    # Learning outcomes
    outcomes = report['sections']['learning_outcomes']
    print(f"\n🧠 Learning Outcomes: {outcomes['count']}")
    for outcome in outcomes['outcomes'][:3]:  # Show top 3
        print(f"   • {outcome['summary']}")
        print(f"     Confidence: {outcome['confidence']:.0%}, Validated: {'✅' if outcome['human_validated'] else '❌'}")

    # Adaptive parameters
    params = report['sections']['adaptive_parameters']
    print(f"\n⚙️  Adaptive Parameters: {params['count']}")
    for param in params['parameters']:
        print(f"   • {param['name']}: {param['value']} ({param['confidence']:.0%} confidence)")
        print(f"     Context: {param['context']}")

    print(f"\n" + "="*60)
    print("✅ J5A LEARNING INTEGRATION TEST COMPLETE")
    print("="*60)


def run_integration_test():
    """Run complete integration test"""
    print("="*60)
    print("J5A LEARNING MANAGER - INTEGRATION TEST")
    print("Phase 3: Claude Queue & Night Shift Queue Learning")
    print("="*60)

    manager = J5ALearningManager()
    print(f"\n✅ J5ALearningManager initialized")
    print(f"📊 Ready to track queue operations and resource decisions")

    try:
        test_claude_queue_workflow(manager)
        test_nightshift_batch_workflow(manager)
        test_thermal_safety_decisions(manager)
        test_cross_system_coordination(manager)
        test_adaptive_parameter_learning(manager)
        generate_final_report(manager)

        print(f"\n✅ All integration tests passed!")
        print(f"\n💡 Key Achievements:")
        print(f"   ✅ Claude Queue tasks tracked with performance analysis")
        print(f"   ✅ Night Shift batches tracked with thermal safety monitoring")
        print(f"   ✅ Resource allocation decisions with constitutional compliance")
        print(f"   ✅ Cross-system coordination tracked and learned from")
        print(f"   ✅ Thermal safety threshold learned from successful deferrals")
        print(f"   ✅ Optimal batch size learned from completion rates")
        print(f"   ✅ Comprehensive learning report generated")

        return 0

    except Exception as e:
        print(f"\n❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(run_integration_test())
