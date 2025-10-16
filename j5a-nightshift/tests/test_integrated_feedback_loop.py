#!/usr/bin/env python3
"""
Integration Test Suite for J5A Feedback Loop

Tests the complete Retrieve → Reason → Act → Remember → Refine loop

Constitutional Authority: J5A_CONSTITUTION.md
Strategic Framework: J5A_STRATEGIC_AI_PRINCIPLES.md
"""

import unittest
import sys
import os
from pathlib import Path

# Add core to path - handle nested j5a-nightshift structure
core_path = Path(__file__).parent.parent / "j5a-nightshift" / "core"
if not core_path.exists():
    core_path = Path(__file__).parent.parent / "core"
sys.path.insert(0, str(core_path))

from feedback_loop_orchestrator import FeedbackLoopOrchestrator
from j5a_memory import J5AMemory
from context_engineer import ContextEngineer
from adaptive_feedback import AdaptiveFeedbackLoop
from governance_logger import GovernanceLogger


class TestFeedbackLoopIntegration(unittest.TestCase):
    """Test complete feedback loop integration"""

    def setUp(self):
        """Set up test fixtures"""
        self.memory = J5AMemory(base_path="/tmp/j5a_test/knowledge")
        self.gov_logger = GovernanceLogger(log_dir="/tmp/j5a_test/governance")

        self.orchestrator = FeedbackLoopOrchestrator(
            test_mode=True,
            base_path="/tmp/j5a_test"
        )
        self.orchestrator.memory = self.memory
        self.orchestrator.gov_logger = self.gov_logger

        self.context_engineer = ContextEngineer()
        self.feedback_loop = AdaptiveFeedbackLoop()

    def tearDown(self):
        """Clean up test artifacts"""
        import shutil
        if os.path.exists("/tmp/j5a_test"):
            shutil.rmtree("/tmp/j5a_test")

    def test_retrieve_phase(self):
        """Test Retrieve: Load relevant context from memory"""
        # Store test entity
        self.memory.remember_entity("test_client", {
            "name": "Test Client",
            "service": "irrigation"
        })

        # Retrieve
        context = self.orchestrator.retrieve(query="irrigation client")

        self.assertIsNotNone(context)
        self.assertIn("entities", context)

    def test_reason_phase(self):
        """Test Reason: Apply strategic principles to context"""
        context = {
            "task": "transcribe_audio",
            "audio_duration_minutes": 120,
            "available_ram_gb": 2.5
        }

        reasoning = self.orchestrator.reason(context)

        self.assertIsNotNone(reasoning)
        self.assertIn("constitutional_compliance", reasoning)
        self.assertIn("model_selection", reasoning)

    def test_act_phase(self):
        """Test Act: Execute decision with governance"""
        decision = {
            "action": "select_model",
            "model": "small",
            "reasoning": "Balanced quality vs resources"
        }

        # Log decision
        self.gov_logger.log_decision(
            decision_type="model_selection",
            context={"available_ram": 2.5},
            decision=decision,
            principle_alignment=["Principle 4: Resource Stewardship"]
        )

        result = self.orchestrator.act(decision)

        self.assertTrue(result.get("logged"))
        self.assertEqual(result.get("action"), "select_model")

    def test_remember_phase(self):
        """Test Remember: Store outcomes in active memory"""
        outcome = {
            "task": "transcription_completed",
            "model_used": "small",
            "success": True,
            "processing_time_minutes": 45,
            "actual_ram_mb": 823
        }

        self.orchestrator.remember(outcome)

        # Verify stored
        session = self.memory.recall_session("latest")
        self.assertIsNotNone(session)

    def test_refine_phase(self):
        """Test Refine: Learn from outcomes to improve"""
        outcomes = [
            {"model": "small", "duration": 120, "success": True, "ram_used": 823},
            {"model": "small", "duration": 90, "success": True, "ram_used": 756},
            {"model": "medium", "duration": 60, "success": False, "ram_used": 1800}
        ]

        for outcome in outcomes:
            self.feedback_loop.record_outcome(outcome)

        refinements = self.feedback_loop.analyze_patterns()

        self.assertIn("model_performance", refinements)
        # Should learn that 'small' is reliable, 'medium' fails
        self.assertTrue(refinements["model_performance"]["small"]["success_rate"] > 0.9)

    def test_complete_feedback_loop(self):
        """Test complete Retrieve → Reason → Act → Remember → Refine cycle"""

        # 1. RETRIEVE context
        self.memory.remember_entity("podcast", {
            "title": "Test Podcast",
            "typical_duration": 90
        })

        context = self.orchestrator.retrieve(query="podcast transcription")

        # 2. REASON about approach
        reasoning = self.orchestrator.reason(context)
        self.assertIn("model_selection", reasoning)

        # 3. ACT on decision
        decision = {
            "action": "transcribe",
            "model": reasoning["model_selection"]["recommended_model"],
            "reasoning": reasoning["rationale"]
        }

        result = self.orchestrator.act(decision)
        self.assertTrue(result.get("success", False))

        # 4. REMEMBER outcome
        outcome = {
            "task": "podcast_transcription",
            "model_used": decision["model"],
            "success": True,
            "quality_score": 0.85
        }

        self.orchestrator.remember(outcome)

        # 5. REFINE based on outcome
        self.feedback_loop.record_outcome(outcome)
        refinements = self.feedback_loop.analyze_patterns()

        self.assertIsNotNone(refinements)

        # Verify complete cycle worked
        self.assertTrue(result.get("success"))
        self.assertIsNotNone(refinements)


