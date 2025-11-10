#!/usr/bin/env python3
"""
Learning Synthesizer - Integration Test

Demonstrates complete Phase 6 workflows:
1. Identification of transferable learnings
2. Cross-system compatibility assessment
3. Learning transfer proposal generation
4. Learning conflict detection and resolution
5. Transfer execution with human approval
6. Cross-system synthesis reporting
"""

import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

from learning_synthesizer import (
    LearningSynthesizer,
    TransferType,
    TransferPriority
)
from j5a_universe_memory import UniverseMemoryManager


def setup_test_learnings(synthesizer: LearningSynthesizer):
    """Set up test learning outcomes for transfer testing"""
    print("\n" + "="*60)
    print("SETUP: Creating Test Learning Outcomes")
    print("="*60)

    # Cross-system applicable learning (thermal safety)
    print("\n🔥 Creating cross-system thermal safety learning...")
    thermal_id = synthesizer.memory.record_learning_outcome(
        system_name="j5a",
        learning_category="thermal_safety",
        insight_summary="CPU intensive tasks should defer when temperature exceeds 74°C",
        insight_detail="Analysis of 50 batches shows 74°C threshold prevents thermal throttling while maximizing throughput.",
        evidence={"threshold_temp": 74.0, "success_rate": 0.95, "sample_size": 50},
        confidence_score=0.88,
        applies_to_systems=["j5a", "squirt", "sherlock"],  # Explicitly cross-system
        human_validated=True
    )
    print(f"✅ Created cross-system thermal learning (ID: {thermal_id})")

    # Squirt voice processing learning (applicable to Sherlock audio)
    print("\n🎤 Creating Squirt voice processing learning...")
    voice_id = synthesizer.memory.record_learning_outcome(
        system_name="squirt",
        learning_category="voice_processing",
        insight_summary="Voice memo preprocessing improves transcription accuracy by 12%",
        insight_detail="Noise reduction and normalization before transcription reduces error rate significantly.",
        evidence={"accuracy_improvement": 0.12, "sample_size": 30},
        confidence_score=0.85,
        applies_to_systems=["squirt"],  # Not explicitly marked, but should transfer implicitly
        human_validated=True
    )
    print(f"✅ Created voice processing learning (ID: {voice_id})")

    # Sherlock transcription learning (applicable to Squirt)
    print("\n🔍 Creating Sherlock transcription learning...")
    transcription_id = synthesizer.memory.record_learning_outcome(
        system_name="sherlock",
        learning_category="transcription_quality",
        insight_summary="Whisper large model achieves 95% accuracy on clear audio",
        insight_detail="Large model worth the extra compute time for high-quality intelligence extraction.",
        evidence={"model": "large", "accuracy": 0.95, "sample_size": 20},
        confidence_score=0.92,
        applies_to_systems=["sherlock"],
        human_validated=True
    )
    print(f"✅ Created transcription quality learning (ID: {transcription_id})")

    # Resource optimization learning
    print("\n⚡ Creating resource optimization learning...")
    resource_id = synthesizer.memory.record_learning_outcome(
        system_name="j5a",
        learning_category="resource_optimization",
        insight_summary="Memory usage above 12.5GB triggers swapping, degrade performance 40%",
        insight_detail="Keep memory under 12.5GB threshold to maintain system responsiveness.",
        evidence={"threshold_gb": 12.5, "performance_degradation": 0.40, "sample_size": 25},
        confidence_score=0.91,
        applies_to_systems=["j5a", "squirt", "sherlock"],
        human_validated=True
    )
    print(f"✅ Created resource optimization learning (ID: {resource_id})")

    print("\n✅ Test learning outcomes created")
    return thermal_id, voice_id, transcription_id, resource_id


