#!/usr/bin/env python3
"""
J5A Nightshift Summary Generator
Generates completion report after queue processing
"""

import os
import sys
import json
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

# Configuration
QUEUE_DB = "/home/johnny5/Johny5Alive/j5a_queue_manager.db"
LOGS_DIR = Path("/home/johnny5/Johny5Alive/j5a-nightshift/ops/logs")
SUMMARIES_DIR = LOGS_DIR / "summaries"
LATEST_LOG = LOGS_DIR / "nightshift_20251008_005533.log"  # Will auto-detect latest


class NightshiftSummary:
    """Generate summary of Night Shift processing run"""

    def __init__(self, db_path: str = QUEUE_DB):
        """Initialize summary generator"""
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row

        # Create summaries directory
        SUMMARIES_DIR.mkdir(parents=True, exist_ok=True)

    def generate_summary(self, start_time: Optional[datetime] = None) -> str:
        """
        Generate markdown summary of processing run

        Args:
            start_time: Start of processing window (default: last 24 hours)

        Returns:
            Markdown formatted summary
        """
        if start_time is None:
            start_time = datetime.now() - timedelta(hours=24)

        # Query recent jobs
        recent_jobs = self._get_recent_jobs(start_time)

        # Calculate statistics
        stats = self._calculate_stats(recent_jobs)

        # Get thermal data
        thermal_data = self._get_thermal_stats()

        # Build summary
        summary = self._build_summary_markdown(stats, thermal_data, start_time)

        return summary

    def _get_recent_jobs(self, since: datetime) -> List[Dict[str, Any]]:
        """Get jobs processed since specified time"""
        cursor = self.conn.execute("""
            SELECT *
            FROM task_executions
            WHERE end_time >= ?
            ORDER BY end_time DESC
        """, (since.isoformat(),))

        return [dict(row) for row in cursor.fetchall()]

    def _calculate_stats(self, jobs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate processing statistics"""
        stats = {
            "total": len(jobs),
            "completed": 0,
            "parked": 0,
            "deferred": 0,
            "failed": 0,
            "insufficient_evidence": 0,
            "processing_times": [],
            "by_type": {},
            "by_class": {}
        }

        for job in jobs:
            status = job.get("status", "unknown")

            # Count by status
            if status == "completed":
                stats["completed"] += 1
            elif status == "parked":
                stats["parked"] += 1
            elif status == "deferred":
                stats["deferred"] += 1
            elif status == "insufficient_evidence":
                stats["insufficient_evidence"] += 1
            else:
                stats["failed"] += 1

            # Calculate processing time
            if job.get("start_time") and job.get("end_time"):
                start = datetime.fromisoformat(job["start_time"])
                end = datetime.fromisoformat(job["end_time"])
                duration = (end - start).total_seconds()
                stats["processing_times"].append(duration)

        # Calculate success rate
        processable = stats["total"] - stats["parked"]
        if processable > 0:
            stats["success_rate"] = (stats["completed"] + stats["insufficient_evidence"]) / processable
        else:
            stats["success_rate"] = 0.0

        # Calculate avg processing time
        if stats["processing_times"]:
            stats["avg_processing_time"] = sum(stats["processing_times"]) / len(stats["processing_times"])
            stats["max_processing_time"] = max(stats["processing_times"])
            stats["min_processing_time"] = min(stats["processing_times"])
        else:
            stats["avg_processing_time"] = 0
            stats["max_processing_time"] = 0
            stats["min_processing_time"] = 0

        return stats

    def _get_thermal_stats(self) -> Dict[str, Any]:
        """Get thermal statistics (if available)"""
        try:
            import subprocess
            result = subprocess.run(
                ['sensors'],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if 'Package id 0' in line:
                        import re
                        match = re.search(r'\+(\d+\.\d+)°C', line)
                        if match:
                            temp = float(match.group(1))
                            return {
                                "current_temp": temp,
                                "status": self._thermal_status(temp)
                            }
        except Exception:
            pass

        return {"current_temp": None, "status": "unknown"}

    def _thermal_status(self, temp: float) -> str:
        """Determine thermal status"""
        if temp < 70:
            return "EXCELLENT"
        elif temp < 75:
            return "GOOD"
        elif temp < 80:
            return "WARM"
        elif temp < 85:
            return "HOT"
        else:
            return "CRITICAL"

    def _build_summary_markdown(
        self,
        stats: Dict[str, Any],
        thermal: Dict[str, Any],
        start_time: datetime
    ) -> str:
        """Build markdown summary"""
        lines = []

        # Header
        lines.append("# J5A Nightshift Processing Summary")
        lines.append("")
        lines.append(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"**Processing Window**: Since {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")
        lines.append("---")
        lines.append("")

        # Processing Statistics
        lines.append("## Processing Statistics")
        lines.append("")
        lines.append(f"- **Total Jobs**: {stats['total']}")
        lines.append(f"- ✅ **Completed**: {stats['completed']}")
        lines.append(f"- 📦 **Parked** (Phase 2): {stats['parked']}")
        lines.append(f"- ⏸️  **Deferred** (thermal/resource): {stats['deferred']}")
        lines.append(f"- ⚠️  **Insufficient Evidence**: {stats['insufficient_evidence']}")
        lines.append(f"- ❌ **Failed**: {stats['failed']}")
        lines.append("")

        # Success Rate
        if stats['total'] > 0:
            success_pct = stats['success_rate'] * 100
            target_pct = 85.0

            lines.append("### Success Rate")
            lines.append("")
            lines.append(f"- **Phase 1 Success Rate**: {success_pct:.1f}%")
            lines.append(f"- **Target**: ≥{target_pct:.0f}%")

            if success_pct >= target_pct:
                lines.append(f"- **Status**: 🎯 **TARGET ACHIEVED**")
            else:
                lines.append(f"- **Status**: ⚠️  Below target (needs {target_pct - success_pct:.1f}% improvement)")
            lines.append("")

        # Processing Time
        if stats['avg_processing_time'] > 0:
            lines.append("### Processing Time")
            lines.append("")
            lines.append(f"- **Average**: {self._format_duration(stats['avg_processing_time'])}")
            lines.append(f"- **Minimum**: {self._format_duration(stats['min_processing_time'])}")
            lines.append(f"- **Maximum**: {self._format_duration(stats['max_processing_time'])}")
            lines.append("")

        # Thermal Status
        lines.append("## System Health")
        lines.append("")

        if thermal["current_temp"]:
            temp = thermal["current_temp"]
            status = thermal["status"]

            if status == "EXCELLENT":
                icon = "✅"
            elif status in ["GOOD", "WARM"]:
                icon = "⚠️"
            else:
                icon = "🔥"

            lines.append(f"- **CPU Temperature**: {icon} {temp:.1f}°C ({status})")
        else:
            lines.append("- **CPU Temperature**: ⚠️  Unable to read")

        lines.append(f"- **Thermal Limit**: 87°C (critical)")
        lines.append("")

        # Next Run
        lines.append("## Next Scheduled Run")
        lines.append("")
        next_run = self._get_next_run()
        if next_run:
            lines.append(f"- **Next Run**: {next_run.strftime('%Y-%m-%d %H:%M:%S')}")
            time_until = next_run - datetime.now()
            lines.append(f"- **Time Until**: {self._format_duration(time_until.total_seconds())}")
        else:
            lines.append("- **Next Run**: Not scheduled (manual execution)")
        lines.append("")

        # Recommendations
        if stats['deferred'] > 0 or stats['failed'] > 0:
            lines.append("## Recommendations")
            lines.append("")

            if stats['deferred'] > 5:
                lines.append(f"- ⚠️  **{stats['deferred']} deferred jobs** - Investigate root causes")

            if stats['failed'] > 0:
                lines.append(f"- ❌ **{stats['failed']} failed jobs** - Review error logs")

            if stats['total'] < 10:
                lines.append("- ℹ️  **Small sample size** - Run more jobs to validate success rate")

            lines.append("")

        # Footer
        lines.append("---")
        lines.append("")
        lines.append("*Generated by J5A Nightshift Automation*")
        lines.append("")

        return "\n".join(lines)

    def _format_duration(self, seconds: float) -> str:
        """Format duration in human-readable format"""
        if seconds < 60:
            return f"{seconds:.0f}s"
        elif seconds < 3600:
            minutes = seconds / 60
            return f"{minutes:.1f}m"
        else:
            hours = seconds / 3600
            return f"{hours:.1f}h"

    def _get_next_run(self) -> Optional[datetime]:
        """Get next scheduled run time"""
        # Calculate next 7pm
        now = datetime.now()
        next_run = now.replace(hour=19, minute=0, second=0, microsecond=0)

        if next_run <= now:
            # Today's 7pm has passed, schedule for tomorrow
            next_run += timedelta(days=1)

        return next_run

    def save_summary(self, summary: str, filename: Optional[str] = None) -> Path:
        """
        Save summary to file

        Args:
            summary: Summary markdown content
            filename: Custom filename (default: YYYY-MM-DD.md)

        Returns:
            Path to saved summary
        """
        if filename is None:
            filename = f"{datetime.now().strftime('%Y-%m-%d')}.md"

        filepath = SUMMARIES_DIR / filename

        with open(filepath, 'w') as f:
            f.write(summary)

        return filepath

    def close(self):
        """Close database connection"""
        self.conn.close()


def main():
    """Main entry point"""
    # Generate summary
    generator = NightshiftSummary()

    try:
        # Generate for last 24 hours (or since last run)
        summary = generator.generate_summary()

        # Save to file
        filepath = generator.save_summary(summary)

        # Print summary to stdout
        print(summary)

        print(f"\nSummary saved to: {filepath}")

    finally:
        generator.close()


if __name__ == "__main__":
    main()