class TestConstitutionalCompliance(unittest.TestCase):
    """Test constitutional principle enforcement"""

    def setUp(self):
        """Set up test fixtures"""
        self.gov_logger = GovernanceLogger(log_dir="/tmp/j5a_test/governance")
        self.orchestrator = FeedbackLoopOrchestrator(test_mode=True)
        self.orchestrator.gov_logger = self.gov_logger

    def tearDown(self):
        """Clean up"""
        import shutil
        if os.path.exists("/tmp/j5a_test"):
            shutil.rmtree("/tmp/j5a_test")

    def test_principle_1_human_agency(self):
        """Verify high-risk decisions require approval"""
        high_risk_decision = {
            "action": "modify_core_system",
            "risk_level": "high"
        }

        result = self.orchestrator.evaluate_risk(high_risk_decision)

        self.assertEqual(result["requires_approval"], True)
        self.assertIn("human_approval_required", result["next_steps"])

    def test_principle_2_transparency(self):
        """Verify all decisions are logged"""
        decision = {
            "action": "test_action",
            "reasoning": "test reasoning"
        }

        self.orchestrator.act(decision)

        # Verify logged
        logs = self.gov_logger.get_recent_decisions(limit=1)
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0]["decision"]["action"], "test_action")

    def test_principle_3_system_viability(self):
        """Verify completion prioritized over speed"""
        task_params = {
            "audio_duration_hours": 12,
            "available_ram_gb": 2.5,
            "quality_preference": "maximum"
        }

        decision = self.orchestrator.reason(task_params)

        # Should select chunked processing (slower but completes)
        # rather than attempting large model (faster but crashes)
        self.assertTrue(decision.get("chunking_required"))
        self.assertNotEqual(decision["model_selection"]["recommended_model"], "large-v3")

    def test_principle_4_resource_stewardship(self):
        """Verify resource constraints respected"""
        constrained_context = {
            "available_ram_gb": 1.5,
            "cpu_temp_celsius": 78
        }

        decision = self.orchestrator.reason(constrained_context)

        # Should select conservative model due to constraints
        self.assertIn(decision["model_selection"]["recommended_model"], ["tiny", "base"])
        self.assertTrue(decision.get("thermal_warning_acknowledged"))


