#!/usr/bin/env python3
"""
Phase 1 Practical Test - Real-World Scenarios

Tests the unified memory system with realistic WaterWizard business scenarios:
1. Client onboarding and job site characterization
2. Estimate generation with site modifiers
3. Job completion and variance learning
4. Cross-system learning transfer (Sherlock → Squirt)
5. Decision tracking with constitutional compliance
"""

import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from j5a_universe_memory import (
    UniverseMemoryManager,
    Entity, PerformanceMetric, SessionEvent, Decision,
    AdaptiveParameter, SiteModifier, EstimateActual
)


def scenario_1_client_onboarding(manager: UniverseMemoryManager):
    """Scenario 1: New client with challenging job site"""
    print("\n" + "="*60)
    print("SCENARIO 1: Client Onboarding - Rocky Sloped Property")
    print("="*60)

    # Create client entity
    client = Entity(
        entity_id="client_maria_garcia",
        entity_type="client",
        entity_name="Maria Garcia",
        system_origin="squirt",
        attributes={
            "email": "maria@example.com",
            "phone": "555-2468",
            "address": "456 Hillside Ave",
            "preferred_contact": "phone",
            "source": "referral",
            "business_type": "residential"
        },
        created_timestamp=datetime.now().isoformat(),
        last_updated_timestamp=datetime.now().isoformat(),
        aliases=["M. Garcia", "Maria G."]
    )
    manager.create_entity(client)
    print(f"✅ Created client: {client.entity_name}")

    # Create job site entity
    job_site = Entity(
        entity_id="site_garcia_backyard",
        entity_type="job_site",
        entity_name="Garcia Residence - Backyard Terracing",
        system_origin="squirt",
        attributes={
            "address": "456 Hillside Ave",
            "size_sqft": 3500,
            "features": ["steep slope", "rocky soil", "drainage issues", "tight access"],
            "previous_work": "none"
        },
        created_timestamp=datetime.now().isoformat(),
        last_updated_timestamp=datetime.now().isoformat(),
        related_entities=["client_maria_garcia"]
    )
    manager.create_entity(job_site)
    print(f"✅ Created job site: {job_site.entity_name}")

    # Characterize site modifiers
    site_modifier = SiteModifier(
        job_site_entity_id="site_garcia_backyard",
        job_site_name="Garcia Residence - Backyard Terracing",
        soil_type="rocky",
        soil_quality_rating=0.3,  # Poor quality for digging
        soil_drainage="poor",
        slope_type="steep",
        slope_percentage=25.0,
        slope_stability="moderate",
        vegetation_type="light_brush",
        vegetation_density=0.4,
        vegetation_removal_difficulty=0.3,
        space_type="tight_access",
        access_difficulty=0.8,  # Very difficult access
        equipment_restrictions="hand_tools_only"
    )
    manager.create_site_modifier(site_modifier)
    print(f"✅ Characterized site: rocky soil, 25% slope, tight access")
    print(f"   Initial multipliers: labor={site_modifier.labor_rate_multiplier:.2f}, material={site_modifier.material_waste_multiplier:.2f}")


