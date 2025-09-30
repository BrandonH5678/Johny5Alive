#!/usr/bin/env python3
"""
Protocol Manager for Johny5Alive Multi-System Operations
Manages coordination between Squirt, Sherlock, and future AI systems.
"""

import json
import psutil
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


class Johny5ProtocolManager:
    """Manages AI operator protocols across multiple systems"""

    def __init__(self, johny5_root="/home/johnny5/Desktop/Johny5Alive"):
        self.johny5_root = Path(johny5_root)
        self.squirt_root = Path("/home/johnny5/Squirt")
        self.sherlock_root = Path("/home/johnny5/Desktop/Sherlock")

        self.protocol_file = self.johny5_root / "JOHNY5_AI_OPERATOR_MANUAL.md"
        self.development_log = self.johny5_root / "development_log.json"
        self.session_log = []

        # Initialize development log if it doesn't exist
        if not self.development_log.exists():
            self._initialize_development_log()

    def inject_session_context(self) -> Dict:
        """Inject current protocols and system status into AI operator context"""
        context = {
            'timestamp': datetime.now().isoformat(),
            'system_overview': self._get_system_overview(),
            'resource_status': self._get_resource_status(),
            'development_status': self._get_development_status(),
            'priority_matrix': self._get_priority_matrix(),
            'squirt_status': self._get_squirt_status(),
            'sherlock_status': self._get_sherlock_status(),
            'coordination_rules': self._get_coordination_rules(),
            'milestone_tracking': self._get_milestone_tracking()
        }

        # Log context injection
        self.session_log.append({
            'action': 'context_injection',
            'timestamp': datetime.now().isoformat(),
            'context_size': len(str(context)),
            'systems_active': list(context['system_overview']['active_systems'].keys())
        })

        return context

    def _get_system_overview(self) -> Dict:
        """Get overview of all Johny5 systems"""
        return {
            'machine': 'Late-2012 Mac mini (Linux Mint MATE)',
            'current_ram': self._get_memory_info()['total_gb'],
            'planned_upgrade': '16GB RAM (Monday/Tuesday)',
            'active_systems': {
                'Squirt': {
                    'status': 'PRODUCTION',
                    'priority': 'BUSINESS_CRITICAL',
                    'location': str(self.squirt_root)
                },
                'Sherlock': {
                    'status': 'DEVELOPMENT',
                    'priority': 'RESEARCH',
                    'location': str(self.sherlock_root)
                },
                'Johny5Alive': {
                    'status': 'ACTIVE',
                    'priority': 'COORDINATION',
                    'location': str(self.johny5_root)
                }
            }
        }

    def _get_resource_status(self) -> Dict:
        """Get current resource allocation and usage"""
        memory = self._get_memory_info()
        cpu = self._get_cpu_info()

        return {
            'memory': memory,
            'cpu': cpu,
            'business_hours_active': self._is_business_hours(),
            'resource_priority': 'SQUIRT' if self._is_business_hours() else 'BALANCED',
            'libreoffice_running': self._check_libreoffice_status(),
            'heavy_processing_allowed': not self._is_business_hours()
        }

    def _get_development_status(self) -> Dict:
        """Get current development milestone status"""
        log_data = self._load_development_log()

        current_phase = log_data.get('current_phase', 'Phase 1: Foundation')
        milestones = log_data.get('milestones', {})

        return {
            'current_phase': current_phase,
            'phase_progress': self._calculate_phase_progress(milestones),
            'recent_milestones': self._get_recent_milestones(log_data),
            'next_priorities': self._get_next_priorities(milestones),
            'blocked_items': self._get_blocked_items(milestones)
        }

    def _get_priority_matrix(self) -> Dict:
        """Get resource priority rules for current time"""
        is_business_hours = self._is_business_hours()

        if is_business_hours:
            return {
                'primary': 'Squirt (business operations)',
                'secondary': 'Johny5Alive (coordination)',
                'background': 'Sherlock (light processing only)',
                'restrictions': [
                    'No heavy Sherlock processing',
                    'Yield LibreOffice resources to Squirt',
                    'Pause large model loading for Squirt requests'
                ]
            }
        else:
            return {
                'primary': 'Development work (all systems)',
                'secondary': 'Sherlock (heavy processing allowed)',
                'background': 'Squirt (maintenance only)',
                'opportunities': [
                    'Full Sherlock voice processing',
                    'Large model training/optimization',
                    'Cross-system integration testing'
                ]
            }

    def _get_squirt_status(self) -> Dict:
        """Get Squirt system status"""
        try:
            squirt_manual = self.squirt_root / "SQUIRT_AI_OPERATOR_MANUAL.md"
            if squirt_manual.exists():
                # Parse key status from Squirt manual
                return {
                    'operational_status': 'PRODUCTION_READY',
                    'template_processing': 'OPERATIONAL',
                    'validation_system': 'ACTIVE',
                    'libreoffice_integration': 'ACTIVE',
                    'phase': 'Phase 1 Complete, Voice Processing Planned',
                    'priority_during_business_hours': 'ABSOLUTE'
                }
            else:
                return {'status': 'MANUAL_NOT_FOUND'}
        except Exception as e:
            return {'status': 'ERROR', 'error': str(e)}

    def _get_sherlock_status(self) -> Dict:
        """Get Sherlock system status"""
        try:
            sherlock_status = self.sherlock_root / "SHERLOCK_STATUS.md"
            if sherlock_status.exists():
                return {
                    'operational_status': 'DEVELOPMENT',
                    'voice_processing': 'FOUNDATION_BUILT',
                    'diarization': 'SUPERVISED_COMPLETE',
                    'auto_anchor_system': 'PLANNED',
                    'evidence_pipeline': 'DESIGNED',
                    'current_focus': 'Dual-engine voice processing for Squirt integration'
                }
            else:
                return {'status': 'STATUS_FILE_NOT_FOUND'}
        except Exception as e:
            return {'status': 'ERROR', 'error': str(e)}

    def _get_coordination_rules(self) -> Dict:
        """Get system coordination rules"""
        return {
            'resource_conflicts': {
                'libreoffice': 'Squirt has absolute priority',
                'memory_intensive': 'Check business hours before large allocations',
                'cpu_intensive': 'Background priority during business hours'
            },
            'development_coordination': {
                'milestone_updates': 'Update manual immediately upon completion',
                'cross_system_changes': 'Coordinate through Johny5Alive',
                'testing': 'Ensure no interference between systems'
            },
            'emergency_procedures': {
                'squirt_urgent': 'Pause all other processing immediately',
                'system_overload': 'Reduce Sherlock processing first',
                'manual_update_required': 'Stop and update documentation'
            }
        }

    def _get_milestone_tracking(self) -> Dict:
        """Get milestone tracking information"""
        log_data = self._load_development_log()

        return {
            'update_required': self._check_if_update_required(),
            'last_manual_update': log_data.get('last_manual_update', 'NEVER'),
            'pending_milestones': self._get_pending_milestones(log_data),
            'completion_rate': self._calculate_completion_rate(log_data),
            'next_manual_update_trigger': self._get_next_update_trigger(log_data)
        }

    def log_milestone_completion(self, milestone: str, phase: str, details: Dict = None):
        """Log completion of a development milestone"""
        log_data = self._load_development_log()

        completion_entry = {
            'milestone': milestone,
            'phase': phase,
            'completed_at': datetime.now().isoformat(),
            'details': details or {},
            'requires_manual_update': True
        }

        # Add to completed milestones
        if 'completed_milestones' not in log_data:
            log_data['completed_milestones'] = []
        log_data['completed_milestones'].append(completion_entry)

        # Update current phase if needed
        log_data['current_phase'] = phase
        log_data['last_milestone_completion'] = datetime.now().isoformat()

        # Save updated log
        self._save_development_log(log_data)

        # Add to session log
        self.session_log.append({
            'action': 'milestone_completed',
            'milestone': milestone,
            'phase': phase,
            'timestamp': datetime.now().isoformat()
        })

        return completion_entry

    def update_manual_completed(self):
        """Mark that the manual has been updated for recent milestones"""
        log_data = self._load_development_log()
        log_data['last_manual_update'] = datetime.now().isoformat()

        # Mark recent milestones as documented
        if 'completed_milestones' in log_data:
            for milestone in log_data['completed_milestones']:
                if milestone.get('requires_manual_update', False):
                    milestone['requires_manual_update'] = False
                    milestone['documented_at'] = datetime.now().isoformat()

        self._save_development_log(log_data)

    def _initialize_development_log(self):
        """Initialize the development log file"""
        initial_data = {
            'created_at': datetime.now().isoformat(),
            'current_phase': 'Phase 1: Foundation',
            'milestones': {
                'Phase 1: Foundation': [
                    {'name': 'Rename Bench Test → Sherlock', 'status': 'completed'},
                    {'name': 'Create Johny5Alive umbrella system', 'status': 'completed'},
                    {'name': 'Clone AI Operator Manual and Context Injection', 'status': 'in_progress'},
                    {'name': 'Set up automatic milestone tracking', 'status': 'in_progress'},
                    {'name': 'Configure umbrella management system', 'status': 'pending'}
                ]
            },
            'completed_milestones': [],
            'last_manual_update': 'NEVER'
        }

        self._save_development_log(initial_data)

    def _load_development_log(self) -> Dict:
        """Load development log data"""
        try:
            if self.development_log.exists():
                with open(self.development_log, 'r') as f:
                    return json.load(f)
            else:
                self._initialize_development_log()
                return self._load_development_log()
        except Exception:
            # If file is corrupted, reinitialize
            self._initialize_development_log()
            return self._load_development_log()

    def _save_development_log(self, data: Dict):
        """Save development log data"""
        with open(self.development_log, 'w') as f:
            json.dump(data, f, indent=2)

    def _get_memory_info(self) -> Dict:
        """Get system memory information"""
        memory = psutil.virtual_memory()
        return {
            'total_gb': round(memory.total / (1024**3), 1),
            'available_gb': round(memory.available / (1024**3), 1),
            'used_gb': round(memory.used / (1024**3), 1),
            'percent_used': memory.percent
        }

    def _get_cpu_info(self) -> Dict:
        """Get CPU usage information"""
        return {
            'cores': psutil.cpu_count(),
            'current_percent': psutil.cpu_percent(interval=1),
            'load_average': psutil.getloadavg() if hasattr(psutil, 'getloadavg') else None
        }

    def _is_business_hours(self) -> bool:
        """Check if currently in business hours (6am-7pm Mon-Fri)"""
        now = datetime.now()

        # Check if weekday (0=Monday, 6=Sunday)
        if now.weekday() >= 5:  # Saturday or Sunday
            return False

        # Check if between 6am and 7pm
        hour = now.hour
        return 6 <= hour < 19

    def _check_libreoffice_status(self) -> Dict:
        """Check if LibreOffice is running"""
        try:
            result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
            libreoffice_processes = [line for line in result.stdout.split('\n')
                                   if 'soffice' in line or 'libreoffice' in line]

            return {
                'running': len(libreoffice_processes) > 0,
                'process_count': len(libreoffice_processes),
                'processes': libreoffice_processes
            }
        except Exception as e:
            return {'running': False, 'error': str(e)}

    def _calculate_phase_progress(self, milestones: Dict) -> Dict:
        """Calculate progress for current phase"""
        current_phase_milestones = milestones.get('Phase 1: Foundation', [])

        total = len(current_phase_milestones)
        completed = len([m for m in current_phase_milestones if m.get('status') == 'completed'])
        in_progress = len([m for m in current_phase_milestones if m.get('status') == 'in_progress'])

        return {
            'total_milestones': total,
            'completed': completed,
            'in_progress': in_progress,
            'pending': total - completed - in_progress,
            'completion_percent': round((completed / total) * 100, 1) if total > 0 else 0
        }

    def _get_recent_milestones(self, log_data: Dict) -> List[Dict]:
        """Get recently completed milestones"""
        completed = log_data.get('completed_milestones', [])
        # Return last 5 completed milestones
        return sorted(completed, key=lambda x: x['completed_at'], reverse=True)[:5]

    def _get_next_priorities(self, milestones: Dict) -> List[str]:
        """Get next priority milestones"""
        current_phase_milestones = milestones.get('Phase 1: Foundation', [])

        # Get in-progress items first, then pending
        priorities = []
        for milestone in current_phase_milestones:
            if milestone.get('status') == 'in_progress':
                priorities.append(f"COMPLETE: {milestone['name']}")
            elif milestone.get('status') == 'pending':
                priorities.append(f"START: {milestone['name']}")

        return priorities[:3]  # Top 3 priorities

    def _get_blocked_items(self, milestones: Dict) -> List[str]:
        """Get any blocked milestones"""
        # Placeholder for blocked item detection
        return []

    def _check_if_update_required(self) -> bool:
        """Check if manual update is required"""
        log_data = self._load_development_log()
        completed = log_data.get('completed_milestones', [])

        # Check if any completed milestones require manual update
        return any(m.get('requires_manual_update', False) for m in completed)

    def _get_pending_milestones(self, log_data: Dict) -> List[str]:
        """Get milestones pending documentation"""
        completed = log_data.get('completed_milestones', [])
        return [m['milestone'] for m in completed if m.get('requires_manual_update', False)]

    def _calculate_completion_rate(self, log_data: Dict) -> float:
        """Calculate overall completion rate"""
        total_milestones = 0
        completed_milestones = 0

        for phase_milestones in log_data.get('milestones', {}).values():
            total_milestones += len(phase_milestones)
            completed_milestones += len([m for m in phase_milestones if m.get('status') == 'completed'])

        return round((completed_milestones / total_milestones) * 100, 1) if total_milestones > 0 else 0

    def _get_next_update_trigger(self, log_data: Dict) -> str:
        """Get description of next manual update trigger"""
        if self._check_if_update_required():
            return "UPDATE REQUIRED NOW - Completed milestones need documentation"
        else:
            return "Next in-progress milestone completion"


# Global instance
johny5_protocol = Johny5ProtocolManager()