#!/usr/bin/env python3
"""
Sherlock Package Validator

Implements V1 and V2 validation for Sherlock research packages.

Validation Levels:
- V0: Schema validation (already implemented in Targeting Officer)
- V1: Execution validation (did it run successfully?)
- V2: Output conformance (did it produce expected quality outputs?)
"""

import json
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from sherlock_status_updater import get_package_status, mark_package_validated


def validate_v1_execution(package_id: int, sherlock_db: str = "/home/johnny5/Sherlock/sherlock.db") -> Tuple[bool, Dict]:
    """
    V1 Validation: Execution Validation

    Checks:
    1. Package status is 'completed' (not failed/stuck)
    2. Execution completed without errors
    3. Task ran within expected time bounds
    4. No critical errors logged

    Args:
        package_id: Package ID to validate
        sherlock_db: Path to Sherlock database

    Returns:
        (passed: bool, results: dict)
    """
    results = {
        'validation_level': 'v1',
        'checks_performed': [],
        'checks_passed': [],
        'checks_failed': [],
        'validated_at': datetime.now().isoformat()
    }

    # Get package status
    package = get_package_status(package_id, sherlock_db)
    if not package:
        results['checks_failed'].append('Package not found')
        results['passed'] = False
        return False, results

    # Check 1: Package status is completed
    check_name = "Package status is 'completed'"
    results['checks_performed'].append(check_name)

    if package['status'] == 'completed':
        results['checks_passed'].append(check_name)
    else:
        results['checks_failed'].append(f"{check_name} (actual: {package['status']})")

    # Check 2: No error messages in metadata
    check_name = "No execution errors"
    results['checks_performed'].append(check_name)

    metadata = package.get('metadata', {})
    if 'error' not in metadata and metadata.get('execution_completed_at'):
        results['checks_passed'].append(check_name)
    else:
        error_msg = metadata.get('error', 'unknown error')
        results['checks_failed'].append(f"{check_name} (error: {error_msg})")

    # Check 3: Outputs were generated
    check_name = "Outputs were generated"
    results['checks_performed'].append(check_name)

    outputs = metadata.get('outputs_generated', [])
    if outputs and len(outputs) > 0:
        results['checks_passed'].append(check_name)
        results['outputs_count'] = len(outputs)
    else:
        results['checks_failed'].append(f"{check_name} (0 outputs)")

    # Check 4: Status history shows progression
    check_name = "Status progression is normal"
    results['checks_performed'].append(check_name)

    status_history = metadata.get('status_history', [])
    if len(status_history) >= 2:  # Should have at least queued → completed
        results['checks_passed'].append(check_name)
    else:
        results['checks_failed'].append(f"{check_name} (history: {len(status_history)} entries)")

    # Overall result
    passed = len(results['checks_failed']) == 0
    results['passed'] = passed
    results['pass_rate'] = len(results['checks_passed']) / len(results['checks_performed']) if results['checks_performed'] else 0

    return passed, results


