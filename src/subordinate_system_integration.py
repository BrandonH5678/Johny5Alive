#!/usr/bin/env python3
"""
J5A Subordinate System Integration Framework
Enables J5A to directly access and use tools from Squirt and Sherlock systems
"""

import os
import sys
import importlib.util
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable
import json
from datetime import datetime


class SubordinateSystemIntegration:
    """
    Framework for integrating tools and functions from subordinate systems
    """

    def __init__(self):
        self.system_paths = {
            'squirt': Path('/home/johnny5/Squirt'),
            'sherlock': Path('/home/johnny5/Desktop/Sherlock'),
            'j5a': Path('/home/johnny5/Johny5Alive')
        }

        self.loaded_modules = {}
        self.available_tools = {}
        self.integration_log = []

    def discover_system_tools(self, system_name: str) -> Dict[str, Any]:
        """
        Discover available tools and functions in a subordinate system

        Args:
            system_name: Name of system (squirt, sherlock)

        Returns:
            Dictionary of discovered tools and their metadata
        """

        if system_name not in self.system_paths:
            return {'error': f'Unknown system: {system_name}'}

        system_path = self.system_paths[system_name]
        if not system_path.exists():
            return {'error': f'System path not found: {system_path}'}

        try:
            discovered_tools = {}

            # Find Python modules in src directory
            src_path = system_path / 'src'
            if src_path.exists():
                for py_file in src_path.glob('*.py'):
                    if py_file.name.startswith('__'):
                        continue

                    module_info = self._analyze_python_module(py_file, system_name)
                    if module_info['classes'] or module_info['functions']:
                        discovered_tools[py_file.stem] = module_info

            # Find executable scripts
            for py_file in system_path.glob('*.py'):
                if py_file.name.startswith('__'):
                    continue

                script_info = self._analyze_python_script(py_file, system_name)
                if script_info['executable']:
                    discovered_tools[f"script_{py_file.stem}"] = script_info

            self.available_tools[system_name] = discovered_tools

            self._log_integration_action(
                'discovery',
                f'Discovered {len(discovered_tools)} tools in {system_name}'
            )

            return {
                'success': True,
                'system': system_name,
                'tools_found': len(discovered_tools),
                'tools': discovered_tools
            }

        except Exception as e:
            return {'error': f'Discovery failed: {e}'}

    def _analyze_python_module(self, py_file: Path, system_name: str) -> Dict[str, Any]:
        """Analyze a Python module for classes and functions"""

        try:
            with open(py_file, 'r') as f:
                content = f.read()

            # Simple parsing for classes and functions
            classes = []
            functions = []
            docstring = ""

            lines = content.split('\n')
            for i, line in enumerate(lines):
                stripped = line.strip()

                # Extract module docstring
                if i < 10 and '"""' in stripped and not docstring:
                    docstring = self._extract_docstring(lines, i)

                # Find class definitions
                if stripped.startswith('class '):
                    class_name = stripped.split('class ')[1].split('(')[0].split(':')[0].strip()
                    classes.append({
                        'name': class_name,
                        'line': i + 1,
                        'type': 'class'
                    })

                # Find function definitions
                if stripped.startswith('def ') and not stripped.startswith('def _'):
                    func_name = stripped.split('def ')[1].split('(')[0].strip()
                    functions.append({
                        'name': func_name,
                        'line': i + 1,
                        'type': 'function'
                    })

            return {
                'file_path': str(py_file),
                'system': system_name,
                'module_name': py_file.stem,
                'docstring': docstring,
                'classes': classes,
                'functions': functions,
                'type': 'module'
            }

        except Exception as e:
            return {
                'file_path': str(py_file),
                'error': str(e),
                'classes': [],
                'functions': [],
                'type': 'module'
            }

    def _analyze_python_script(self, py_file: Path, system_name: str) -> Dict[str, Any]:
        """Analyze a Python script for executable capabilities"""

        try:
            with open(py_file, 'r') as f:
                content = f.read()

            # Check if script is executable
            has_main = '__main__' in content
            has_shebang = content.startswith('#!')

            # Extract description from docstring or comments
            description = ""
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if '"""' in line:
                    description = self._extract_docstring(lines, i)
                    break
                elif line.strip().startswith('#') and i < 10:
                    description += line.strip()[1:].strip() + " "

            return {
                'file_path': str(py_file),
                'system': system_name,
                'script_name': py_file.stem,
                'description': description.strip(),
                'executable': has_main or has_shebang,
                'type': 'script'
            }

        except Exception as e:
            return {
                'file_path': str(py_file),
                'error': str(e),
                'executable': False,
                'type': 'script'
            }

    def _extract_docstring(self, lines: List[str], start_index: int) -> str:
        """Extract docstring from lines starting at index"""

        docstring = ""
        in_docstring = False
        quote_style = None

        for i in range(start_index, min(start_index + 20, len(lines))):
            line = lines[i].strip()

            if not in_docstring:
                if '"""' in line:
                    quote_style = '"""'
                    in_docstring = True
                    # Get text after opening quotes
                    after_quotes = line.split('"""', 1)[1]
                    if '"""' in after_quotes:  # Single line docstring
                        docstring = after_quotes.split('"""')[0].strip()
                        break
                    else:
                        docstring = after_quotes.strip()
                elif "'''" in line:
                    quote_style = "'''"
                    in_docstring = True
                    after_quotes = line.split("'''", 1)[1]
                    if "'''" in after_quotes:
                        docstring = after_quotes.split("'''")[0].strip()
                        break
                    else:
                        docstring = after_quotes.strip()
            else:
                if quote_style in line:
                    # End of docstring
                    before_quotes = line.split(quote_style)[0]
                    if before_quotes.strip():
                        docstring += " " + before_quotes.strip()
                    break
                else:
                    docstring += " " + line

        return docstring.strip()

    def load_system_module(self, system_name: str, module_name: str) -> Dict[str, Any]:
        """
        Dynamically load a module from a subordinate system

        Args:
            system_name: Name of system (squirt, sherlock)
            module_name: Name of module to load

        Returns:
            Module loading result
        """

        if system_name not in self.available_tools:
            discovery_result = self.discover_system_tools(system_name)
            if 'error' in discovery_result:
                return discovery_result

        tools = self.available_tools[system_name]
        if module_name not in tools:
            return {'error': f'Module {module_name} not found in {system_name}'}

        module_info = tools[module_name]
        module_path = module_info['file_path']

        try:
            # Add system path to Python path
            system_src_path = str(self.system_paths[system_name] / 'src')
            if system_src_path not in sys.path:
                sys.path.insert(0, system_src_path)
                sys.path.insert(0, str(self.system_paths[system_name]))

            # Load module dynamically
            spec = importlib.util.spec_from_file_location(module_name, module_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Cache loaded module
            cache_key = f"{system_name}.{module_name}"
            self.loaded_modules[cache_key] = {
                'module': module,
                'info': module_info,
                'loaded_at': datetime.now().isoformat()
            }

            self._log_integration_action(
                'module_load',
                f'Loaded {module_name} from {system_name}'
            )

            return {
                'success': True,
                'system': system_name,
                'module': module_name,
                'classes': [cls['name'] for cls in module_info['classes']],
                'functions': [func['name'] for func in module_info['functions']],
                'module_object': module
            }

        except Exception as e:
            return {'error': f'Module loading failed: {e}'}

    def get_system_function(self, system_name: str, module_name: str,
                          function_name: str) -> Optional[Callable]:
        """
        Get a specific function from a subordinate system

        Args:
            system_name: Name of system
            module_name: Name of module
            function_name: Name of function

        Returns:
            Function object or None if not found
        """

        cache_key = f"{system_name}.{module_name}"

        # Load module if not already loaded
        if cache_key not in self.loaded_modules:
            load_result = self.load_system_module(system_name, module_name)
            if 'error' in load_result:
                return None

        try:
            module_data = self.loaded_modules[cache_key]
            module = module_data['module']

            if hasattr(module, function_name):
                function = getattr(module, function_name)

                self._log_integration_action(
                    'function_access',
                    f'Accessed {function_name} from {system_name}.{module_name}'
                )

                return function
            else:
                return None

        except Exception:
            return None

    def get_system_class(self, system_name: str, module_name: str,
                        class_name: str) -> Optional[type]:
        """
        Get a specific class from a subordinate system

        Args:
            system_name: Name of system
            module_name: Name of module
            class_name: Name of class

        Returns:
            Class object or None if not found
        """

        cache_key = f"{system_name}.{module_name}"

        # Load module if not already loaded
        if cache_key not in self.loaded_modules:
            load_result = self.load_system_module(system_name, module_name)
            if 'error' in load_result:
                return None

        try:
            module_data = self.loaded_modules[cache_key]
            module = module_data['module']

            if hasattr(module, class_name):
                class_obj = getattr(module, class_name)

                self._log_integration_action(
                    'class_access',
                    f'Accessed {class_name} from {system_name}.{module_name}'
                )

                return class_obj
            else:
                return None

        except Exception:
            return None

    def execute_system_script(self, system_name: str, script_name: str,
                            args: List[str] = None) -> Dict[str, Any]:
        """
        Execute a script from a subordinate system

        Args:
            system_name: Name of system
            script_name: Name of script (without .py)
            args: Arguments to pass to script

        Returns:
            Execution result
        """

        if system_name not in self.system_paths:
            return {'error': f'Unknown system: {system_name}'}

        script_key = f"script_{script_name}"
        if (system_name not in self.available_tools or
            script_key not in self.available_tools[system_name]):

            # Try to discover tools first
            discovery_result = self.discover_system_tools(system_name)
            if 'error' in discovery_result:
                return discovery_result

        if script_key not in self.available_tools[system_name]:
            return {'error': f'Script {script_name} not found in {system_name}'}

        script_info = self.available_tools[system_name][script_key]
        script_path = script_info['file_path']

        try:
            # Prepare command
            cmd = ['python3', script_path]
            if args:
                cmd.extend(args)

            # Execute script
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
                cwd=str(self.system_paths[system_name])
            )

            self._log_integration_action(
                'script_execution',
                f'Executed {script_name} from {system_name}'
            )

            return {
                'success': True,
                'system': system_name,
                'script': script_name,
                'return_code': result.returncode,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'command': ' '.join(cmd)
            }

        except subprocess.TimeoutExpired:
            return {'error': 'Script execution timeout'}
        except Exception as e:
            return {'error': f'Script execution failed: {e}'}

    def _log_integration_action(self, action_type: str, description: str):
        """Log integration actions for debugging and monitoring"""

        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'action': action_type,
            'description': description
        }

        self.integration_log.append(log_entry)

        # Keep only last 100 entries
        if len(self.integration_log) > 100:
            self.integration_log = self.integration_log[-100:]

    def get_integration_status(self) -> Dict[str, Any]:
        """Get current integration status and statistics"""

        return {
            'loaded_modules': len(self.loaded_modules),
            'available_systems': list(self.available_tools.keys()),
            'total_tools_discovered': sum(
                len(tools) for tools in self.available_tools.values()
            ),
            'recent_actions': self.integration_log[-10:],  # Last 10 actions
            'module_cache': list(self.loaded_modules.keys())
        }

    def save_integration_report(self) -> str:
        """Save integration status to file"""

        report_path = self.system_paths['j5a'] / f"integration_report_{int(datetime.now().timestamp())}.json"

        report_data = {
            'generated_at': datetime.now().isoformat(),
            'integration_status': self.get_integration_status(),
            'available_tools': self.available_tools,
            'loaded_modules': {
                key: {
                    'info': data['info'],
                    'loaded_at': data['loaded_at']
                }
                for key, data in self.loaded_modules.items()
            }
        }

        try:
            with open(report_path, 'w') as f:
                json.dump(report_data, f, indent=2)

            return str(report_path)
        except Exception as e:
            return f"Report save failed: {e}"


