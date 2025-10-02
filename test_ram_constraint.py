#!/usr/bin/env python3
"""
Test RAM Constraint Logic

Verify that J5A properly blocks multi-speaker audio until RAM upgrade.
"""

import json
from pathlib import Path

def analyze_queue_with_ram_constraint():
    """Analyze which packages will be blocked by RAM constraint"""
    queue_dir = Path("/home/johnny5/Johny5Alive/queue")

    blocked_types = ["podcast", "interview_series", "youtube", "multi_speaker_audio"]
    allowed_types = ["document", "book", "single_speaker_audio", "visual_media"]

    blocked = []
    allowed = []

    for pkg_file in queue_dir.glob("sherlock_pkg_*.json"):
        with open(pkg_file) as f:
            pkg = json.load(f)
            package_type = pkg.get('package_type', '').lower()

            if package_type in blocked_types:
                blocked.append({
                    'package_id': pkg['package_id'],
                    'target_name': pkg['target_name'],
                    'package_type': package_type,
                    'priority': pkg['priority']
                })
            else:
                allowed.append({
                    'package_id': pkg['package_id'],
                    'target_name': pkg['target_name'],
                    'package_type': package_type,
                    'priority': pkg['priority']
                })

    print("=" * 70)
    print("RAM CONSTRAINT ANALYSIS - Sherlock Queue")
    print("=" * 70)
    print()

    print(f"🚫 BLOCKED (Multi-speaker audio - requires RAM upgrade): {len(blocked)}")
    print("-" * 70)
    for pkg in blocked:
        print(f"  [{pkg['package_id']}] {pkg['target_name'][:50]}")
        print(f"      Type: {pkg['package_type']}, Priority: {pkg['priority']}")

    print()
    print(f"✅ ALLOWED (Document/print/visual/single-speaker): {len(allowed)}")
    print("-" * 70)
    for pkg in allowed[:10]:  # Show first 10
        print(f"  [{pkg['package_id']}] {pkg['target_name'][:50]}")
        print(f"      Type: {pkg['package_type']}, Priority: {pkg['priority']}")

    if len(allowed) > 10:
        print(f"  ... and {len(allowed) - 10} more")

    print()
    print("=" * 70)
    print(f"Summary: {len(allowed)} can execute now, {len(blocked)} deferred until RAM upgrade")
    print("=" * 70)
    print()

    # Show priority breakdown
    blocked_p1 = [p for p in blocked if p['priority'] == 1]
    allowed_p1 = [p for p in allowed if p['priority'] == 1]

    if blocked_p1:
        print(f"⚠️  {len(blocked_p1)} Priority 1 (Critical) packages blocked by RAM constraint:")
        for pkg in blocked_p1:
            print(f"   - {pkg['target_name']} ({pkg['package_type']})")
        print()

    if allowed_p1:
        print(f"✅ {len(allowed_p1)} Priority 1 (Critical) packages can execute now:")
        for pkg in allowed_p1:
            print(f"   - {pkg['target_name']} ({pkg['package_type']})")
        print()

if __name__ == "__main__":
    analyze_queue_with_ram_constraint()