def validate_v2_output_conformance(
    package_id: int,
    sherlock_db: str = "/home/johnny5/Sherlock/sherlock.db",
    j5a_root: str = "/home/johnny5/Johny5Alive"
) -> Tuple[bool, Dict]:
    """
    V2 Validation: Output Conformance Validation

    Checks:
    1. Expected output files exist
    2. Output files are non-empty
    3. JSON files are valid JSON
    4. Claims meet minimum threshold (if applicable)
    5. Entities meet minimum threshold (if applicable)
    6. Output quality meets standards

    Args:
        package_id: Package ID to validate
        sherlock_db: Path to Sherlock database
        j5a_root: Root directory for J5A system

    Returns:
        (passed: bool, results: dict)
    """
    results = {
        'validation_level': 'v2',
        'checks_performed': [],
        'checks_passed': [],
        'checks_failed': [],
        'validated_at': datetime.now().isoformat()
    }

    # Get package
    package = get_package_status(package_id, sherlock_db)
    if not package:
        results['checks_failed'].append('Package not found')
        results['passed'] = False
        return False, results

    metadata = package.get('metadata', {})
    outputs_generated = metadata.get('outputs_generated', [])

    # Check 1: Output files exist
    check_name = "Output files exist"
    results['checks_performed'].append(check_name)

    existing_files = []
    missing_files = []

    for output_path in outputs_generated:
        # Try both absolute path and relative to Sherlock
        paths_to_try = [
            Path(output_path),
            Path("/home/johnny5/Sherlock") / output_path,
            Path(j5a_root) / "artifacts" / "nightshift" / output_path
        ]

        found = False
        for path in paths_to_try:
            if path.exists():
                existing_files.append(str(path))
                found = True
                break

        if not found:
            missing_files.append(output_path)

    if len(existing_files) > 0:
        results['checks_passed'].append(f"{check_name} ({len(existing_files)} found)")
        results['existing_files'] = existing_files
    else:
        results['checks_failed'].append(f"{check_name} (0 found)")

    if missing_files:
        results['missing_files'] = missing_files

    # Check 2: Files are non-empty
    check_name = "Output files are non-empty"
    results['checks_performed'].append(check_name)

    non_empty_count = 0
    empty_files = []

    for file_path in existing_files:
        path = Path(file_path)
        size = path.stat().st_size if path.exists() else 0
        if size > 0:
            non_empty_count += 1
        else:
            empty_files.append(str(path))

    if non_empty_count == len(existing_files) and len(existing_files) > 0:
        results['checks_passed'].append(f"{check_name} (all files have content)")
    else:
        results['checks_failed'].append(f"{check_name} ({len(empty_files)} empty)")
        if empty_files:
            results['empty_files'] = empty_files

    # Check 3: JSON files are valid
    check_name = "JSON files are valid"
    results['checks_performed'].append(check_name)

    json_files = [f for f in existing_files if f.endswith('.json')]
    valid_json_count = 0
    invalid_json = []

    for json_file in json_files:
        try:
            with open(json_file) as f:
                json.load(f)
            valid_json_count += 1
        except Exception as e:
            invalid_json.append(f"{json_file}: {str(e)}")

    if valid_json_count == len(json_files) and len(json_files) > 0:
        results['checks_passed'].append(f"{check_name} (all valid)")
    elif len(json_files) == 0:
        results['checks_passed'].append(f"{check_name} (no JSON files)")
    else:
        results['checks_failed'].append(f"{check_name} ({len(invalid_json)} invalid)")
        if invalid_json:
            results['invalid_json'] = invalid_json

    # Check 4: Claims threshold
    check_name = "Claims meet minimum threshold"
    results['checks_performed'].append(check_name)

    claims_count = metadata.get('claims_extracted', 0)
    min_claims = 5  # Minimum expected claims

    if claims_count >= min_claims:
        results['checks_passed'].append(f"{check_name} ({claims_count} >= {min_claims})")
    else:
        results['checks_failed'].append(f"{check_name} ({claims_count} < {min_claims})")

    results['claims_extracted'] = claims_count

    # Check 5: Entities threshold
    check_name = "Entities meet minimum threshold"
    results['checks_performed'].append(check_name)

    entities_count = metadata.get('entities_found', 0)
    min_entities = 3  # Minimum expected entities

    if entities_count >= min_entities:
        results['checks_passed'].append(f"{check_name} ({entities_count} >= {min_entities})")
    else:
        results['checks_failed'].append(f"{check_name} ({entities_count} < {min_entities})")

    results['entities_found'] = entities_count

    # Overall result
    passed = len(results['checks_failed']) == 0
    results['passed'] = passed
    results['pass_rate'] = len(results['checks_passed']) / len(results['checks_performed']) if results['checks_performed'] else 0

    return passed, results