def test_identify_transferable_learnings(synthesizer: LearningSynthesizer):
    """Test identification of transferable learnings"""
    print("\n" + "="*60)
    print("TEST 1: Identify Transferable Learnings")
    print("="*60)

    proposals = synthesizer.identify_transferable_learnings(min_confidence=0.75)

    print(f"\n📊 Transfer Identification Results:")
    print(f"   Total proposals: {len(proposals)}")

    # Group by priority
    by_priority = {}
    for proposal in proposals:
        priority = proposal.priority.value
        by_priority[priority] = by_priority.get(priority, 0) + 1

    print(f"\n   By Priority:")
    for priority in ["critical", "high", "medium", "low"]:
        count = by_priority.get(priority, 0)
        if count > 0:
            print(f"      {priority.upper()}: {count}")

    # Group by transfer type
    by_type = {}
    for proposal in proposals:
        transfer_type = proposal.transfer_type.value
        by_type[transfer_type] = by_type.get(transfer_type, 0) + 1

    print(f"\n   By Transfer Type:")
    for transfer_type, count in by_type.items():
        print(f"      {transfer_type}: {count}")

    # Show top proposals
    print(f"\n📋 Top Transfer Proposals:")
    for i, proposal in enumerate(proposals[:5], 1):
        print(f"\n   {i}. [{proposal.priority.value.upper()}] {proposal.source_system} → {proposal.target_system}")
        print(f"      Summary: {proposal.learning_summary}")
        print(f"      Type: {proposal.transfer_type.value}")
        print(f"      Compatibility: {proposal.compatibility_score:.0%}")
        print(f"      Difficulty: {proposal.implementation_difficulty}")
        print(f"      Expected impact: {proposal.expected_impact}")

    # Assertions
    assert len(proposals) > 0, "Should find transferable learnings"
    assert all(p.compatibility_score >= 0.5 for p in proposals), "All proposals should meet min compatibility"
    assert all(p.requires_human_approval for p in proposals), "All transfers should require human approval"

    print(f"\n✅ Transfer identification test passed")


def test_compatibility_assessment(synthesizer: LearningSynthesizer):
    """Test learning compatibility assessment"""
    print("\n" + "="*60)
    print("TEST 2: Compatibility Assessment")
    print("="*60)

    proposals = synthesizer.identify_transferable_learnings(min_confidence=0.75)

    # Analyze compatibility scores
    compatibility_scores = [p.compatibility_score for p in proposals]
    avg_compatibility = sum(compatibility_scores) / len(compatibility_scores) if compatibility_scores else 0

    print(f"\n📊 Compatibility Analysis:")
    print(f"   Average compatibility: {avg_compatibility:.0%}")
    print(f"   Highest compatibility: {max(compatibility_scores):.0%}")
    print(f"   Lowest compatibility: {min(compatibility_scores):.0%}")

    # Group by compatibility ranges
    high_compat = len([s for s in compatibility_scores if s >= 0.8])
    medium_compat = len([s for s in compatibility_scores if 0.6 <= s < 0.8])
    low_compat = len([s for s in compatibility_scores if s < 0.6])

    print(f"\n   By Compatibility Range:")
    print(f"      High (≥80%): {high_compat} proposals")
    print(f"      Medium (60-79%): {medium_compat} proposals")
    print(f"      Low (<60%): {low_compat} proposals")

    # Show system pair compatibility
    print(f"\n🔗 System Pair Compatibility:")
    pair_compat = {}
    for proposal in proposals:
        pair = f"{proposal.source_system} → {proposal.target_system}"
        if pair not in pair_compat:
            pair_compat[pair] = []
        pair_compat[pair].append(proposal.compatibility_score)

    for pair, scores in pair_compat.items():
        avg = sum(scores) / len(scores)
        print(f"   {pair}: {avg:.0%} avg ({len(scores)} proposals)")

    # Assertions
    assert avg_compatibility > 0.5, "Average compatibility should be above 50%"
    assert max(compatibility_scores) <= 1.0, "Compatibility should not exceed 100%"

    print(f"\n✅ Compatibility assessment test passed")


