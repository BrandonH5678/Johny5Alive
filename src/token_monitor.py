#!/usr/bin/env python3
"""
Token Monitoring System

Tracks token usage, cache hit rates, and efficiency metrics across J5A, Squirt, and Sherlock.

KEY METRICS:
- Cache hit rate: % of tokens served from cache vs fresh computation
- Token savings: Total tokens saved through caching and optimization
- Cost reduction: Dollar savings from reduced token usage
- System efficiency: Per-system token usage trends

Usage:
    from src.token_monitor import TokenMonitor, TokenEvent, SystemType

    monitor = TokenMonitor()
    monitor.log_event(TokenEvent(
        system=SystemType.SQUIRT,
        operation="voice_to_pdf",
        tokens_input=15000,
        tokens_output=3000,
        cache_hit=True,
        cached_tokens=12000
    ))

    report = monitor.generate_report()
    print(report)
"""

import json
import sqlite3
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum


class SystemType(Enum):
    """AI systems in J5A ecosystem"""
    J5A = "j5a"
    SQUIRT = "squirt"
    SHERLOCK = "sherlock"


class OperationType(Enum):
    """Common operation types"""
    # J5A operations
    THERMAL_CHECK = "thermal_check"
    VALIDATION = "validation"
    QUEUE_MANAGEMENT = "queue_management"

    # Squirt operations
    VOICE_TO_PDF = "voice_to_pdf"
    TRANSCRIPTION = "transcription"
    DOCUMENT_GENERATION = "document_generation"

    # Sherlock operations
    EVIDENCE_QUERY = "evidence_query"
    RETRIEVAL = "retrieval"
    ANALYSIS = "analysis"


@dataclass
class TokenEvent:
    """A single token usage event"""
    system: SystemType
    operation: str
    tokens_input: int
    tokens_output: int
    cache_hit: bool
    cached_tokens: int = 0
    timestamp: Optional[datetime] = None
    metadata: Dict = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.metadata is None:
            self.metadata = {}

    @property
    def total_tokens(self) -> int:
        """Total tokens for this event"""
        return self.tokens_input + self.tokens_output

    @property
    def effective_tokens(self) -> int:
        """Effective tokens after cache savings"""
        return self.total_tokens - self.cached_tokens

    @property
    def cache_efficiency(self) -> float:
        """Cache efficiency as percentage"""
        if self.total_tokens == 0:
            return 0.0
        return (self.cached_tokens / self.total_tokens) * 100

    def to_dict(self):
        return {
            'system': self.system.value,
            'operation': self.operation,
            'tokens_input': self.tokens_input,
            'tokens_output': self.tokens_output,
            'cache_hit': self.cache_hit,
            'cached_tokens': self.cached_tokens,
            'timestamp': self.timestamp.isoformat(),
            'metadata': self.metadata
        }


@dataclass
class TokenReport:
    """Summary report of token usage"""
    period_start: datetime
    period_end: datetime
    total_events: int
    total_tokens: int
    effective_tokens: int
    cached_tokens: int
    cache_hit_rate: float
    cost_without_cache: float
    cost_with_cache: float
    cost_savings: float
    by_system: Dict[str, Dict]
    top_operations: List[Dict]

    def to_dict(self):
        return {
            'period_start': self.period_start.isoformat(),
            'period_end': self.period_end.isoformat(),
            'total_events': self.total_events,
            'total_tokens': self.total_tokens,
            'effective_tokens': self.effective_tokens,
            'cached_tokens': self.cached_tokens,
            'cache_hit_rate': self.cache_hit_rate,
            'cost_without_cache': self.cost_without_cache,
            'cost_with_cache': self.cost_with_cache,
            'cost_savings': self.cost_savings,
            'by_system': self.by_system,
            'top_operations': self.top_operations
        }