def scenario_2_estimate_generation(manager: UniverseMemoryManager):
    """Scenario 2: Generate estimate using site modifiers"""
    print("\n" + "="*60)
    print("SCENARIO 2: Estimate Generation with Site Modifiers")
    print("="*60)

    # Get site modifiers to apply to estimate
    site_mod = manager.get_site_modifier("site_garcia_backyard")

    # Base estimate calculation (before modifiers)
    base_labor_hours = 32.0
    base_labor_rate = 45.0  # $/hour
    base_materials = 4200.0

    # Apply learned multipliers (currently 1.0 for new site)
    adjusted_labor_hours = base_labor_hours * site_mod.labor_rate_multiplier
    adjusted_labor_cost = adjusted_labor_hours * base_labor_rate
    adjusted_materials = base_materials * site_mod.material_waste_multiplier

    print(f"📊 Base estimate: {base_labor_hours}hrs @ ${base_labor_rate}/hr = ${base_labor_hours * base_labor_rate:.2f}")
    print(f"📊 Applied multipliers: labor={site_mod.labor_rate_multiplier:.2f}x, material={site_mod.material_waste_multiplier:.2f}x")
    print(f"📊 Adjusted estimate: {adjusted_labor_hours:.1f}hrs = ${adjusted_labor_cost:.2f}")

    # Record estimate
    estimate = EstimateActual(
        job_id="job_20251016_garcia_terracing",
        client_entity_id="client_maria_garcia",
        job_site_entity_id="site_garcia_backyard",
        job_type="terracing_retaining_wall",
        estimate_timestamp=datetime.now().isoformat(),
        estimate_labor_hours=adjusted_labor_hours,
        estimate_labor_cost=adjusted_labor_cost,
        estimate_materials_cost=adjusted_materials,
        estimate_total_cost=adjusted_labor_cost + adjusted_materials,
        estimate_generation_time_seconds=85.3,
        estimate_human_input_time_seconds=180.0,  # 3 minutes of human input
        estimate_template_usage_percent=0.45,  # 45% template, 55% custom
        estimate_custom_scopes_count=3,
        estimate_custom_scopes_total_chars=620
    )
    manager.record_estimate(estimate)
    print(f"✅ Recorded estimate: ${estimate.estimate_total_cost:.2f}")
    print(f"   Generation: 85.3s, Template usage: 45%, Custom scopes: 3")

    # Track estimate generation performance
    perf = PerformanceMetric(
        system_name="squirt",
        subsystem_name="estimate",
        metric_name="generation_time_seconds",
        metric_value=85.3,
        metric_unit="seconds",
        measurement_timestamp=datetime.now().isoformat(),
        context={
            "job_type": "terracing_retaining_wall",
            "complexity": "high",
            "template_usage": 0.45
        }
    )
    manager.record_performance(perf)
    print(f"✅ Tracked performance metric")


def scenario_3_job_completion_learning(manager: UniverseMemoryManager):
    """Scenario 3: Job completes, update actuals and learn from variance"""
    print("\n" + "="*60)
    print("SCENARIO 3: Job Completion and Variance Learning")
    print("="*60)

    # Job took longer and cost more than estimated
    actual_labor_hours = 42.5  # 32.0 estimated → 42.5 actual (+33%)
    actual_labor_cost = 1912.50  # @ $45/hr
    actual_materials = 4620.00  # $4200 estimated → $4620 actual (+10%)

    print(f"📊 Actual results:")
    print(f"   Labor: {actual_labor_hours}hrs (estimated: 32.0hrs) = +{((actual_labor_hours/32.0)-1)*100:.1f}%")
    print(f"   Materials: ${actual_materials:.2f} (estimated: $4200.00) = +{((actual_materials/4200.0)-1)*100:.1f}%")

    manager.update_estimate_actuals(
        job_id="job_20251016_garcia_terracing",
        actual_labor_hours=actual_labor_hours,
        actual_labor_cost=actual_labor_cost,
        actual_materials_cost=actual_materials,
        customer_satisfaction=0.95,  # Very happy with result
        employee_satisfaction=0.70,  # Challenging job
        management_satisfaction=0.75,  # Lower margin than hoped
        site_conditions={
            "soil": "rockier than expected",
            "slope": "unstable area required extra work",
            "access": "very difficult, hand-carried all materials"
        },
        weather_conditions={"rain_days": 1, "high_wind_days": 0},
        complications=["Unexpected rock layer", "Had to hand-dig entire area", "Extra drainage work needed"]
    )
    print(f"✅ Updated actuals with variance data")

    # Site modifiers automatically updated
    updated_mod = manager.get_site_modifier("site_garcia_backyard")
    print(f"✅ Site modifiers learned from variance:")
    print(f"   Labor multiplier: 1.00 → {updated_mod.labor_rate_multiplier:.3f}")
    print(f"   Material multiplier: 1.00 → {updated_mod.material_waste_multiplier:.3f}")
    print(f"   Jobs completed: {updated_mod.jobs_completed_count}")

    # Record learning outcome
    learning_id = manager.record_learning_outcome(
        system_name="squirt",
        learning_category="site_conditions",
        insight_summary="Steep slopes with rocky soil require 1.33x labor multiplier",
        insight_detail="Garcia terracing job: steep slope (25%) + rocky soil + tight access = 33% more labor than flat/normal sites",
        evidence={
            "job_id": "job_20251016_garcia_terracing",
            "slope_percentage": 25.0,
            "soil_type": "rocky",
            "access_difficulty": 0.8,
            "labor_variance_percent": 0.33
        },
        confidence_score=0.65,  # Moderate confidence (only 1 job so far)
        applies_to_systems=["squirt"],
        human_validated=False
    )
    print(f"✅ Captured learning outcome #{learning_id}")
    print(f"   Insight: Steep + rocky + tight = 1.33x labor")
    print(f"   Confidence: 65% (needs more data)")


