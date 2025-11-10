#!/usr/bin/env python3
"""
Integration Tests for J5A Universe Memory Manager

Tests all major functionality of the unified memory system:
- Entity management
- Performance tracking
- Session memory
- Context refresh (evergreen knowledge)
- Decision history
- Adaptive parameters
- Quality benchmarks
- Learning outcomes
- Learning transfers
- WaterWizard site modifiers
- WaterWizard estimate actuals
"""

import sys
import os
from datetime import datetime
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from j5a_universe_memory import (
    UniverseMemoryManager,
    Entity, PerformanceMetric, SessionEvent, Decision,
    AdaptiveParameter, SiteModifier, EstimateActual
)


def test_entity_management(manager: UniverseMemoryManager):
    """Test entity creation, retrieval, and search"""
    print("\n🧪 Testing Entity Management...")

    # Create a WaterWizard client entity
    client = Entity(
        entity_id="client_waterwizard_john_smith",
        entity_type="client",
        entity_name="John Smith",
        system_origin="squirt",
        attributes={
            "email": "john@example.com",
            "phone": "555-1234",
            "address": "123 Main St",
            "preferred_contact": "email"
        },
        created_timestamp=datetime.now().isoformat(),
        last_updated_timestamp=datetime.now().isoformat(),
        aliases=["J. Smith", "John S."]
    )
    manager.create_entity(client)

    # Create a job site entity
    job_site = Entity(
        entity_id="job_site_smith_backyard",
        entity_type="job_site",
        entity_name="Smith Residence - Backyard",
        system_origin="squirt",
        attributes={
            "address": "123 Main St",
            "size_sqft": 2000,
            "features": ["sloped", "rocky soil", "mature trees"]
        },
        created_timestamp=datetime.now().isoformat(),
        last_updated_timestamp=datetime.now().isoformat(),
        related_entities=["client_waterwizard_john_smith"]
    )
    manager.create_entity(job_site)

    # Create a Sherlock entity
    speaker = Entity(
        entity_id="speaker_david_grusch",
        entity_type="speaker",
        entity_name="David Grusch",
        system_origin="sherlock",
        attributes={
            "title": "Former USAF Intelligence Officer",
            "affiliation": "AARO Whistleblower",
            "topics": ["UAP", "crash retrieval", "reverse engineering"]
        },
        created_timestamp=datetime.now().isoformat(),
        last_updated_timestamp=datetime.now().isoformat(),
        aliases=["Dave Grusch", "D. Grusch"]
    )
    manager.create_entity(speaker)

    # Test retrieval
    retrieved = manager.get_entity("client_waterwizard_john_smith")
    assert retrieved is not None
    assert retrieved.entity_name == "John Smith"
    print(f"  ✅ Retrieved entity: {retrieved.entity_name}")

    # Test search by type
    clients = manager.search_entities(entity_type="client")
    assert len(clients) >= 1
    print(f"  ✅ Found {len(clients)} client entities")

    # Test search by system
    squirt_entities = manager.search_entities(system_origin="squirt")
    assert len(squirt_entities) >= 2
    print(f"  ✅ Found {len(squirt_entities)} Squirt entities")

    # Test usage increment
    manager.increment_entity_usage("client_waterwizard_john_smith")
    retrieved_after = manager.get_entity("client_waterwizard_john_smith")
    assert retrieved_after.usage_count == 1
    print(f"  ✅ Usage count incremented to {retrieved_after.usage_count}")


def test_performance_tracking(manager: UniverseMemoryManager):
    """Test performance metric recording and trend analysis"""
    print("\n🧪 Testing Performance Tracking...")

    # Record Squirt invoice generation metrics
    for i, time in enumerate([28.5, 26.2, 29.8, 25.1, 27.3]):
        metric = PerformanceMetric(
            system_name="squirt",
            subsystem_name="invoice",
            metric_name="generation_time_seconds",
            metric_value=time,
            metric_unit="seconds",
            measurement_timestamp=datetime.now().isoformat(),
            context={"iteration": i+1}
        )
        manager.record_performance(metric)

    # Get trend
    trend = manager.get_performance_trend("squirt", "invoice", "generation_time_seconds", limit=5)
    assert len(trend) == 5
    print(f"  ✅ Recorded 5 invoice generation metrics")
    print(f"  📊 Average time: {sum(t['value'] for t in trend) / len(trend):.1f}s")

    # Record J5A queue metrics
    queue_metric = PerformanceMetric(
        system_name="j5a",
        subsystem_name="nightshift_queue",
        metric_name="task_completion_rate",
        metric_value=0.87,
        metric_unit="proportion",
        measurement_timestamp=datetime.now().isoformat()
    )
    manager.record_performance(queue_metric)

    # Get latest performance for J5A
    latest = manager.get_latest_performance("j5a", "nightshift_queue")
    assert "task_completion_rate" in latest
    print(f"  ✅ J5A Night Shift completion rate: {latest['task_completion_rate']['value']:.2%}")


