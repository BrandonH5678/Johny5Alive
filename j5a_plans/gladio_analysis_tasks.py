#!/usr/bin/env python3
"""
Operation Gladio Intelligence Analysis - J5A Work Assignments
Background processing for entity extraction, relationship mapping, and analysis
"""

import sys
from datetime import datetime
from pathlib import Path

# Add parent directory to path for J5A imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from j5a_work_assignment import (
    J5AWorkAssignment,
    Priority,
    OutputSpecification,
    QuantitativeMeasure,
    TestOracle,
    EscalationPolicy
)

# Base paths
SHERLOCK_PATH = Path("/home/johnny5/Sherlock")
GLADIO_PATH = SHERLOCK_PATH / "audiobooks" / "operation_gladio"

def create_gladio_analysis_tasks():
    """Create all Gladio analysis tasks for J5A queue"""

    tasks = []

    # ===== PHASE 2: ENTITY EXTRACTION =====

    # Task 2.1: Batch Entity Extractor
    task_2_1 = J5AWorkAssignment(
        task_id="gladio_analysis_2_1",
        task_name="Create BatchEntityExtractor for incremental processing",
        domain="intelligence_analysis",
        description="Build entity extractor that processes transcript in small batches with checkpoint saving",
        assigned_date=datetime.now(),
        priority=Priority.NORMAL,  # Background processing

        expected_outputs=[
            OutputSpecification(
                file_path=SHERLOCK_PATH / "gladio_batch_entity_extractor.py",
                format="Python",
                description="Batch entity extractor with checkpoint pattern",
                min_size_bytes=3000,
                quality_checks=["valid_python", "imports_work", "checkpoint_pattern", "low_memory"]
            )
        ],

        success_criteria={
            "valid_syntax": QuantitativeMeasure("syntax_errors", 0, "==", "count"),
            "low_memory": QuantitativeMeasure("peak_ram_mb", 150, "<=", "MB"),
            "checkpoints_work": QuantitativeMeasure("checkpoint_saves", 1.0, "==", "boolean"),
            "resume_works": QuantitativeMeasure("resume_from_checkpoint", 1.0, "==", "boolean"),
            "extracts_entities": QuantitativeMeasure("entities_found", 10, ">=", "count")
        },

        test_oracle=TestOracle(
            name="Entity extractor validation",
            description="Verify batch processing, checkpoint saving, memory efficiency",
            expected_behavior="Processes batches, saves checkpoints, uses <150MB RAM, can resume",
            validation_method="Process sample batches, verify checkpoints, measure memory",
            test_cases=[
                {"test": "process_small_batch", "expected": "entities_extracted"},
                {"test": "checkpoint_saved", "expected": "file_exists"},
                {"test": "resume_from_checkpoint", "expected": "skips_completed"},
                {"test": "memory_usage", "expected": "under_150mb"}
            ]
        ),

        approved_architectures=["pathlib", "json", "re", "spacy_small_optional"],
        forbidden_patterns=[
            r"\.read\(\)(?!.*batch)",  # Don't read entire file at once
            r"results\s*=\s*\[\].*(?!.*save)",  # Accumulation without saves
        ],

        rollback_plan="rm -f gladio_batch_entity_extractor.py",
        failure_escalation=EscalationPolicy(
            notify_immediately=False,
            max_retry_attempts=2,
            rollback_on_failure=True
        ),

    )
    tasks.append(task_2_1)

    # Task 2.2: Entity Dossier Builder
    task_2_2 = J5AWorkAssignment(
        task_id="gladio_analysis_2_2",
        task_name="Create EntityDossierBuilder for structured profiles",
        domain="intelligence_analysis",
        description="Build dossier generator that consolidates entity mentions into structured profiles",
        assigned_date=datetime.now(),
        priority=Priority.NORMAL,

        expected_outputs=[
            OutputSpecification(
                file_path=SHERLOCK_PATH / "gladio_dossier_builder.py",
                format="Python",
                description="Entity dossier builder with deduplication and merging",
                min_size_bytes=2000,
                quality_checks=["valid_python", "imports_work", "deduplication_works"]
            )
        ],

        success_criteria={
            "valid_syntax": QuantitativeMeasure("syntax_errors", 0, "==", "count"),
            "deduplicates": QuantitativeMeasure("duplicate_removal", 0.9, ">=", "%"),
            "consolidates": QuantitativeMeasure("mentions_merged", 1.0, "==", "boolean"),
            "output_format": QuantitativeMeasure("json_valid", 1.0, "==", "boolean")
        },

        test_oracle=TestOracle(
            name="Dossier builder validation",
            description="Verify entity consolidation, deduplication, structured output",
            expected_behavior="Merges duplicate mentions, builds structured dossiers, outputs valid JSON",
            validation_method="Test with sample entities, verify deduplication",
            test_cases=[
                {"test": "merge_duplicates", "expected": "single_entity"},
                {"test": "extract_roles", "expected": "roles_list"},
                {"test": "extract_dates", "expected": "temporal_refs"},
                {"test": "output_json", "expected": "valid_structure"}
            ]
        ),

        approved_architectures=["json", "dataclasses", "evidence_schema_gladio"],
        forbidden_patterns=[],

        rollback_plan="rm -f gladio_dossier_builder.py",
        failure_escalation=EscalationPolicy(
            notify_immediately=False,
            max_retry_attempts=2,
            rollback_on_failure=True
        ),

    )
    tasks.append(task_2_2)

    # Task 2.3: Database Population
    task_2_3 = J5AWorkAssignment(
        task_id="gladio_analysis_2_3",
        task_name="Populate people and organizations tables",
        domain="intelligence_analysis",
        description="Load entity dossiers into database with atomic inserts and duplicate detection",
        assigned_date=datetime.now(),
        priority=Priority.NORMAL,

        expected_outputs=[
            OutputSpecification(
                file_path=SHERLOCK_PATH / "gladio_populate_entities.py",
                format="Python",
                description="Database population script with atomic inserts",
                min_size_bytes=1500,
                quality_checks=["valid_python", "imports_work", "populates_db"]
            )
        ],

        success_criteria={
            "valid_syntax": QuantitativeMeasure("syntax_errors", 0, "==", "count"),
            "populates_people": QuantitativeMeasure("people_inserted", 50, ">=", "count"),
            "populates_orgs": QuantitativeMeasure("orgs_inserted", 30, ">=", "count"),
            "no_duplicates": QuantitativeMeasure("duplicate_insertions", 0, "==", "count")
        },

        test_oracle=TestOracle(
            name="Database population validation",
            description="Verify entity insertion, duplicate detection, data integrity",
            expected_behavior="Inserts entities atomically, detects duplicates, maintains integrity",
            validation_method="Run population, query database, verify counts",
            test_cases=[
                {"test": "insert_people", "expected": "50_plus_records"},
                {"test": "insert_orgs", "expected": "30_plus_records"},
                {"test": "duplicate_handling", "expected": "no_errors"},
                {"test": "data_integrity", "expected": "valid_json_fields"}
            ]
        ),

        approved_architectures=["sqlite3", "json", "evidence_schema_gladio"],
        forbidden_patterns=[],

        rollback_plan="python3 -c \"import sqlite3; conn=sqlite3.connect('gladio_intelligence.db'); conn.execute('DELETE FROM people'); conn.execute('DELETE FROM organizations'); conn.commit()\"",
        failure_escalation=EscalationPolicy(
            notify_immediately=False,
            max_retry_attempts=2,
            rollback_on_failure=True
        ),


    )
    tasks.append(task_2_3)

    # Task 2.4: Entity Validation
    task_2_4 = J5AWorkAssignment(
        task_id="gladio_analysis_2_4",
        task_name="Validate entity extraction quality",
        domain="intelligence_analysis",
        description="Generate quality report for entity extraction (completeness, accuracy)",
        assigned_date=datetime.now(),
        priority=Priority.LOW,

        expected_outputs=[
            OutputSpecification(
                file_path=GLADIO_PATH / "entity_extraction_report.json",
                format="JSON",
                description="Entity extraction quality report",
                min_size_bytes=500,
                quality_checks=["valid_json", "contains_metrics"]
            )
        ],

        success_criteria={
            "completeness": QuantitativeMeasure("entities_captured_pct", 0.8, ">=", "%"),
            "accuracy": QuantitativeMeasure("entity_accuracy_sample", 0.85, ">=", "%"),
            "report_generated": QuantitativeMeasure("report_exists", 1.0, "==", "boolean")
        },

        test_oracle=TestOracle(
            name="Entity quality validation",
            description="Verify extraction completeness and accuracy",
            expected_behavior="Reports >80% capture rate, >85% accuracy",
            validation_method="Sample entities, compare to transcript",
            test_cases=[
                {"test": "sample_accuracy", "expected": "85_percent_correct"},
                {"test": "major_entities_present", "expected": "all_found"},
                {"test": "report_structure", "expected": "valid_json"}
            ]
        ),

        approved_architectures=["json", "sqlite3", "random_sampling"],
        forbidden_patterns=[],

        rollback_plan="rm -f audiobooks/operation_gladio/entity_extraction_report.json",
        failure_escalation=EscalationPolicy(
            notify_immediately=False,
            max_retry_attempts=1,
            rollback_on_failure=False
        ),


    )
    tasks.append(task_2_4)

    # ===== PHASE 3: RELATIONSHIP MAPPING =====

    # Task 3.1: Relationship Extractor
    task_3_1 = J5AWorkAssignment(
        task_id="gladio_analysis_3_1",
        task_name="Create RelationshipExtractor for network mapping",
        domain="intelligence_analysis",
        description="Extract relationships between entities via co-occurrence and context analysis",
        assigned_date=datetime.now(),
        priority=Priority.NORMAL,

        expected_outputs=[
            OutputSpecification(
                file_path=SHERLOCK_PATH / "gladio_relationship_extractor.py",
                format="Python",
                description="Relationship extractor with checkpoint pattern",
                min_size_bytes=2500,
                quality_checks=["valid_python", "imports_work", "extracts_relationships"]
            )
        ],

        success_criteria={
            "valid_syntax": QuantitativeMeasure("syntax_errors", 0, "==", "count"),
            "low_memory": QuantitativeMeasure("peak_ram_mb", 150, "<=", "MB"),
            "extracts_relationships": QuantitativeMeasure("relationships_found", 50, ">=", "count"),
            "checkpoints_work": QuantitativeMeasure("checkpoint_saves", 1.0, "==", "boolean")
        },

        test_oracle=TestOracle(
            name="Relationship extractor validation",
            description="Verify relationship extraction, typing, checkpoint saving",
            expected_behavior="Finds entity co-occurrences, types relationships, saves incrementally",
            validation_method="Process batches, verify relationships, check memory",
            test_cases=[
                {"test": "co_occurrence_detection", "expected": "relationships_found"},
                {"test": "relationship_typing", "expected": "types_assigned"},
                {"test": "checkpoint_pattern", "expected": "incremental_saves"},
                {"test": "memory_efficiency", "expected": "under_150mb"}
            ]
        ),

        approved_architectures=["pathlib", "json", "sqlite3", "evidence_schema_gladio"],
        forbidden_patterns=[
            r"\.read\(\)(?!.*batch)",  # Batch reading only
        ],

        rollback_plan="rm -f gladio_relationship_extractor.py",
        failure_escalation=EscalationPolicy(
            notify_immediately=False,
            max_retry_attempts=2,
            rollback_on_failure=True
        ),


    )
    tasks.append(task_3_1)

    # Task 3.2: Resource Flow Tracker
    task_3_2 = J5AWorkAssignment(
        task_id="gladio_analysis_3_2",
        task_name="Create ResourceFlowTracker for money/drugs/arms",
        domain="intelligence_analysis",
        description="Extract and track resource flows (money, drugs, weapons) through networks",
        assigned_date=datetime.now(),
        priority=Priority.NORMAL,

        expected_outputs=[
            OutputSpecification(
                file_path=SHERLOCK_PATH / "gladio_resource_flow_tracker.py",
                format="Python",
                description="Resource flow tracker with checkpoint pattern",
                min_size_bytes=2000,
                quality_checks=["valid_python", "imports_work", "tracks_flows"]
            )
        ],

        success_criteria={
            "valid_syntax": QuantitativeMeasure("syntax_errors", 0, "==", "count"),
            "low_memory": QuantitativeMeasure("peak_ram_mb", 150, "<=", "MB"),
            "tracks_flows": QuantitativeMeasure("flows_extracted", 20, ">=", "count"),
            "flow_types": QuantitativeMeasure("flow_types_found", 3, ">=", "count")
        },

        test_oracle=TestOracle(
            name="Resource flow tracker validation",
            description="Verify flow extraction for money, drugs, weapons",
            expected_behavior="Extracts resource movements, tracks origin/destination/facilitators",
            validation_method="Process batches, verify flow records",
            test_cases=[
                {"test": "money_flows", "expected": "financial_transfers_found"},
                {"test": "drug_flows", "expected": "heroin_routes_mapped"},
                {"test": "weapons_flows", "expected": "arms_transfers_found"},
                {"test": "checkpoint_pattern", "expected": "incremental_saves"}
            ]
        ),

        approved_architectures=["pathlib", "json", "sqlite3", "evidence_schema_gladio"],
        forbidden_patterns=[],

        rollback_plan="rm -f gladio_resource_flow_tracker.py",
        failure_escalation=EscalationPolicy(
            notify_immediately=False,
            max_retry_attempts=2,
            rollback_on_failure=True
        ),


    )
    tasks.append(task_3_2)

    # Task 3.3: Network Graph Builder
    task_3_3 = J5AWorkAssignment(
        task_id="gladio_analysis_3_3",
        task_name="Build network graph from relationships",
        domain="intelligence_analysis",
        description="Generate network graph visualization from relationship database",
        assigned_date=datetime.now(),
        priority=Priority.LOW,

        expected_outputs=[
            OutputSpecification(
                file_path=GLADIO_PATH / "gladio_network.dot",
                format="GraphViz DOT",
                description="Network graph in DOT format",
                min_size_bytes=1000,
                quality_checks=["valid_dot_syntax", "contains_nodes"]
            ),
            OutputSpecification(
                file_path=GLADIO_PATH / "network_metrics.json",
                format="JSON",
                description="Network analysis metrics",
                min_size_bytes=300,
                quality_checks=["valid_json", "contains_metrics"]
            )
        ],

        success_criteria={
            "valid_syntax": QuantitativeMeasure("syntax_errors", 0, "==", "count"),
            "nodes_present": QuantitativeMeasure("node_count", 50, ">=", "count"),
            "edges_present": QuantitativeMeasure("edge_count", 50, ">=", "count"),
            "metrics_calculated": QuantitativeMeasure("metrics_present", 1.0, "==", "boolean")
        },

        test_oracle=TestOracle(
            name="Network graph validation",
            description="Verify graph generation, metrics calculation",
            expected_behavior="Generates valid DOT file, calculates centrality metrics",
            validation_method="Generate graph, validate structure, check metrics",
            test_cases=[
                {"test": "graph_generation", "expected": "dot_file_created"},
                {"test": "node_count", "expected": "50_plus_nodes"},
                {"test": "centrality_metrics", "expected": "top_nodes_ranked"},
                {"test": "community_detection", "expected": "clusters_identified"}
            ]
        ),

        approved_architectures=["sqlite3", "json", "networkx_optional"],
        forbidden_patterns=[],

        rollback_plan="rm -f audiobooks/operation_gladio/gladio_network.dot audiobooks/operation_gladio/network_metrics.json",
        failure_escalation=EscalationPolicy(
            notify_immediately=False,
            max_retry_attempts=1,
            rollback_on_failure=False
        ),


    )
    tasks.append(task_3_3)

    # Task 3.4: Relationship Validation
    task_3_4 = J5AWorkAssignment(
        task_id="gladio_analysis_3_4",
        task_name="Validate relationship mapping quality",
        domain="intelligence_analysis",
        description="Generate quality report for relationship extraction",
        assigned_date=datetime.now(),
        priority=Priority.LOW,

        expected_outputs=[
            OutputSpecification(
                file_path=GLADIO_PATH / "relationship_mapping_report.json",
                format="JSON",
                description="Relationship mapping quality report",
                min_size_bytes=400,
                quality_checks=["valid_json", "contains_metrics"]
            )
        ],

        success_criteria={
            "relationships_mapped": QuantitativeMeasure("relationship_count", 100, ">=", "count"),
            "network_density": QuantitativeMeasure("connection_density", 0.05, ">=", "ratio"),
            "report_generated": QuantitativeMeasure("report_exists", 1.0, "==", "boolean")
        },

        test_oracle=TestOracle(
            name="Relationship quality validation",
            description="Verify relationship mapping completeness",
            expected_behavior="Reports network statistics, identifies key connections",
            validation_method="Query database, calculate metrics",
            test_cases=[
                {"test": "relationship_count", "expected": "100_plus_relationships"},
                {"test": "network_connected", "expected": "no_orphans"},
                {"test": "key_nodes_identified", "expected": "high_centrality_nodes"}
            ]
        ),

        approved_architectures=["json", "sqlite3"],
        forbidden_patterns=[],

        rollback_plan="rm -f audiobooks/operation_gladio/relationship_mapping_report.json",
        failure_escalation=EscalationPolicy(
            notify_immediately=False,
            max_retry_attempts=1,
            rollback_on_failure=False
        ),


    )
    tasks.append(task_3_4)

    # ===== PHASE 4: INTELLIGENCE ANALYSIS =====

    # Task 4.1: Timeline Constructor
    task_4_1 = J5AWorkAssignment(
        task_id="gladio_analysis_4_1",
        task_name="Build chronological event timeline",
        domain="intelligence_analysis",
        description="Extract temporal references and construct event timeline",
        assigned_date=datetime.now(),
        priority=Priority.NORMAL,

        expected_outputs=[
            OutputSpecification(
                file_path=SHERLOCK_PATH / "gladio_timeline_constructor.py",
                format="Python",
                description="Timeline constructor with temporal extraction",
                min_size_bytes=2000,
                quality_checks=["valid_python", "imports_work", "extracts_dates"]
            )
        ],

        success_criteria={
            "valid_syntax": QuantitativeMeasure("syntax_errors", 0, "==", "count"),
            "events_extracted": QuantitativeMeasure("timeline_events", 50, ">=", "count"),
            "dates_parsed": QuantitativeMeasure("temporal_refs_valid", 0.9, ">=", "%"),
            "populates_timeline": QuantitativeMeasure("timeline_table_populated", 1.0, "==", "boolean")
        },

        test_oracle=TestOracle(
            name="Timeline constructor validation",
            description="Verify temporal extraction and chronological ordering",
            expected_behavior="Extracts dates, sequences events, populates timeline table",
            validation_method="Process transcript, verify timeline ordering",
            test_cases=[
                {"test": "date_extraction", "expected": "temporal_refs_found"},
                {"test": "event_sequencing", "expected": "chronological_order"},
                {"test": "timeline_population", "expected": "50_plus_events"},
                {"test": "date_parsing", "expected": "valid_timestamps"}
            ]
        ),

        approved_architectures=["pathlib", "json", "sqlite3", "dateutil", "evidence_schema_gladio"],
        forbidden_patterns=[],

        rollback_plan="python3 -c \"import sqlite3; conn=sqlite3.connect('gladio_intelligence.db'); conn.execute('DELETE FROM timeline'); conn.commit()\"",
        failure_escalation=EscalationPolicy(
            notify_immediately=False,
            max_retry_attempts=2,
            rollback_on_failure=True
        ),


    )
    tasks.append(task_4_1)

    # Task 4.2: Evidence Correlator
    task_4_2 = J5AWorkAssignment(
        task_id="gladio_analysis_4_2",
        task_name="Build evidence correlation system",
        domain="intelligence_analysis",
        description="Extract claims, assign confidence levels, populate evidence table",
        assigned_date=datetime.now(),
        priority=Priority.NORMAL,

        expected_outputs=[
            OutputSpecification(
                file_path=SHERLOCK_PATH / "gladio_evidence_correlator.py",
                format="Python",
                description="Evidence correlator with confidence assessment",
                min_size_bytes=2000,
                quality_checks=["valid_python", "imports_work", "assigns_confidence"]
            )
        ],

        success_criteria={
            "valid_syntax": QuantitativeMeasure("syntax_errors", 0, "==", "count"),
            "claims_extracted": QuantitativeMeasure("evidence_records", 30, ">=", "count"),
            "confidence_assigned": QuantitativeMeasure("has_confidence_levels", 1.0, "==", "boolean"),
            "populates_evidence": QuantitativeMeasure("evidence_table_populated", 1.0, "==", "boolean")
        },

        test_oracle=TestOracle(
            name="Evidence correlator validation",
            description="Verify claim extraction and confidence assessment",
            expected_behavior="Extracts key claims, assigns confidence levels, links evidence",
            validation_method="Process transcript, verify evidence records",
            test_cases=[
                {"test": "claim_extraction", "expected": "claims_found"},
                {"test": "confidence_levels", "expected": "levels_assigned"},
                {"test": "evidence_linking", "expected": "sources_referenced"},
                {"test": "evidence_population", "expected": "30_plus_records"}
            ]
        ),

        approved_architectures=["pathlib", "json", "sqlite3", "evidence_schema_gladio"],
        forbidden_patterns=[],

        rollback_plan="python3 -c \"import sqlite3; conn=sqlite3.connect('gladio_intelligence.db'); conn.execute('DELETE FROM evidence'); conn.commit()\"",
        failure_escalation=EscalationPolicy(
            notify_immediately=False,
            max_retry_attempts=2,
            rollback_on_failure=True
        ),


    )
    tasks.append(task_4_2)

    # Task 4.3: Pattern Analyzer
    task_4_3 = J5AWorkAssignment(
        task_id="gladio_analysis_4_3",
        task_name="Analyze patterns in intelligence network",
        domain="intelligence_analysis",
        description="Detect patterns in network, resource flows, temporal clusters",
        assigned_date=datetime.now(),
        priority=Priority.NORMAL,

        expected_outputs=[
            OutputSpecification(
                file_path=GLADIO_PATH / "pattern_analysis_report.json",
                format="JSON",
                description="Pattern analysis findings",
                min_size_bytes=1000,
                quality_checks=["valid_json", "contains_patterns"]
            )
        ],

        success_criteria={
            "patterns_found": QuantitativeMeasure("pattern_count", 5, ">=", "count"),
            "network_analysis": QuantitativeMeasure("centrality_calculated", 1.0, "==", "boolean"),
            "flow_analysis": QuantitativeMeasure("resource_patterns_found", 1.0, "==", "boolean"),
            "report_generated": QuantitativeMeasure("report_exists", 1.0, "==", "boolean")
        },

        test_oracle=TestOracle(
            name="Pattern analyzer validation",
            description="Verify pattern detection in network and flows",
            expected_behavior="Identifies key nodes, resource flow patterns, temporal clusters",
            validation_method="Query database, analyze patterns, generate report",
            test_cases=[
                {"test": "centrality_analysis", "expected": "key_nodes_identified"},
                {"test": "flow_patterns", "expected": "resource_routes_mapped"},
                {"test": "temporal_clusters", "expected": "event_grouping"},
                {"test": "report_structure", "expected": "valid_json"}
            ]
        ),

        approved_architectures=["json", "sqlite3", "statistics"],
        forbidden_patterns=[],

        rollback_plan="rm -f audiobooks/operation_gladio/pattern_analysis_report.json",
        failure_escalation=EscalationPolicy(
            notify_immediately=False,
            max_retry_attempts=1,
            rollback_on_failure=False
        ),


    )
    tasks.append(task_4_3)

    # Task 4.4: Intelligence Report Generator
    task_4_4 = J5AWorkAssignment(
        task_id="gladio_analysis_4_4",
        task_name="Generate comprehensive intelligence reports",
        domain="intelligence_analysis",
        description="Create summary reports: top entities, key findings, network visualizations",
        assigned_date=datetime.now(),
        priority=Priority.LOW,

        expected_outputs=[
            OutputSpecification(
                file_path=GLADIO_PATH / "gladio_intelligence_summary.md",
                format="Markdown",
                description="Comprehensive intelligence summary",
                min_size_bytes=3000,
                quality_checks=["valid_markdown", "contains_findings"]
            ),
            OutputSpecification(
                file_path=GLADIO_PATH / "top_entities_report.json",
                format="JSON",
                description="Top 20 people and organizations",
                min_size_bytes=500,
                quality_checks=["valid_json", "contains_rankings"]
            )
        ],

        success_criteria={
            "summary_generated": QuantitativeMeasure("summary_exists", 1.0, "==", "boolean"),
            "top_entities": QuantitativeMeasure("entities_ranked", 20, ">=", "count"),
            "key_findings": QuantitativeMeasure("findings_documented", 10, ">=", "count"),
            "visualizations": QuantitativeMeasure("graph_files_created", 1, ">=", "count")
        },

        test_oracle=TestOracle(
            name="Intelligence report validation",
            description="Verify comprehensive reporting with all analysis components",
            expected_behavior="Generates readable summary with top entities, findings, graphs",
            validation_method="Review generated reports, verify completeness",
            test_cases=[
                {"test": "summary_content", "expected": "comprehensive_coverage"},
                {"test": "entity_rankings", "expected": "top_20_listed"},
                {"test": "findings_quality", "expected": "actionable_insights"},
                {"test": "visualization_quality", "expected": "readable_graphs"}
            ]
        ),

        approved_architectures=["json", "sqlite3", "markdown"],
        forbidden_patterns=[],

        rollback_plan="rm -f audiobooks/operation_gladio/gladio_intelligence_summary.md audiobooks/operation_gladio/top_entities_report.json",
        failure_escalation=EscalationPolicy(
            notify_immediately=False,
            max_retry_attempts=1,
            rollback_on_failure=False
        ),


    )
    tasks.append(task_4_4)

    return tasks


