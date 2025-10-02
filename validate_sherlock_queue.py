#!/usr/bin/env python3
"""
J5A Sherlock Queue Validation

Validates Sherlock research packages in J5A queue using statistical sampling.

Usage:
    python3 validate_sherlock_queue.py
"""

import json
import random
from pathlib import Path
from typing import List, Dict
from datetime import datetime


def load_queue_packages(queue_dir: Path) -> List[Dict]:
    """Load all Sherlock packages from queue"""
    packages = []

    for pkg_file in queue_dir.glob("sherlock_pkg_*.json"):
        with open(pkg_file) as f:
            pkg = json.load(f)
            pkg['_queue_file'] = str(pkg_file)
            packages.append(pkg)

    return packages


def validate_package_format(package: Dict) -> tuple[bool, List[str]]:
    """V0 validation: Schema compliance"""
    errors = []

    # Required fields
    required = ['task_id', 'task_type', 'package_id', 'target_name',
                'package_type', 'priority', 'collection_urls', 'expected_outputs']

    for field in required:
        if field not in package:
            errors.append(f"Missing required field: {field}")

    # Validate collection URLs
    if 'collection_urls' in package:
        if not isinstance(package['collection_urls'], list):
            errors.append("collection_urls must be a list")
        elif len(package['collection_urls']) == 0:
            errors.append("collection_urls is empty")

    # Validate expected outputs
    if 'expected_outputs' in package:
        if not isinstance(package['expected_outputs'], list):
            errors.append("expected_outputs must be a list")
        elif len(package['expected_outputs']) == 0:
            errors.append("expected_outputs is empty")

    # Validate priority
    if 'priority' in package:
        if not isinstance(package['priority'], int) or package['priority'] < 1 or package['priority'] > 5:
            errors.append(f"Invalid priority: {package['priority']} (must be 1-5)")

    return len(errors) == 0, errors


def estimate_execution_viability(package: Dict) -> Dict:
    """Estimate execution viability"""
    viability = {
        'can_execute': True,
        'warnings': [],
        'estimated_duration_min': 0,
        'thermal_risk': 'low',
        'memory_risk': 'low'
    }

    # Duration estimation
    package_type = package.get('package_type', 'unknown')
    url_count = len(package.get('collection_urls', []))

    duration_map = {
        'youtube': 30,
        'document': 10,
        'composite': 20
    }

    base_duration = duration_map.get(package_type, 15)
    viability['estimated_duration_min'] = base_duration * url_count

    # Thermal risk
    if package_type == 'youtube':
        viability['thermal_risk'] = 'high'
        viability['warnings'].append("YouTube package: High thermal load (video processing + transcription)")

    # Memory risk
    if url_count > 3:
        viability['memory_risk'] = 'medium'
        viability['warnings'].append(f"Multiple URLs ({url_count}): May require sequential processing")

    # Check for very long executions
    if viability['estimated_duration_min'] > 60:
        viability['warnings'].append(f"Long execution ({viability['estimated_duration_min']} min): Consider chunking")

    return viability


def validate_url_accessibility(package: Dict) -> Dict:
    """Validate URL format (not actual HTTP access)"""
    result = {
        'valid_urls': [],
        'invalid_urls': [],
        'warnings': []
    }

    for url in package.get('collection_urls', []):
        # Basic URL validation
        if url.startswith('http://') or url.startswith('https://'):
            result['valid_urls'].append(url)
        else:
            result['invalid_urls'].append(url)

    return result