def test_session_memory(manager: UniverseMemoryManager):
    """Test session event recording and context retrieval"""
    print("\n🧪 Testing Session Memory...")

    # Record a critical session event
    event = SessionEvent(
        system_name="squirt",
        session_id="session_20251016_estimate_generation",
        event_type="learning",
        event_summary="Customer requested labor breakdown detail for deck estimate",
        importance_score=0.8,
        event_timestamp=datetime.now().isoformat(),
        full_context={
            "customer_request": "Can you break down the labor hours by task?",
            "adaptation": "Added task-level labor breakdown to estimate template"
        },
        related_entities=["client_waterwizard_john_smith"]
    )
    manager.record_session_event(event)

    # Retrieve session context
    context = manager.get_session_context("squirt", min_importance=0.5)
    assert len(context) >= 1
    print(f"  ✅ Recorded session event with importance {event.importance_score}")
    print(f"  📋 Retrieved {len(context)} high-importance events")


def test_context_refresh(manager: UniverseMemoryManager):
    """Test evergreen knowledge management"""
    print("\n🧪 Testing Context Refresh (Evergreen Knowledge)...")

    # Set evergreen knowledge for Squirt
    manager.set_context_refresh(
        system_name="squirt",
        knowledge_key="deck_labor_rates",
        knowledge_summary="Labor rates for deck construction by complexity",
        full_content="""
        Standard deck: $45/hour base rate
        Complex deck (multi-level, custom): $65/hour base rate
        Site modifiers apply: soil, slope, access difficulty
        """,
        refresh_priority=0.9
    )

    manager.set_context_refresh(
        system_name="squirt",
        knowledge_key="irrigation_materials_costs",
        knowledge_summary="Standard irrigation materials pricing",
        full_content="Sprinkler heads: $8-15 each, PVC pipe: $0.50/ft, Controller: $150-400",
        refresh_priority=0.7
    )

    # Retrieve evergreen knowledge
    knowledge = manager.get_context_refresh("squirt", min_priority=0.6)
    assert len(knowledge) >= 2
    print(f"  ✅ Set 2 pieces of evergreen knowledge")
    print(f"  📚 Retrieved {len(knowledge)} high-priority knowledge items")


def test_decision_history(manager: UniverseMemoryManager):
    """Test decision recording with constitutional compliance"""
    print("\n🧪 Testing Decision History...")

    # Record a significant decision
    decision = Decision(
        system_name="j5a",
        decision_type="resource_allocation",
        decision_summary="Defer Sherlock transcription task due to thermal constraints",
        decision_rationale="CPU temperature 78°C, projected to reach 85°C during transcription",
        constitutional_compliance={
            "principle_3": "System Viability - preventing thermal shutdown",
            "principle_4": "Resource Stewardship - respecting thermal limits"
        },
        strategic_alignment={
            "principle_7": "Autonomous Workflows - automatic thermal safety gate",
            "principle_9": "Local LLM Optimization - constraint-aware scheduling"
        },
        decision_timestamp=datetime.now().isoformat(),
        decided_by="j5a_thermal_safety_gate",
        outcome_expected="Task deferred until CPU < 75°C, preventing crash",
        parameters_used={
            "cpu_temp": 78.0,
            "thermal_limit": 80.0,
            "projected_temp": 85.0
        }
    )
    manager.record_decision(decision)

    # Update outcome later
    manager.update_decision_outcome(
        decision_summary=decision.decision_summary,
        outcome_actual="Task successfully executed 2 hours later at 72°C, completed without issues"
    )

    # Retrieve decision history
    decisions = manager.get_decision_history("j5a", decision_type="resource_allocation")
    assert len(decisions) >= 1
    print(f"  ✅ Recorded decision with constitutional compliance")
    print(f"  ⚖️ Aligned with {len(decision.constitutional_compliance)} constitutional principles")


def test_adaptive_parameters(manager: UniverseMemoryManager):
    """Test adaptive parameter learning"""
    print("\n🧪 Testing Adaptive Parameters...")

    # Set learned parameter for Squirt
    param = AdaptiveParameter(
        system_name="squirt",
        parameter_name="deck_labor_rate",
        parameter_value=52.5,
        parameter_context="2-level deck, sloped yard, rocky soil",
        learning_source="actual variance from 5 completed jobs",
        confidence_score=0.85,
        last_updated_timestamp=datetime.now().isoformat()
    )
    manager.set_adaptive_parameter(param)

    # Retrieve parameter
    retrieved_param = manager.get_adaptive_parameter(
        "squirt", "deck_labor_rate", "2-level deck, sloped yard, rocky soil"
    )
    assert retrieved_param is not None
    assert retrieved_param.parameter_value == 52.5
    print(f"  ✅ Set adaptive parameter: {param.parameter_name} = ${param.parameter_value}/hr")
    print(f"  📈 Confidence: {param.confidence_score:.2%}")

    # Get all parameters for Squirt
    all_params = manager.get_all_adaptive_parameters("squirt", min_confidence=0.5)
    assert len(all_params) >= 1
    print(f"  📋 Retrieved {len(all_params)} high-confidence parameters")


