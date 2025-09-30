#!/usr/bin/env python3
"""
J5A Thermal Check Utility
Quick thermal verification for system operations
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from thermal_monitor import thermal_check_required

def main():
    """Run thermal check for specified operation"""

    if len(sys.argv) < 2:
        operation_name = "System Operation"
    else:
        operation_name = " ".join(sys.argv[1:])

    print("🤖 J5A Thermal Safety Protocol")
    print("=" * 50)

    # Perform thermal check
    allowed = thermal_check_required(operation_name)

    if allowed:
        print("\n✅ THERMAL CHECK PASSED")
        print("🚀 Operation approved to proceed")
        sys.exit(0)
    else:
        print("\n❌ THERMAL CHECK FAILED")
        print("🚨 Operation must be deferred")
        print("\n📋 Next Steps:")
        print("  1. Implement external cooling")
        print("  2. Reduce system load")
        print("  3. Wait for temperatures to stabilize")
        print("  4. Re-run thermal check")
        sys.exit(1)

if __name__ == "__main__":
    main()