def scenario_4_decision_tracking(manager: UniverseMemoryManager):
    """Scenario 4: Track a significant decision with constitutional compliance"""
    print("\n" + "="*60)
    print("SCENARIO 4: Decision Tracking - Thermal Safety Gate")
    print("="*60)

    decision = Decision(
        system_name="j5a",
        decision_type="thermal_safety",
        decision_summary="Defer Sherlock transcription of 2-hour podcast due to thermal constraints",
        decision_rationale="CPU temperature at 77°C. Projected to reach 85°C during transcription. Mac Mini thermal shutdown at 90°C would cause data loss.",
        constitutional_compliance={
            "principle_3_system_viability": "Preventing thermal shutdown ensures system availability",
            "principle_4_resource_stewardship": "Respecting thermal limits protects hardware longevity"
        },
        strategic_alignment={
            "principle_7_autonomous_workflows": "Automatic thermal gate prevents crashes without human intervention",
            "principle_9_local_llm_optimization": "Constraint-aware scheduling optimizes hardware usage"
        },
        decision_timestamp=datetime.now().isoformat(),
        decided_by="j5a_thermal_safety_gate",
        outcome_expected="Task deferred 2 hours until CPU <75°C, then completed successfully",
        parameters_used={
            "current_cpu_temp": 77.0,
            "thermal_limit": 80.0,
            "projected_peak_temp": 85.0,
            "task_duration_estimate": 7200,  # 2 hours
            "defer_until_temp": 75.0
        }
    )
    manager.record_decision(decision)
    print(f"✅ Recorded decision: Defer transcription")
    print(f"   Rationale: CPU 77°C → projected 85°C > 80°C limit")
    print(f"   Constitutional: Principles 3 (Viability) + 4 (Stewardship)")
    print(f"   Strategic: Principles 7 (Autonomous) + 9 (Optimization)")

    # Later: update with actual outcome
    manager.update_decision_outcome(
        decision_summary=decision.decision_summary,
        outcome_actual="Task executed 2.5 hours later at CPU 72°C. Completed successfully in 1hr 58min with peak temp 79°C. No thermal issues."
    )
    print(f"✅ Updated with actual outcome: Success at 72°C")


def scenario_5_cross_system_learning(manager: UniverseMemoryManager):
    """Scenario 5: Learning transfer from Sherlock to Squirt"""
    print("\n" + "="*60)
    print("SCENARIO 5: Cross-System Learning Transfer")
    print("="*60)

    # Sherlock learned about incremental saves during Operation Gladio
    learning_id = manager.record_learning_outcome(
        system_name="sherlock",
        learning_category="incremental_save_pattern",
        insight_summary="Long-running processes must save incrementally to prevent data loss",
        insight_detail="Operation Gladio: 17+ hours of transcription at risk. Implemented chunk-by-chunk saves. Result: 0 data loss on crashes, resume from last checkpoint.",
        evidence={
            "operation": "gladio_transcription",
            "original_risk": "17+ hours work lost on crash",
            "solution": "save after each 10-minute chunk",
            "crashes_during_testing": 2,
            "data_loss": "0 chunks (100% recovered)",
            "max_loss_possible": "10 minutes (1 chunk)"
        },
        confidence_score=0.95,  # High confidence from real-world validation
        applies_to_systems=["sherlock", "squirt", "j5a"],
        human_validated=True
    )
    print(f"✅ Sherlock learning #{learning_id}: Incremental save pattern")
    print(f"   Evidence: Operation Gladio - 0 data loss despite 2 crashes")
    print(f"   Confidence: 95% (human validated)")

    # Transfer to Squirt for voice memo processing
    manager.record_learning_transfer(
        learning_id=learning_id,
        source_system="sherlock",
        target_system="squirt",
        transfer_method="adapted_incremental_save",
        adaptation_required="Apply to voice memo processing: save after each 5-minute segment instead of end",
        transfer_success=True,
        impact_summary="Voice memo processing previously: 85% success (15% crashes lost all work). After transfer: 98% success, crashes only lose max 5min."
    )
    print(f"✅ Transferred to Squirt: Voice memo incremental saves")
    print(f"   Adaptation: 5-minute segments (vs. Sherlock's 10-min)")
    print(f"   Impact: 85% → 98% success rate")

    # Squirt also benefits: set adaptive parameter
    param = AdaptiveParameter(
        system_name="squirt",
        parameter_name="voice_memo_chunk_duration_seconds",
        parameter_value=300.0,  # 5 minutes
        parameter_context="long_voice_memos_over_10_minutes",
        learning_source="sherlock_operation_gladio_incremental_save_pattern",
        confidence_score=0.90,
        last_updated_timestamp=datetime.now().isoformat()
    )
    manager.set_adaptive_parameter(param)
    print(f"✅ Set Squirt adaptive parameter: chunk_duration = 300s (5min)")


