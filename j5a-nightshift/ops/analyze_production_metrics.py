#!/usr/bin/env python3
"""
Production Metrics Analyzer for Night Shift
Analyzes job processing results and generates production validation reports
"""

import os
import json
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from collections import defaultdict

QUEUE_DB = "/home/johnny5/Johny5Alive/j5a_queue_manager.db"
REPORTS_DIR = Path("/home/johnny5/Johny5Alive/j5a-nightshift/ops/reports")


class ProductionMetricsAnalyzer:
    """Analyze production metrics for Night Shift validation"""

    def __init__(self, db_path: str = QUEUE_DB):
        """Initialize analyzer"""
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row

        # Create reports directory
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    def analyze_period(self, days: int = 7) -> Dict[str, Any]:
        """
        Analyze jobs processed in the last N days

        Args:
            days: Number of days to analyze

        Returns:
            Metrics dictionary
        """
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()

        # Get all jobs in period
        cursor = self.conn.execute("""
            SELECT *
            FROM task_executions
            WHERE end_time >= ?
            ORDER BY end_time DESC
        """, (cutoff,))

        jobs = [dict(row) for row in cursor.fetchall()]

        # Calculate metrics
        metrics = {
            "period_days": days,
            "analysis_date": datetime.now().isoformat(),
            "total_jobs": len(jobs),
            "by_status": self._count_by_status(jobs),
            "success_rate": self._calculate_success_rate(jobs),
            "processing_times": self._analyze_processing_times(jobs),
            "daily_breakdown": self._daily_breakdown(jobs),
            "failure_analysis": self._analyze_failures(jobs),
            "recommendations": []
        }

        # Add recommendations
        metrics["recommendations"] = self._generate_recommendations(metrics)

        return metrics

    def _count_by_status(self, jobs: List[Dict]) -> Dict[str, int]:
        """Count jobs by status"""
        counts = defaultdict(int)
        for job in jobs:
            counts[job["status"]] += 1
        return dict(counts)

    def _calculate_success_rate(self, jobs: List[Dict]) -> Dict[str, Any]:
        """Calculate success rate"""
        if not jobs:
            return {"rate": 0.0, "completed": 0, "total": 0}

        completed = sum(1 for j in jobs if j["status"] in ["completed", "insufficient_evidence"])
        parked = sum(1 for j in jobs if j["status"] == "parked")
        processable = len(jobs) - parked

        if processable == 0:
            return {"rate": 0.0, "completed": 0, "total": 0, "parked": parked}

        rate = completed / processable

        return {
            "rate": rate,
            "percentage": f"{rate * 100:.1f}%",
            "completed": completed,
            "processable": processable,
            "parked": parked,
            "meets_target": rate >= 0.85
        }

    def _analyze_processing_times(self, jobs: List[Dict]) -> Dict[str, Any]:
        """Analyze processing times"""
        times = []

        for job in jobs:
            if job.get("start_time") and job.get("end_time"):
                start = datetime.fromisoformat(job["start_time"])
                end = datetime.fromisoformat(job["end_time"])
                duration = (end - start).total_seconds()
                times.append(duration)

        if not times:
            return {"avg": 0, "min": 0, "max": 0, "total": 0}

        return {
            "avg_seconds": sum(times) / len(times),
            "avg_minutes": sum(times) / len(times) / 60,
            "min_seconds": min(times),
            "max_seconds": max(times),
            "total_jobs_timed": len(times)
        }

    def _daily_breakdown(self, jobs: List[Dict]) -> List[Dict[str, Any]]:
        """Break down jobs by day"""
        by_day = defaultdict(lambda: {"completed": 0, "failed": 0, "parked": 0, "deferred": 0})

        for job in jobs:
            if job.get("end_time"):
                date = job["end_time"][:10]  # YYYY-MM-DD
                status = job["status"]

                if status == "completed":
                    by_day[date]["completed"] += 1
                elif status == "failed":
                    by_day[date]["failed"] += 1
                elif status == "parked":
                    by_day[date]["parked"] += 1
                elif status == "deferred":
                    by_day[date]["deferred"] += 1

        # Convert to list and sort by date
        breakdown = [
            {"date": date, **counts}
            for date, counts in by_day.items()
        ]
        breakdown.sort(key=lambda x: x["date"], reverse=True)

        return breakdown

    def _analyze_failures(self, jobs: List[Dict]) -> Dict[str, Any]:
        """Analyze failure patterns"""
        failed = [j for j in jobs if j["status"] == "failed"]

        if not failed:
            return {"count": 0, "patterns": []}

        # Extract error patterns
        error_patterns = defaultdict(int)
        for job in failed:
            error = job.get("error_log", "Unknown error")
            if error:
                # Simplify error message to pattern
                pattern = error[:100] if error else "Unknown"
                error_patterns[pattern] += 1

        patterns = [
            {"error": pattern, "count": count}
            for pattern, count in error_patterns.items()
        ]
        patterns.sort(key=lambda x: x["count"], reverse=True)

        return {
            "count": len(failed),
            "patterns": patterns[:5]  # Top 5
        }

    def _generate_recommendations(self, metrics: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on metrics"""
        recommendations = []

        # Check success rate
        success_rate = metrics["success_rate"]
        if success_rate["meets_target"]:
            recommendations.append("✅ SUCCESS: Phase 1 success rate target (≥85%) achieved!")
        else:
            target_rate = 85.0
            current_rate = success_rate["rate"] * 100
            recommendations.append(f"⚠️  Success rate {current_rate:.1f}% below target {target_rate}% - needs optimization")

        # Check sample size
        if metrics["total_jobs"] < 20:
            recommendations.append(f"ℹ️  Sample size ({metrics['total_jobs']} jobs) below recommended 20+ for validation")

        # Check failures
        failures = metrics["by_status"].get("failed", 0)
        if failures > 0:
            recommendations.append(f"⚠️  {failures} failed jobs need root cause analysis")

        # Check deferred jobs
        deferred = metrics["by_status"].get("deferred", 0)
        if deferred > 10:
            recommendations.append(f"⚠️  {deferred} deferred jobs may indicate systemic issues")

        # Check parked jobs
        parked = metrics["by_status"].get("parked", 0)
        if parked > 0:
            recommendations.append(f"ℹ️  {parked} demanding jobs parked for Phase 2 API integration")

        return recommendations

    def generate_report(self, days: int = 7) -> str:
        """Generate markdown report"""
        metrics = self.analyze_period(days)

        lines = []

        # Header
        lines.append("# Night Shift Production Metrics Report")
        lines.append("")
        lines.append(f"**Analysis Period**: Last {days} days")
        lines.append(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")
        lines.append("---")
        lines.append("")

        # Summary
        lines.append("## Summary")
        lines.append("")
        lines.append(f"- **Total Jobs Processed**: {metrics['total_jobs']}")
        lines.append("")

        # Status Breakdown
        lines.append("### Jobs by Status")
        lines.append("")
        for status, count in metrics["by_status"].items():
            lines.append(f"- **{status.title()}**: {count}")
        lines.append("")

        # Success Rate
        lines.append("## Phase 1 Success Rate")
        lines.append("")
        sr = metrics["success_rate"]
        lines.append(f"- **Success Rate**: {sr['percentage']}")
        lines.append(f"- **Target**: ≥85%")
        lines.append(f"- **Completed**: {sr['completed']}/{sr['processable']} processable jobs")

        if sr["meets_target"]:
            lines.append(f"- **Status**: 🎯 **TARGET ACHIEVED**")
        else:
            lines.append(f"- **Status**: ⚠️  Below target")

        lines.append("")

        # Processing Times
        if metrics["processing_times"]["total_jobs_timed"] > 0:
            lines.append("## Processing Performance")
            lines.append("")
            pt = metrics["processing_times"]
            lines.append(f"- **Average Time**: {pt['avg_minutes']:.1f} minutes")
            lines.append(f"- **Range**: {pt['min_seconds']:.0f}s - {pt['max_seconds']:.0f}s")
            lines.append("")

        # Daily Breakdown
        if metrics["daily_breakdown"]:
            lines.append("## Daily Breakdown")
            lines.append("")
            for day in metrics["daily_breakdown"]:
                lines.append(f"### {day['date']}")
                lines.append(f"- Completed: {day['completed']}")
                lines.append(f"- Parked: {day['parked']}")
                lines.append(f"- Deferred: {day['deferred']}")
                lines.append(f"- Failed: {day['failed']}")
                lines.append("")

        # Failures
        if metrics["failure_analysis"]["count"] > 0:
            lines.append("## Failure Analysis")
            lines.append("")
            lines.append(f"**Total Failures**: {metrics['failure_analysis']['count']}")
            lines.append("")

            if metrics["failure_analysis"]["patterns"]:
                lines.append("### Top Error Patterns")
                lines.append("")
                for pattern in metrics["failure_analysis"]["patterns"]:
                    lines.append(f"- ({pattern['count']}x) {pattern['error']}")
                lines.append("")

        # Recommendations
        lines.append("## Recommendations")
        lines.append("")
        for rec in metrics["recommendations"]:
            lines.append(f"- {rec}")
        lines.append("")

        # Footer
        lines.append("---")
        lines.append("")
        lines.append("*Generated by Night Shift Production Metrics Analyzer*")
        lines.append("")

        return "\n".join(lines)

    def save_report(self, days: int = 7, filename: Optional[str] = None) -> Path:
        """Save report to file"""
        if filename is None:
            filename = f"production_metrics_{datetime.now().strftime('%Y%m%d')}.md"

        report = self.generate_report(days)
        filepath = REPORTS_DIR / filename

        with open(filepath, 'w') as f:
            f.write(report)

        return filepath

    def close(self):
        """Close database connection"""
        self.conn.close()


def main():
    """Main entry point"""
    import sys

    days = 7
    if len(sys.argv) > 1:
        try:
            days = int(sys.argv[1])
        except ValueError:
            print(f"Usage: {sys.argv[0]} [days]")
            sys.exit(1)

    analyzer = ProductionMetricsAnalyzer()

    try:
        # Generate and save report
        filepath = analyzer.save_report(days=days)

        # Print to stdout
        report = analyzer.generate_report(days=days)
        print(report)

        print(f"\nReport saved to: {filepath}")

    finally:
        analyzer.close()


if __name__ == "__main__":
    main()