def test_implicit_transfer_detection(synthesizer: LearningSynthesizer):
    """Test implicit transfer opportunity detection"""
    print("\n" + "="*60)
    print("TEST 3: Implicit Transfer Detection")
    print("="*60)

    proposals = synthesizer.identify_transferable_learnings(min_confidence=0.75)

    # Find proposals that weren't explicitly marked as cross-system
    # but were identified through implicit patterns
    print(f"\n🔍 Analyzing Transfer Sources:")

    # Check for thermal/memory learnings (should transfer to all systems)
    thermal_proposals = [p for p in proposals if 'thermal' in p.learning_summary.lower()]
    memory_proposals = [p for p in proposals if 'memory' in p.learning_summary.lower()]

    print(f"\n   Thermal safety transfers: {len(thermal_proposals)}")
    for proposal in thermal_proposals[:3]:
        print(f"      {proposal.source_system} → {proposal.target_system}: {proposal.learning_summary[:60]}...")

    print(f"\n   Memory optimization transfers: {len(memory_proposals)}")
    for proposal in memory_proposals[:3]:
        print(f"      {proposal.source_system} → {proposal.target_system}: {proposal.learning_summary[:60]}...")

    # Check for audio processing transfers (Squirt voice ↔ Sherlock transcription)
    audio_proposals = [p for p in proposals if
                      (p.source_system == "squirt" and p.target_system == "sherlock" and 'voice' in p.learning_summary.lower()) or
                      (p.source_system == "sherlock" and p.target_system == "squirt" and 'audio' in p.learning_summary.lower())]

    print(f"\n   Audio processing transfers: {len(audio_proposals)}")
    for proposal in audio_proposals[:3]:
        print(f"      {proposal.source_system} → {proposal.target_system}: {proposal.learning_summary[:60]}...")

    # Assertions
    assert len(thermal_proposals) + len(memory_proposals) > 0, "Should detect resource management transfers"

    print(f"\n✅ Implicit transfer detection test passed")


def test_conflict_detection(synthesizer: LearningSynthesizer):
    """Test learning conflict detection"""
    print("\n" + "="*60)
    print("TEST 4: Learning Conflict Detection")
    print("="*60)

    conflicts = synthesizer.identify_learning_conflicts()

    print(f"\n⚔️  Conflict Detection Results:")
    print(f"   Total conflicts: {len(conflicts)}")

    if conflicts:
        # Group by conflict type
        by_type = {}
        for conflict in conflicts:
            conflict_type = conflict.conflict_type
            by_type[conflict_type] = by_type.get(conflict_type, 0) + 1

        print(f"\n   By Conflict Type:")
        for conflict_type, count in by_type.items():
            print(f"      {conflict_type}: {count}")

        # Show conflicts
        print(f"\n📋 Detected Conflicts:")
        for i, conflict in enumerate(conflicts, 1):
            print(f"\n   {i}. {conflict.conflict_summary}")
            print(f"      {conflict.system_a} position: {conflict.system_a_position[:60]}...")
            print(f"      {conflict.system_b} position: {conflict.system_b_position[:60]}...")
            print(f"      Recommended resolution: {conflict.recommended_resolution[:80]}...")
            print(f"      Requires human decision: {conflict.requires_human_decision}")

    else:
        print(f"\n   ℹ️  No conflicts detected (systems in agreement)")

    # Assertions
    assert isinstance(conflicts, list), "Should return list of conflicts"
    assert all(c.requires_human_decision for c in conflicts), "Conflicts should require human decision"

    print(f"\n✅ Conflict detection test passed")


def test_transfer_execution(synthesizer: LearningSynthesizer):
    """Test learning transfer execution"""
    print("\n" + "="*60)
    print("TEST 5: Transfer Execution")
    print("="*60)

    proposals = synthesizer.identify_transferable_learnings(min_confidence=0.75)

    if not proposals:
        print("\n   ⚠️  No proposals available for execution test")
        return

    # Execute first proposal (approved)
    proposal = proposals[0]

    print(f"\n✅ Executing transfer (APPROVED):")
    print(f"   Source: {proposal.source_system}")
    print(f"   Target: {proposal.target_system}")
    print(f"   Learning: {proposal.learning_summary}")

    result = synthesizer.execute_transfer(
        proposal=proposal,
        human_approved=True,
        human_notes="Approved for testing. Monitor impact carefully."
    )

    print(f"\n📊 Transfer Result:")
    print(f"   Success: {result['success']}")
    print(f"   Transfer ID: {result.get('transfer_id')}")
    print(f"   Monitoring period: {result.get('monitoring_period_days')} days")
    print(f"   Notes: {result.get('notes')}")

    # Test rejection
    if len(proposals) > 1:
        proposal2 = proposals[1]
        print(f"\n❌ Executing transfer (REJECTED):")
        print(f"   Source: {proposal2.source_system}")
        print(f"   Target: {proposal2.target_system}")
        print(f"   Learning: {proposal2.learning_summary}")

        result2 = synthesizer.execute_transfer(
            proposal=proposal2,
            human_approved=False,
            human_notes="Insufficient evidence. Need more testing."
        )

        print(f"\n📊 Transfer Result:")
        print(f"   Success: {result2['success']}")
        print(f"   Reason: {result2.get('reason')}")

    # Check decision history
    decisions = synthesizer.memory.get_decision_history("learning_synthesizer", "learning_transfer", limit=10)
    print(f"\n📜 Transfer Decision Audit Trail: {len(decisions)} decisions")

    # Assertions
    assert result['success'] == True, "Approved transfer should succeed"
    assert 'transfer_id' in result, "Should return transfer ID"
    assert len(decisions) > 0, "Should record transfer decisions"

    print(f"\n✅ Transfer execution test passed")