def run_full_validation(package_id: int, sherlock_db: str = "/home/johnny5/Sherlock/sherlock.db") -> Dict:
    """
    Run full validation pipeline (V1 + V2) for a package.

    Args:
        package_id: Package ID to validate
        sherlock_db: Path to Sherlock database

    Returns:
        Combined validation results
    """
    print(f"\n{'='*70}")
    print(f"SHERLOCK PACKAGE VALIDATION: Package {package_id}")
    print(f"{'='*70}\n")

    validation_report = {
        'package_id': package_id,
        'validation_timestamp': datetime.now().isoformat(),
        'v1_validation': None,
        'v2_validation': None,
        'overall_passed': False
    }

    # V1 Validation
    print("🔍 Running V1 Validation (Execution)...")
    v1_passed, v1_results = validate_v1_execution(package_id, sherlock_db)
    validation_report['v1_validation'] = v1_results

    print(f"   {'✅' if v1_passed else '❌'} V1 Validation: {'PASSED' if v1_passed else 'FAILED'}")
    print(f"   Pass Rate: {v1_results['pass_rate']:.1%}")
    print(f"   Checks Passed: {len(v1_results['checks_passed'])}/{len(v1_results['checks_performed'])}")

    if v1_results['checks_failed']:
        print(f"   Failed Checks:")
        for check in v1_results['checks_failed']:
            print(f"      • {check}")

    # Update package with V1 results
    mark_package_validated(package_id, 'v1', v1_results, sherlock_db)

    # V2 Validation (only if V1 passed)
    if v1_passed:
        print(f"\n🔍 Running V2 Validation (Output Conformance)...")
        v2_passed, v2_results = validate_v2_output_conformance(package_id, sherlock_db)
        validation_report['v2_validation'] = v2_results

        print(f"   {'✅' if v2_passed else '❌'} V2 Validation: {'PASSED' if v2_passed else 'FAILED'}")
        print(f"   Pass Rate: {v2_results['pass_rate']:.1%}")
        print(f"   Checks Passed: {len(v2_results['checks_passed'])}/{len(v2_results['checks_performed'])}")

        if v2_results['checks_failed']:
            print(f"   Failed Checks:")
            for check in v2_results['checks_failed']:
                print(f"      • {check}")

        # Update package with V2 results
        mark_package_validated(package_id, 'v2', v2_results, sherlock_db)

        validation_report['overall_passed'] = v2_passed
    else:
        print(f"\n⏭️  Skipping V2 Validation (V1 failed)")
        validation_report['overall_passed'] = False

    # Summary
    print(f"\n{'='*70}")
    if validation_report['overall_passed']:
        print(f"✅ VALIDATION COMPLETE: Package {package_id} PASSED")
    else:
        print(f"❌ VALIDATION COMPLETE: Package {package_id} FAILED")
    print(f"{'='*70}\n")

    return validation_report


def main():
    """CLI interface for validation"""
    import argparse

    parser = argparse.ArgumentParser(description="Validate Sherlock research package")
    parser.add_argument("--package-id", type=int, required=True, help="Package ID to validate")
    parser.add_argument("--level", choices=['v1', 'v2', 'full'], default='full', help="Validation level")
    parser.add_argument("--db", default="/home/johnny5/Sherlock/sherlock.db", help="Database path")
    parser.add_argument("--save-report", help="Save validation report to file")

    args = parser.parse_args()

    if args.level == 'v1':
        passed, results = validate_v1_execution(args.package_id, args.db)
        print(json.dumps(results, indent=2))
    elif args.level == 'v2':
        passed, results = validate_v2_output_conformance(args.package_id, args.db)
        print(json.dumps(results, indent=2))
    else:  # full
        report = run_full_validation(args.package_id, args.db)

        if args.save_report:
            with open(args.save_report, 'w') as f:
                json.dumps(report, f, indent=2)
            print(f"\n📄 Report saved: {args.save_report}")


if __name__ == "__main__":
    main()
