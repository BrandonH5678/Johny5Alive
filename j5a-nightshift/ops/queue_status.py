#!/usr/bin/env python3
"""
J5A Queue Status Dashboard
Provides detailed queue analysis and statistics for Night Shift operations.
"""

import argparse
import json
import sqlite3
import sys
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any


class QueueStatusDashboard:
    """Comprehensive queue analysis and reporting."""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = None

    def connect(self):
        """Connect to queue database."""
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row
            return True
        except sqlite3.Error as e:
            print(f"❌ Database connection failed: {e}", file=sys.stderr)
            return False

    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()

    def get_job_distribution(self) -> Dict[str, Any]:
        """Analyze job distribution by type, class, and status."""
        cursor = self.conn.cursor()

        # Job counts by status
        cursor.execute("""
            SELECT status, COUNT(*) as count
            FROM task_executions
            GROUP BY status
        """)
        status_counts = {row['status']: row['count'] for row in cursor.fetchall()}

        # Job counts by type
        cursor.execute("""
            SELECT td.task_type, te.status, COUNT(*) as count
            FROM task_definitions td
            LEFT JOIN task_executions te ON td.task_id = te.task_id
            GROUP BY td.task_type, te.status
        """)
        type_distribution = defaultdict(lambda: defaultdict(int))
        for row in cursor.fetchall():
            type_distribution[row['task_type']][row['status']] = row['count']

        # Job counts by priority
        cursor.execute("""
            SELECT td.priority, te.status, COUNT(*) as count
            FROM task_definitions td
            LEFT JOIN task_executions te ON td.task_id = te.task_id
            GROUP BY td.priority, te.status
        """)
        priority_distribution = defaultdict(lambda: defaultdict(int))
        for row in cursor.fetchall():
            priority_distribution[row['priority']][row['status']] = row['count']

        # Job counts by target system
        cursor.execute("""
            SELECT td.target_system, te.status, COUNT(*) as count
            FROM task_definitions td
            LEFT JOIN task_executions te ON td.task_id = te.task_id
            GROUP BY td.target_system, te.status
        """)
        system_distribution = defaultdict(lambda: defaultdict(int))
        for row in cursor.fetchall():
            system_distribution[row['target_system']][row['status']] = row['count']

        return {
            'by_status': dict(status_counts),
            'by_type': {k: dict(v) for k, v in type_distribution.items()},
            'by_priority': {k: dict(v) for k, v in priority_distribution.items()},
            'by_system': {k: dict(v) for k, v in system_distribution.items()}
        }

    def get_processing_time_trends(self) -> Dict[str, Any]:
        """Analyze processing time trends."""
        cursor = self.conn.cursor()

        # Average processing time by task type
        cursor.execute("""
            SELECT
                td.task_type,
                td.estimated_duration_minutes,
                AVG((julianday(te.end_time) - julianday(te.start_time)) * 24 * 60) as avg_actual_minutes,
                MIN((julianday(te.end_time) - julianday(te.start_time)) * 24 * 60) as min_minutes,
                MAX((julianday(te.end_time) - julianday(te.start_time)) * 24 * 60) as max_minutes,
                COUNT(*) as sample_count
            FROM task_definitions td
            JOIN task_executions te ON td.task_id = te.task_id
            WHERE te.status = 'completed'
              AND te.end_time IS NOT NULL
              AND te.start_time IS NOT NULL
            GROUP BY td.task_type
        """)

        time_trends = []
        for row in cursor.fetchall():
            time_trends.append({
                'task_type': row['task_type'],
                'estimated_minutes': row['estimated_duration_minutes'],
                'avg_actual_minutes': round(row['avg_actual_minutes'], 2) if row['avg_actual_minutes'] else None,
                'min_minutes': round(row['min_minutes'], 2) if row['min_minutes'] else None,
                'max_minutes': round(row['max_minutes'], 2) if row['max_minutes'] else None,
                'sample_count': row['sample_count']
            })

        # Recent processing time trend (last 7 days)
        cursor.execute("""
            SELECT
                DATE(te.start_time) as date,
                AVG((julianday(te.end_time) - julianday(te.start_time)) * 24 * 60) as avg_minutes,
                COUNT(*) as jobs_completed
            FROM task_executions te
            WHERE te.status = 'completed'
              AND te.end_time IS NOT NULL
              AND te.start_time IS NOT NULL
              AND te.start_time >= datetime('now', '-7 days')
            GROUP BY DATE(te.start_time)
            ORDER BY date
        """)

        daily_trends = []
        for row in cursor.fetchall():
            daily_trends.append({
                'date': row['date'],
                'avg_minutes': round(row['avg_minutes'], 2) if row['avg_minutes'] else None,
                'jobs_completed': row['jobs_completed']
            })

        return {
            'by_task_type': time_trends,
            'daily_trend': daily_trends
        }

    def get_success_rate_over_time(self) -> Dict[str, Any]:
        """Calculate success rate trends."""
        cursor = self.conn.cursor()

        # Overall success rate
        cursor.execute("""
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed,
                SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed,
                SUM(CASE WHEN status = 'deferred' THEN 1 ELSE 0 END) as deferred,
                SUM(CASE WHEN status = 'parked' THEN 1 ELSE 0 END) as parked
            FROM task_executions
        """)

        row = cursor.fetchone()
        total = row['total']
        completed = row['completed']
        failed = row['failed']
        deferred = row['deferred']
        parked = row['parked']

        overall = {
            'total_jobs': total,
            'completed': completed,
            'failed': failed,
            'deferred': deferred,
            'parked': parked,
            'success_rate': round(completed / total * 100, 2) if total > 0 else 0,
            'failure_rate': round(failed / total * 100, 2) if total > 0 else 0
        }

        # Success rate by task type
        cursor.execute("""
            SELECT
                td.task_type,
                COUNT(*) as total,
                SUM(CASE WHEN te.status = 'completed' THEN 1 ELSE 0 END) as completed,
                SUM(CASE WHEN te.status = 'failed' THEN 1 ELSE 0 END) as failed
            FROM task_definitions td
            JOIN task_executions te ON td.task_id = te.task_id
            GROUP BY td.task_type
        """)

        by_type = []
        for row in cursor.fetchall():
            total = row['total']
            completed = row['completed']
            failed = row['failed']
            by_type.append({
                'task_type': row['task_type'],
                'total': total,
                'completed': completed,
                'failed': failed,
                'success_rate': round(completed / total * 100, 2) if total > 0 else 0
            })

        # Daily success rate (last 7 days)
        cursor.execute("""
            SELECT
                DATE(te.start_time) as date,
                COUNT(*) as total,
                SUM(CASE WHEN te.status = 'completed' THEN 1 ELSE 0 END) as completed,
                SUM(CASE WHEN te.status = 'failed' THEN 1 ELSE 0 END) as failed
            FROM task_executions te
            WHERE te.start_time IS NOT NULL
              AND te.start_time >= datetime('now', '-7 days')
            GROUP BY DATE(te.start_time)
            ORDER BY date
        """)

        daily = []
        for row in cursor.fetchall():
            total = row['total']
            completed = row['completed']
            daily.append({
                'date': row['date'],
                'total': total,
                'completed': completed,
                'failed': row['failed'],
                'success_rate': round(completed / total * 100, 2) if total > 0 else 0
            })

        return {
            'overall': overall,
            'by_type': by_type,
            'daily_trend': daily
        }

    def get_failure_patterns(self) -> Dict[str, Any]:
        """Analyze failure patterns and common error types."""
        cursor = self.conn.cursor()

        # Failed jobs with error details
        cursor.execute("""
            SELECT
                td.task_id,
                td.name,
                td.task_type,
                te.error_log,
                te.retry_count,
                te.start_time
            FROM task_definitions td
            JOIN task_executions te ON td.task_id = te.task_id
            WHERE te.status = 'failed'
            ORDER BY te.start_time DESC
            LIMIT 20
        """)

        recent_failures = []
        error_categories = defaultdict(int)

        for row in cursor.fetchall():
            error_log = json.loads(row['error_log']) if row['error_log'] and row['error_log'] != '[]' else []

            # Categorize error
            error_category = 'unknown'
            if error_log:
                last_error = error_log[-1] if isinstance(error_log, list) else str(error_log)
                if isinstance(last_error, dict):
                    last_error = last_error.get('error', str(last_error))

                if 'thermal' in str(last_error).lower() or 'temperature' in str(last_error).lower():
                    error_category = 'thermal'
                elif 'memory' in str(last_error).lower() or 'oom' in str(last_error).lower():
                    error_category = 'memory'
                elif 'timeout' in str(last_error).lower():
                    error_category = 'timeout'
                elif 'validation' in str(last_error).lower():
                    error_category = 'validation'
                elif 'llm' in str(last_error).lower() or 'model' in str(last_error).lower():
                    error_category = 'llm'
                else:
                    error_category = 'other'

            error_categories[error_category] += 1

            recent_failures.append({
                'task_id': row['task_id'],
                'name': row['name'],
                'task_type': row['task_type'],
                'error_category': error_category,
                'error_details': error_log[-1] if error_log else None,
                'retry_count': row['retry_count'],
                'timestamp': row['start_time']
            })

        # Deferred jobs analysis
        cursor.execute("""
            SELECT
                td.task_id,
                td.name,
                td.task_type,
                te.error_log
            FROM task_definitions td
            JOIN task_executions te ON td.task_id = te.task_id
            WHERE te.status = 'deferred'
        """)

        deferred_jobs = []
        for row in cursor.fetchall():
            error_log = json.loads(row['error_log']) if row['error_log'] and row['error_log'] != '[]' else []
            deferred_jobs.append({
                'task_id': row['task_id'],
                'name': row['name'],
                'task_type': row['task_type'],
                'reason': error_log[-1] if error_log else 'unknown'
            })

        return {
            'recent_failures': recent_failures,
            'error_categories': dict(error_categories),
            'deferred_count': len(deferred_jobs),
            'deferred_jobs': deferred_jobs[:10]  # Limit to first 10
        }

    def get_resource_utilization(self) -> Dict[str, Any]:
        """Analyze resource utilization stats."""
        cursor = self.conn.cursor()

        # Thermal safety analysis
        cursor.execute("""
            SELECT
                td.thermal_safety_required,
                te.status,
                COUNT(*) as count
            FROM task_definitions td
            JOIN task_executions te ON td.task_id = te.task_id
            GROUP BY td.thermal_safety_required, te.status
        """)

        thermal_stats = defaultdict(lambda: defaultdict(int))
        for row in cursor.fetchall():
            key = 'thermal_required' if row['thermal_safety_required'] else 'no_thermal_required'
            thermal_stats[key][row['status']] = row['count']

        # Jobs with performance metrics
        cursor.execute("""
            SELECT
                td.task_type,
                te.performance_metrics
            FROM task_definitions td
            JOIN task_executions te ON td.task_id = te.task_id
            WHERE te.status = 'completed'
              AND te.performance_metrics IS NOT NULL
              AND te.performance_metrics != '{}'
        """)

        performance_stats = []
        for row in cursor.fetchall():
            try:
                metrics = json.loads(row['performance_metrics']) if row['performance_metrics'] else {}
                if metrics:
                    performance_stats.append({
                        'task_type': row['task_type'],
                        'metrics': metrics
                    })
            except json.JSONDecodeError:
                pass

        return {
            'thermal_safety_stats': {k: dict(v) for k, v in thermal_stats.items()},
            'performance_samples': len(performance_stats),
            'sample_metrics': performance_stats[:5]  # Show first 5
        }

    def generate_cli_report(self):
        """Generate formatted CLI output."""
        print("=" * 80)
        print("J5A QUEUE STATUS DASHBOARD")
        print("=" * 80)
        print()

        # Job Distribution
        print("📊 JOB DISTRIBUTION")
        print("-" * 80)
        distribution = self.get_job_distribution()

        print("\nBy Status:")
        for status, count in sorted(distribution['by_status'].items()):
            icon = {
                'queued': '⏳',
                'completed': '✅',
                'failed': '❌',
                'deferred': '⏸️',
                'parked': '📦',
                'running': '🔄'
            }.get(status, '  ')
            print(f"  {icon} {status.capitalize():12} {count:3} jobs")

        print("\nBy Task Type:")
        for task_type, statuses in sorted(distribution['by_type'].items()):
            total = sum(statuses.values())
            print(f"  {task_type:20} {total:3} jobs")
            for status, count in sorted(statuses.items()):
                if count > 0:
                    print(f"    - {status:12} {count:3}")

        print("\nBy Target System:")
        for system, statuses in sorted(distribution['by_system'].items()):
            total = sum(statuses.values())
            print(f"  {system:20} {total:3} jobs")

        print()

        # Processing Time Trends
        print("⏱️  PROCESSING TIME TRENDS")
        print("-" * 80)
        time_trends = self.get_processing_time_trends()

        if time_trends['by_task_type']:
            print("\nBy Task Type:")
            for trend in time_trends['by_task_type']:
                print(f"  {trend['task_type']:20}")
                print(f"    Estimated:  {trend['estimated_minutes']:6.1f} min")
                if trend['avg_actual_minutes']:
                    print(f"    Actual avg: {trend['avg_actual_minutes']:6.1f} min")
                    print(f"    Range:      {trend['min_minutes']:6.1f} - {trend['max_minutes']:6.1f} min")
                    print(f"    Samples:    {trend['sample_count']}")
        else:
            print("  No completed jobs with timing data")

        if time_trends['daily_trend']:
            print("\nDaily Trend (Last 7 Days):")
            for day in time_trends['daily_trend']:
                print(f"  {day['date']}: {day['avg_minutes']:6.1f} min avg ({day['jobs_completed']} jobs)")

        print()

        # Success Rate
        print("📈 SUCCESS RATE ANALYSIS")
        print("-" * 80)
        success_rate = self.get_success_rate_over_time()

        overall = success_rate['overall']
        print("\nOverall:")
        print(f"  Total jobs:    {overall['total_jobs']:3}")
        print(f"  ✅ Completed:  {overall['completed']:3} ({overall['success_rate']:5.1f}%)")
        print(f"  ❌ Failed:     {overall['failed']:3} ({overall['failure_rate']:5.1f}%)")
        print(f"  ⏸️  Deferred:   {overall['deferred']:3}")
        print(f"  📦 Parked:     {overall['parked']:3}")

        print("\nBy Task Type:")
        for type_stat in success_rate['by_type']:
            print(f"  {type_stat['task_type']:20} {type_stat['success_rate']:5.1f}% ({type_stat['completed']}/{type_stat['total']})")

        if success_rate['daily_trend']:
            print("\nDaily Trend (Last 7 Days):")
            for day in success_rate['daily_trend']:
                print(f"  {day['date']}: {day['success_rate']:5.1f}% ({day['completed']}/{day['total']} jobs)")

        print()

        # Failure Patterns
        print("🔍 FAILURE PATTERN ANALYSIS")
        print("-" * 80)
        failures = self.get_failure_patterns()

        if failures['error_categories']:
            print("\nError Categories:")
            for category, count in sorted(failures['error_categories'].items(), key=lambda x: x[1], reverse=True):
                icon = {
                    'thermal': '🌡️',
                    'memory': '💾',
                    'timeout': '⏰',
                    'validation': '✓',
                    'llm': '🤖',
                    'other': '❓'
                }.get(category, '  ')
                print(f"  {icon} {category:15} {count:3} failures")

        if failures['recent_failures']:
            print(f"\nRecent Failures (last {len(failures['recent_failures'])}):")
            for failure in failures['recent_failures'][:5]:
                print(f"  {failure['task_id']:20} {failure['error_category']:12} (retries: {failure['retry_count']})")

        if failures['deferred_count'] > 0:
            print(f"\nDeferred Jobs: {failures['deferred_count']}")
            if failures['deferred_jobs']:
                for job in failures['deferred_jobs'][:3]:
                    print(f"  ⏸️  {job['task_id']:20} {job['task_type']}")

        print()

        # Resource Utilization
        print("🖥️  RESOURCE UTILIZATION")
        print("-" * 80)
        resources = self.get_resource_utilization()

        print("\nThermal Safety Stats:")
        for category, statuses in resources['thermal_safety_stats'].items():
            total = sum(statuses.values())
            print(f"  {category.replace('_', ' ').title():25} {total:3} jobs")
            for status, count in sorted(statuses.items()):
                if count > 0:
                    print(f"    - {status:12} {count:3}")

        if resources['performance_samples'] > 0:
            print(f"\nPerformance Metrics: {resources['performance_samples']} jobs with detailed metrics")

        print()
        print("=" * 80)

    def export_json(self, output_file: str):
        """Export all statistics as JSON."""
        data = {
            'timestamp': datetime.now().isoformat(),
            'job_distribution': self.get_job_distribution(),
            'processing_time_trends': self.get_processing_time_trends(),
            'success_rate': self.get_success_rate_over_time(),
            'failure_patterns': self.get_failure_patterns(),
            'resource_utilization': self.get_resource_utilization()
        }

        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)

        print(f"✅ Queue status exported to: {output_file}")


def main():
    parser = argparse.ArgumentParser(
        description="J5A Queue Status Dashboard - Comprehensive queue analysis"
    )
    parser.add_argument(
        '--db',
        default='/home/johnny5/Johny5Alive/j5a_queue_manager.db',
        help='Path to queue database'
    )
    parser.add_argument(
        '--export-json',
        metavar='FILE',
        help='Export statistics to JSON file'
    )
    parser.add_argument(
        '--quiet',
        action='store_true',
        help='Suppress CLI output (only export JSON)'
    )

    args = parser.parse_args()

    dashboard = QueueStatusDashboard(args.db)

    if not dashboard.connect():
        return 1

    try:
        if not args.quiet:
            dashboard.generate_cli_report()

        if args.export_json:
            dashboard.export_json(args.export_json)

        return 0

    except Exception as e:
        print(f"❌ Error generating dashboard: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1

    finally:
        dashboard.close()


if __name__ == '__main__':
    sys.exit(main())
