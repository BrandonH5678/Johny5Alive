"""
JavaBridge - Python-Java interoperability via JPype
"""
from __future__ import annotations
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class JavaBridge:
    """
    Bridges Python and Java for accessing Java libraries

    Supports:
    - JVM startup/shutdown
    - Java class loading
    - Method invocation
    - Type conversion between Python and Java
    - JAR file classpath management
    """

    def __init__(
        self,
        backend: str = 'jpype',
        jvm_path: Optional[str] = None,
        classpath: Optional[List[str]] = None,
        jvm_options: Optional[List[str]] = None
    ):
        """
        Initialize JavaBridge

        Args:
            backend: Java bridge backend ('jpype' or 'jep')
            jvm_path: Path to JVM library (optional, auto-detected if not provided)
            classpath: List of JAR files and directories to add to classpath
            jvm_options: JVM startup options (e.g. ['-Xmx512m'])
        """
        self.backend = backend.lower()
        self.jvm_path = jvm_path
        self.classpath = classpath or []
        self.jvm_options = jvm_options or []
        self.started = False
        self.jpype = None

        logger.info(f"JavaBridge initialized with {self.backend} backend")

    def start(self):
        """Start JVM"""
        if self.started:
            logger.warning("JVM already started")
            return

        if self.backend == 'jpype':
            self._start_jpype()
        elif self.backend == 'jep':
            self._start_jep()
        else:
            raise ValueError(f"Unknown backend: {self.backend}")

        self.started = True
        logger.info("JVM started successfully")

    def stop(self):
        """Stop JVM"""
        if not self.started:
            logger.warning("JVM not running")
            return

        if self.backend == 'jpype':
            self._stop_jpype()
        elif self.backend == 'jep':
            self._stop_jep()

        self.started = False
        logger.info("JVM stopped")

    def call_method(
        self,
        class_name: str,
        method_name: str,
        args: Optional[List[Any]] = None,
        static: bool = True
    ) -> Any:
        """
        Call Java method

        Args:
            class_name: Fully qualified Java class name (e.g. 'java.lang.Math')
            method_name: Method name
            args: Method arguments
            static: Whether this is a static method

        Returns:
            Method return value (converted to Python type)
        """
        if not self.started:
            raise RuntimeError("JVM not started - call start() first")

        args = args or []

        logger.info(f"Calling {class_name}.{method_name}({args})")

        if self.backend == 'jpype':
            return self._call_method_jpype(class_name, method_name, args, static)
        elif self.backend == 'jep':
            return self._call_method_jep(class_name, method_name, args, static)
        else:
            raise ValueError(f"Unknown backend: {self.backend}")

    def create_instance(self, class_name: str, args: Optional[List[Any]] = None) -> Any:
        """
        Create Java object instance

        Args:
            class_name: Fully qualified Java class name
            args: Constructor arguments

        Returns:
            Java object instance
        """
        if not self.started:
            raise RuntimeError("JVM not started - call start() first")

        args = args or []

        logger.info(f"Creating instance of {class_name}({args})")

        if self.backend == 'jpype':
            return self._create_instance_jpype(class_name, args)
        elif self.backend == 'jep':
            return self._create_instance_jep(class_name, args)
        else:
            raise ValueError(f"Unknown backend: {self.backend}")

    def add_classpath(self, path: str):
        """
        Add JAR file or directory to classpath

        Args:
            path: Path to JAR file or directory
        """
        if self.started:
            logger.warning("Cannot modify classpath after JVM start")
            return

        if not Path(path).exists():
            raise FileNotFoundError(f"Classpath entry not found: {path}")

        self.classpath.append(path)
        logger.info(f"Added to classpath: {path}")

    # JPype backend methods

    def _start_jpype(self):
        """Start JVM using JPype"""
        try:
            import jpype
            import jpype.imports
            self.jpype = jpype
        except ImportError:
            raise ImportError(
                "JPype not installed. Install with: pip install jpype1"
            )

        if jpype.isJVMStarted():
            logger.warning("JVM already started (externally)")
            return

        # Build JVM arguments
        jvm_args = list(self.jvm_options)

        # Add classpath
        if self.classpath:
            classpath_str = ':'.join(self.classpath)  # Unix-style separator
            jvm_args.append(f'-Djava.class.path={classpath_str}')

        logger.info(f"Starting JVM with args: {jvm_args}")

        # Start JVM
        if self.jvm_path:
            jpype.startJVM(self.jvm_path, *jvm_args)
        else:
            jpype.startJVM(*jvm_args)  # Auto-detect JVM

    def _stop_jpype(self):
        """Stop JVM using JPype"""
        if self.jpype and self.jpype.isJVMStarted():
            self.jpype.shutdownJVM()

    def _call_method_jpype(
        self,
        class_name: str,
        method_name: str,
        args: List[Any],
        static: bool
    ) -> Any:
        """Call Java method using JPype"""
        # Import the Java class
        java_class = self.jpype.JClass(class_name)

        if static:
            # Call static method
            method = getattr(java_class, method_name)
            result = method(*args)
        else:
            # Instance method requires an instance
            raise NotImplementedError("Instance method calls require create_instance() first")

        return result

    def _create_instance_jpype(self, class_name: str, args: List[Any]) -> Any:
        """Create Java instance using JPype"""
        java_class = self.jpype.JClass(class_name)
        instance = java_class(*args)
        return instance

    # Jep backend methods

    def _start_jep(self):
        """Start JVM using Jep"""
        try:
            import jep
        except ImportError:
            raise ImportError(
                "Jep not installed. Install with: pip install jep"
            )

        # Jep starts JVM automatically when creating Jep instance
        # We'll create a shared Jep instance
        self.jep_instance = jep.Jep()

        logger.info("Jep instance created (JVM started)")

    def _stop_jep(self):
        """Stop JVM using Jep"""
        if hasattr(self, 'jep_instance'):
            self.jep_instance.close()
            del self.jep_instance

    def _call_method_jep(
        self,
        class_name: str,
        method_name: str,
        args: List[Any],
        static: bool
    ) -> Any:
        """Call Java method using Jep"""
        # Jep uses Python-style method calls
        # This is simplified - real implementation would need more complex marshalling
        raise NotImplementedError("Jep backend method calls not yet implemented")

    def _create_instance_jep(self, class_name: str, args: List[Any]) -> Any:
        """Create Java instance using Jep"""
        raise NotImplementedError("Jep backend instance creation not yet implemented")

    # Utility methods

    def is_started(self) -> bool:
        """Check if JVM is running"""
        return self.started

    def get_java_version(self) -> str:
        """Get Java version"""
        if not self.started:
            raise RuntimeError("JVM not started")

        if self.backend == 'jpype':
            result = self.call_method(
                'java.lang.System',
                'getProperty',
                ['java.version'],
                static=True
            )
            return str(result)
        else:
            return "unknown"
