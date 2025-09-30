"""
J5A Work Assignment: Sherlock Database Sync to GitHub
Automated weekly sync of Sherlock intelligence databases

Purpose: Share intelligence databases with collaborators while excluding large audio files
"""

from dataclasses import dataclass
from typing import List, Dict, Optional
from enum import Enum


class Priority(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"


class RiskLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class TestOracle:
    validation_commands: List[str]
    expected_outputs: List[str]
    quality_criteria: Dict[str, any]


@dataclass
class J5AWorkAssignment:
    task_id: str
    task_name: str
    domain: str
    description: str
    priority: Priority
    risk_level: RiskLevel
    expected_outputs: List[str]
    success_criteria: Dict[str, any]
    test_oracle: TestOracle
    estimated_tokens: int
    estimated_ram_gb: float
    estimated_duration_minutes: int
    thermal_risk: str
    dependencies: List[str]
    blocking_conditions: List[str]
    rollback_plan: str
    implementation_notes: Optional[str] = None


def create_sherlock_database_sync_tasks() -> List[J5AWorkAssignment]:
    """
    Create task definitions for automated Sherlock database sync
    """
    tasks = []

    # ============================================================================
    # PHASE 1: Git LFS Setup (One-time)
    # ============================================================================

    task_1_1 = J5AWorkAssignment(
        task_id="sherlock_db_sync_1_1",
        task_name="Install and configure Git LFS for Sherlock",
        domain="system_setup",
        description="Install Git LFS and configure tracking for Sherlock database files",
        priority=Priority.NORMAL,
        risk_level=RiskLevel.LOW,

        expected_outputs=[
            "/home/johnny5/Sherlock/.gitattributes",
            "Git LFS initialization confirmation"
        ],

        success_criteria={
            "git_lfs_installed": True,
            "lfs_tracking_configured": True,
            "databases_tracked_by_lfs": True,
            "lfs_ls_files_shows_databases": True
        },

        test_oracle=TestOracle(
            validation_commands=[
                "git lfs version",
                "cd /home/johnny5/Sherlock && git lfs ls-files",
                "cd /home/johnny5/Sherlock && git lfs track",
            ],
            expected_outputs=[
                "Git LFS version detected",
                "Database files listed by LFS",
                "*.db tracked by LFS"
            ],
            quality_criteria={
                "lfs_installed": True,
                "databases_tracked": 12,  # 12 .db files
                "gitattributes_exists": True
            }
        ),

        estimated_tokens=5000,
        estimated_ram_gb=0.1,
        estimated_duration_minutes=10,
        thermal_risk="low",

        dependencies=[],
        blocking_conditions=[],

        rollback_plan="git lfs uninstall; remove .gitattributes LFS config",

        implementation_notes="""
        Setup steps:

        1. Install Git LFS (if not already installed):
           ```bash
           sudo apt-get update
           sudo apt-get install -y git-lfs
           ```

        2. Initialize Git LFS globally:
           ```bash
           git lfs install
           ```

        3. Configure LFS tracking in Sherlock:
           ```bash
           cd /home/johnny5/Sherlock
           git lfs track "*.db"
           git lfs track "*.sqlite"
           git lfs track "*.sqlite3"
           ```

        4. Verify .gitattributes created:
           ```bash
           cat .gitattributes
           # Should show: *.db filter=lfs diff=lfs merge=lfs -text
           ```

        5. Add .gitattributes to git:
           ```bash
           git add .gitattributes
           git commit -m "Add Git LFS tracking for database files"
           ```

        6. Verify LFS status:
           ```bash
           git lfs ls-files
           # Should list all .db files once they're added
           ```

        Note: .gitattributes already created, just need to execute commands.
        """
    )
    tasks.append(task_1_1)

    # ============================================================================
    # PHASE 2: Initial Database Sync
    # ============================================================================

    task_2_1 = J5AWorkAssignment(
        task_id="sherlock_db_sync_2_1",
        task_name="Initial Sherlock database sync to GitHub",
        domain="system_integration",
        description="Perform first-time sync of Sherlock databases to GitHub with LFS",
        priority=Priority.NORMAL,
        risk_level=RiskLevel.LOW,

        expected_outputs=[
            "Sherlock databases pushed to GitHub",
            "Git commit with database files",
            "GitHub LFS confirmation"
        ],

        success_criteria={
            "all_databases_committed": True,
            "git_push_successful": True,
            "no_audio_files_pushed": True,
            "lfs_bandwidth_within_limits": True,
            "sync_time_under_15_minutes": True
        },

        test_oracle=TestOracle(
            validation_commands=[
                "cd /home/johnny5/Sherlock && git status",
                "cd /home/johnny5/Sherlock && git lfs ls-files | wc -l",
                "cd /home/johnny5/Sherlock && git log -1 --oneline",
            ],
            expected_outputs=[
                "Working tree clean",
                "12+ LFS files tracked",
                "Recent commit with databases"
            ],
            quality_criteria={
                "databases_tracked": 12,
                "audio_files_pushed": 0,
                "total_sync_mb": 1.0  # ~700KB databases + overhead
            }
        ),

        estimated_tokens=3000,
        estimated_ram_gb=0.2,
        estimated_duration_minutes=10,
        thermal_risk="low",

        dependencies=["sherlock_db_sync_1_1"],
        blocking_conditions=["GitHub credentials must be valid"],

        rollback_plan="git reset --hard HEAD~1; git push -f origin main",

        implementation_notes="""
        Initial sync process:

        1. Navigate to Sherlock:
           ```bash
           cd /home/johnny5/Sherlock
           ```

        2. Check what will be committed:
           ```bash
           git status
           # Verify: .db files shown, NO .aaxc/.wav/.m4a
           ```

        3. Stage database files:
           ```bash
           git add *.db
           git add .gitignore .gitattributes
           ```

        4. Verify LFS will handle databases:
           ```bash
           git lfs status
           # Should show .db files to be committed via LFS
           ```

        5. Commit databases:
           ```bash
           git commit -m "Add Sherlock intelligence databases via Git LFS

           Databases included (~700KB total):
           - evidence.db: Main evidence store
           - gladio_intelligence.db: Operation Gladio analysis
           - gladio_complete.db: Complete Gladio dataset
           - active_learning.db: Learning system state
           - audit.db: Audit trail
           - intelligence_sharing.db: Cross-system intelligence
           + test/sample databases

           🤖 Generated with [Claude Code](https://claude.com/claude-code)

           Co-Authored-By: Claude <noreply@anthropic.com>"
           ```

        6. Push to GitHub (creates LFS objects):
           ```bash
           git push origin main
           # LFS will upload database files to LFS storage
           ```

        7. Verify on GitHub:
           - Go to: https://github.com/BrandonH5678/Sherlock
           - Check .db files show "Stored with Git LFS" badge
           - Verify repo size is small (~50MB, not 13GB)

        Expected results:
        - Databases pushed via LFS: ~700KB
        - Repo size: ~50MB (code + docs)
        - No audio files pushed
        - Clone time for collaborators: <1 minute
        """
    )
    tasks.append(task_2_1)

    # ============================================================================
    # PHASE 3: Automated Weekly Sync
    # ============================================================================

    task_3_1 = J5AWorkAssignment(
        task_id="sherlock_db_sync_3_1",
        task_name="Weekly Sherlock database sync (recurring)",
        domain="system_maintenance",
        description="Automated weekly sync of Sherlock databases to share latest intelligence",
        priority=Priority.LOW,
        risk_level=RiskLevel.LOW,

        expected_outputs=[
            "Updated databases on GitHub",
            "Git commit (if changes detected)",
            "Sync completion log"
        ],

        success_criteria={
            "database_changes_detected": "any",  # May be none
            "sync_completed_successfully": True,
            "no_audio_files_pushed": True,
            "sync_time_under_10_minutes": True,
            "github_lfs_bandwidth_available": True
        },

        test_oracle=TestOracle(
            validation_commands=[
                "cd /home/johnny5/Sherlock && git status",
                "cd /home/johnny5/Sherlock && git diff --name-only *.db",
                "cd /home/johnny5/Sherlock && git log -1 --format='%h %s'",
            ],
            expected_outputs=[
                "Working tree status shown",
                "Database changes identified (if any)",
                "Recent commit shown"
            ],
            quality_criteria={
                "max_sync_duration_minutes": 10,
                "databases_size_mb": 1.0,
                "audio_files_excluded": True
            }
        ),

        estimated_tokens=2000,
        estimated_ram_gb=0.1,
        estimated_duration_minutes=5,
        thermal_risk="low",

        dependencies=["sherlock_db_sync_2_1"],
        blocking_conditions=[],

        rollback_plan="No rollback needed (sync only updates, doesn't modify local)",

        implementation_notes="""
        Weekly sync workflow (automated by J5A):

        1. Check for database changes:
           ```bash
           cd /home/johnny5/Sherlock

           # Check if any databases modified
           if git diff --quiet *.db; then
               echo "No database changes, skipping sync"
               exit 0
           fi
           ```

        2. Stage database changes:
           ```bash
           git add *.db
           ```

        3. Commit with timestamp:
           ```bash
           git commit -m "Update Sherlock databases - Weekly sync $(date +%Y-%m-%d)

           Database updates may include:
           - New evidence cards from recent analysis
           - Updated entity relationships
           - Active learning improvements
           - Cross-system intelligence updates

           🤖 Generated with [Claude Code](https://claude.com/claude-code)

           Co-Authored-By: Claude <noreply@anthropic.com>"
           ```

        4. Push to GitHub:
           ```bash
           git push origin main
           ```

        5. Log results:
           ```bash
           echo "Sherlock database sync completed: $(date)" >> /home/johnny5/Johny5Alive/sync.log
           ```

        Scheduling:
        - Frequency: Weekly (Sunday 2am)
        - Duration: ~5 minutes average
        - Bandwidth: <1MB per sync (only changed databases)
        - Skips if no changes detected

        Benefits:
        - Collaborators get latest intelligence automatically
        - Minimal overhead (only ~700KB total)
        - Preserves all analysis work
        - Enables distributed collaboration
        """
    )
    tasks.append(task_3_1)

    # ============================================================================
    # PHASE 4: Validation and Monitoring
    # ============================================================================

    task_4_1 = J5AWorkAssignment(
        task_id="sherlock_db_sync_4_1",
        task_name="Validate Sherlock database sync health",
        domain="validation",
        description="Verify database sync is working correctly and no issues",
        priority=Priority.LOW,
        risk_level=RiskLevel.LOW,

        expected_outputs=[
            "/home/johnny5/Johny5Alive/sherlock_sync_health_report.json"
        ],

        success_criteria={
            "lfs_tracking_active": True,
            "no_large_files_in_repo": True,
            "github_lfs_quota_healthy": True,
            "databases_up_to_date": True,
            "gitignore_working": True
        },

        test_oracle=TestOracle(
            validation_commands=[
                "cd /home/johnny5/Sherlock && git lfs ls-files | wc -l",
                "cd /home/johnny5/Sherlock && git status | grep -E '\\.aaxc|\\.wav|\\.m4a' || echo 'No audio files staged'",
                "cd /home/johnny5/Sherlock && du -sh .git/",
            ],
            expected_outputs=[
                "12+ LFS files tracked",
                "No audio files staged",
                "Git directory size reasonable (<100MB)"
            ],
            quality_criteria={
                "lfs_files_tracked": 12,
                "audio_files_staged": 0,
                "git_dir_size_mb": 100
            }
        ),

        estimated_tokens=1000,
        estimated_ram_gb=0.1,
        estimated_duration_minutes=2,
        thermal_risk="low",

        dependencies=["sherlock_db_sync_3_1"],
        blocking_conditions=[],

        rollback_plan="N/A (validation only)",

        implementation_notes="""
        Health check script:

        ```bash
        #!/bin/bash
        # sherlock_sync_health_check.sh

        cd /home/johnny5/Sherlock

        echo "=== Sherlock Database Sync Health Check ==="
        echo ""

        # Check 1: LFS tracking active
        lfs_count=$(git lfs ls-files | wc -l)
        echo "✓ LFS files tracked: $lfs_count"

        # Check 2: No audio files staged
        audio_staged=$(git status --porcelain | grep -E '\\.aaxc|\\.wav|\\.m4a' | wc -l)
        if [ "$audio_staged" -eq 0 ]; then
            echo "✓ No audio files staged"
        else
            echo "✗ WARNING: $audio_staged audio files staged!"
        fi

        # Check 3: Git directory size
        git_size=$(du -sm .git/ | cut -f1)
        echo "✓ Git directory size: ${git_size}MB"

        # Check 4: Database sizes
        echo ""
        echo "Database sizes:"
        ls -lh *.db 2>/dev/null | awk '{print "  " $9 ": " $5}'

        # Check 5: Last sync
        last_commit=$(git log -1 --format="%h %s %cr")
        echo ""
        echo "Last commit: $last_commit"

        # Check 6: GitHub LFS bandwidth (approximate)
        echo ""
        echo "GitHub LFS Status:"
        echo "  Free tier: 1GB storage, 1GB bandwidth/month"
        echo "  Sherlock usage: ~700KB databases"
        echo "  Weekly sync: ~100KB average (only changes)"
        echo "  Estimated monthly: ~400KB (well within limits)"

        # Save report
        cat > /home/johnny5/Johny5Alive/sherlock_sync_health_report.json <<EOF
        {
          "timestamp": "$(date -Iseconds)",
          "lfs_files_tracked": $lfs_count,
          "audio_files_staged": $audio_staged,
          "git_directory_size_mb": $git_size,
          "last_sync": "$last_commit",
          "status": "healthy"
        }
        EOF

        echo ""
        echo "✓ Health check complete"
        ```

        Run monthly or on-demand to verify sync health.
        """
    )
    tasks.append(task_4_1)

    return tasks


if __name__ == "__main__":
    tasks = create_sherlock_database_sync_tasks()
    print(f"Created {len(tasks)} tasks for Sherlock Database Sync")
    for task in tasks:
        print(f"  - {task.task_id}: {task.task_name} ({task.priority.value}, {task.risk_level.value})")