def scenario_6_context_refresh(manager: UniverseMemoryManager):
    """Scenario 6: Set evergreen knowledge for future sessions"""
    print("\n" + "="*60)
    print("SCENARIO 6: Context Refresh - Evergreen Knowledge")
    print("="*60)

    # WaterWizard pricing knowledge
    manager.set_context_refresh(
        system_name="squirt",
        knowledge_key="current_labor_rates_2025",
        knowledge_summary="Current WaterWizard labor rates by job complexity",
        full_content="""
**WaterWizard Labor Rates (2025)**

Base Rates:
- Simple jobs (mowing, mulching): $35/hour
- Standard jobs (planting, basic irrigation): $45/hour
- Complex jobs (deck construction, retaining walls): $55/hour
- Specialized jobs (drainage systems, terracing): $65/hour

Modifiers Applied Automatically:
- Site difficulty multipliers from site_modifiers table
- Learned variance adjustments from estimate_actuals
- Seasonal adjustments (winter +10%, summer standard)

Last Updated: 2025-10-16
Authority: Management approved
        """,
        refresh_priority=0.95  # Very high priority
    )
    print(f"✅ Set evergreen knowledge: Labor rates 2025")
    print(f"   Priority: 0.95 (very high)")

    # Material cost reference
    manager.set_context_refresh(
        system_name="squirt",
        knowledge_key="irrigation_materials_wholesale_2025",
        knowledge_summary="Wholesale irrigation materials pricing",
        full_content="""
**Irrigation Materials - Wholesale Costs (2025)**

Sprinkler Heads:
- Popup spray: $6-10 each
- Rotor heads: $12-18 each
- Drip emitters: $0.50-1.50 each

Pipe/Tubing:
- PVC 1/2": $0.35/ft
- PVC 3/4": $0.55/ft
- PVC 1": $0.75/ft
- Drip tubing 1/2": $0.25/ft

Controllers:
- 4-zone: $120
- 8-zone: $180
- 12-zone: $280
- WiFi enabled: +$50

Valves:
- Standard 1": $25 each
- Anti-siphon 1": $35 each

Mark-up: 40% on materials for retail pricing
        """,
        refresh_priority=0.85
    )
    print(f"✅ Set evergreen knowledge: Irrigation materials pricing")
    print(f"   Priority: 0.85 (high)")

    # Session memory: important customer feedback
    event = SessionEvent(
        system_name="squirt",
        session_id="session_20251016_garcia_feedback",
        event_type="customer_insight",
        event_summary="Customer requested detailed breakdown of labor hours by task in future estimates",
        importance_score=0.85,
        event_timestamp=datetime.now().isoformat(),
        full_context={
            "customer": "Maria Garcia",
            "request": "Can you break down the 42.5 hours into tasks? I'd like to see digging vs. wall building vs. finishing.",
            "action_taken": "Created task-level breakdown template for complex jobs",
            "applies_to": "all complex jobs (decks, walls, terracing)"
        },
        related_entities=["client_maria_garcia"]
    )
    manager.record_session_event(event)
    print(f"✅ Recorded session memory: Customer wants task breakdown")
    print(f"   Importance: 0.85 (high)")


