#!/usr/bin/env python3
"""
J5A Statistical Sampling Validator
Adapted from Sherlock's statistical sampling concepts for multi-system validation
"""

import os
import sys
import json
import time
import random
import logging
import subprocess
from pathlib import Path
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum

# Add parent directory for imports
sys.path.append(str(Path(__file__).parent.parent))

try:
    from thermal_check import check_thermal_status
except ImportError:
    print("Warning: Thermal check not available")


class ValidationScope(Enum):
    """Scope of validation testing"""
    SYSTEM_INTEGRATION = "system_integration"
    OUTPUT_DELIVERY = "output_delivery"
    PERFORMANCE = "performance"
    RESOURCE_USAGE = "resource_usage"
    CROSS_SYSTEM = "cross_system"


class SystemTarget(Enum):
    """Target system for validation"""
    SQUIRT = "squirt"
    SHERLOCK = "sherlock"
    J5A = "j5a"
    MULTI_SYSTEM = "multi_system"


@dataclass
class J5AValidationSample:
    """J5A-specific validation sample"""
    sample_id: str
    system_target: SystemTarget
    validation_scope: ValidationScope
    sample_data: Any  # File path, config, or test data
    expected_outputs: List[str]
    success_criteria: Dict[str, Any]

    # Validation results
    format_valid: bool = False
    processing_success: bool = False
    output_generation_success: bool = False
    performance_acceptable: bool = False
    quality_score: float = 0.0
    processing_time: float = 0.0
    error_message: Optional[str] = None
    metrics: Dict[str, Any] = None

    def __post_init__(self):
        if self.metrics is None:
            self.metrics = {}


@dataclass
class J5AValidationReport:
    """J5A validation report for multi-system coordination"""
    validation_id: str
    system_target: SystemTarget
    validation_scope: ValidationScope
    timestamp: str

    # Sample statistics
    total_samples: int
    successful_samples: int
    average_quality_score: float
    success_rate: float

    # Specific metrics
    format_success_rate: float
    processing_success_rate: float
    output_generation_rate: float
    performance_acceptance_rate: float

    # Viability assessment
    processing_viability: bool
    recommendations: List[str]
    blocked_progression: bool

    # System-specific metrics
    thermal_safety_status: Dict[str, Any]
    memory_usage_status: Dict[str, Any]
    cross_system_compatibility: Dict[str, Any]


