#!/usr/bin/env python3
"""
AI Operator Helper Script for Johny5Alive
Provides easy integration of multi-system protocol management for AI operations.
"""

import sys
import json
from pathlib import Path
from typing import Dict

# Add src directory to path for imports
sys.path.append(str(Path(__file__).parent / "src"))

from protocol_manager import Johny5ProtocolManager


def load_protocols():
    """Load and display current protocols for AI operator"""
    print("🤖 Loading Johny5Alive Multi-System Protocols...")
    print("=" * 60)

    manager = Johny5ProtocolManager()
    context = manager.inject_session_context()

    print("🏗️ SYSTEM OVERVIEW:")
    overview = context['system_overview']
    print(f"   Machine: {overview['machine']}")
    print(f"   RAM: {overview['current_ram']}GB (→ {overview['planned_upgrade']})")
    print(f"   Active Systems: {len(overview['active_systems'])}")
    for name, system in overview['active_systems'].items():
        print(f"      {name}: {system['status']} ({system['priority']})")

    print(f"\n💾 RESOURCE STATUS:")
    resources = context['resource_status']
    memory = resources['memory']
    print(f"   Memory: {memory['used_gb']:.1f}GB used / {memory['total_gb']:.1f}GB total ({memory['percent_used']:.1f}%)")
    print(f"   Business Hours: {'YES' if resources['business_hours_active'] else 'NO'}")
    print(f"   Priority: {resources['resource_priority']}")
    print(f"   Heavy Processing: {'ALLOWED' if resources['heavy_processing_allowed'] else 'RESTRICTED'}")

    print(f"\n🎯 DEVELOPMENT STATUS:")
    dev_status = context['development_status']
    print(f"   Current Phase: {dev_status['current_phase']}")
    print(f"   Progress: {dev_status['phase_progress']['completion_percent']}% complete")
    print(f"   ({dev_status['phase_progress']['completed']}/{dev_status['phase_progress']['total_milestones']} milestones)")

    print(f"\n📋 PRIORITY MATRIX:")
    priority = context['priority_matrix']
    print(f"   Primary: {priority['primary']}")
    print(f"   Secondary: {priority['secondary']}")
    print(f"   Background: {priority['background']}")

    if 'restrictions' in priority:
        print("   ⚠️ Current Restrictions:")
        for restriction in priority['restrictions']:
            print(f"      • {restriction}")

    if 'opportunities' in priority:
        print("   ✅ Current Opportunities:")
        for opportunity in priority['opportunities']:
            print(f"      • {opportunity}")

    print(f"\n🔄 MILESTONE TRACKING:")
    milestones = context['milestone_tracking']
    print(f"   Manual Update Required: {'YES' if milestones['update_required'] else 'NO'}")
    print(f"   Last Update: {milestones['last_manual_update']}")
    print(f"   Completion Rate: {milestones['completion_rate']}%")

    if milestones['pending_milestones']:
        print("   📝 Pending Documentation:")
        for milestone in milestones['pending_milestones']:
            print(f"      • {milestone}")

    return manager


def before_development_operation(operation_type="development", system="multi-system", milestone=None):
    """Execute pre-operation protocol checks"""
    print(f"\n🚀 STARTING {operation_type.upper()} OPERATION ({system})")
    print("=" * 60)

    manager = Johny5ProtocolManager()

    # Check for required manual updates
    context = manager.inject_session_context()
    if context['milestone_tracking']['update_required']:
        print("⚠️ MANUAL UPDATE REQUIRED BEFORE PROCEEDING!")
        print("   The following milestones need documentation:")
        for milestone in context['milestone_tracking']['pending_milestones']:
            print(f"      • {milestone}")
        print("   Please update JOHNY5_AI_OPERATOR_MANUAL.md first")
        return False

    # Resource availability check
    resources = context['resource_status']
    if resources['business_hours_active'] and system == "sherlock":
        print("⚠️ BUSINESS HOURS ACTIVE - SHERLOCK RESTRICTED")
        print("   Heavy Sherlock processing should be deferred until after 7pm")
        proceed = input("   Proceed with light processing only? (y/N): ")
        if proceed.lower() != 'y':
            return False

    # System status checks
    print("✅ PRE-OPERATION CHECKS:")
    print(f"   Resource priority: {resources['resource_priority']}")
    print(f"   Memory available: {resources['memory']['available_gb']:.1f}GB")
    print(f"   LibreOffice status: {'RUNNING' if resources['libreoffice_running']['running'] else 'AVAILABLE'}")

    return True


