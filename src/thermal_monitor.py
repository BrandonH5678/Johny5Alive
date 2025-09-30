#!/usr/bin/env python3
"""
J5A Thermal Monitoring System
Automatic thermal safety checks for all system operations
"""

import subprocess
import time
from datetime import datetime
from typing import Dict, Any, Optional


class ThermalMonitor:
    """
    Critical thermal monitoring for 2012 Mac Mini heat management
    """

    def __init__(self):
        self.temperature_threshold_normal = 80.0  # °C
        self.temperature_threshold_warning = 85.0  # °C
        self.temperature_threshold_critical = 90.0  # °C
        self.load_threshold_caution = 2.0
        self.load_threshold_critical = 4.0

    def get_thermal_status(self) -> Dict[str, Any]:
        """
        Get comprehensive thermal status for the system

        Returns:
            Dictionary with thermal status and safety recommendations
        """

        try:
            # Get CPU temperature
            temp_result = subprocess.run([
                'sensors', '-u'
            ], capture_output=True, text=True, timeout=10)

            cpu_temp = self._parse_cpu_temperature(temp_result.stdout)

            # Get system load
            load_result = subprocess.run([
                'cat', '/proc/loadavg'
            ], capture_output=True, text=True, timeout=5)

            load_avg = self._parse_load_average(load_result.stdout)

            # Get fan status
            fan_rpm = self._get_fan_status()

            # Assess thermal safety
            safety_status = self._assess_thermal_safety(cpu_temp, load_avg, fan_rpm)

            return {
                'timestamp': datetime.now().isoformat(),
                'cpu_temperature': cpu_temp,
                'load_average': load_avg,
                'fan_rpm': fan_rpm,
                'safety_status': safety_status,
                'recommendations': self._get_thermal_recommendations(safety_status),
                'operation_allowed': safety_status['level'] != 'CRITICAL'
            }

        except Exception as e:
            return {
                'timestamp': datetime.now().isoformat(),
                'error': f'Thermal monitoring failed: {e}',
                'operation_allowed': False,
                'safety_status': {'level': 'ERROR', 'message': 'Cannot assess thermal state'}
            }

    def _parse_cpu_temperature(self, sensors_output: str) -> Optional[float]:
        """Parse CPU temperature from sensors output"""

        # Try direct sensors command first (more reliable)
        try:
            result = subprocess.run([
                'sensors'
            ], capture_output=True, text=True, timeout=10)

            lines = result.stdout.split('\n')
            for line in lines:
                if 'Package id 0:' in line and '+' in line and '°C' in line:
                    try:
                        temp_str = line.split('+')[1].split('°C')[0].strip()
                        return float(temp_str)
                    except (IndexError, ValueError):
                        continue

        except Exception:
            pass

        # Fallback: parse from provided output
        lines = sensors_output.split('\n')
        for line in lines:
            if 'Package id 0' in line and 'input' in line:
                try:
                    temp_str = line.split(':')[1].strip()
                    return float(temp_str)
                except (IndexError, ValueError):
                    continue

        # Additional fallback: look for coretemp
        for line in lines:
            if 'temp1_input' in line:
                try:
                    temp_str = line.split(':')[1].strip()
                    return float(temp_str) / 1000.0  # Convert millidegrees to degrees
                except (IndexError, ValueError):
                    continue

        return None

    def _parse_load_average(self, loadavg_output: str) -> Optional[float]:
        """Parse 1-minute load average"""

        try:
            parts = loadavg_output.strip().split()
            return float(parts[0])
        except (IndexError, ValueError):
            return None

    def _get_fan_status(self) -> Optional[int]:
        """Get fan RPM status"""

        try:
            result = subprocess.run([
                'sensors'
            ], capture_output=True, text=True, timeout=10)

            lines = result.stdout.split('\n')
            for line in lines:
                if 'Exhaust' in line and 'RPM' in line:
                    try:
                        rpm_str = line.split(':')[1].strip().split(' ')[0]
                        return int(rpm_str)
                    except (IndexError, ValueError):
                        continue

            return None

        except Exception:
            return None

    def _assess_thermal_safety(self, cpu_temp: Optional[float],
                             load_avg: Optional[float],
                             fan_rpm: Optional[int]) -> Dict[str, Any]:
        """Assess overall thermal safety status"""

        if cpu_temp is None or load_avg is None:
            return {
                'level': 'ERROR',
                'message': 'Cannot read thermal sensors',
                'cpu_status': 'UNKNOWN',
                'load_status': 'UNKNOWN',
                'fan_status': 'UNKNOWN'
            }

        # Assess CPU temperature
        if cpu_temp >= self.temperature_threshold_critical:
            cpu_status = 'CRITICAL'
            level = 'CRITICAL'
        elif cpu_temp >= self.temperature_threshold_warning:
            cpu_status = 'WARNING'
            level = 'WARNING'
        elif cpu_temp >= self.temperature_threshold_normal:
            cpu_status = 'CAUTION'
            level = 'CAUTION' if level != 'CRITICAL' else 'CRITICAL'
        else:
            cpu_status = 'NORMAL'
            level = 'NORMAL'

        # Assess system load
        if load_avg >= self.load_threshold_critical:
            load_status = 'CRITICAL'
            level = 'CRITICAL'
        elif load_avg >= self.load_threshold_caution:
            load_status = 'CAUTION'
            if level == 'NORMAL':
                level = 'CAUTION'
        else:
            load_status = 'NORMAL'

        # Assess fan status
        if fan_rpm is None or fan_rpm == 0:
            fan_status = 'FAILED'
            if level != 'CRITICAL':
                level = 'WARNING'  # Fan failure is always at least warning
        elif fan_rpm < 1800:
            fan_status = 'LOW'
        else:
            fan_status = 'NORMAL'

        return {
            'level': level,
            'message': self._get_status_message(level, cpu_temp, load_avg, fan_rpm),
            'cpu_status': cpu_status,
            'load_status': load_status,
            'fan_status': fan_status,
            'cpu_temperature': cpu_temp,
            'load_average': load_avg,
            'fan_rpm': fan_rpm
        }

    def _get_status_message(self, level: str, cpu_temp: float,
                          load_avg: float, fan_rpm: Optional[int]) -> str:
        """Generate status message based on thermal assessment"""

        if level == 'CRITICAL':
            return f"🚨 THERMAL EMERGENCY: CPU {cpu_temp:.1f}°C, Load {load_avg:.1f} - SUSPEND ALL OPERATIONS"
        elif level == 'WARNING':
            return f"⚠️ THERMAL WARNING: CPU {cpu_temp:.1f}°C, Load {load_avg:.1f} - External cooling required"
        elif level == 'CAUTION':
            return f"🟡 THERMAL CAUTION: CPU {cpu_temp:.1f}°C, Load {load_avg:.1f} - Monitor closely"
        else:
            return f"✅ THERMAL NORMAL: CPU {cpu_temp:.1f}°C, Load {load_avg:.1f} - Operations safe"

    def _get_thermal_recommendations(self, safety_status: Dict[str, Any]) -> list:
        """Get specific recommendations based on thermal status"""

        level = safety_status.get('level', 'ERROR')
        recommendations = []

        if level == 'CRITICAL':
            recommendations.extend([
                "🚨 IMMEDIATE: Suspend all AI operations",
                "🔥 IMMEDIATE: Kill high-CPU processes",
                "💨 IMMEDIATE: Activate external cooling",
                "📞 URGENT: Schedule thermal paste replacement",
                "⏸️ DO NOT PROCEED with J5A/Squirt/Sherlock operations"
            ])
        elif level == 'WARNING':
            recommendations.extend([
                "💨 Activate external cooling before proceeding",
                "🔍 Monitor temperature continuously during operations",
                "⚡ Limit concurrent AI processes",
                "🕐 Consider deferring heavy workloads",
                "📊 Log thermal data for trend analysis"
            ])
        elif level == 'CAUTION':
            recommendations.extend([
                "🔍 Monitor temperature during operations",
                "💨 Ensure external cooling is available",
                "⚡ Avoid simultaneous heavy operations",
                "📊 Track thermal trends",
                "🕐 Plan operations during cooler periods"
            ])
        else:  # NORMAL
            recommendations.extend([
                "✅ Normal operations permitted",
                "📊 Continue thermal monitoring",
                "💨 Maintain cooling setup",
                "🔧 Plan preventive maintenance"
            ])

        # Fan-specific recommendations
        fan_status = safety_status.get('fan_status', 'UNKNOWN')
        if fan_status == 'FAILED':
            recommendations.append("🛠️ CRITICAL: Internal fan failed - external cooling only")
        elif fan_status == 'LOW':
            recommendations.append("🔧 Internal fan running low - check for obstruction")

        return recommendations

    def prompt_thermal_check(self, operation_name: str) -> bool:
        """
        Prompt user with thermal check before operation

        Args:
            operation_name: Name of operation to be performed

        Returns:
            True if operation should proceed, False if should abort
        """

        print(f"\n🌡️ THERMAL CHECK REQUIRED BEFORE: {operation_name}")
        print("=" * 60)

        thermal_status = self.get_thermal_status()

        if 'error' in thermal_status:
            print(f"❌ Thermal monitoring error: {thermal_status['error']}")
            print("🚨 Cannot assess thermal safety - operation not recommended")
            return False

        # Display thermal status
        safety = thermal_status['safety_status']
        print(f"🌡️ CPU Temperature: {thermal_status['cpu_temperature']:.1f}°C")
        print(f"⚡ System Load: {thermal_status['load_average']:.2f}")
        print(f"💨 Fan Status: {thermal_status['fan_rpm']} RPM")
        print()
        print(f"📊 Status: {safety['message']}")
        print()

        # Display recommendations
        print("📋 THERMAL RECOMMENDATIONS:")
        for i, rec in enumerate(thermal_status['recommendations'], 1):
            print(f"  {i}. {rec}")
        print()

        # Operation decision
        if thermal_status['operation_allowed']:
            if safety['level'] in ['WARNING', 'CAUTION']:
                print("⚠️ OPERATION PERMITTED WITH CAUTION")
                print("🔍 Enhanced thermal monitoring required during operation")
            else:
                print("✅ OPERATION PERMITTED - Thermal conditions normal")
            return True
        else:
            print("🚨 OPERATION NOT PERMITTED - Thermal emergency protocols active")
            print("❌ Must resolve thermal issues before proceeding")
            return False

    def log_thermal_event(self, event_type: str, details: str = ""):
        """Log thermal events to management file"""

        log_entry = f"{datetime.now().isoformat()} | {event_type} | {details}\n"

        try:
            with open('/home/johnny5/Johny5Alive/thermal_log.txt', 'a') as f:
                f.write(log_entry)
        except Exception as e:
            print(f"⚠️ Failed to log thermal event: {e}")


def thermal_check_required(operation_name: str) -> bool:
    """
    Convenience function for thermal checks
    Use this before any J5A, Squirt, or Sherlock operations
    """

    monitor = ThermalMonitor()
    return monitor.prompt_thermal_check(operation_name)


if __name__ == "__main__":
    # Test thermal monitoring
    monitor = ThermalMonitor()

    print("🧪 Testing Thermal Monitoring System...")

    # Get current status
    status = monitor.get_thermal_status()

    if 'error' in status:
        print(f"❌ Thermal monitoring error: {status['error']}")
    else:
        safety = status['safety_status']
        print(f"🌡️ Current Status: {safety['message']}")
        print(f"📊 Operation Allowed: {status['operation_allowed']}")

        print("\n📋 Current Recommendations:")
        for rec in status['recommendations']:
            print(f"  • {rec}")

    # Test operation check
    print("\n" + "="*60)
    print("🧪 Testing Operation Thermal Check...")
    allowed = monitor.prompt_thermal_check("Test Operation")
    print(f"\n📊 Test Result: {'PROCEED' if allowed else 'ABORT'}")