def test_quality_benchmarks(manager: UniverseMemoryManager):
    """Test quality benchmark management"""
    print("\n🧪 Testing Quality Benchmarks...")

    # Set new benchmark
    manager.set_quality_benchmark(
        system_name="squirt",
        subsystem_name="estimate",
        metric_name="template_usage_percent",
        benchmark_type="target",
        benchmark_value=0.75,
        set_by="human_operator",
        reasoning="Target 75% template usage to maintain efficiency while allowing customization"
    )

    # Retrieve benchmarks
    benchmarks = manager.get_quality_benchmarks("squirt", subsystem_name="estimate")
    assert "estimate" in benchmarks
    print(f"  ✅ Set quality benchmark for estimate template usage: 75%")
    print(f"  📊 Total benchmarks for Squirt estimate: {len(benchmarks['estimate'])}")


def test_learning_outcomes(manager: UniverseMemoryManager):
    """Test learning outcome capture and validation"""
    print("\n🧪 Testing Learning Outcomes...")

    # Record a learning outcome
    learning_id = manager.record_learning_outcome(
        system_name="squirt",
        learning_category="estimate_accuracy",
        insight_summary="Sloped yards require 1.3x labor multiplier",
        insight_detail="Analysis of 15 completed jobs shows consistent 30% labor increase for sloped yards",
        evidence={
            "sample_size": 15,
            "avg_variance": 0.31,
            "std_dev": 0.08,
            "job_types": ["deck", "patio", "retaining_wall"]
        },
        confidence_score=0.88,
        applies_to_systems=["squirt"],
        human_validated=False
    )

    # Validate the learning
    manager.validate_learning_outcome(learning_id, validated=True)

    # Retrieve learning outcomes
    outcomes = manager.get_learning_outcomes(
        system_name="squirt",
        min_confidence=0.7,
        human_validated_only=False
    )
    assert len(outcomes) >= 1
    print(f"  ✅ Recorded learning outcome #{learning_id}")
    print(f"  📚 Retrieved {len(outcomes)} high-confidence learnings")


def test_learning_transfers(manager: UniverseMemoryManager):
    """Test cross-system learning transfer"""
    print("\n🧪 Testing Learning Transfers...")

    # First create a learning outcome in Sherlock
    learning_id = manager.record_learning_outcome(
        system_name="sherlock",
        learning_category="audio_processing",
        insight_summary="Chunked processing prevents memory crashes",
        insight_detail="Processing audio in 10-minute chunks with incremental saves eliminates OOM crashes",
        evidence={
            "sample_size": 8,
            "success_rate_before": 0.40,
            "success_rate_after": 0.95
        },
        confidence_score=0.92,
        applies_to_systems=["sherlock", "squirt", "j5a"],
        human_validated=True
    )

    # Record transfer to Squirt
    manager.record_learning_transfer(
        learning_id=learning_id,
        source_system="sherlock",
        target_system="squirt",
        transfer_method="adapted_chunking_strategy",
        adaptation_required="Applied to voice memo processing with 5-minute chunks",
        transfer_success=True,
        impact_summary="Voice memo processing success rate improved from 85% to 98%"
    )

    # Retrieve transfers
    transfers = manager.get_learning_transfers(source_system="sherlock", successful_only=True)
    assert len(transfers) >= 1
    print(f"  ✅ Recorded learning transfer: Sherlock → Squirt")
    print(f"  🔄 Total successful transfers from Sherlock: {len(transfers)}")