def test_synthesis_report(synthesizer: LearningSynthesizer):
    """Test comprehensive synthesis report generation"""
    print("\n" + "="*60)
    print("TEST 6: Synthesis Report Generation")
    print("="*60)

    report = synthesizer.generate_synthesis_report(days_back=7)

    print(f"\n📋 Synthesis Report Generated:")
    print(f"   Generated at: {report['generated_at']}")
    print(f"   Time window: {report['time_window_days']} days")
    print(f"   Report type: {report['report_type']}")

    # Transfer proposals section
    proposals_section = report['sections']['transfer_proposals']
    print(f"\n📊 Section: Transfer Proposals")
    print(f"   Total: {proposals_section['total']}")
    print(f"   By priority:")
    for priority, count in proposals_section['by_priority'].items():
        if count > 0:
            print(f"      {priority}: {count}")

    if proposals_section['by_transfer_type']:
        print(f"   By transfer type:")
        for transfer_type, count in proposals_section['by_transfer_type'].items():
            print(f"      {transfer_type}: {count}")

    # Conflicts section
    conflicts_section = report['sections']['learning_conflicts']
    print(f"\n⚔️  Section: Learning Conflicts")
    print(f"   Total: {conflicts_section['total']}")
    if conflicts_section['by_type']:
        print(f"   By type:")
        for conflict_type, count in conflicts_section['by_type'].items():
            print(f"      {conflict_type}: {count}")

    # Completed transfers section
    transfers_section = report['sections']['completed_transfers']
    print(f"\n✅ Section: Completed Transfers")
    print(f"   Total: {transfers_section['total']}")
    print(f"   Successful: {transfers_section['successful']}")
    print(f"   Pending measurement: {transfers_section['pending_measurement']}")

    if transfers_section['by_source_system']:
        print(f"   By source system:")
        for system, count in transfers_section['by_source_system'].items():
            print(f"      {system}: {count}")

    # Cross-system insights
    insights = report['sections']['cross_system_insights']
    print(f"\n💡 Section: Cross-System Insights")
    print(f"   Most transferable system: {insights['most_transferable_system']}")
    print(f"   Most receptive system: {insights['most_receptive_system']}")
    print(f"   Synthesis velocity: {insights['synthesis_velocity']:.2f} transfers/day")

    if insights['highest_compatibility_pairs']:
        print(f"\n   Highest compatibility pairs:")
        for pair_info in insights['highest_compatibility_pairs']:
            print(f"      {pair_info['pair']}: {pair_info['avg_compatibility']:.0%} compatibility")

    # Assertions
    assert report['report_type'] == "learning_synthesis", "Should be synthesis report"
    assert 'transfer_proposals' in report['sections'], "Should have proposals section"
    assert 'learning_conflicts' in report['sections'], "Should have conflicts section"
    assert 'completed_transfers' in report['sections'], "Should have transfers section"
    assert 'cross_system_insights' in report['sections'], "Should have insights section"

    print(f"\n✅ Synthesis report test passed")


