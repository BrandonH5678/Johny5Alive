"""
FSAgent - Filesystem retrieval with pattern matching and metadata extraction
"""
from __future__ import annotations
import os
import fnmatch
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Set
from datetime import datetime
from .base import BaseAgent

logger = logging.getLogger(__name__)


class FSAgent(BaseAgent):
    """
    Retrieves files and directories from filesystem

    Supports:
    - File and directory discovery
    - Glob/wildcard pattern matching
    - Regex pattern matching
    - File metadata extraction (size, modified time, permissions)
    - Recursive directory traversal
    - File filtering by size, type, date
    """

    def __init__(self, max_results: int = 1000, follow_symlinks: bool = False):
        """
        Initialize FSAgent

        Args:
            max_results: Maximum number of results to return
            follow_symlinks: Whether to follow symbolic links
        """
        self.max_results = max_results
        self.follow_symlinks = follow_symlinks

    def supports(self, target: Any) -> bool:
        """Check if target is a filesystem operation"""
        if not isinstance(target, dict):
            return False

        target_type = target.get('type', '').lower()
        return target_type in ('fs', 'filesystem', 'file', 'directory')

    def retrieve(self, target: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """
        Retrieve files from filesystem

        Target structure:
            {
                'type': 'fs',
                'path': '/base/path' or '.',
                'pattern': '*.py' (optional, glob pattern),
                'regex': r'.*\.py$' (optional, regex pattern),
                'recursive': True (optional, default False),
                'include_dirs': False (optional, default False),
                'filters': {
                    'min_size': 1024 (optional, bytes),
                    'max_size': 1048576 (optional, bytes),
                    'modified_after': '2024-01-01' (optional, ISO date),
                    'modified_before': '2024-12-31' (optional, ISO date),
                    'extensions': ['.py', '.txt'] (optional)
                }
            }

        Returns:
            {
                'artifacts': [
                    {
                        'path': '/absolute/path/to/file.py',
                        'name': 'file.py',
                        'size_bytes': 12345,
                        'modified': '2024-01-01T12:00:00',
                        'is_dir': False,
                        'extension': '.py',
                        'permissions': 'rw-r--r--'
                    },
                    ...
                ],
                'count': 42,
                'meta': {
                    'method': 'fs',
                    'base_path': '/base/path',
                    'pattern': '*.py',
                    'recursive': True,
                    'search_time_ms': 123
                }
            }
        """
        import time

        start_time = time.time()

        base_path = target.get('path', '.')
        pattern = target.get('pattern')
        regex_pattern = target.get('regex')
        recursive = target.get('recursive', False)
        include_dirs = target.get('include_dirs', False)
        filters = target.get('filters', {})

        logger.info(f"Searching filesystem: {base_path} (pattern={pattern}, recursive={recursive})")

        # Validate base path
        base_path_obj = Path(base_path).resolve()
        if not base_path_obj.exists():
            raise FileNotFoundError(f"Base path does not exist: {base_path}")

        # Discover files
        artifacts = []

        if recursive:
            artifacts = self._search_recursive(
                base_path_obj,
                pattern=pattern,
                regex_pattern=regex_pattern,
                include_dirs=include_dirs,
                filters=filters
            )
        else:
            artifacts = self._search_single_dir(
                base_path_obj,
                pattern=pattern,
                regex_pattern=regex_pattern,
                include_dirs=include_dirs,
                filters=filters
            )

        # Limit results
        if len(artifacts) > self.max_results:
            logger.warning(f"Limiting results from {len(artifacts)} to {self.max_results}")
            artifacts = artifacts[:self.max_results]

        search_time_ms = int((time.time() - start_time) * 1000)

        logger.info(f"Found {len(artifacts)} artifacts in {search_time_ms}ms")

        return {
            'artifacts': artifacts,
            'count': len(artifacts),
            'meta': {
                'method': 'fs',
                'base_path': str(base_path_obj),
                'pattern': pattern,
                'regex': regex_pattern,
                'recursive': recursive,
                'search_time_ms': search_time_ms,
                'truncated': len(artifacts) >= self.max_results
            }
        }

    def _search_single_dir(
        self,
        directory: Path,
        pattern: Optional[str] = None,
        regex_pattern: Optional[str] = None,
        include_dirs: bool = False,
        filters: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """Search a single directory"""
        artifacts = []

        try:
            for item in directory.iterdir():
                if item.is_symlink() and not self.follow_symlinks:
                    continue

                if item.is_dir() and not include_dirs:
                    continue

                # Apply pattern matching
                if pattern and not fnmatch.fnmatch(item.name, pattern):
                    continue

                if regex_pattern:
                    import re
                    if not re.match(regex_pattern, item.name):
                        continue

                # Extract metadata
                metadata = self._extract_metadata(item)

                # Apply filters
                if filters and not self._apply_filters(metadata, filters):
                    continue

                artifacts.append(metadata)

        except PermissionError:
            logger.warning(f"Permission denied: {directory}")

        return artifacts

    def _search_recursive(
        self,
        directory: Path,
        pattern: Optional[str] = None,
        regex_pattern: Optional[str] = None,
        include_dirs: bool = False,
        filters: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """Search directory recursively"""
        artifacts = []
        visited: Set[Path] = set()

        def walk_directory(dir_path: Path):
            if len(artifacts) >= self.max_results:
                return

            # Avoid infinite loops from symlinks
            real_path = dir_path.resolve()
            if real_path in visited:
                return
            visited.add(real_path)

            try:
                for item in dir_path.iterdir():
                    if len(artifacts) >= self.max_results:
                        return

                    if item.is_symlink() and not self.follow_symlinks:
                        continue

                    if item.is_dir():
                        if include_dirs:
                            # Apply pattern matching for directories
                            if pattern and not fnmatch.fnmatch(item.name, pattern):
                                walk_directory(item)
                                continue

                            if regex_pattern:
                                import re
                                if not re.match(regex_pattern, item.name):
                                    walk_directory(item)
                                    continue

                            metadata = self._extract_metadata(item)
                            if filters and not self._apply_filters(metadata, filters):
                                walk_directory(item)
                                continue

                            artifacts.append(metadata)

                        # Recurse into directory
                        walk_directory(item)
                    else:
                        # Apply pattern matching for files
                        if pattern and not fnmatch.fnmatch(item.name, pattern):
                            continue

                        if regex_pattern:
                            import re
                            if not re.match(regex_pattern, item.name):
                                continue

                        metadata = self._extract_metadata(item)

                        # Apply filters
                        if filters and not self._apply_filters(metadata, filters):
                            continue

                        artifacts.append(metadata)

            except PermissionError:
                logger.warning(f"Permission denied: {dir_path}")

        walk_directory(directory)
        return artifacts

    def _extract_metadata(self, path: Path) -> Dict[str, Any]:
        """Extract file/directory metadata"""
        stat = path.stat()

        # Get permissions string
        permissions = oct(stat.st_mode)[-3:]  # Last 3 octal digits

        # Convert to rwx format
        perm_str = ''
        for digit in permissions:
            val = int(digit)
            perm_str += 'r' if val & 4 else '-'
            perm_str += 'w' if val & 2 else '-'
            perm_str += 'x' if val & 1 else '-'

        return {
            'path': str(path.resolve()),
            'name': path.name,
            'size_bytes': stat.st_size if path.is_file() else 0,
            'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
            'created': datetime.fromtimestamp(stat.st_ctime).isoformat(),
            'is_dir': path.is_dir(),
            'is_file': path.is_file(),
            'extension': path.suffix.lower() if path.is_file() else '',
            'permissions': perm_str
        }

    def _apply_filters(self, metadata: Dict[str, Any], filters: Dict[str, Any]) -> bool:
        """Apply filters to file metadata"""
        # Size filters
        min_size = filters.get('min_size')
        if min_size is not None and metadata['size_bytes'] < min_size:
            return False

        max_size = filters.get('max_size')
        if max_size is not None and metadata['size_bytes'] > max_size:
            return False

        # Date filters
        modified_after = filters.get('modified_after')
        if modified_after:
            if metadata['modified'] < modified_after:
                return False

        modified_before = filters.get('modified_before')
        if modified_before:
            if metadata['modified'] > modified_before:
                return False

        # Extension filter
        extensions = filters.get('extensions')
        if extensions:
            if metadata['extension'] not in extensions:
                return False

        return True
