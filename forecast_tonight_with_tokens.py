#!/usr/bin/env python3
"""
J5A Queue Forecast with Token Management

Simulates tonight's queue execution with token budget constraints,
showing how tasks will be adapted/deferred across multiple sessions.
"""

import json
from pathlib import Path
from src.j5a_token_governor import TokenGovernor, AdaptationTier

# Token budget constants
SESSION_BUDGET = 200_000
RESERVE = 20_000  # 10% reserve


def forecast_queue_execution():
    """Forecast queue execution with token management"""

    # Load all packages
    packages = []
    blocked_by_ram = []

    blocked_types = ['podcast', 'interview_series', 'youtube', 'multi_speaker_audio']

    for pkg_file in sorted(Path('queue').glob('sherlock_pkg_*.json')):
        with open(pkg_file) as f:
            pkg = json.load(f)

        if pkg['package_type'] in blocked_types:
            blocked_by_ram.append(pkg)
            continue

        packages.append(pkg)

    # Sort by priority
    packages.sort(key=lambda x: (x['priority'], x['package_id']))

    print("=" * 80)
    print("J5A OVERNIGHT FORECAST WITH TOKEN MANAGEMENT")
    print("=" * 80)
    print()

    # Initialize token governor
    gov = TokenGovernor()

    # Session tracking
    sessions = []
    current_session = {
        'session_num': 1,
        'tasks': [],
        'tokens_used': 0,
        'tokens_remaining': SESSION_BUDGET,
        'deferred_by_tokens': []
    }

    # Process each package
    for pkg in packages:
        pkg_type = pkg['package_type']
        url_count = len(pkg['collection_urls'])

        # Estimate tokens
        estimate = gov.estimate_sherlock_task(pkg_type, url_count)

        # Check if can run
        if gov.can_run(estimate):
            # Execute
            current_session['tasks'].append({
                'id': pkg['package_id'],
                'name': pkg['target_name'][:45],
                'type': pkg_type,
                'priority': pkg['priority'],
                'urls': url_count,
                'tokens': estimate.total,
                'tier': gov.current_tier().value
            })

            # Record usage
            gov.record(estimate.input_tokens, estimate.output_tokens)
            current_session['tokens_used'] += estimate.total
            current_session['tokens_remaining'] = gov.remaining()

        else:
            # Try adaptation
            priority = pkg['priority']
            can_exec, reason, adapted = gov.adapt_or_defer(
                task_id=f"pkg_{pkg['package_id']}",
                estimate=estimate,
                priority=priority
            )

            if can_exec and adapted:
                # Execute with adaptation
                current_session['tasks'].append({
                    'id': pkg['package_id'],
                    'name': pkg['target_name'][:45],
                    'type': pkg_type,
                    'priority': pkg['priority'],
                    'urls': url_count,
                    'tokens': adapted.total,
                    'tier': gov.current_tier().value,
                    'adapted': True
                })

                gov.record(adapted.input_tokens, adapted.output_tokens)
                current_session['tokens_used'] += adapted.total
                current_session['tokens_remaining'] = gov.remaining()

            else:
                # Defer to next session
                current_session['deferred_by_tokens'].append({
                    'id': pkg['package_id'],
                    'name': pkg['target_name'][:45],
                    'reason': reason
                })

                # Check if should start new session
                if gov.remaining_ratio() < 0.10:
                    # End current session
                    sessions.append(current_session)

                    # Start new session
                    gov = TokenGovernor()  # Reset for new session
                    current_session = {
                        'session_num': len(sessions) + 1,
                        'tasks': [],
                        'tokens_used': 0,
                        'tokens_remaining': SESSION_BUDGET,
                        'deferred_by_tokens': []
                    }

                    # Retry task in new session
                    estimate = gov.estimate_sherlock_task(pkg_type, url_count)
                    if gov.can_run(estimate):
                        current_session['tasks'].append({
                            'id': pkg['package_id'],
                            'name': pkg['target_name'][:45],
                            'type': pkg_type,
                            'priority': pkg['priority'],
                            'urls': url_count,
                            'tokens': estimate.total,
                            'tier': 'full'
                        })
                        gov.record(estimate.input_tokens, estimate.output_tokens)
                        current_session['tokens_used'] += estimate.total
                        current_session['tokens_remaining'] = gov.remaining()

    # Add final session
    if current_session['tasks'] or current_session['deferred_by_tokens']:
        sessions.append(current_session)

    # Display forecast
    total_completed = 0
    total_deferred = 0

    for session in sessions:
        print(f"SESSION {session['session_num']}")
        print("-" * 80)

        if session['tasks']:
            print(f"\nTasks Executed ({len(session['tasks'])}):")
            print()

            for task in session['tasks']:
                adapted_mark = " [ADAPTED]" if task.get('adapted') else ""
                print(f"  [{task['id']:3d}] {task['name'][:40]:<40} | P{task['priority']} | "
                      f"{task['type']:<10} | {task['tokens']:>6,} tok | {task['tier']:>11}{adapted_mark}")

            total_completed += len(session['tasks'])

        if session['deferred_by_tokens']:
            print(f"\nDeferred by Token Constraint ({len(session['deferred_by_tokens'])}):")
            for task in session['deferred_by_tokens']:
                print(f"  [{task['id']:3d}] {task['name'][:50]}")
                print(f"       Reason: {task['reason']}")

            total_deferred += len(session['deferred_by_tokens'])

        print()
        print(f"Session Tokens: {session['tokens_used']:,} used | {session['tokens_remaining']:,} remaining")
        print()
        print("=" * 80)
        print()

    # Summary
    print("FORECAST SUMMARY")
    print("-" * 80)
    print(f"Total Sessions Required: {len(sessions)}")
    print(f"Total Tasks Completed: {total_completed}")
    print(f"Total Tasks Deferred: {total_deferred}")
    print(f"RAM-Blocked Tasks: {len(blocked_by_ram)}")
    print()

    # Session breakdown
    print("Session Breakdown:")
    for i, session in enumerate(sessions, 1):
        token_efficiency = (session['tokens_used'] / SESSION_BUDGET) * 100
        print(f"  Session {i}: {len(session['tasks'])} tasks, {session['tokens_used']:,} tokens ({token_efficiency:.1f}% utilization)")

    print()
    print("=" * 80)


if __name__ == "__main__":
    forecast_queue_execution()