def after_development_operation(operation_type="development", system="multi-system", milestone_completed=None, details=None):
    """Execute post-operation protocol and milestone tracking"""
    print(f"\n✅ COMPLETED {operation_type.upper()} OPERATION ({system})")
    print("=" * 60)

    manager = Johny5ProtocolManager()

    # Log milestone completion if provided
    if milestone_completed:
        current_phase = "Phase 1: Foundation"  # TODO: Make this dynamic
        completion_entry = manager.log_milestone_completion(
            milestone=milestone_completed,
            phase=current_phase,
            details=details or {}
        )

        print(f"📝 MILESTONE COMPLETED: {milestone_completed}")
        print(f"   Phase: {current_phase}")
        print(f"   Completed at: {completion_entry['completed_at']}")
        print(f"   Manual update required: {'YES' if completion_entry['requires_manual_update'] else 'NO'}")

        # Prompt for immediate manual update
        if completion_entry['requires_manual_update']:
            print("\n🔄 MANUAL UPDATE REQUIRED:")
            print("   Please update JOHNY5_AI_OPERATOR_MANUAL.md with this milestone completion")
            print("   Run update_manual_completed() when documentation is updated")

    # Display session summary
    print(f"\n📊 SESSION SUMMARY:")
    session_log = manager.session_log
    operations = len([log for log in session_log if log['action'] in ['development_operation', 'milestone_completed']])
    milestones = len([log for log in session_log if log['action'] == 'milestone_completed'])

    print(f"   Operations completed: {operations}")
    print(f"   Milestones achieved: {milestones}")
    print(f"   Session duration: {len(session_log)} actions logged")

    return True


def complete_milestone(milestone_name: str, phase: str = "Phase 1: Foundation", details: Dict = None):
    """Mark a milestone as completed and require manual update"""
    manager = Johny5ProtocolManager()

    completion_entry = manager.log_milestone_completion(
        milestone=milestone_name,
        phase=phase,
        details=details or {}
    )

    print(f"✅ MILESTONE COMPLETED: {milestone_name}")
    print(f"📝 MANUAL UPDATE REQUIRED")
    print(f"   Please update JOHNY5_AI_OPERATOR_MANUAL.md")
    print(f"   Run confirm_manual_updated() when complete")

    return completion_entry


def confirm_manual_updated():
    """Confirm that the manual has been updated with recent milestones"""
    manager = Johny5ProtocolManager()
    manager.update_manual_completed()

    print("✅ MANUAL UPDATE CONFIRMED")
    print("   All recent milestones marked as documented")

    return True


def get_status():
    """Get comprehensive system status"""
    manager = Johny5ProtocolManager()
    context = manager.inject_session_context()

    return {
        "system_overview": context['system_overview'],
        "resource_status": context['resource_status'],
        "development_status": context['development_status'],
        "priority_matrix": context['priority_matrix'],
        "milestone_tracking": context['milestone_tracking']
    }


def main():
    """Main CLI interface"""
    if len(sys.argv) < 2:
        print("Johny5Alive AI Operator Helper")
        print("Usage:")
        print("  python ai_operator_helper.py status        - Show system status")
        print("  python ai_operator_helper.py protocols     - Load protocols")
        print("  python ai_operator_helper.py milestone <name> - Complete milestone")
        print("  python ai_operator_helper.py updated       - Confirm manual updated")
        sys.exit(1)

    command = sys.argv[1]

    if command == "status":
        status = get_status()
        print(json.dumps(status, indent=2))

    elif command == "protocols":
        load_protocols()

    elif command == "milestone":
        if len(sys.argv) < 3:
            print("Error: Milestone name required")
            sys.exit(1)
        milestone_name = sys.argv[2]
        complete_milestone(milestone_name)

    elif command == "updated":
        confirm_manual_updated()

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()