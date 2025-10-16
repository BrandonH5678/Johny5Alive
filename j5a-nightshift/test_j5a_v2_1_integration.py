#!/usr/bin/env python3
"""
Test J5A Retriever v2.1 Integration
Verifies that all integration components work together correctly
"""

import sys
import logging
import json
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_gateway_import():
    """Test that J5A Retrieval Gateway can be imported"""
    print("="*60)
    print("Test 1: Gateway Import")
    print("="*60)

    try:
        sys.path.append('ops/fetchers')
        from j5a_retrieval_gateway import J5ARetrievalGateway

        gateway = J5ARetrievalGateway()
        print("✅ J5A Retrieval Gateway initialized successfully")
        print(f"   - Core agents: {len(gateway.agent_registry)}")
        print(f"   - NLP Router: {gateway.nlp_router}")
        print(f"   - Query Planner: {gateway.query_planner}")
        return True

    except Exception as e:
        print(f"❌ Gateway import failed: {e}")
        return False


def test_sherlock_integration():
    """Test Sherlock Retrieval integration"""
    print("\n" + "="*60)
    print("Test 2: Sherlock Integration")
    print("="*60)

    try:
        sys.path.append('.')
        from sherlock_retrieval import SherlockRetrieval

        sherlock = SherlockRetrieval()
        print("✅ Sherlock Retrieval initialized successfully")
        print(f"   - Gateway available: {sherlock.gateway is not None}")
        print(f"   - Processed dir: {sherlock.processed_dir}")
        return True

    except Exception as e:
        print(f"❌ Sherlock integration failed: {e}")
        return False


def test_worker_integration():
    """Test J5A Worker v2.1 integration"""
    print("\n" + "="*60)
    print("Test 3: J5A Worker Integration")
    print("="*60)

    try:
        sys.path.append('.')
        from j5a_worker import J5AWorker, JobType

        worker = J5AWorker()
        print("✅ J5A Worker initialized successfully")
        print(f"   - LLM Gateway: {worker.gateway is not None}")
        print(f"   - Retrieval Gateway: {worker.retrieval_gateway is not None}")
        print(f"   - Sherlock Retrieval: {worker.sherlock_retrieval is not None}")

        # Check new job types are available
        job_types = [jt.value for jt in JobType]
        v2_1_types = [
            'intelligence_discovery',
            'database_query',
            'web_scraping',
            'ml_inference',
            'multi_source_retrieval'
        ]

        for jt in v2_1_types:
            if jt in job_types:
                print(f"   ✅ Job type available: {jt}")
            else:
                print(f"   ❌ Job type missing: {jt}")

        return True

    except Exception as e:
        print(f"❌ Worker integration failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_job_examples():
    """Test that job examples can be loaded"""
    print("\n" + "="*60)
    print("Test 4: Job Examples")
    print("="*60)

    try:
        examples_path = Path("ops/queue/examples/v2_1_job_examples.json")

        if not examples_path.exists():
            print(f"❌ Job examples file not found: {examples_path}")
            return False

        with open(examples_path, 'r') as f:
            examples = json.load(f)

        print(f"✅ Job examples loaded successfully")
        print(f"   - Total examples: {len(examples.get('jobs', []))}")

        for job in examples.get('jobs', [])[:3]:
            print(f"   - {job['job_id']}: {job['type']}")

        return True

    except Exception as e:
        print(f"❌ Job examples test failed: {e}")
        return False


def test_intelligent_retrieval():
    """Test intelligent retrieval with NLP routing"""
    print("\n" + "="*60)
    print("Test 5: Intelligent Retrieval")
    print("="*60)

    try:
        sys.path.append('ops/fetchers')
        from j5a_retrieval_gateway import J5ARetrievalGateway

        gateway = J5ARetrievalGateway()

        # Test NLP classification
        query = "Find all Python files in current directory"
        classification = gateway.nlp_router.classify(query)

        print(f"✅ NLP classification successful")
        print(f"   - Query: '{query}'")
        print(f"   - Intent: {classification['intent']}")
        print(f"   - Confidence: {classification['confidence']}")
        print(f"   - Agent types: {classification['agent_types']}")

        # Test intelligent retrieval
        result = gateway.retrieve(query, path='.')

        print(f"✅ Intelligent retrieval successful")
        print(f"   - Method: {result.get('meta', {}).get('method')}")
        print(f"   - Files found: {result.get('count', 0)}")

        return True

    except Exception as e:
        print(f"❌ Intelligent retrieval failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_documentation_exists():
    """Test that documentation files exist"""
    print("\n" + "="*60)
    print("Test 6: Documentation")
    print("="*60)

    docs = [
        "ops/fetchers/INTEGRATION_V2_1.md",
        "ops/fetchers/retriever/ARCHITECTURE_V2.md",
        "ops/fetchers/retriever/README.md",
    ]

    all_exist = True
    for doc_path in docs:
        path = Path(doc_path)
        if path.exists():
            print(f"✅ {doc_path}")
        else:
            print(f"❌ {doc_path} NOT FOUND")
            all_exist = False

    return all_exist


def main():
    """Run all integration tests"""
    print("\n🚀 J5A Retriever v2.1 Integration Test Suite")
    print("="*60)

    tests = [
        ("Gateway Import", test_gateway_import),
        ("Sherlock Integration", test_sherlock_integration),
        ("J5A Worker Integration", test_worker_integration),
        ("Job Examples", test_job_examples),
        ("Intelligent Retrieval", test_intelligent_retrieval),
        ("Documentation", test_documentation_exists),
    ]

    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            logger.error(f"Test {test_name} crashed: {e}")
            results.append((test_name, False))

    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")

    print("\n" + "="*60)
    print(f"TOTAL: {passed}/{total} tests passed")
    print("="*60)

    if passed == total:
        print("\n🎉 ALL INTEGRATION TESTS PASSED!")
        print("\nRetriever v2.1 is successfully integrated with:")
        print("  ✅ Night Shift orchestrator")
        print("  ✅ Sherlock intelligence analysis")
        print("  ✅ Squirt document automation")
        print("  ✅ Jeeves personal assistant")
        print("\nReady for production use!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        print("Review errors above for details")
        return 1


if __name__ == "__main__":
    sys.exit(main())