def test_subordinate_integration():
    """Test the subordinate system integration framework"""

    integration = SubordinateSystemIntegration()

    print("🧪 Testing Subordinate System Integration Framework...")

    # Test 1: Discover Squirt tools
    print("\n🔍 Test 1: Discovering Squirt Tools")
    squirt_discovery = integration.discover_system_tools('squirt')

    if squirt_discovery.get('success'):
        print(f"✅ Discovered {squirt_discovery['tools_found']} tools in Squirt")

        # Test 2: Load a module
        print("\n📦 Test 2: Loading Vision Validator Module")
        load_result = integration.load_system_module('squirt', 'vision_validator')

        if load_result.get('success'):
            print(f"✅ Loaded vision_validator: {len(load_result['classes'])} classes")

            # Test 3: Get a class from the module
            print("\n🏗️ Test 3: Getting VisionValidator Class")
            validator_class = integration.get_system_class('squirt', 'vision_validator', 'VisionValidator')

            if validator_class:
                print("✅ Successfully accessed VisionValidator class")

                # Test 4: Create instance and test
                print("\n⚡ Test 4: Creating VisionValidator Instance")
                try:
                    validator_instance = validator_class()
                    print("✅ Successfully created VisionValidator instance")

                    # Test 5: Save integration report
                    print("\n📋 Test 5: Saving Integration Report")
                    report_path = integration.save_integration_report()

                    if "failed" not in report_path:
                        print(f"✅ Integration report saved: {Path(report_path).name}")
                        print("✅ Subordinate System Integration Framework fully operational!")
                        return True

                except Exception as e:
                    print(f"❌ Instance creation failed: {e}")
            else:
                print("❌ Could not access VisionValidator class")
        else:
            print(f"❌ Module loading failed: {load_result.get('error', 'Unknown error')}")
    else:
        print(f"❌ Discovery failed: {squirt_discovery.get('error', 'Unknown error')}")

    print("❌ Subordinate System Integration Framework needs debugging")
    return False


if __name__ == "__main__":
    success = test_subordinate_integration()
    if success:
        print("\n🎉 J5A can now access tools from subordinate systems!")
        print("🚀 Visual validation and system coordination capabilities active!")
    else:
        print("\n❌ Integration framework requires fixes")