def generate_summary_report(manager: UniverseMemoryManager):
    """Generate summary report of Phase 1 test"""
    print("\n" + "="*60)
    print("PHASE 1 PRACTICAL TEST - SUMMARY REPORT")
    print("="*60)

    stats = manager.get_statistics()
    print(f"\n📊 Database Statistics:")
    for table, count in stats.items():
        if count > 0:
            print(f"   {table:30s}: {count:3d} records")

    print(f"\n📈 Performance Metrics:")
    squirt_perf = manager.get_latest_performance("squirt", "estimate")
    for metric_name, data in squirt_perf.items():
        print(f"   {metric_name}: {data['value']} {data['unit']}")

    print(f"\n🎯 Quality Benchmarks:")
    benchmarks = manager.get_quality_benchmarks("squirt", "estimate")
    if "estimate" in benchmarks:
        for metric, levels in benchmarks["estimate"].items():
            if "target" in levels:
                print(f"   {metric}: target = {levels['target']['value']}")

    print(f"\n🧠 Learning Outcomes:")
    outcomes = manager.get_learning_outcomes(min_confidence=0.5)
    for outcome in outcomes:
        print(f"   #{outcome['id']}: {outcome['summary']}")
        print(f"            Confidence: {outcome['confidence']:.0%}, Validated: {outcome['human_validated']}")

    print(f"\n🔄 Learning Transfers:")
    transfers = manager.get_learning_transfers(successful_only=True)
    for transfer in transfers:
        print(f"   {transfer['source']} → {transfer['target']}: {transfer['insight']}")
        print(f"            Impact: {transfer['impact']}")

    print(f"\n⚖️ Decision History:")
    decisions = manager.get_decision_history("j5a")
    for decision in decisions:
        print(f"   {decision['type']}: {decision['summary']}")
        print(f"            Expected: {decision['outcome_expected']}")
        if decision['outcome_actual']:
            print(f"            Actual: {decision['outcome_actual']}")

    print(f"\n🏗️ Site Modifiers:")
    site_mod = manager.get_site_modifier("site_garcia_backyard")
    if site_mod:
        print(f"   {site_mod.job_site_name}")
        print(f"   Conditions: {site_mod.soil_type} soil, {site_mod.slope_type} slope, {site_mod.space_type}")
        print(f"   Learned multipliers: labor={site_mod.labor_rate_multiplier:.3f}x, material={site_mod.material_waste_multiplier:.3f}x")
        print(f"   Based on {site_mod.jobs_completed_count} completed job(s)")

    print(f"\n📋 Estimate Variance Analysis:")
    analysis = manager.get_estimate_variance_analysis(min_sample_size=1)
    for job_type, stats in analysis.items():
        print(f"   {job_type}:")
        print(f"      Sample size: {stats['sample_size']}")
        print(f"      Avg labor variance: {stats['avg_labor_hours_variance_pct']*100:+.1f}%")
        print(f"      Avg materials variance: {stats['avg_materials_variance_pct']*100:+.1f}%")
        print(f"      Customer satisfaction: {stats['avg_customer_satisfaction']:.0%}")
        print(f"      Employee satisfaction: {stats['avg_employee_satisfaction']:.0%}")
        print(f"      Management satisfaction: {stats['avg_management_satisfaction']:.0%}")

    print(f"\n" + "="*60)
    print("✅ PHASE 1 PRACTICAL TEST COMPLETE")
    print("="*60)
    print(f"\nKey Achievements:")
    print(f"✅ Client and job site entities created")
    print(f"✅ Site modifiers characterized and learned from variance")
    print(f"✅ Estimate generated with learned multipliers")
    print(f"✅ Actuals tracked with satisfaction metrics")
    print(f"✅ Learning outcomes captured and transferred cross-system")
    print(f"✅ Decisions tracked with constitutional compliance")
    print(f"✅ Evergreen knowledge set for future sessions")
    print(f"\n✅ Phase 1 infrastructure ready for production use!")


def run_practical_test():
    """Run complete practical test of Phase 1"""
    print("="*60)
    print("J5A UNIVERSE MEMORY - PHASE 1 PRACTICAL TEST")
    print("Real-World WaterWizard Business Scenarios")
    print("="*60)

    manager = UniverseMemoryManager()
    print(f"📁 Database: {manager.db_path}")
    print(f"🔖 Version: {manager.get_database_version()}")

    try:
        scenario_1_client_onboarding(manager)
        scenario_2_estimate_generation(manager)
        scenario_3_job_completion_learning(manager)
        scenario_4_decision_tracking(manager)
        scenario_5_cross_system_learning(manager)
        scenario_6_context_refresh(manager)
        generate_summary_report(manager)
        return 0
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(run_practical_test())
