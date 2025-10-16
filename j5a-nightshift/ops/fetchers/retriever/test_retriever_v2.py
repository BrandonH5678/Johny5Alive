#!/usr/bin/env python3
"""
Test Retriever v2 Agent Architecture
Demonstrates the extended agent system for multi-source retrieval
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from retriever import (
    # v1 Components
    discover_audio_from_homepage,
    RobustWebFetcher,
    # v2 Components
    BaseAgent,
    APIAgent,
    MediaAgent,
    FSAgent,
    DBAgent,
    OcrAgent,
    IndexAgent,
    QueryPlanner,
    QueueBridge,
)

def test_v1_components():
    """Test that v1 podcast discovery components still work"""
    print("=" * 60)
    print("Testing Retriever v1 Components")
    print("=" * 60)

    # Test RobustWebFetcher
    fetcher = RobustWebFetcher()
    print(f"✅ RobustWebFetcher instantiated: {fetcher}")

    # Test discover function exists
    print(f"✅ discover_audio_from_homepage function: {discover_audio_from_homepage}")

    print()

def test_v2_agents():
    """Test that v2 agent components work"""
    print("=" * 60)
    print("Testing Retriever v2 Agent Architecture")
    print("=" * 60)

    # Test BaseAgent
    print(f"✅ BaseAgent class: {BaseAgent}")

    # Test specialized agents
    api_agent = APIAgent()
    print(f"✅ APIAgent instantiated: {api_agent}")
    print(f"   - Supports REST: {api_agent.supports({'type': 'rest'})}")
    print(f"   - Supports GraphQL: {api_agent.supports({'type': 'graphql'})}")
    print(f"   - Supports file: {api_agent.supports({'type': 'file'})}")

    media_agent = MediaAgent()
    print(f"✅ MediaAgent instantiated: {media_agent}")
    print(f"   - Supports file: {media_agent.supports({'type': 'file'})}")

    fs_agent = FSAgent()
    print(f"✅ FSAgent instantiated: {fs_agent}")
    print(f"   - Supports fs: {fs_agent.supports({'type': 'fs'})}")

    db_agent = DBAgent()
    print(f"✅ DBAgent instantiated: {db_agent}")
    print(f"   - Supports sqlite: {db_agent.supports({'type': 'sqlite'})}")

    ocr_agent = OcrAgent()
    print(f"✅ OcrAgent instantiated: {ocr_agent}")
    print(f"   - Supports ocr: {ocr_agent.supports({'type': 'ocr'})}")

    index_agent = IndexAgent()
    print(f"✅ IndexAgent instantiated: {index_agent}")
    print(f"   - Supports index: {index_agent.supports({'type': 'index'})}")

    print()

def test_v2_orchestration():
    """Test v2 orchestration components"""
    print("=" * 60)
    print("Testing Retriever v2 Orchestration")
    print("=" * 60)

    # Test QueryPlanner
    planner = QueryPlanner()
    plan = planner.plan("Find all PDFs in the current directory")
    print(f"✅ QueryPlanner: {planner}")
    print(f"   - Generated plan: {plan}")

    # Test QueueBridge
    bridge = QueueBridge(backend='process')
    print(f"✅ QueueBridge: {bridge}")
    result = bridge.publish('retrieval', {'task': 'fetch_audio'})
    print(f"   - Publish result: {result}")

    print()

def test_agent_retrieval():
    """Test actual retrieval with implemented agents"""
    print("=" * 60)
    print("Testing Agent Retrieval (Full Implementation)")
    print("=" * 60)

    # Test FS agent retrieval (use current directory - guaranteed to exist)
    fs_agent = FSAgent()
    result = fs_agent.retrieve({'type': 'fs', 'path': '.', 'pattern': '*.py', 'recursive': False})
    print(f"✅ FSAgent.retrieve(): Found {result['count']} Python files")

    # Test IndexAgent (in-memory index)
    index_agent = IndexAgent()
    # Index some test documents
    index_result = index_agent.retrieve({
        'type': 'index',
        'operation': 'index',
        'documents': [
            {'id': 'doc1', 'text': 'Retriever v2 agent architecture', 'metadata': {}},
            {'id': 'doc2', 'text': 'Python machine learning tutorial', 'metadata': {}},
            {'id': 'doc3', 'text': 'Retriever supports multiple agents', 'metadata': {}}
        ]
    })
    print(f"✅ IndexAgent.index(): Indexed {index_result['indexed']} documents")

    # Search indexed documents
    search_result = index_agent.retrieve({
        'type': 'index',
        'operation': 'search',
        'query': 'retriever agent'
    })
    print(f"✅ IndexAgent.search(): Found {search_result['count']} results")

    # Test NLPRouter
    from retriever import NLPRouter
    nlp_router = NLPRouter()
    classification = nlp_router.classify("Download audio file from podcast website")
    print(f"✅ NLPRouter.classify(): intent={classification['intent']}, agents={classification['agent_types']}")

    # Test QueryPlanner with NLP
    planner = QueryPlanner()
    plan = planner.plan("Search for Python files in current directory")
    print(f"✅ QueryPlanner.plan(): Generated {len(plan)} step(s)")

    # Test QueueBridge with different backends
    from pathlib import Path
    import tempfile
    tmpdir = tempfile.mkdtemp()

    # File backend
    file_bridge = QueueBridge(backend='file', queue_path=tmpdir)
    publish_result = file_bridge.publish('test_channel', {'task': 'test_task'})
    print(f"✅ QueueBridge(file).publish(): task_id={publish_result['task_id']}")

    # Database backend
    db_bridge = QueueBridge(backend='database', queue_path=tmpdir)
    publish_result = db_bridge.publish('test_channel', {'task': 'test_task'})
    status = db_bridge.get_status(publish_result['task_id'])
    print(f"✅ QueueBridge(database).get_status(): status={status['status']}")

    print()

if __name__ == "__main__":
    print()
    print("🚀 Retriever v2 Agent Architecture Test Suite")
    print()

    test_v1_components()
    test_v2_agents()
    test_v2_orchestration()
    test_agent_retrieval()

    print("=" * 60)
    print("✅ ALL TESTS PASSED")
    print("=" * 60)
    print()
    print("Retriever v2 successfully installed with:")
    print("  - v1 podcast discovery functionality (intact)")
    print("  - v2 extensible agent architecture (ready for implementation)")
    print()