if __name__ == "__main__":
    """Generate Gladio analysis tasks for J5A queue"""

    tasks = create_gladio_analysis_tasks()

    print("=" * 80)
    print("Operation Gladio Intelligence Analysis - J5A Tasks")
    print("=" * 80)
    print(f"\nGenerated {len(tasks)} tasks for background processing:\n")

    phase_2 = [t for t in tasks if t.task_id.startswith("gladio_analysis_2")]
    phase_3 = [t for t in tasks if t.task_id.startswith("gladio_analysis_3")]
    phase_4 = [t for t in tasks if t.task_id.startswith("gladio_analysis_4")]

    print(f"PHASE 2: Entity Extraction ({len(phase_2)} tasks)")
    for task in phase_2:
        print(f"  • {task.task_id}: {task.task_name}")
    print()

    print(f"PHASE 3: Relationship Mapping ({len(phase_3)} tasks)")
    for task in phase_3:
        print(f"  • {task.task_id}: {task.task_name}")
    print()

    print(f"PHASE 4: Intelligence Analysis ({len(phase_4)} tasks)")
    for task in phase_4:
        print(f"  • {task.task_id}: {task.task_name}")
    print()

    print("=" * 80)
    print("Resource Profile:")
    print("  • Max RAM per task: 150MB")
    print("  • Max tokens per task: 8,000")
    print("  • Priority: BACKGROUND (yields to Squirt/Sherlock)")
    print("  • All tasks use checkpoint pattern (resume capability)")
    print("=" * 80)
    print("\nReady to queue in J5A overnight manager")
    print("Total estimated time: 8-10 hours (spread across multiple sessions)")
    print("=" * 80)
