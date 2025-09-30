#!/usr/bin/env python3
"""
J5A Visual Validation System
Advanced screenshot and GUI interaction capabilities for Johny5Alive system coordination.
Inherits and extends Squirt's visual validation for system management purposes.
"""

import subprocess
import os
import time
import base64
import json
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime


class J5AVisualValidator:
    """
    J5A Visual Validation System for GUI interaction and system coordination
    Extends Squirt's validation capabilities for managing subordinate systems
    """

    def __init__(self):
        self.screenshot_dir = Path(__file__).parent.parent / "validation_screenshots"
        self.screenshot_dir.mkdir(exist_ok=True)
        self.validation_history_dir = Path(__file__).parent.parent / "validation_history"
        self.validation_history_dir.mkdir(exist_ok=True)
        self.system_screenshot_dir = Path(__file__).parent.parent / "system_screenshots"
        self.system_screenshot_dir.mkdir(exist_ok=True)

    def capture_application_screenshot(self, window_title: Optional[str] = None,
                                     application_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Capture screenshot of specific application or dialog box for GUI interaction

        Args:
            window_title: Specific window title to capture
            application_name: Application name to focus on

        Returns:
            Dictionary with screenshot data and metadata
        """

        try:
            timestamp = int(time.time() * 1000)
            screenshot_path = self.system_screenshot_dir / f"app_capture_{timestamp}.png"

            # Method 1: Capture specific window by title
            if window_title:
                success = self._capture_window_by_title(window_title, str(screenshot_path))
                if success:
                    return self._create_screenshot_result(str(screenshot_path),
                                                        f"window: {window_title}")

            # Method 2: Capture by application name
            if application_name:
                success = self._capture_window_by_app(application_name, str(screenshot_path))
                if success:
                    return self._create_screenshot_result(str(screenshot_path),
                                                        f"application: {application_name}")

            # Method 3: Interactive window selection
            success = self._capture_interactive_window(str(screenshot_path))
            if success:
                return self._create_screenshot_result(str(screenshot_path), "interactive selection")

            # Method 4: Full screen fallback
            success = self._capture_full_screen(str(screenshot_path))
            if success:
                return self._create_screenshot_result(str(screenshot_path), "full screen")

            return {
                'success': False,
                'error': 'All screenshot capture methods failed'
            }

        except Exception as e:
            return {
                'success': False,
                'error': f'Screenshot capture failed: {e}'
            }

    def _capture_window_by_title(self, window_title: str, screenshot_path: str) -> bool:
        """Capture specific window by title"""
        try:
            # Use xdotool to find and focus window, then screenshot
            result = subprocess.run([
                'xdotool', 'search', '--name', window_title, 'windowactivate'
            ], capture_output=True, timeout=5)

            if result.returncode == 0:
                time.sleep(0.5)  # Let window activate
                return self._take_active_window_screenshot(screenshot_path)

        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            pass
        return False

    def _capture_window_by_app(self, app_name: str, screenshot_path: str) -> bool:
        """Capture window by application name"""
        try:
            # Find window by application class
            result = subprocess.run([
                'xdotool', 'search', '--class', app_name, 'windowactivate'
            ], capture_output=True, timeout=5)

            if result.returncode == 0:
                time.sleep(0.5)
                return self._take_active_window_screenshot(screenshot_path)

        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            pass
        return False

    def _capture_interactive_window(self, screenshot_path: str) -> bool:
        """Allow user to select window interactively"""
        try:
            # Use gnome-screenshot window selection
            result = subprocess.run([
                'gnome-screenshot', '--window', '-f', screenshot_path
            ], capture_output=True, timeout=15)

            return result.returncode == 0 and os.path.exists(screenshot_path)

        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            pass
        return False

    def _capture_full_screen(self, screenshot_path: str) -> bool:
        """Capture full screen as fallback"""
        try:
            result = subprocess.run([
                'gnome-screenshot', '-f', screenshot_path
            ], capture_output=True, timeout=10)

            return result.returncode == 0 and os.path.exists(screenshot_path)

        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            pass
        return False

    def _take_active_window_screenshot(self, screenshot_path: str) -> bool:
        """Take screenshot of currently active window"""
        try:
            result = subprocess.run([
                'gnome-screenshot', '--window', '-f', screenshot_path
            ], capture_output=True, timeout=10)

            return result.returncode == 0 and os.path.exists(screenshot_path)

        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            pass
        return False

    def _create_screenshot_result(self, screenshot_path: str, method: str) -> Dict[str, Any]:
        """Create standardized screenshot result"""
        base64_image = self._encode_image_to_base64(screenshot_path)

        return {
            'success': True,
            'screenshot_path': screenshot_path,
            'screenshot_base64': base64_image,
            'capture_method': method,
            'timestamp': datetime.now().isoformat(),
            'ready_for_vision': bool(base64_image)
        }

    def analyze_gui_elements(self, screenshot_data: Dict[str, Any],
                           analysis_type: str = "dialog_analysis") -> Dict[str, Any]:
        """
        Analyze GUI elements for system coordination tasks

        Args:
            screenshot_data: Data from capture_application_screenshot
            analysis_type: Type of analysis (dialog_analysis, system_status, error_detection)

        Returns:
            Analysis results for GUI interaction
        """

        if not screenshot_data.get('success'):
            return {
                'success': False,
                'error': 'Invalid screenshot data provided'
            }

        base64_image = screenshot_data.get('screenshot_base64')
        if not base64_image:
            return {
                'success': False,
                'error': 'No image data available for analysis'
            }

        # Create analysis prompt based on type
        prompt = self._create_gui_analysis_prompt(analysis_type)

        return {
            'success': True,
            'analysis_type': analysis_type,
            'prompt': prompt,
            'image_data': base64_image,
            'ready_for_claude_vision': True,
            'capture_info': {
                'method': screenshot_data.get('capture_method'),
                'timestamp': screenshot_data.get('timestamp'),
                'screenshot_path': screenshot_data.get('screenshot_path')
            }
        }

    def _create_gui_analysis_prompt(self, analysis_type: str) -> str:
        """Create analysis prompts for different GUI analysis types"""

        prompts = {
            'dialog_analysis': """Analyze this GUI dialog or window and identify:

**DIALOG ELEMENTS:**
1. **Dialog Type**: Error dialog, confirmation, settings, file chooser, etc.
2. **Buttons Available**: List all visible buttons (OK, Cancel, Yes, No, etc.)
3. **Input Fields**: Text boxes, dropdowns, checkboxes, radio buttons
4. **Status Indicators**: Progress bars, status text, icons
5. **Error Messages**: Any error text or warning indicators

**INTERACTION GUIDANCE:**
- What actions are available to the user?
- What is the dialog asking for or indicating?
- Are there any error conditions that need addressing?
- What would be the appropriate response options?

**OUTPUT FORMAT:**
Provide structured analysis with:
- Dialog type and purpose
- Available interaction elements
- Recommended actions
- Any issues or errors detected""",

            'system_status': """Analyze this system interface and assess:

**SYSTEM STATUS INDICATORS:**
1. **Application State**: Running, loading, error, ready
2. **Resource Usage**: CPU, memory, disk indicators if visible
3. **Process Status**: Active processes, background tasks
4. **Network Status**: Connection indicators, transfer status
5. **System Health**: Error indicators, warnings, notifications

**COORDINATION ASSESSMENT:**
- Is the system ready for new tasks?
- Are there any blocking conditions?
- What resources are currently in use?
- Are there any priority conflicts with other systems?

**OUTPUT FORMAT:**
Provide assessment with:
- Overall system status (Ready/Busy/Error)
- Specific status details
- Resource availability
- Recommended coordination actions""",

            'error_detection': """Analyze this interface for error conditions and issues:

**ERROR DETECTION:**
1. **Visual Error Indicators**: Red text, warning icons, error dialogs
2. **System Messages**: Error messages, warnings, notifications
3. **UI Anomalies**: Broken layouts, missing elements, corrupted display
4. **Performance Issues**: Frozen interfaces, slow responses
5. **Resource Problems**: Out of memory, disk full, network errors

**TROUBLESHOOTING GUIDANCE:**
- What specific errors are present?
- What are the likely causes?
- What immediate actions should be taken?
- Are there system coordination implications?

**OUTPUT FORMAT:**
Provide error analysis with:
- Specific errors identified
- Severity assessment (Critical/Warning/Info)
- Recommended resolution steps
- System coordination impact"""
        }

        return prompts.get(analysis_type, prompts['dialog_analysis'])

    def capture_subordinate_system_status(self, system_name: str) -> Dict[str, Any]:
        """
        Capture status of subordinate systems (Squirt, Sherlock) for coordination

        Args:
            system_name: Name of system to check (squirt, sherlock)

        Returns:
            System status with visual validation
        """

        system_paths = {
            'squirt': '/home/johnny5/Squirt',
            'sherlock': '/home/johnny5/Desktop/Sherlock'
        }

        if system_name.lower() not in system_paths:
            return {
                'success': False,
                'error': f'Unknown system: {system_name}'
            }

        try:
            # Check if system has GUI components running
            gui_processes = self._check_system_gui_processes(system_name.lower())

            # Capture any visible GUI elements
            screenshot_result = self.capture_application_screenshot(
                application_name=system_name.lower()
            )

            # Analyze system status
            if screenshot_result['success']:
                status_analysis = self.analyze_gui_elements(
                    screenshot_result,
                    analysis_type="system_status"
                )

                return {
                    'success': True,
                    'system_name': system_name,
                    'gui_processes': gui_processes,
                    'visual_status': status_analysis,
                    'coordination_ready': True
                }
            else:
                # No GUI visible, check processes only
                return {
                    'success': True,
                    'system_name': system_name,
                    'gui_processes': gui_processes,
                    'visual_status': None,
                    'coordination_ready': len(gui_processes) == 0  # Ready if no blocking GUI
                }

        except Exception as e:
            return {
                'success': False,
                'error': f'System status check failed: {e}'
            }

    def _check_system_gui_processes(self, system_name: str) -> List[Dict[str, str]]:
        """Check for running GUI processes related to the system"""

        try:
            # Check for common GUI processes
            process_checks = [
                'libreoffice',
                'soffice',
                'writer',
                'calc',
                system_name
            ]

            running_processes = []

            for process in process_checks:
                result = subprocess.run([
                    'pgrep', '-f', process
                ], capture_output=True, text=True)

                if result.returncode == 0 and result.stdout.strip():
                    pids = result.stdout.strip().split('\n')
                    for pid in pids:
                        running_processes.append({
                            'process': process,
                            'pid': pid,
                            'system': system_name
                        })

            return running_processes

        except Exception:
            return []

    def _encode_image_to_base64(self, image_path: str) -> Optional[str]:
        """Encode image to base64 for vision API"""
        try:
            with open(image_path, "rb") as image_file:
                encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
                return encoded_string
        except Exception as e:
            print(f"❌ Image encoding failed: {e}")
            return None

    def save_system_validation_history(self, validation_result: Dict[str, Any],
                                     system_context: str) -> str:
        """Save system validation results to history"""

        timestamp = datetime.now().isoformat()
        history_file = self.validation_history_dir / f"j5a_validation_{int(time.time())}.json"

        history_data = {
            'timestamp': timestamp,
            'system_context': system_context,
            'validation_result': validation_result,
            'validator_info': {
                'version': '1.0',
                'type': 'j5a_system_coordinator',
                'capabilities': ['gui_interaction', 'system_status', 'error_detection']
            }
        }

        try:
            with open(history_file, 'w') as f:
                json.dump(history_data, f, indent=2)

            print(f"📋 J5A validation history saved: {history_file}")
            return str(history_file)

        except Exception as e:
            print(f"❌ Failed to save validation history: {e}")
            return ""


def test_j5a_visual_validator():
    """Test the J5A visual validation system"""

    validator = J5AVisualValidator()

    print("🧪 Testing J5A Visual Validation System...")

    # Test 1: General GUI screenshot
    print("\n📸 Test 1: Application Screenshot Capture")
    screenshot_result = validator.capture_application_screenshot()

    if screenshot_result['success']:
        print(f"✅ Screenshot captured: {screenshot_result['capture_method']}")

        # Test 2: GUI Analysis
        print("\n🔍 Test 2: GUI Element Analysis")
        analysis_result = validator.analyze_gui_elements(
            screenshot_result,
            analysis_type="dialog_analysis"
        )

        if analysis_result['success']:
            print(f"✅ GUI analysis ready: {analysis_result['analysis_type']}")

            # Test 3: System Status Check
            print("\n⚙️ Test 3: Subordinate System Status")
            squirt_status = validator.capture_subordinate_system_status('squirt')

            if squirt_status['success']:
                print(f"✅ Squirt status check: {len(squirt_status['gui_processes'])} GUI processes")

                # Test 4: Save validation history
                print("\n📋 Test 4: Validation History")
                history_file = validator.save_system_validation_history(
                    analysis_result,
                    "J5A System Test"
                )

                if history_file:
                    print("✅ J5A Visual Validation System fully operational!")
                    return True

    print("❌ J5A Visual Validation System needs debugging")
    return False


if __name__ == "__main__":
    success = test_j5a_visual_validator()
    if success:
        print("\n🎉 J5A Visual Validation System ready for system coordination!")
        print("🚀 GUI interaction and subordinate system monitoring active!")
    else:
        print("\n❌ J5A Visual Validation System requires fixes")