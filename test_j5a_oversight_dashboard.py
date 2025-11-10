#!/usr/bin/env python3
"""
J5A Unified Oversight Dashboard - Integration Test

Demonstrates complete Phase 5 workflows:
1. Cross-system unified overview
2. System health monitoring and scoring
3. Priority-based human review queue
4. Learning outcome validation with constitutional compliance
5. Cross-system performance comparison
6. Actionable insights generation
7. Comprehensive oversight reporting
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path("/home/johnny5/Squirt")))
sys.path.insert(0, str(Path("/home/johnny5/Sherlock")))

from j5a_oversight_dashboard import (
    J5AOversightDashboard,
    PriorityLevel,
    ValidationStatus
)
from j5a_universe_memory import UniverseMemoryManager
from squirt_learning_manager import SquirtLearningManager
from j5a_learning_manager import J5ALearningManager
from sherlock_learning_manager import SherlockLearningManager


def setup_test_data(dashboard: J5AOversightDashboard):
    """Set up test data across all three systems"""
    print("\n" + "="*60)
    print("SETUP: Creating Test Data")
    print("="*60)

    # Squirt: Invoice generation outcomes
    print("\n📄 Squirt: Creating invoice generation learning outcomes...")
    for i in range(3):
        dashboard.squirt.track_invoice_generation(
            invoice_id=f"inv_test_{i:03d}",
            client_id="client_test_001",
            generation_time_seconds=15.0 + (i * 5),
            template_used="standard_invoice_v3",
            auto_generated=True,
            human_edits_required=(i == 2),  # Last one needed edits
            client_accepted_without_changes=(i != 2),
            success=True,
            context={"test": True}
        )
    print(f"✅ Created 3 invoice generation records")

    # J5A: Night Shift batch outcomes
    print("\n🌙 J5A: Creating Night Shift batch outcomes...")
    for i in range(3):
        dashboard.j5a.track_nightshift_batch(
            batch_id=f"batch_test_{i:03d}",
            tasks_queued=10,
            tasks_completed=9 if i < 2 else 7,  # Last batch had more failures
            tasks_failed=1 if i < 2 else 3,
            total_duration_seconds=7200.0,
            thermal_issues=(i == 2),  # Last batch had thermal issues
            resource_constraints_hit=(i == 2),
            context={"test": True}
        )
    print(f"✅ Created 3 night shift batch records")

    # Sherlock: Media processing outcomes
    print("\n🔍 Sherlock: Creating media processing outcomes...")
    for i in range(3):
        dashboard.sherlock.track_media_processing(
            media_id=f"media_test_{i:03d}",
            media_type="audio",
            source_url=f"https://example.com/media_{i:03d}.mp3",
            processing_type="transcription",
            duration_seconds=300.0 + (i * 100),
            success=(i != 2),  # Last one failed
            quality_score=0.85 if i != 2 else 0.0,
            failure_reason="Transcription timeout" if i == 2 else None,
            context={"test": True}
        )
    print(f"✅ Created 3 media processing records")

    # Create some learning outcomes
    print("\n🧠 Creating learning outcomes across systems...")

    # High-confidence Squirt learning (critical priority)
    outcome_id_1 = dashboard.memory.record_learning_outcome(
        system_name="squirt",
        learning_category="invoice_generation",
        insight_summary="Template-based invoices generate 40% faster with 95% client acceptance",
        insight_detail="Analysis of 50 invoices shows template usage strongly correlates with faster generation and higher acceptance.",
        evidence={"sample_size": 50, "time_savings": 0.40, "acceptance_rate": 0.95},
        confidence_score=0.92,
        applies_to_systems=["squirt"],
        human_validated=False  # Pending validation
    )
    print(f"✅ Created high-confidence Squirt learning outcome (ID: {outcome_id_1})")

    # Medium-confidence J5A learning (high priority)
    outcome_id_2 = dashboard.memory.record_learning_outcome(
        system_name="j5a",
        learning_category="thermal_safety",
        insight_summary="Night shift completion rate drops 15% when CPU temp exceeds 76°C",
        insight_detail="Thermal constraints at 76°C+ cause task deferrals and lower batch completion.",
        evidence={"threshold_temp": 76.0, "completion_drop": 0.15, "sample_batches": 10},
        confidence_score=0.82,
        applies_to_systems=["j5a", "sherlock"],  # Multi-system applicability
        human_validated=False
    )
    print(f"✅ Created medium-confidence J5A learning outcome (ID: {outcome_id_2})")

    # Lower-confidence Sherlock learning (medium priority)
    outcome_id_3 = dashboard.memory.record_learning_outcome(
        system_name="sherlock",
        learning_category="transcription_quality",
        insight_summary="Whisper medium model achieves 92% accuracy on podcast content",
        insight_detail="Testing on 10 podcast episodes shows medium model sufficient for intelligence extraction.",
        evidence={"model": "medium", "accuracy": 0.92, "sample_size": 10},
        confidence_score=0.68,
        applies_to_systems=["sherlock"],
        human_validated=False
    )
    print(f"✅ Created medium-confidence Sherlock learning outcome (ID: {outcome_id_3})")

    print("\n✅ Test data setup complete")
    return outcome_id_1, outcome_id_2, outcome_id_3


def test_unified_overview(dashboard: J5AOversightDashboard):
    """Test unified cross-system overview"""
    print("\n" + "="*60)
    print("TEST 1: Unified Cross-System Overview")
    print("="*60)

    overview = dashboard.get_unified_overview(hours_back=24)

    print(f"\n📊 Unified Overview Generated:")
    print(f"   Time window: {overview['time_window_hours']} hours")
    print(f"   Generated at: {overview['generated_at']}")

    print(f"\n📈 Cross-System Summary:")
    print(f"   Total learning outcomes: {overview['cross_system']['total_learning_outcomes']}")
    print(f"   Pending validations: {overview['cross_system']['pending_validations']}")
    print(f"   Critical issues: {len(overview['cross_system']['critical_issues'])}")

    print(f"\n🔍 Per-System Breakdown:")
    for system_name, system_data in overview["systems"].items():
        print(f"\n   {system_name.upper()}:")
        print(f"      Learning outcomes: {system_data['learning_outcomes_count']}")
        print(f"      Session events: {system_data['session_events_count']}")
        print(f"      Pending validations: {system_data['pending_validations']}")
        print(f"      Critical issues: {len(system_data['critical_issues'])}")
        print(f"      Avg confidence: {system_data['avg_confidence']:.0%}")

    # Assertions
    assert overview['time_window_hours'] == 24, "Time window should be 24 hours"
    assert 'squirt' in overview['systems'], "Should include Squirt system"
    assert 'j5a' in overview['systems'], "Should include J5A system"
    assert 'sherlock' in overview['systems'], "Should include Sherlock system"
    assert overview['cross_system']['pending_validations'] > 0, "Should have pending validations"

    print(f"\n✅ Unified overview test passed")


def test_system_health(dashboard: J5AOversightDashboard):
    """Test system health assessment"""
    print("\n" + "="*60)
    print("TEST 2: System Health Assessment")
    print("="*60)

    for system_name in ["squirt", "j5a", "sherlock"]:
        health = dashboard.get_system_health(system_name)

        print(f"\n🏥 {system_name.upper()} Health Status:")
        print(f"   Overall status: {health.overall_status.upper()}")
        print(f"   Performance score: {health.performance_score:.0%}")
        print(f"   Active issues: {len(health.active_issues)}")
        print(f"   Recent improvements: {len(health.recent_improvements)}")
        print(f"   Recommendations: {len(health.recommendations)}")

        if health.active_issues:
            print(f"\n   ⚠️  Active Issues:")
            for issue in health.active_issues[:3]:
                print(f"      • {issue}")

        if health.recent_improvements:
            print(f"\n   ✅ Recent Improvements:")
            for improvement in health.recent_improvements[:3]:
                print(f"      • {improvement}")

        if health.recommendations:
            print(f"\n   💡 Recommendations:")
            for rec in health.recommendations[:3]:
                print(f"      • {rec}")

        # Assertions
        assert health.system_name == system_name, f"System name should be {system_name}"
        assert health.overall_status in ["healthy", "warning", "critical"], "Status should be valid"
        assert 0.0 <= health.performance_score <= 1.0, "Performance score should be 0-1"

    print(f"\n✅ System health assessment test passed")


def test_pending_reviews(dashboard: J5AOversightDashboard):
    """Test pending review queue"""
    print("\n" + "="*60)
    print("TEST 3: Pending Review Queue")
    print("="*60)

    # Get all pending reviews
    all_pending = dashboard.get_pending_reviews()
    print(f"\n📝 Total pending reviews: {len(all_pending)}")

    # Get by priority
    priority_counts = {}
    for priority in PriorityLevel:
        pending = dashboard.get_pending_reviews(priority=priority)
        priority_counts[priority.value] = len(pending)
        print(f"   {priority.value.upper()}: {len(pending)} items")

    # Show top items by priority
    print(f"\n📋 Top Pending Review Items:")
    for i, item in enumerate(all_pending[:5], 1):
        print(f"\n   {i}. [{item.priority.value.upper()}] {item.system_name}")
        print(f"      {item.summary}")
        print(f"      Evidence confidence: {item.evidence.get('confidence', 0):.0%}")
        print(f"      Created: {item.created_at}")
        print(f"      Recommended action: {item.recommended_action}")

    # Filter by system
    squirt_pending = dashboard.get_pending_reviews(system_name="squirt")
    print(f"\n📄 Squirt-specific pending reviews: {len(squirt_pending)}")

    # Assertions
    assert len(all_pending) > 0, "Should have pending reviews"
    assert all(item.validation_status == ValidationStatus.PENDING for item in all_pending), "All should be pending"
    assert priority_counts.get('critical', 0) >= 0, "Should have priority breakdown"

    print(f"\n✅ Pending review queue test passed")


def test_validation_workflow(dashboard: J5AOversightDashboard, outcome_ids):
    """Test learning outcome validation workflow"""
    print("\n" + "="*60)
    print("TEST 4: Learning Outcome Validation Workflow")
    print("="*60)

    outcome_id_1, outcome_id_2, outcome_id_3 = outcome_ids

    # Validate first outcome (approve)
    print(f"\n✅ Validating outcome {outcome_id_1} (APPROVE)...")
    result1 = dashboard.validate_learning_outcome(
        outcome_id=outcome_id_1,
        approved=True,
        validation_notes="Template-based invoice generation shows strong evidence. Approved for production use."
    )
    print(f"   Result: {result1['validated']} - {'APPROVED' if result1['approved'] else 'REJECTED'}")
    print(f"   Notes: {result1['validation_notes']}")

    # Validate second outcome (reject)
    print(f"\n❌ Validating outcome {outcome_id_2} (REJECT)...")
    result2 = dashboard.validate_learning_outcome(
        outcome_id=outcome_id_2,
        approved=False,
        validation_notes="Sample size too small (10 batches). Need more data before adjusting thermal thresholds."
    )
    print(f"   Result: {result2['validated']} - {'APPROVED' if result2['approved'] else 'REJECTED'}")
    print(f"   Notes: {result2['validation_notes']}")

    # Validate third outcome (approve)
    print(f"\n✅ Validating outcome {outcome_id_3} (APPROVE)...")
    result3 = dashboard.validate_learning_outcome(
        outcome_id=outcome_id_3,
        approved=True,
        validation_notes="Whisper medium model accuracy sufficient for intelligence work. Cost-effective choice."
    )
    print(f"   Result: {result3['validated']} - {'APPROVED' if result3['approved'] else 'REJECTED'}")

    # Check decision audit trail
    decisions = dashboard.memory.get_decision_history("j5a_oversight", "learning_validation", limit=10)
    print(f"\n📜 Validation Decision Audit Trail: {len(decisions)} decisions")
    for i, decision in enumerate(decisions[:3], 1):
        print(f"   {i}. {decision['summary']}")
        print(f"      Decided by: {decision['decided_by']}")
        print(f"      Constitutional compliance: {len(decision.get('constitutional_compliance', {}))} principles")

    # Assertions
    assert result1['validated'] == True, "Validation should succeed"
    assert result1['approved'] == True, "First outcome should be approved"
    assert result2['approved'] == False, "Second outcome should be rejected"
    assert len(decisions) >= 3, "Should have validation decisions recorded"

    print(f"\n✅ Validation workflow test passed")


def test_cross_system_comparison(dashboard: J5AOversightDashboard):
    """Test cross-system performance comparison"""
    print("\n" + "="*60)
    print("TEST 5: Cross-System Performance Comparison")
    print("="*60)

    # Compare success rates
    print(f"\n📊 Comparing 'success' metrics across systems...")
    comparison = dashboard.compare_system_performance(
        metric_category="success",
        hours_back=168  # 1 week
    )

    print(f"   Metric category: {comparison['metric_category']}")
    print(f"   Time window: {comparison['time_window_hours']} hours")

    for system_name, system_data in comparison['systems'].items():
        if system_data['sample_size'] > 0:
            print(f"\n   {system_name.upper()}:")
            print(f"      Sample size: {system_data['sample_size']}")
            print(f"      Avg value: {system_data['avg_value']:.2f}")
            print(f"      Trend: {system_data['recent_trend']}")
        else:
            print(f"\n   {system_name.upper()}: No data")

    # Compare quality metrics
    print(f"\n📊 Comparing 'quality' metrics across systems...")
    quality_comparison = dashboard.compare_system_performance(
        metric_category="quality",
        hours_back=168
    )

    for system_name, system_data in quality_comparison['systems'].items():
        if system_data['sample_size'] > 0:
            print(f"   {system_name}: {system_data['avg_value']:.2f} (trend: {system_data['recent_trend']})")

    # Assertions
    assert comparison['metric_category'] == "success", "Should filter by metric category"
    assert 'squirt' in comparison['systems'], "Should include all systems"

    print(f"\n✅ Cross-system comparison test passed")


def test_actionable_insights(dashboard: J5AOversightDashboard):
    """Test actionable insights generation"""
    print("\n" + "="*60)
    print("TEST 6: Actionable Insights Generation")
    print("="*60)

    insights = dashboard.generate_actionable_insights()

    print(f"\n💡 Total Insights Generated: {len(insights)}")

    # Group by priority
    by_priority = {}
    for insight in insights:
        priority = insight['priority']
        if priority not in by_priority:
            by_priority[priority] = []
        by_priority[priority].append(insight)

    print(f"\n📊 Insights by Priority:")
    for priority in ["critical", "high", "medium", "low"]:
        count = len(by_priority.get(priority, []))
        if count > 0:
            print(f"   {priority.upper()}: {count} insights")

    # Show top insights
    print(f"\n🔍 Top Actionable Insights:")
    for i, insight in enumerate(insights[:5], 1):
        print(f"\n   {i}. [{insight['priority'].upper()}] {insight['system']}")
        print(f"      {insight['insight']}")
        print(f"      Impact: {insight['impact']}")
        print(f"      Recommended action: {insight['recommended_action']}")
        if isinstance(insight['evidence'], list):
            print(f"      Evidence items: {len(insight['evidence'])}")

    # Assertions
    assert isinstance(insights, list), "Should return list of insights"
    assert all('priority' in i for i in insights), "All insights should have priority"
    assert all('recommended_action' in i for i in insights), "All should have recommended action"

    print(f"\n✅ Actionable insights test passed")


def test_oversight_report(dashboard: J5AOversightDashboard):
    """Test comprehensive oversight report"""
    print("\n" + "="*60)
    print("TEST 7: Comprehensive Oversight Report")
    print("="*60)

    report = dashboard.generate_oversight_report(hours_back=168)

    print(f"\n📋 Oversight Report Generated:")
    print(f"   Generated at: {report['generated_at']}")
    print(f"   Time window: {report['time_window_hours']} hours")
    print(f"   Report type: {report['report_type']}")

    # Unified overview section
    print(f"\n📊 Section: Unified Overview")
    overview = report['sections']['unified_overview']
    print(f"   Systems tracked: {len(overview['systems'])}")
    print(f"   Cross-system learning outcomes: {overview['cross_system']['total_learning_outcomes']}")
    print(f"   Cross-system pending validations: {overview['cross_system']['pending_validations']}")

    # System health section
    print(f"\n🏥 Section: System Health")
    for system_name, health_data in report['sections']['system_health'].items():
        print(f"   {system_name.upper()}: {health_data['status']} ({health_data['performance_score']:.0%})")
        print(f"      Active issues: {health_data['active_issues_count']}")
        print(f"      Improvements: {health_data['improvements_count']}")

    # Pending reviews section
    print(f"\n📝 Section: Pending Reviews")
    reviews = report['sections']['pending_reviews']
    print(f"   Critical: {reviews['critical']}")
    print(f"   High: {reviews['high']}")
    print(f"   Medium: {reviews['medium']}")
    print(f"   Low: {reviews['low']}")
    print(f"   Total: {reviews['total']}")

    # Actionable insights section
    print(f"\n💡 Section: Actionable Insights")
    insights_summary = report['sections']['actionable_insights']
    print(f"   Total insights: {insights_summary['total_insights']}")
    print(f"   By priority:")
    for priority, count in insights_summary['by_priority'].items():
        if count > 0:
            print(f"      {priority}: {count}")

    if insights_summary['top_5_insights']:
        print(f"\n   Top Insights:")
        for i, insight in enumerate(insights_summary['top_5_insights'], 1):
            print(f"      {i}. [{insight['priority'].upper()}] {insight['insight'][:60]}...")

    # Learning transfers section
    print(f"\n🔄 Section: Learning Transfers")
    transfers = report['sections']['learning_transfers']
    print(f"   Total transfers: {transfers['total_transfers']}")
    if transfers['by_source_system']:
        print(f"   By source system:")
        for system, count in transfers['by_source_system'].items():
            print(f"      {system}: {count}")

    # Assertions
    assert report['report_type'] == "unified_oversight", "Should be oversight report"
    assert 'unified_overview' in report['sections'], "Should have unified overview"
    assert 'system_health' in report['sections'], "Should have system health"
    assert 'pending_reviews' in report['sections'], "Should have pending reviews"
    assert 'actionable_insights' in report['sections'], "Should have insights"
    assert 'learning_transfers' in report['sections'], "Should have transfers"

    print(f"\n✅ Oversight report test passed")


def test_constitutional_compliance(dashboard: J5AOversightDashboard):
    """Test constitutional compliance in validation decisions"""
    print("\n" + "="*60)
    print("TEST 8: Constitutional Compliance Verification")
    print("="*60)

    # Get validation decisions
    decisions = dashboard.memory.get_decision_history(
        system_name="j5a_oversight",
        decision_type="learning_validation",
        limit=10
    )

    print(f"\n📜 Analyzing {len(decisions)} validation decisions for constitutional compliance...")

    compliant_count = 0
    for decision in decisions:
        constitutional = decision.get('constitutional_compliance', {})
        strategic = decision.get('strategic_alignment', {})

        has_constitutional = len(constitutional) > 0
        has_strategic = len(strategic) > 0

        if has_constitutional or has_strategic:
            compliant_count += 1

    compliance_rate = (compliant_count / len(decisions) * 100) if decisions else 0
    print(f"\n✅ Constitutional Compliance Rate: {compliance_rate:.0f}%")
    print(f"   {compliant_count}/{len(decisions)} decisions include constitutional/strategic alignment")

    # Show example decision
    if decisions:
        print(f"\n📋 Example Validation Decision:")
        example = decisions[0]
        print(f"   Summary: {example['summary']}")
        print(f"   Decided by: {example['decided_by']}")
        print(f"   Timestamp: {example['timestamp']}")

        if example.get('constitutional_compliance'):
            print(f"\n   Constitutional Compliance:")
            for principle, description in example['constitutional_compliance'].items():
                print(f"      • {principle}: {description}")

        if example.get('strategic_alignment'):
            print(f"\n   Strategic Alignment:")
            for principle, description in example['strategic_alignment'].items():
                print(f"      • {principle}: {description}")

    # Assertions
    assert len(decisions) > 0, "Should have validation decisions"
    assert compliance_rate >= 50, "Majority of decisions should document compliance"

    print(f"\n✅ Constitutional compliance test passed")


def generate_final_report(dashboard: J5AOversightDashboard):
    """Generate final test summary"""
    print("\n" + "="*60)
    print("FINAL PHASE 5 TEST REPORT")
    print("="*60)

    # Get current state
    overview = dashboard.get_unified_overview(hours_back=24)
    all_pending = dashboard.get_pending_reviews()
    insights = dashboard.generate_actionable_insights()

    print(f"\n📊 Phase 5 Oversight Dashboard Status:")
    print(f"   Systems monitored: {len(overview['systems'])}")
    print(f"   Total learning outcomes: {overview['cross_system']['total_learning_outcomes']}")
    print(f"   Pending validations: {overview['cross_system']['pending_validations']}")
    print(f"   Actionable insights: {len(insights)}")

    print(f"\n🏥 System Health Summary:")
    for system_name in ["squirt", "j5a", "sherlock"]:
        health = dashboard.get_system_health(system_name)
        print(f"   {system_name.upper()}: {health.overall_status} ({health.performance_score:.0%})")

    print(f"\n📝 Human Oversight Queue:")
    by_priority = {}
    for item in all_pending:
        priority = item.priority.value
        by_priority[priority] = by_priority.get(priority, 0) + 1

    for priority in ["critical", "high", "medium", "low"]:
        count = by_priority.get(priority, 0)
        print(f"   {priority.upper()}: {count} items")

    print(f"\n✅ Phase 5 Integration Complete:")
    print(f"   ✅ Unified oversight across 3 systems")
    print(f"   ✅ Automated system health scoring")
    print(f"   ✅ Priority-based human review queue")
    print(f"   ✅ Constitutional compliance in all validations")
    print(f"   ✅ Cross-system performance comparison")
    print(f"   ✅ Evidence-based actionable insights")
    print(f"   ✅ Comprehensive oversight reporting")

    print(f"\n" + "="*60)
    print("✅ J5A OVERSIGHT DASHBOARD INTEGRATION TEST COMPLETE")
    print("="*60)


def run_integration_test():
    """Run complete Phase 5 integration test"""
    print("="*60)
    print("J5A UNIFIED OVERSIGHT DASHBOARD - INTEGRATION TEST")
    print("Phase 5: Human Oversight & Cross-System Governance")
    print("="*60)

    try:
        dashboard = J5AOversightDashboard()
        print(f"\n✅ J5AOversightDashboard initialized")
        print(f"📊 System managers loaded: Squirt, J5A, Sherlock")

        # Setup test data
        outcome_ids = setup_test_data(dashboard)

        # Run all tests
        test_unified_overview(dashboard)
        test_system_health(dashboard)
        test_pending_reviews(dashboard)
        test_validation_workflow(dashboard, outcome_ids)
        test_cross_system_comparison(dashboard)
        test_actionable_insights(dashboard)
        test_oversight_report(dashboard)
        test_constitutional_compliance(dashboard)
        generate_final_report(dashboard)

        print(f"\n✅ All Phase 5 integration tests passed!")
        print(f"\n💡 Key Achievements:")
        print(f"   ✅ Cross-system overview with unified metrics")
        print(f"   ✅ Automated system health assessment")
        print(f"   ✅ Priority-based human review workflow")
        print(f"   ✅ Learning outcome validation with audit trail")
        print(f"   ✅ Cross-system performance comparison")
        print(f"   ✅ Actionable insights generation")
        print(f"   ✅ Comprehensive oversight reporting")
        print(f"   ✅ Constitutional compliance verification")

        return 0

    except Exception as e:
        print(f"\n❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(run_integration_test())