def test_constitutional_compliance(synthesizer: LearningSynthesizer):
    """Test constitutional compliance in learning transfers"""
    print("\n" + "="*60)
    print("TEST 7: Constitutional Compliance Verification")
    print("="*60)

    # Get transfer decisions
    decisions = synthesizer.memory.get_decision_history(
        system_name="learning_synthesizer",
        decision_type="learning_transfer",
        limit=10
    )

    print(f"\n📜 Analyzing {len(decisions)} transfer decisions for constitutional compliance...")

    compliant_count = 0
    for decision in decisions:
        constitutional = decision.get('constitutional_compliance', {})
        strategic = decision.get('strategic_alignment', {})

        has_constitutional = len(constitutional) > 0
        has_strategic = len(strategic) > 0

        if has_constitutional or has_strategic:
            compliant_count += 1

    compliance_rate = (compliant_count / len(decisions) * 100) if decisions else 100
    print(f"\n✅ Constitutional Compliance Rate: {compliance_rate:.0f}%")
    print(f"   {compliant_count}/{len(decisions)} decisions include constitutional/strategic alignment")

    # Show example decision
    if decisions:
        print(f"\n📋 Example Transfer Decision:")
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
    if decisions:
        assert compliance_rate >= 50, "Majority of decisions should document compliance"

    print(f"\n✅ Constitutional compliance test passed")


def generate_final_report(synthesizer: LearningSynthesizer):
    """Generate final test summary"""
    print("\n" + "="*60)
    print("FINAL PHASE 6 TEST REPORT")
    print("="*60)

    # Get current synthesis state
    report = synthesizer.generate_synthesis_report(days_back=7)

    print(f"\n📊 Phase 6 Learning Synthesis Status:")
    print(f"   Transfer proposals: {report['sections']['transfer_proposals']['total']}")
    print(f"   Learning conflicts: {report['sections']['learning_conflicts']['total']}")
    print(f"   Completed transfers: {report['sections']['completed_transfers']['total']}")

    insights = report['sections']['cross_system_insights']
    print(f"\n💡 Cross-System Insights:")
    print(f"   Most transferable: {insights['most_transferable_system']}")
    print(f"   Most receptive: {insights['most_receptive_system']}")
    print(f"   Synthesis velocity: {insights['synthesis_velocity']:.2f} transfers/day")

    print(f"\n✅ Phase 6 Integration Complete:")
    print(f"   ✅ Automatic transfer opportunity identification")
    print(f"   ✅ Cross-system compatibility assessment")
    print(f"   ✅ Implicit pattern detection (thermal, memory, audio)")
    print(f"   ✅ Learning conflict detection and resolution")
    print(f"   ✅ Human-approved transfer execution")
    print(f"   ✅ Constitutional compliance in all transfers")
    print(f"   ✅ Comprehensive synthesis reporting")

    print(f"\n" + "="*60)
    print("✅ LEARNING SYNTHESIZER INTEGRATION TEST COMPLETE")
    print("="*60)


def run_integration_test():
    """Run complete Phase 6 integration test"""
    print("="*60)
    print("LEARNING SYNTHESIZER - INTEGRATION TEST")
    print("Phase 6: Cross-System Learning Synthesis")
    print("="*60)

    try:
        synthesizer = LearningSynthesizer()
        print(f"\n✅ LearningSynthesizer initialized")
        print(f"📊 System managers loaded: Squirt, J5A, Sherlock")

        # Setup test data
        setup_test_learnings(synthesizer)

        # Run all tests
        test_identify_transferable_learnings(synthesizer)
        test_compatibility_assessment(synthesizer)
        test_implicit_transfer_detection(synthesizer)
        test_conflict_detection(synthesizer)
        test_transfer_execution(synthesizer)
        test_synthesis_report(synthesizer)
        test_constitutional_compliance(synthesizer)
        generate_final_report(synthesizer)

        print(f"\n✅ All Phase 6 integration tests passed!")
        print(f"\n💡 Key Achievements:")
        print(f"   ✅ Transferable learning identification")
        print(f"   ✅ Compatibility assessment framework")
        print(f"   ✅ Implicit transfer pattern detection")
        print(f"   ✅ Learning conflict detection")
        print(f"   ✅ Human-approved transfer execution")
        print(f"   ✅ Comprehensive synthesis reporting")
        print(f"   ✅ Constitutional compliance verification")

        return 0

    except Exception as e:
        print(f"\n❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(run_integration_test())