class TokenMonitor:
    """
    Monitor token usage and cache efficiency.

    Tracks all token events and provides analytics on:
    - Cache hit rates
    - Token savings
    - Cost reduction
    - System efficiency trends
    """

    # Pricing (Claude Sonnet 3.5 as baseline)
    PRICE_PER_1M_INPUT = 3.00   # $3 per 1M input tokens
    PRICE_PER_1M_OUTPUT = 15.00  # $15 per 1M output tokens
    CACHE_PRICE_PER_1M = 0.30    # $0.30 per 1M cached tokens (90% discount)

    def __init__(self, db_path: str = "token_monitor.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Initialize SQLite database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS token_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                system TEXT NOT NULL,
                operation TEXT NOT NULL,
                tokens_input INTEGER NOT NULL,
                tokens_output INTEGER NOT NULL,
                cache_hit BOOLEAN NOT NULL,
                cached_tokens INTEGER DEFAULT 0,
                timestamp DATETIME NOT NULL,
                metadata JSON
            )
        ''')

        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_system ON token_events(system)
        ''')

        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_timestamp ON token_events(timestamp)
        ''')

        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_cache_hit ON token_events(cache_hit)
        ''')

        conn.commit()
        conn.close()

    def log_event(self, event: TokenEvent):
        """Log a token usage event"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO token_events
            (system, operation, tokens_input, tokens_output, cache_hit, cached_tokens, timestamp, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            event.system.value,
            event.operation,
            event.tokens_input,
            event.tokens_output,
            event.cache_hit,
            event.cached_tokens,
            event.timestamp.isoformat(),
            json.dumps(event.metadata)
        ))

        conn.commit()
        conn.close()

    def get_events(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        system: Optional[SystemType] = None
    ) -> List[TokenEvent]:
        """Retrieve token events with optional filtering"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        query = "SELECT * FROM token_events WHERE 1=1"
        params = []

        if start_date:
            query += " AND timestamp >= ?"
            params.append(start_date.isoformat())

        if end_date:
            query += " AND timestamp <= ?"
            params.append(end_date.isoformat())

        if system:
            query += " AND system = ?"
            params.append(system.value)

        query += " ORDER BY timestamp DESC"

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        events = []
        for row in rows:
            events.append(TokenEvent(
                system=SystemType(row[1]),
                operation=row[2],
                tokens_input=row[3],
                tokens_output=row[4],
                cache_hit=bool(row[5]),
                cached_tokens=row[6],
                timestamp=datetime.fromisoformat(row[7]),
                metadata=json.loads(row[8]) if row[8] else {}
            ))

        return events

    def generate_report(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> TokenReport:
        """
        Generate comprehensive token usage report.

        Args:
            start_date: Report start (default: 30 days ago)
            end_date: Report end (default: now)

        Returns:
            TokenReport object with all metrics
        """
        if end_date is None:
            end_date = datetime.now()
        if start_date is None:
            start_date = end_date - timedelta(days=30)

        events = self.get_events(start_date, end_date)

        # Calculate totals
        total_events = len(events)
        total_tokens = sum(e.total_tokens for e in events)
        cached_tokens = sum(e.cached_tokens for e in events)
        effective_tokens = total_tokens - cached_tokens

        # Cache hit rate
        cache_hits = sum(1 for e in events if e.cache_hit)
        cache_hit_rate = (cache_hits / total_events * 100) if total_events > 0 else 0.0

        # Cost calculations
        total_input = sum(e.tokens_input for e in events)
        total_output = sum(e.tokens_output for e in events)

        cost_without_cache = (
            (total_input / 1_000_000 * self.PRICE_PER_1M_INPUT) +
            (total_output / 1_000_000 * self.PRICE_PER_1M_OUTPUT)
        )

        # With cache: cached tokens at 90% discount
        effective_input = total_input - sum(e.cached_tokens for e in events if e.tokens_input > 0)
        cost_with_cache = (
            (effective_input / 1_000_000 * self.PRICE_PER_1M_INPUT) +
            (total_output / 1_000_000 * self.PRICE_PER_1M_OUTPUT) +
            (cached_tokens / 1_000_000 * self.CACHE_PRICE_PER_1M)
        )

        cost_savings = cost_without_cache - cost_with_cache

        # By-system breakdown
        by_system = {}
        for system_type in SystemType:
            system_events = [e for e in events if e.system == system_type]
            if system_events:
                by_system[system_type.value] = {
                    'events': len(system_events),
                    'total_tokens': sum(e.total_tokens for e in system_events),
                    'cached_tokens': sum(e.cached_tokens for e in system_events),
                    'cache_hit_rate': (sum(1 for e in system_events if e.cache_hit) / len(system_events) * 100)
                }

        # Top operations
        operation_stats = {}
        for event in events:
            key = f"{event.system.value}:{event.operation}"
            if key not in operation_stats:
                operation_stats[key] = {
                    'count': 0,
                    'total_tokens': 0,
                    'cached_tokens': 0
                }
            operation_stats[key]['count'] += 1
            operation_stats[key]['total_tokens'] += event.total_tokens
            operation_stats[key]['cached_tokens'] += event.cached_tokens

        top_operations = sorted(
            [
                {
                    'operation': key,
                    'count': stats['count'],
                    'total_tokens': stats['total_tokens'],
                    'cached_tokens': stats['cached_tokens'],
                    'cache_efficiency': (stats['cached_tokens'] / stats['total_tokens'] * 100) if stats['total_tokens'] > 0 else 0
                }
                for key, stats in operation_stats.items()
            ],
            key=lambda x: x['total_tokens'],
            reverse=True
        )[:10]

        return TokenReport(
            period_start=start_date,
            period_end=end_date,
            total_events=total_events,
            total_tokens=total_tokens,
            effective_tokens=effective_tokens,
            cached_tokens=cached_tokens,
            cache_hit_rate=cache_hit_rate,
            cost_without_cache=cost_without_cache,
            cost_with_cache=cost_with_cache,
            cost_savings=cost_savings,
            by_system=by_system,
            top_operations=top_operations
        )

    def get_cache_efficiency_for_html(self) -> Dict:
        """
        Get current cache efficiency metrics for HTML display.

        Returns dict for JavaScript integration in PROMPT_LIBRARY.html
        """
        # Last 24 hours
        end_date = datetime.now()
        start_date = end_date - timedelta(days=1)

        events = self.get_events(start_date, end_date)

        if not events:
            return {
                'cache_hit_rate': 0.0,
                'tokens_saved': 0,
                'cost_savings': 0.0,
                'status': 'no_data'
            }

        cache_hits = sum(1 for e in events if e.cache_hit)
        cached_tokens = sum(e.cached_tokens for e in events)
        total_tokens = sum(e.total_tokens for e in events)

        cache_hit_rate = (cache_hits / len(events) * 100) if events else 0.0

        # Cost savings (last 24h)
        total_input = sum(e.tokens_input for e in events)
        total_output = sum(e.tokens_output for e in events)

        cost_without = (
            (total_input / 1_000_000 * self.PRICE_PER_1M_INPUT) +
            (total_output / 1_000_000 * self.PRICE_PER_1M_OUTPUT)
        )

        effective_input = total_input - cached_tokens
        cost_with = (
            (effective_input / 1_000_000 * self.PRICE_PER_1M_INPUT) +
            (total_output / 1_000_000 * self.PRICE_PER_1M_OUTPUT) +
            (cached_tokens / 1_000_000 * self.CACHE_PRICE_PER_1M)
        )

        return {
            'cache_hit_rate': round(cache_hit_rate, 1),
            'tokens_saved': cached_tokens,
            'cost_savings': round(cost_without - cost_with, 2),
            'status': 'active'
        }

    def export_report(self, report: TokenReport, output_path: str):
        """Export report to JSON"""
        with open(output_path, 'w') as f:
            json.dump(report.to_dict(), f, indent=2)

        print(f"✅ Exported token report to {output_path}")


def main():
    """Example usage and testing"""
    print("=" * 70)
    print("Token Monitor - Test Suite")
    print("=" * 70)
    print()

    # Initialize monitor
    monitor = TokenMonitor(db_path="test_token_monitor.db")

    # Simulate some events
    print("Logging sample token events...")
    print("-" * 70)

    # J5A events
    monitor.log_event(TokenEvent(
        system=SystemType.J5A,
        operation="thermal_check",
        tokens_input=500,
        tokens_output=100,
        cache_hit=True,
        cached_tokens=450,
        metadata={'thermal_safe': True}
    ))

    monitor.log_event(TokenEvent(
        system=SystemType.J5A,
        operation="validation",
        tokens_input=2000,
        tokens_output=500,
        cache_hit=True,
        cached_tokens=1800,
        metadata={'validation_passed': True}
    ))

    # Squirt events
    monitor.log_event(TokenEvent(
        system=SystemType.SQUIRT,
        operation="voice_to_pdf",
        tokens_input=15000,
        tokens_output=3000,
        cache_hit=True,
        cached_tokens=12000,
        metadata={'document_type': 'estimate'}
    ))

    monitor.log_event(TokenEvent(
        system=SystemType.SQUIRT,
        operation="transcription",
        tokens_input=8000,
        tokens_output=1000,
        cache_hit=False,
        cached_tokens=0,
        metadata={'audio_duration_sec': 600}
    ))

    # Sherlock events
    monitor.log_event(TokenEvent(
        system=SystemType.SHERLOCK,
        operation="evidence_query",
        tokens_input=25000,
        tokens_output=2000,
        cache_hit=False,
        cached_tokens=0,
        metadata={'query': 'Operation Mockingbird'}
    ))

    monitor.log_event(TokenEvent(
        system=SystemType.SHERLOCK,
        operation="evidence_query",
        tokens_input=1500,
        tokens_output=300,
        cache_hit=True,
        cached_tokens=1200,
        metadata={'query': 'Wisner Wurlitzer', 'retrieval_used': True}
    ))

    print("✅ Logged 6 sample events")
    print()

    # Generate report
    print("Generating token usage report...")
    print("-" * 70)
    report = monitor.generate_report()

    print(f"\nToken Usage Report")
    print(f"Period: {report.period_start.date()} to {report.period_end.date()}")
    print(f"\nOverall Metrics:")
    print(f"  Total events: {report.total_events}")
    print(f"  Total tokens: {report.total_tokens:,}")
    print(f"  Cached tokens: {report.cached_tokens:,}")
    print(f"  Effective tokens: {report.effective_tokens:,}")
    print(f"  Cache hit rate: {report.cache_hit_rate:.1f}%")
    print(f"\nCost Analysis:")
    print(f"  Without cache: ${report.cost_without_cache:.2f}")
    print(f"  With cache: ${report.cost_with_cache:.2f}")
    print(f"  Savings: ${report.cost_savings:.2f} ({(report.cost_savings/report.cost_without_cache*100):.1f}%)")

    print(f"\nBy System:")
    for system, stats in report.by_system.items():
        print(f"  {system.upper()}:")
        print(f"    Events: {stats['events']}")
        print(f"    Total tokens: {stats['total_tokens']:,}")
        print(f"    Cached tokens: {stats['cached_tokens']:,}")
        print(f"    Cache hit rate: {stats['cache_hit_rate']:.1f}%")

    print(f"\nTop Operations:")
    for op in report.top_operations[:5]:
        print(f"  {op['operation']}:")
        print(f"    Count: {op['count']}")
        print(f"    Tokens: {op['total_tokens']:,}")
        print(f"    Cache efficiency: {op['cache_efficiency']:.1f}%")

    # Export report
    monitor.export_report(report, "test_token_report.json")

    # Test HTML integration
    print()
    print("HTML Integration Data:")
    print("-" * 70)
    html_data = monitor.get_cache_efficiency_for_html()
    print(json.dumps(html_data, indent=2))

    print()
    print("=" * 70)
    print("✅ Token monitoring test complete")
    print("=" * 70)

    # Cleanup
    Path("test_token_monitor.db").unlink()
    Path("test_token_report.json").unlink()


if __name__ == "__main__":
    main()