class TestStrategicPrincipleImplementation(unittest.TestCase):
    """Test strategic principle implementation"""

    def setUp(self):
        """Set up test fixtures"""
        self.context_eng = ContextEngineer()
        self.feedback = AdaptiveFeedbackLoop()
        self.memory = J5AMemory(base_path="/tmp/j5a_test/knowledge")

    def tearDown(self):
        """Clean up"""
        import shutil
        if os.path.exists("/tmp/j5a_test"):
            shutil.rmtree("/tmp/j5a_test")

    def test_principle_3_context_engineering(self):
        """Test efficient context window usage"""
        large_context = {
            "data": ["item_" + str(i) for i in range(1000)],
            "metadata": {"very": "verbose", "lots": "of", "extra": "data"}
        }

        optimized = self.context_eng.optimize_context(
            large_context,
            max_tokens=500
        )

        self.assertLess(len(str(optimized)), len(str(large_context)))
        # Should preserve essential data
        self.assertIn("data", optimized)

    def test_principle_4_active_memory(self):
        """Test persistent knowledge across sessions"""
        # Session 1: Remember entity
        self.memory.remember_entity("client", {"name": "Test Client", "id": 123})

        # Session 2: Recall entity
        entity = self.memory.recall_entity("client", entity_id=123)

        self.assertIsNotNone(entity)
        self.assertEqual(entity["name"], "Test Client")

    def test_principle_5_adaptive_feedback(self):
        """Test learning from outcomes"""
        # Record multiple outcomes
        for i in range(10):
            outcome = {
                "approach": "chunked_processing",
                "success": True,
                "quality_score": 0.85 + (i * 0.01)
            }
            self.feedback.record_outcome(outcome)

        # Should learn that chunked_processing works well
        patterns = self.feedback.analyze_patterns()

        self.assertIn("chunked_processing", patterns["successful_approaches"])


class TestErrorHandlingAndGracefulDegradation(unittest.TestCase):
    """Test error handling and graceful degradation"""

    def setUp(self):
        """Set up test fixtures"""
        self.orchestrator = FeedbackLoopOrchestrator(test_mode=True)

    def test_memory_unavailable_fallback(self):
        """Test graceful handling when memory system unavailable"""
        # Simulate memory failure
        context = self.orchestrator.retrieve(
            query="test",
            allow_fallback=True
        )

        # Should fall back to empty context rather than crash
        self.assertIsNotNone(context)
        self.assertEqual(context.get("fallback_used"), True)

    def test_model_selection_fallback(self):
        """Test fallback to smaller model if preferred unavailable"""
        constrained = {
            "available_ram_gb": 0.8,  # Very constrained
            "quality_preference": "maximum"  # Wants large model
        }

        reasoning = self.orchestrator.reason(constrained)

        # Should fall back to tiny model despite preference
        self.assertEqual(reasoning["model_selection"]["recommended_model"], "tiny")
        self.assertIn("fallback", reasoning["model_selection"]["notes"])


def run_integration_tests():
    """Run complete integration test suite"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add all test cases
    suite.addTests(loader.loadTestsFromTestCase(TestFeedbackLoopIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestConstitutionalCompliance))
    suite.addTests(loader.loadTestsFromTestCase(TestStrategicPrincipleImplementation))
    suite.addTests(loader.loadTestsFromTestCase(TestErrorHandlingAndGracefulDegradation))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return result.wasSuccessful()


if __name__ == "__main__":
    print("=" * 70)
    print("J5A Integrated Feedback Loop - Integration Test Suite")
    print("=" * 70)
    print()

    success = run_integration_tests()

    print()
    print("=" * 70)
    if success:
        print("✅ All integration tests passed!")
    else:
        print("❌ Some tests failed - review output above")
    print("=" * 70)

    sys.exit(0 if success else 1)