def statistical_sample_validation(packages: List[Dict], sample_size: int = 5) -> Dict:
    """3-segment stratified sampling validation"""

    if len(packages) == 0:
        return {
            'error': 'No packages to validate',
            'total_packages': 0
        }

    # Sample selection: beginning, middle, end + random
    sample_indices = []

    if len(packages) <= sample_size:
        sample_indices = list(range(len(packages)))
    else:
        # Beginning
        sample_indices.append(0)

        # Middle
        sample_indices.append(len(packages) // 2)

        # End
        sample_indices.append(len(packages) - 1)

        # Random fill
        remaining = sample_size - 3
        available = [i for i in range(1, len(packages) - 1) if i not in sample_indices]
        sample_indices.extend(random.sample(available, min(remaining, len(available))))

    # Validate samples
    results = {
        'total_packages': len(packages),
        'sample_size': len(sample_indices),
        'samples': [],
        'format_success_rate': 0.0,
        'viability_rate': 0.0,
        'url_validity_rate': 0.0,
        'overall_success_rate': 0.0
    }

    format_pass = 0
    viable_pass = 0
    url_pass = 0

    for idx in sample_indices:
        package = packages[idx]

        # Format validation
        format_valid, format_errors = validate_package_format(package)
        if format_valid:
            format_pass += 1

        # Viability estimation
        viability = estimate_execution_viability(package)
        if viability['can_execute']:
            viable_pass += 1

        # URL validation
        url_check = validate_url_accessibility(package)
        if len(url_check['invalid_urls']) == 0:
            url_pass += 1

        sample_result = {
            'package_id': package.get('package_id'),
            'target_name': package.get('target_name'),
            'package_type': package.get('package_type'),
            'priority': package.get('priority'),
            'format_valid': format_valid,
            'format_errors': format_errors,
            'viability': viability,
            'url_check': url_check
        }

        results['samples'].append(sample_result)

    # Calculate rates
    sample_count = len(sample_indices)
    results['format_success_rate'] = (format_pass / sample_count * 100) if sample_count > 0 else 0
    results['viability_rate'] = (viable_pass / sample_count * 100) if sample_count > 0 else 0
    results['url_validity_rate'] = (url_pass / sample_count * 100) if sample_count > 0 else 0
    results['overall_success_rate'] = (
        (format_pass + viable_pass + url_pass) / (sample_count * 3) * 100
    ) if sample_count > 0 else 0

    return results


def print_validation_report(results: Dict):
    """Print formatted validation report"""
    print("=" * 70)
    print("J5A SHERLOCK QUEUE VALIDATION REPORT")
    print("=" * 70)
    print()

    print(f"📦 Total Packages: {results['total_packages']}")
    print(f"🔬 Sample Size: {results['sample_size']}")
    print()

    print("📊 VALIDATION RESULTS:")
    print("-" * 70)
    print(f"  Format Compliance:  {results['format_success_rate']:.1f}%")
    print(f"  Execution Viability: {results['viability_rate']:.1f}%")
    print(f"  URL Validity:       {results['url_validity_rate']:.1f}%")
    print(f"  Overall Success:    {results['overall_success_rate']:.1f}%")
    print()

    # Determine viability
    if results['overall_success_rate'] >= 80:
        print("✅ PROCESSING VIABLE - Queue ready for execution")
    elif results['overall_success_rate'] >= 60:
        print("⚠️  PROCESSING MARGINAL - Review warnings before execution")
    else:
        print("❌ PROCESSING NOT VIABLE - Address errors before execution")
    print()

    # Sample details
    print("📋 SAMPLE VALIDATION DETAILS:")
    print("-" * 70)

    for i, sample in enumerate(results['samples'], 1):
        print(f"\nSample {i}: Package {sample['package_id']} - {sample['target_name'][:50]}")
        print(f"  Type: {sample['package_type']}, Priority: {sample['priority']}")

        # Format
        if sample['format_valid']:
            print(f"  ✅ Format: Valid")
        else:
            print(f"  ❌ Format: FAILED")
            for error in sample['format_errors']:
                print(f"     - {error}")

        # Viability
        viability = sample['viability']
        if viability['can_execute']:
            print(f"  ✅ Viability: Executable ({viability['estimated_duration_min']} min)")
        else:
            print(f"  ❌ Viability: NOT EXECUTABLE")

        if viability['warnings']:
            for warning in viability['warnings']:
                print(f"     ⚠️  {warning}")

        # URLs
        url_check = sample['url_check']
        print(f"  📡 URLs: {len(url_check['valid_urls'])} valid, {len(url_check['invalid_urls'])} invalid")

        if url_check['invalid_urls']:
            for url in url_check['invalid_urls']:
                print(f"     ❌ {url}")

    print()
    print("=" * 70)

    # Aggregate recommendations
    print("\n💡 RECOMMENDATIONS:")
    print("-" * 70)

    thermal_high = sum(1 for s in results['samples'] if s['viability']['thermal_risk'] == 'high')
    if thermal_high > 0:
        print(f"  🔥 {thermal_high} packages have high thermal risk (YouTube processing)")
        print(f"     → Schedule during off-hours when CPU temperature is low")

    long_duration = sum(1 for s in results['samples'] if s['viability']['estimated_duration_min'] > 60)
    if long_duration > 0:
        print(f"  ⏱️  {long_duration} packages have long execution times (>60 min)")
        print(f"     → Consider chunking or batch processing")

    format_failures = sum(1 for s in results['samples'] if not s['format_valid'])
    if format_failures > 0:
        print(f"  📋 {format_failures} packages have format errors")
        print(f"     → Review package generation logic in Targeting Officer")

    print()


def main():
    """Main execution"""
    queue_dir = Path("/home/johnny5/Johny5Alive/queue")

    print("Loading Sherlock packages from queue...")
    packages = load_queue_packages(queue_dir)

    if len(packages) == 0:
        print("❌ No Sherlock packages found in queue")
        return

    print(f"Found {len(packages)} packages")
    print()

    # Run statistical validation
    results = statistical_sample_validation(packages, sample_size=5)

    # Print report
    print_validation_report(results)

    # Save report
    report_file = f"sherlock_queue_validation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"📄 Full report saved: {report_file}")
    print()


if __name__ == "__main__":
    main()