class J5AStatisticalValidator:
    """
    J5A Statistical Sampling Validator for Multi-System Coordination

    Implements validation-focused protocols adapted from Sherlock for:
    - Multi-system task coordination
    - Output delivery validation
    - Resource usage validation
    - Cross-system compatibility
    """

    def __init__(self, sample_size: int = 3):
        """
        Initialize J5A statistical validator

        Args:
            sample_size: Number of samples per validation cycle
        """
        self.sample_size = sample_size
        self.validation_history = []

        # J5A-specific quality thresholds
        self.quality_thresholds = {
            # Core validation thresholds
            "min_success_rate": 0.6,              # 60% samples must succeed overall
            "min_format_success_rate": 0.8,       # 80% format validation success
            "min_processing_success_rate": 0.6,   # 60% processing success
            "min_output_generation_rate": 0.8,    # 80% output generation success
            "min_performance_acceptance_rate": 0.7, # 70% performance acceptable
            "min_quality_score": 0.5,             # Minimum average quality score

            # System-specific thresholds
            "max_memory_usage_gb": 3.0,           # Maximum memory usage
            "max_cpu_temp": 80.0,                 # Maximum CPU temperature
            "max_processing_time_minutes": 30,     # Maximum processing time per sample

            # Cross-system thresholds
            "min_cross_system_compatibility": 0.8, # Cross-system integration success
            "min_coordination_success_rate": 0.7   # Multi-system coordination success
        }

        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    def validate_system_readiness(self, system_target: SystemTarget,
                                validation_scope: ValidationScope,
                                test_inputs: List[Any]) -> J5AValidationReport:
        """
        Validate system readiness using statistical sampling

        Args:
            system_target: Target system to validate
            validation_scope: Scope of validation testing
            test_inputs: List of test inputs/configurations

        Returns:
            J5AValidationReport with assessment and recommendations
        """
        validation_id = f"j5a_validation_{int(time.time())}"

        self.logger.info(f"🔍 Starting J5A validation: {system_target.value} - {validation_scope.value}")
        self.logger.info(f"📊 Test inputs available: {len(test_inputs)}")

        # Generate validation samples
        samples = self._generate_validation_samples(
            validation_id, system_target, validation_scope, test_inputs
        )

        if not samples:
            return self._create_failed_report(validation_id, system_target, validation_scope,
                                            "No validation samples generated")

        self.logger.info(f"🎯 Generated {len(samples)} validation samples")

        # Execute validation on samples
        validated_samples = []
        for i, sample in enumerate(samples):
            self.logger.info(f"📋 Validating sample {i+1}/{len(samples)}: {sample.sample_id}")
            validated_sample = self._validate_single_sample(sample)
            validated_samples.append(validated_sample)

        # Generate comprehensive validation report
        report = self._generate_j5a_validation_report(
            validation_id, system_target, validation_scope, validated_samples
        )

        # Store validation history
        self.validation_history.append(report)

        # Log validation results
        self._log_j5a_validation_results(report)

        return report

    def _generate_validation_samples(self, validation_id: str, system_target: SystemTarget,
                                   validation_scope: ValidationScope,
                                   test_inputs: List[Any]) -> List[J5AValidationSample]:
        """
        Generate validation samples using stratified sampling

        Args:
            validation_id: Unique validation identifier
            system_target: Target system
            validation_scope: Validation scope
            test_inputs: Available test inputs

        Returns:
            List of validation samples
        """
        samples = []

        try:
            if len(test_inputs) == 0:
                self.logger.warning("⚠️ No test inputs provided for validation")
                return samples

            # Stratified sampling: select representative samples
            sample_inputs = self._select_representative_samples(test_inputs)

            for i, test_input in enumerate(sample_inputs):
                sample = J5AValidationSample(
                    sample_id=f"{validation_id}_sample_{i+1}",
                    system_target=system_target,
                    validation_scope=validation_scope,
                    sample_data=test_input,
                    expected_outputs=self._determine_expected_outputs(system_target, validation_scope, test_input),
                    success_criteria=self._determine_success_criteria(system_target, validation_scope)
                )
                samples.append(sample)

        except Exception as e:
            self.logger.error(f"❌ Sample generation error: {e}")

        return samples

    def _select_representative_samples(self, test_inputs: List[Any]) -> List[Any]:
        """
        Select representative samples using stratified sampling

        Args:
            test_inputs: Available test inputs

        Returns:
            Representative sample subset
        """
        if len(test_inputs) <= self.sample_size:
            return test_inputs

        # Stratified sampling approach adapted from Sherlock
        sample_inputs = []

        if len(test_inputs) >= 3:
            # Always include beginning, middle, end for temporal/ordering coverage
            sample_inputs.append(test_inputs[0])                    # Beginning
            sample_inputs.append(test_inputs[len(test_inputs) // 2])  # Middle
            sample_inputs.append(test_inputs[-1])                   # End

            # Fill remaining slots with random samples
            remaining_inputs = [inp for inp in test_inputs if inp not in sample_inputs]
            remaining_needed = max(0, self.sample_size - 3)

            if remaining_needed > 0 and remaining_inputs:
                additional = random.sample(remaining_inputs,
                                         min(remaining_needed, len(remaining_inputs)))
                sample_inputs.extend(additional)
        else:
            # Too few inputs, take what we have
            sample_inputs = test_inputs[:self.sample_size]

        return sample_inputs

    def _validate_single_sample(self, sample: J5AValidationSample) -> J5AValidationSample:
        """
        Validate a single sample through the complete pipeline

        Args:
            sample: Sample to validate

        Returns:
            Updated sample with validation results
        """
        start_time = time.time()

        try:
            self.logger.debug(f"🔍 Validating sample: {sample.sample_id}")

            # 1. Format/Input Validation
            sample.format_valid = self._validate_sample_format(sample)

            if sample.format_valid:
                # 2. Processing Validation
                sample.processing_success = self._validate_sample_processing(sample)

                if sample.processing_success:
                    # 3. Output Generation Validation
                    sample.output_generation_success = self._validate_output_generation(sample)

                    # 4. Performance Validation
                    sample.performance_acceptable = self._validate_performance_metrics(sample)

            # Calculate overall quality score
            sample.quality_score = self._calculate_j5a_quality_score(sample)

            # Collect system metrics
            sample.metrics = self._collect_system_metrics(sample)

        except Exception as e:
            sample.error_message = str(e)
            self.logger.warning(f"⚠️ Sample validation error: {e}")

        sample.processing_time = time.time() - start_time
        return sample

    def _validate_sample_format(self, sample: J5AValidationSample) -> bool:
        """
        Validate sample format and input compatibility

        Args:
            sample: Sample to validate

        Returns:
            bool: Format validation success
        """
        try:
            if sample.validation_scope == ValidationScope.OUTPUT_DELIVERY:
                # For output delivery, check if input exists and is readable
                if isinstance(sample.sample_data, str) and os.path.exists(sample.sample_data):
                    return os.path.getsize(sample.sample_data) > 0
                elif isinstance(sample.sample_data, dict):
                    # Configuration validation
                    return len(sample.sample_data) > 0
                return False

            elif sample.validation_scope == ValidationScope.SYSTEM_INTEGRATION:
                # For system integration, validate configuration structure
                if isinstance(sample.sample_data, dict):
                    required_keys = ['system_config', 'integration_points']
                    return all(key in sample.sample_data for key in required_keys)
                return False

            elif sample.validation_scope == ValidationScope.PERFORMANCE:
                # For performance testing, validate benchmark data
                return sample.sample_data is not None

            elif sample.validation_scope == ValidationScope.RESOURCE_USAGE:
                # For resource usage, validate monitoring configuration
                return isinstance(sample.sample_data, dict)

            else:
                # Generic validation
                return sample.sample_data is not None

        except Exception as e:
            self.logger.warning(f"Format validation error: {e}")
            return False

    def _validate_sample_processing(self, sample: J5AValidationSample) -> bool:
        """
        Validate sample processing capability

        Args:
            sample: Sample to validate

        Returns:
            bool: Processing validation success
        """
        try:
            if sample.system_target == SystemTarget.SQUIRT:
                return self._validate_squirt_processing(sample)
            elif sample.system_target == SystemTarget.SHERLOCK:
                return self._validate_sherlock_processing(sample)
            elif sample.system_target == SystemTarget.J5A:
                return self._validate_j5a_processing(sample)
            elif sample.system_target == SystemTarget.MULTI_SYSTEM:
                return self._validate_multi_system_processing(sample)
            else:
                return False

        except Exception as e:
            self.logger.warning(f"Processing validation error: {e}")
            return False

    def _validate_output_generation(self, sample: J5AValidationSample) -> bool:
        """
        Validate output generation capability

        Args:
            sample: Sample to validate

        Returns:
            bool: Output generation success
        """
        try:
            # Check if expected outputs can be generated
            for expected_output in sample.expected_outputs:
                # Simulate output generation check
                if isinstance(expected_output, str):
                    # Check if output path is valid
                    output_dir = os.path.dirname(expected_output) if os.path.dirname(expected_output) else '.'
                    if not os.path.exists(output_dir):
                        return False

            return True

        except Exception as e:
            self.logger.warning(f"Output generation validation error: {e}")
            return False

    def _validate_performance_metrics(self, sample: J5AValidationSample) -> bool:
        """
        Validate performance requirements

        Args:
            sample: Sample to validate

        Returns:
            bool: Performance validation success
        """
        try:
            # Check processing time
            if sample.processing_time > self.quality_thresholds["max_processing_time_minutes"] * 60:
                return False

            # Check memory usage (if available)
            memory_usage = self._get_current_memory_usage()
            if memory_usage > self.quality_thresholds["max_memory_usage_gb"]:
                return False

            # Check thermal status
            if not self._check_thermal_safety():
                return False

            return True

        except Exception as e:
            self.logger.warning(f"Performance validation error: {e}")
            return False

    def _calculate_j5a_quality_score(self, sample: J5AValidationSample) -> float:
        """
        Calculate J5A-specific quality score (0.0 to 1.0)

        Args:
            sample: Sample with validation results

        Returns:
            float: Quality score
        """
        score = 0.0

        # Format validation (20%)
        if sample.format_valid:
            score += 0.2

        # Processing success (30%)
        if sample.processing_success:
            score += 0.3

        # Output generation (30%)
        if sample.output_generation_success:
            score += 0.3

        # Performance acceptability (20%)
        if sample.performance_acceptable:
            score += 0.2

        return min(1.0, score)

    def _generate_j5a_validation_report(self, validation_id: str, system_target: SystemTarget,
                                      validation_scope: ValidationScope,
                                      samples: List[J5AValidationSample]) -> J5AValidationReport:
        """
        Generate comprehensive J5A validation report

        Args:
            validation_id: Unique validation identifier
            system_target: Target system
            validation_scope: Validation scope
            samples: Validated samples

        Returns:
            J5AValidationReport
        """
        total_samples = len(samples)
        successful_samples = len([s for s in samples if s.quality_score >= 0.5])

        # Calculate metrics
        format_success_rate = len([s for s in samples if s.format_valid]) / total_samples
        processing_success_rate = len([s for s in samples if s.processing_success]) / total_samples
        output_generation_rate = len([s for s in samples if s.output_generation_success]) / total_samples
        performance_acceptance_rate = len([s for s in samples if s.performance_acceptable]) / total_samples

        success_rate = successful_samples / total_samples
        average_quality_score = sum(s.quality_score for s in samples) / total_samples

        # Determine processing viability
        processing_viability = (
            success_rate >= self.quality_thresholds["min_success_rate"] and
            format_success_rate >= self.quality_thresholds["min_format_success_rate"] and
            processing_success_rate >= self.quality_thresholds["min_processing_success_rate"] and
            output_generation_rate >= self.quality_thresholds["min_output_generation_rate"] and
            average_quality_score >= self.quality_thresholds["min_quality_score"]
        )

        # Generate recommendations
        recommendations = self._generate_j5a_recommendations(
            format_success_rate, processing_success_rate,
            output_generation_rate, performance_acceptance_rate, average_quality_score
        )

        # Collect system status
        thermal_status = self._get_thermal_status()
        memory_status = self._get_memory_status()
        cross_system_status = self._get_cross_system_status()

        return J5AValidationReport(
            validation_id=validation_id,
            system_target=system_target,
            validation_scope=validation_scope,
            timestamp=datetime.now().isoformat(),
            total_samples=total_samples,
            successful_samples=successful_samples,
            average_quality_score=average_quality_score,
            success_rate=success_rate,
            format_success_rate=format_success_rate,
            processing_success_rate=processing_success_rate,
            output_generation_rate=output_generation_rate,
            performance_acceptance_rate=performance_acceptance_rate,
            processing_viability=processing_viability,
            recommendations=recommendations,
            blocked_progression=not processing_viability,
            thermal_safety_status=thermal_status,
            memory_usage_status=memory_status,
            cross_system_compatibility=cross_system_status
        )

    def _generate_j5a_recommendations(self, format_rate: float, processing_rate: float,
                                    output_rate: float, performance_rate: float,
                                    quality_score: float) -> List[str]:
        """
        Generate actionable recommendations for J5A systems

        Args:
            format_rate: Format validation success rate
            processing_rate: Processing success rate
            output_rate: Output generation rate
            performance_rate: Performance acceptance rate
            quality_score: Average quality score

        Returns:
            List of recommendations
        """
        recommendations = []

        if format_rate < self.quality_thresholds["min_format_success_rate"]:
            recommendations.append(f"❌ Format validation failing ({format_rate:.1%}). Review input compatibility and format handling.")

        if processing_rate < self.quality_thresholds["min_processing_success_rate"]:
            recommendations.append(f"❌ Processing rate low ({processing_rate:.1%}). Check system integration and error handling.")

        if output_rate < self.quality_thresholds["min_output_generation_rate"]:
            recommendations.append(f"❌ Output generation rate low ({output_rate:.1%}). Verify output pipeline and file permissions.")

        if performance_rate < self.quality_thresholds["min_performance_acceptance_rate"]:
            recommendations.append(f"⚠️ Performance issues detected ({performance_rate:.1%}). Check system resources and optimization.")

        if quality_score < self.quality_thresholds["min_quality_score"]:
            recommendations.append(f"⚠️ Overall quality below threshold ({quality_score:.1%}). Comprehensive pipeline review needed.")

        # System-specific recommendations
        thermal_status = self._get_thermal_status()
        if thermal_status.get('cpu_temp', 0) > 75:
            recommendations.append(f"🔥 Thermal concerns detected. CPU: {thermal_status.get('cpu_temp', 0):.1f}°C")

        memory_status = self._get_memory_status()
        if memory_status.get('usage_gb', 0) > 2.5:
            recommendations.append(f"💾 Memory usage high: {memory_status.get('usage_gb', 0):.1f}GB")

        if not recommendations:
            recommendations.append("✅ All validation metrics within acceptable thresholds.")

        return recommendations

    def _log_j5a_validation_results(self, report: J5AValidationReport):
        """
        Log J5A validation results with comprehensive assessment

        Args:
            report: Validation report to log
        """
        self.logger.info("=" * 70)
        self.logger.info("📊 J5A STATISTICAL VALIDATION RESULTS")
        self.logger.info("=" * 70)
        self.logger.info(f"🎯 System: {report.system_target.value} | Scope: {report.validation_scope.value}")
        self.logger.info(f"📈 Samples Tested: {report.total_samples}")
        self.logger.info(f"✅ Successful Samples: {report.successful_samples}")
        self.logger.info(f"🎯 Overall Success Rate: {report.success_rate:.1%}")
        self.logger.info(f"🔍 Quality Score: {report.average_quality_score:.1%}")

        self.logger.info("\n📋 Detailed Metrics:")
        self.logger.info(f"   📁 Format Success: {report.format_success_rate:.1%}")
        self.logger.info(f"   ⚙️ Processing Success: {report.processing_success_rate:.1%}")
        self.logger.info(f"   📤 Output Generation: {report.output_generation_rate:.1%}")
        self.logger.info(f"   🚀 Performance: {report.performance_acceptance_rate:.1%}")

        viability_status = "✅ VIABLE" if report.processing_viability else "❌ NOT VIABLE"
        self.logger.info(f"\n⚖️ Processing Viability: {viability_status}")

        if report.blocked_progression:
            self.logger.warning("🚨 PROGRESSION BLOCKED - Validation thresholds not met")

        self.logger.info("\n🔧 System Status:")
        self.logger.info(f"   🌡️ Thermal: {report.thermal_safety_status.get('status', 'unknown')}")
        self.logger.info(f"   💾 Memory: {report.memory_usage_status.get('usage_gb', 0):.1f}GB")
        self.logger.info(f"   🔗 Cross-system: {report.cross_system_compatibility.get('status', 'unknown')}")

        self.logger.info("\n💡 Recommendations:")
        for rec in report.recommendations:
            self.logger.info(f"   {rec}")
        self.logger.info("=" * 70)

    # System-specific validation methods (to be implemented)
    def _validate_squirt_processing(self, sample: J5AValidationSample) -> bool:
        return True  # Placeholder

    def _validate_sherlock_processing(self, sample: J5AValidationSample) -> bool:
        return True  # Placeholder

    def _validate_j5a_processing(self, sample: J5AValidationSample) -> bool:
        return True  # Placeholder

    def _validate_multi_system_processing(self, sample: J5AValidationSample) -> bool:
        return True  # Placeholder

    # Utility methods
    def _determine_expected_outputs(self, system_target: SystemTarget,
                                  validation_scope: ValidationScope,
                                  test_input: Any) -> List[str]:
        return ["output.json", "results.txt"]  # Placeholder

    def _determine_success_criteria(self, system_target: SystemTarget,
                                  validation_scope: ValidationScope) -> Dict[str, Any]:
        return {"min_accuracy": 0.8, "max_time_seconds": 300}  # Placeholder

    def _collect_system_metrics(self, sample: J5AValidationSample) -> Dict[str, Any]:
        return {"memory_usage_mb": 512, "cpu_usage_percent": 45}  # Placeholder

    def _get_current_memory_usage(self) -> float:
        try:
            import psutil
            return psutil.virtual_memory().used / (1024**3)  # GB
        except:
            return 1.0  # Default fallback

    def _check_thermal_safety(self) -> bool:
        try:
            thermal_status = check_thermal_status()
            return thermal_status.get('cpu_temp', 0) < self.quality_thresholds["max_cpu_temp"]
        except:
            return True  # Default to safe if check fails

    def _get_thermal_status(self) -> Dict[str, Any]:
        try:
            return check_thermal_status()
        except:
            return {"status": "unknown", "cpu_temp": 0}

    def _get_memory_status(self) -> Dict[str, Any]:
        try:
            import psutil
            mem = psutil.virtual_memory()
            return {
                "usage_gb": mem.used / (1024**3),
                "available_gb": mem.available / (1024**3),
                "percent": mem.percent
            }
        except:
            return {"usage_gb": 0, "available_gb": 0, "percent": 0}

    def _get_cross_system_status(self) -> Dict[str, Any]:
        return {"status": "operational", "systems_connected": ["squirt", "sherlock"]}  # Placeholder

    def _create_failed_report(self, validation_id: str, system_target: SystemTarget,
                            validation_scope: ValidationScope, error_message: str) -> J5AValidationReport:
        """Create a failed validation report"""
        return J5AValidationReport(
            validation_id=validation_id,
            system_target=system_target,
            validation_scope=validation_scope,
            timestamp=datetime.now().isoformat(),
            total_samples=0,
            successful_samples=0,
            average_quality_score=0.0,
            success_rate=0.0,
            format_success_rate=0.0,
            processing_success_rate=0.0,
            output_generation_rate=0.0,
            performance_acceptance_rate=0.0,
            processing_viability=False,
            recommendations=[f"❌ Validation failed: {error_message}"],
            blocked_progression=True,
            thermal_safety_status={"status": "unknown"},
            memory_usage_status={"usage_gb": 0},
            cross_system_compatibility={"status": "unknown"}
        )

    def save_validation_report(self, report: J5AValidationReport,
                             filename: Optional[str] = None) -> str:
        """
        Save validation report to JSON file

        Args:
            report: Validation report to save
            filename: Optional filename, auto-generated if not provided

        Returns:
            str: Saved filename
        """
        if not filename:
            filename = f"j5a_validation_{report.validation_id}.json"

        report_data = asdict(report)

        with open(filename, 'w') as f:
            json.dump(report_data, f, indent=2)

        self.logger.info(f"💾 J5A validation report saved: {filename}")
        return filename


if __name__ == "__main__":
    # Example usage
    validator = J5AStatisticalValidator(sample_size=3)

    # Example validation
    test_inputs = [
        {"config": "test1", "data": "sample1.txt"},
        {"config": "test2", "data": "sample2.txt"},
        {"config": "test3", "data": "sample3.txt"}
    ]

    report = validator.validate_system_readiness(
        system_target=SystemTarget.J5A,
        validation_scope=ValidationScope.SYSTEM_INTEGRATION,
        test_inputs=test_inputs
    )

    # Save report
    validator.save_validation_report(report)

    print(f"Validation completed - Viable: {report.processing_viability}")