def test_site_modifiers(manager: UniverseMemoryManager):
    """Test WaterWizard site modifier management"""
    print("\n🧪 Testing WaterWizard Site Modifiers...")

    # Create site modifier
    modifier = SiteModifier(
        job_site_entity_id="job_site_smith_backyard",
        job_site_name="Smith Residence - Backyard",
        soil_type="rocky",
        soil_quality_rating=0.4,
        soil_drainage="moderate",
        slope_type="moderate",
        slope_percentage=15.0,
        slope_stability="stable",
        vegetation_type="trees_small",
        vegetation_density=0.6,
        vegetation_removal_difficulty=0.5,
        space_type="tight_access",
        access_difficulty=0.7,
        equipment_restrictions="no large excavator",
        labor_rate_multiplier=1.0,
        material_waste_multiplier=1.0,
        time_multiplier=1.0
    )
    manager.create_site_modifier(modifier)

    # Retrieve site modifier
    retrieved = manager.get_site_modifier("job_site_smith_backyard")
    assert retrieved is not None
    assert retrieved.soil_type == "rocky"
    print(f"  ✅ Created site modifier for: {retrieved.job_site_name}")
    print(f"  🏗️ Site characteristics: {retrieved.soil_type}, {retrieved.slope_type} slope, {retrieved.space_type}")

    # Simulate job completion and update multipliers
    manager.update_site_modifier_multipliers(
        job_site_entity_id="job_site_smith_backyard",
        labor_hours_variance=0.25,  # 25% more labor than estimated
        material_cost_variance=0.10   # 10% more materials than estimated
    )

    # Retrieve updated modifier
    updated = manager.get_site_modifier("job_site_smith_backyard")
    assert updated.labor_rate_multiplier > 1.0
    print(f"  📈 Updated multipliers: labor={updated.labor_rate_multiplier:.3f}, material={updated.material_waste_multiplier:.3f}")


def test_estimate_actuals(manager: UniverseMemoryManager):
    """Test WaterWizard estimate vs. actual tracking"""
    print("\n🧪 Testing WaterWizard Estimate Actuals...")

    # Record an estimate
    estimate = EstimateActual(
        job_id="job_20251016_smith_deck",
        client_entity_id="client_waterwizard_john_smith",
        job_site_entity_id="job_site_smith_backyard",
        job_type="deck_construction",
        estimate_timestamp=datetime.now().isoformat(),
        estimate_labor_hours=24.0,
        estimate_labor_cost=1200.00,
        estimate_materials_cost=3500.00,
        estimate_total_cost=4700.00,
        estimate_generation_time_seconds=45.2,
        estimate_human_input_time_seconds=120.0,
        estimate_template_usage_percent=0.68,
        estimate_custom_scopes_count=2,
        estimate_custom_scopes_total_chars=450
    )
    comparison_id = manager.record_estimate(estimate)
    print(f"  ✅ Recorded estimate: ${estimate.estimate_total_cost:.2f}")

    # Update with actual values after job completion
    manager.update_estimate_actuals(
        job_id="job_20251016_smith_deck",
        actual_labor_hours=28.5,
        actual_labor_cost=1425.00,
        actual_materials_cost=3680.00,
        customer_satisfaction=0.92,
        employee_satisfaction=0.85,
        management_satisfaction=0.88,
        site_conditions={"weather": "ideal", "access": "difficult"},
        weather_conditions={"rain_days": 0, "high_wind_days": 1},
        complications=["rocky soil required additional excavation", "tight access required hand-carrying materials"]
    )
    print(f"  ✅ Updated with actuals: labor variance +18.8%, materials variance +5.1%")

    # Get variance analysis
    analysis = manager.get_estimate_variance_analysis(job_type="deck_construction", min_sample_size=1)
    if "deck_construction" in analysis:
        deck_analysis = analysis["deck_construction"]
        print(f"  📊 Deck construction analysis:")
        print(f"     Sample size: {deck_analysis['sample_size']}")
        print(f"     Avg labor variance: {deck_analysis['avg_labor_hours_variance_pct']*100:+.1f}%")
        print(f"     Avg customer satisfaction: {deck_analysis['avg_customer_satisfaction']:.2%}")


def run_all_tests():
    """Run all integration tests"""
    print("=" * 60)
    print("J5A Universe Memory Manager - Integration Tests")
    print("=" * 60)

    manager = UniverseMemoryManager()
    print(f"📁 Database: {manager.db_path}")
    print(f"🔖 Version: {manager.get_database_version()}")

    tests = [
        test_entity_management,
        test_performance_tracking,
        test_session_memory,
        test_context_refresh,
        test_decision_history,
        test_adaptive_parameters,
        test_quality_benchmarks,
        test_learning_outcomes,
        test_learning_transfers,
        test_site_modifiers,
        test_estimate_actuals
    ]

    passed = 0
    failed = 0

    for test_func in tests:
        try:
            test_func(manager)
            passed += 1
        except Exception as e:
            print(f"  ❌ Test failed: {e}")
            failed += 1

    print("\n" + "=" * 60)
    print(f"Test Results: {passed} passed, {failed} failed")
    print("=" * 60)

    # Final database statistics
    print(f"\n📊 Final Database Statistics:")
    stats = manager.get_statistics()
    for table, count in stats.items():
        if count > 0:
            print(f"  {table}: {count} records")

    if failed == 0:
        print("\n✅ All tests passed!")
        return 0
    else:
        print(f"\n❌ {failed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(run_all_tests())
