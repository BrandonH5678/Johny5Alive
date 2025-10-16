#!/usr/bin/env python3
"""
Export cache statistics for PROMPT_LIBRARY.html

Runs token_monitor and exports cache efficiency data to JSON
for real-time display in the prompt library interface.
"""

import json
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.token_monitor import TokenMonitor


def export_cache_stats(output_path: str = "cache_stats.json"):
    """Export current cache statistics to JSON for HTML consumption"""

    # Initialize token monitor
    monitor = TokenMonitor(db_path="/home/johnny5/Johny5Alive/token_monitor.db")

    # Get HTML-ready cache efficiency data
    stats = monitor.get_cache_efficiency_for_html()

    # Add timestamp metadata
    stats['updated_at'] = __import__('datetime').datetime.now().isoformat()

    # Write to JSON file
    output_file = Path(__file__).parent.parent / output_path
    with open(output_file, 'w') as f:
        json.dump(stats, f, indent=2)

    return stats


if __name__ == "__main__":
    stats = export_cache_stats()

    print("✅ Cache statistics exported:")
    print(f"   Cache hit rate: {stats['cache_hit_rate']}%")
    print(f"   Tokens saved: {stats['tokens_saved']:,}")
    print(f"   Cost savings: ${stats['cost_savings']}")
    print(f"   Status: {stats['status']}")
