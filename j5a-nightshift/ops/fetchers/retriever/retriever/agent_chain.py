"""
AgentChain - Automatic output-to-input piping between agents
"""
from __future__ import annotations
import logging
from typing import Dict, Any, List, Optional, Callable
from .base import BaseAgent

logger = logging.getLogger(__name__)


class AgentChain:
    """
    Chains multiple agents together with automatic data flow

    Supports:
    - Sequential agent execution
    - Automatic output-to-input piping
    - Data transformation between steps
    - Conditional execution
    - Error handling and rollback
    - Progress tracking
    """

    def __init__(
        self,
        agents: Optional[Dict[str, BaseAgent]] = None,
        on_step_complete: Optional[Callable] = None,
        on_error: Optional[Callable] = None
    ):
        """
        Initialize AgentChain

        Args:
            agents: Dictionary of agent_type -> agent_instance
            on_step_complete: Callback called after each step (step_num, result)
            on_error: Callback called on error (step_num, error)
        """
        self.agents = agents or {}
        self.on_step_complete = on_step_complete
        self.on_error = on_error
        self.execution_history: List[Dict[str, Any]] = []

    def register_agent(self, agent_type: str, agent: BaseAgent):
        """Register an agent for use in chains"""
        self.agents[agent_type] = agent
        logger.info(f"Registered agent: {agent_type}")

    def execute(
        self,
        plan: List[Dict[str, Any]],
        initial_context: Optional[Dict[str, Any]] = None,
        stop_on_error: bool = True
    ) -> Dict[str, Any]:
        """
        Execute a multi-step plan with agent chaining

        Args:
            plan: List of execution steps:
                [
                    {
                        'agent': 'fs',
                        'target': {...},
                        'description': 'Find files',
                        'depends_on': 0,  # Optional: step index this depends on
                        'transform': 'extract_paths',  # Optional: data transformation
                        'condition': {'field': 'count', 'op': '>', 'value': 0}  # Optional
                    },
                    ...
                ]
            initial_context: Initial context data available to all steps
            stop_on_error: Stop execution on first error

        Returns:
            {
                'results': [step_result1, step_result2, ...],
                'final_result': last_step_result,
                'execution_time_ms': 1234,
                'steps_completed': 5,
                'steps_failed': 0,
                'context': final_context
            }
        """
        import time

        start_time = time.time()
        context = initial_context or {}
        results = []
        steps_completed = 0
        steps_failed = 0

        self.execution_history = []

        logger.info(f"Executing chain with {len(plan)} steps")

        for step_num, step in enumerate(plan):
            try:
                logger.info(f"Step {step_num + 1}/{len(plan)}: {step.get('description', 'Unnamed step')}")

                # Check condition if specified
                if 'condition' in step:
                    if not self._check_condition(step['condition'], context, results):
                        logger.info(f"Step {step_num + 1} condition not met - skipping")
                        continue

                # Get agent
                agent_type = step.get('agent')
                if not agent_type or agent_type not in self.agents:
                    raise ValueError(f"Unknown agent type: {agent_type}")

                agent = self.agents[agent_type]

                # Build target from step config and context
                target = self._build_target(step, context, results)

                # Execute agent
                step_start = time.time()
                result = agent.retrieve(target)
                step_duration = int((time.time() - step_start) * 1000)

                # Transform result if specified
                if 'transform' in step:
                    result = self._transform_result(result, step['transform'])

                # Update context
                context[f'step_{step_num}_result'] = result
                context['last_result'] = result

                # Store result
                results.append(result)
                steps_completed += 1

                # Record in history
                self.execution_history.append({
                    'step': step_num,
                    'agent': agent_type,
                    'description': step.get('description'),
                    'duration_ms': step_duration,
                    'success': True
                })

                # Callback
                if self.on_step_complete:
                    self.on_step_complete(step_num, result)

                logger.info(f"Step {step_num + 1} completed in {step_duration}ms")

            except Exception as e:
                steps_failed += 1
                error_msg = str(e)

                logger.error(f"Step {step_num + 1} failed: {error_msg}")

                # Record error in history
                self.execution_history.append({
                    'step': step_num,
                    'agent': step.get('agent'),
                    'description': step.get('description'),
                    'error': error_msg,
                    'success': False
                })

                # Callback
                if self.on_error:
                    self.on_error(step_num, e)

                # Stop or continue
                if stop_on_error:
                    break
                else:
                    results.append({'error': error_msg})

        execution_time_ms = int((time.time() - start_time) * 1000)

        logger.info(
            f"Chain execution complete: {steps_completed} successful, "
            f"{steps_failed} failed, {execution_time_ms}ms total"
        )

        return {
            'results': results,
            'final_result': results[-1] if results else None,
            'execution_time_ms': execution_time_ms,
            'steps_completed': steps_completed,
            'steps_failed': steps_failed,
            'context': context,
            'history': self.execution_history
        }

    def _build_target(
        self,
        step: Dict[str, Any],
        context: Dict[str, Any],
        results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Build target configuration from step, context, and previous results"""
        target = step.get('target', {}).copy()

        # Handle dependencies (pipe output from previous step)
        if 'depends_on' in step:
            dep_index = step['depends_on']
            if dep_index < len(results):
                prev_result = results[dep_index]

                # Auto-pipe common fields
                if 'artifacts' in prev_result and 'path' not in target:
                    # Pipe first artifact path
                    if prev_result['artifacts']:
                        target['path'] = prev_result['artifacts'][0]['path']

                if 'data' in prev_result and 'input_data' not in target:
                    # Pipe data from previous step
                    target['input_data'] = prev_result['data']

        # Variable substitution from context
        target = self._substitute_variables(target, context)

        return target

    def _substitute_variables(self, obj: Any, context: Dict[str, Any]) -> Any:
        """Recursively substitute variables like {{variable_name}} from context"""
        if isinstance(obj, str):
            # Simple variable substitution
            import re
            pattern = r'\{\{(\w+)\}\}'

            def replace_var(match):
                var_name = match.group(1)
                return str(context.get(var_name, match.group(0)))

            return re.sub(pattern, replace_var, obj)

        elif isinstance(obj, dict):
            return {k: self._substitute_variables(v, context) for k, v in obj.items()}

        elif isinstance(obj, list):
            return [self._substitute_variables(item, context) for item in obj]

        return obj

    def _check_condition(
        self,
        condition: Dict[str, Any],
        context: Dict[str, Any],
        results: List[Dict[str, Any]]
    ) -> bool:
        """Check if condition is met"""
        field = condition.get('field')
        op = condition.get('op')
        value = condition.get('value')

        # Get field value from last result or context
        if results:
            last_result = results[-1]
            field_value = last_result.get(field)
        else:
            field_value = context.get(field)

        # Evaluate condition
        if op == '>':
            return field_value > value
        elif op == '>=':
            return field_value >= value
        elif op == '<':
            return field_value < value
        elif op == '<=':
            return field_value <= value
        elif op == '==':
            return field_value == value
        elif op == '!=':
            return field_value != value
        elif op == 'in':
            return field_value in value
        elif op == 'not_in':
            return field_value not in value
        else:
            logger.warning(f"Unknown condition operator: {op}")
            return True

    def _transform_result(self, result: Dict[str, Any], transform: str) -> Dict[str, Any]:
        """Apply transformation to result"""

        if transform == 'extract_paths':
            # Extract file paths from artifacts
            if 'artifacts' in result:
                return {
                    'paths': [item['path'] for item in result['artifacts']],
                    'count': len(result['artifacts'])
                }

        elif transform == 'extract_data':
            # Extract just the data field
            return {'data': result.get('data')}

        elif transform == 'flatten':
            # Flatten nested results
            if 'results' in result:
                return {'items': result['results']}

        elif transform == 'count_only':
            # Return just counts
            return {
                'count': result.get('count', 0),
                'row_count': result.get('row_count', 0)
            }

        # No transformation
        return result

    def get_history(self) -> List[Dict[str, Any]]:
        """Get execution history"""
        return self.execution_history

    def clear_history(self):
        """Clear execution history"""
        self.execution_history = []
