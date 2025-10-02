#!/usr/bin/env python3
"""
Jeeves Overlap Detector - Duplicate & Similarity Detection

Finds overlapping/duplicated functionality using:
- AST signature hashing (function CFG + normalized tokens)
- Text similarity for docs/scripts
- Interface diff (modules exporting similar API surfaces)
"""

import ast
import hashlib
from pathlib import Path
from typing import List, Dict, Set, Tuple
from dataclasses import dataclass
from collections import defaultdict
import difflib


@dataclass
class OverlapFinding:
    """Single overlap detection finding"""
    file1: str
    file2: str
    repo1: str
    repo2: str
    overlap_type: str  # 'duplicate_function', 'similar_code', 'duplicate_api'
    similarity: float  # 0.0-1.0
    reason: str
    metadata: Dict


class OverlapDetector:
    """Detect duplicated or overlapping functionality"""

    def __init__(self, min_similarity: float = 0.92, min_token_len: int = 120):
        """
        Initialize overlap detector.

        Args:
            min_similarity: Minimum similarity threshold (0.0-1.0)
            min_token_len: Minimum token length to consider
        """
        self.min_similarity = min_similarity
        self.min_token_len = min_token_len
        self.findings: List[OverlapFinding] = []

    def detect_overlaps(
        self,
        repos: List[Dict],
        use_ast: bool = True
    ) -> List[OverlapFinding]:
        """
        Detect overlaps across repositories.

        Args:
            repos: List of repo configs with 'name' and 'path'
            use_ast: Use AST-based detection (Python only)

        Returns:
            List of OverlapFindings
        """
        self.findings = []

        if use_ast:
            # Build function signature database
            function_db = self._build_function_database(repos)

            # Find duplicate functions by signature
            self._find_duplicate_functions(function_db)

            # Find similar API surfaces
            self._find_similar_apis(repos)

        # Text-based similarity for all files
        self._find_similar_text(repos)

        return self.findings

    def _normalize_code(self, code: str) -> str:
        """Normalize Python code for comparison"""
        try:
            tree = ast.parse(code)

            # Remove docstrings and comments
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.Module)):
                    if (ast.get_docstring(node)):
                        node.body = [n for n in node.body if not isinstance(n, ast.Expr) or not isinstance(n.value, ast.Str)]

            # Unparse to normalized form
            return ast.unparse(tree)

        except Exception:
            # Fallback: basic normalization
            lines = []
            for line in code.splitlines():
                line = line.strip()
                if line and not line.startswith('#'):
                    lines.append(line)
            return '\n'.join(lines)

    def _get_function_signature(self, func_node: ast.FunctionDef) -> str:
        """Extract normalized signature of a function"""
        # Get function structure without implementation details
        signature_parts = []

        # Function name
        signature_parts.append(func_node.name)

        # Arguments
        args = []
        for arg in func_node.args.args:
            args.append(arg.arg)
        signature_parts.append(','.join(args))

        # Return type annotation if present
        if func_node.returns:
            signature_parts.append(ast.unparse(func_node.returns))

        # Body structure (control flow)
        body_structure = []
        for node in ast.walk(func_node):
            if isinstance(node, (ast.If, ast.For, ast.While, ast.With)):
                body_structure.append(type(node).__name__)

        signature_parts.append('|'.join(body_structure))

        return '::'.join(signature_parts)

    def _hash_function(self, func_node: ast.FunctionDef, source: str) -> str:
        """Generate hash of function for duplicate detection"""
        # Get normalized code
        try:
            func_code = ast.get_source_segment(source, func_node)
            if func_code:
                normalized = self._normalize_code(func_code)
                return hashlib.sha256(normalized.encode()).hexdigest()[:16]
        except Exception:
            pass

        # Fallback: signature-based hash
        signature = self._get_function_signature(func_node)
        return hashlib.sha256(signature.encode()).hexdigest()[:16]

    def _build_function_database(self, repos: List[Dict]) -> Dict[str, List[Dict]]:
        """Build database of functions across repos"""
        function_db = defaultdict(list)

        for repo in repos:
            repo_path = Path(repo['path'])
            repo_name = repo['name']

            for py_file in repo_path.rglob('*.py'):
                if '__pycache__' in str(py_file) or '.venv' in str(py_file):
                    continue

                try:
                    with open(py_file) as f:
                        source = f.read()

                    tree = ast.parse(source)

                    for node in ast.walk(tree):
                        if isinstance(node, ast.FunctionDef):
                            func_hash = self._hash_function(node, source)

                            function_db[func_hash].append({
                                'file': str(py_file.relative_to(repo_path)),
                                'repo': repo_name,
                                'name': node.name,
                                'lineno': node.lineno,
                                'signature': self._get_function_signature(node)
                            })

                except Exception:
                    continue

        return function_db

    def _find_duplicate_functions(self, function_db: Dict[str, List[Dict]]):
        """Find functions with identical hashes across repos"""
        for func_hash, instances in function_db.items():
            if len(instances) > 1:
                # Found duplicates
                for i in range(len(instances)):
                    for j in range(i + 1, len(instances)):
                        inst1, inst2 = instances[i], instances[j]

                        # Skip if same repo and same file
                        if inst1['repo'] == inst2['repo'] and inst1['file'] == inst2['file']:
                            continue

                        self.findings.append(OverlapFinding(
                            file1=inst1['file'],
                            file2=inst2['file'],
                            repo1=inst1['repo'],
                            repo2=inst2['repo'],
                            overlap_type='duplicate_function',
                            similarity=1.0,
                            reason=f"Identical function '{inst1['name']}' (hash: {func_hash})",
                            metadata={
                                'func1_line': inst1['lineno'],
                                'func2_line': inst2['lineno'],
                                'signature': inst1['signature']
                            }
                        ))

    def _find_similar_apis(self, repos: List[Dict]):
        """Find modules with similar exported APIs"""
        api_db = {}

        for repo in repos:
            repo_path = Path(repo['path'])
            repo_name = repo['name']

            for py_file in repo_path.rglob('*.py'):
                if '__pycache__' in str(py_file) or '.venv' in str(py_file):
                    continue

                try:
                    with open(py_file) as f:
                        tree = ast.parse(f.read())

                    # Extract public API (functions and classes at module level)
                    api_symbols = set()

                    for node in tree.body:
                        if isinstance(node, ast.FunctionDef) and not node.name.startswith('_'):
                            api_symbols.add(f"func:{node.name}")
                        elif isinstance(node, ast.ClassDef) and not node.name.startswith('_'):
                            api_symbols.add(f"class:{node.name}")

                    if api_symbols:
                        api_db[str(py_file.relative_to(repo_path))] = {
                            'repo': repo_name,
                            'symbols': api_symbols
                        }

                except Exception:
                    continue

        # Compare APIs
        files = list(api_db.keys())
        for i in range(len(files)):
            for j in range(i + 1, len(files)):
                file1, file2 = files[i], files[j]
                api1 = api_db[file1]
                api2 = api_db[file2]

                # Skip if same repo
                if api1['repo'] == api2['repo']:
                    continue

                # Calculate Jaccard similarity
                symbols1 = api1['symbols']
                symbols2 = api2['symbols']
                intersection = len(symbols1 & symbols2)
                union = len(symbols1 | symbols2)

                if union > 0:
                    similarity = intersection / union

                    if similarity >= self.min_similarity:
                        self.findings.append(OverlapFinding(
                            file1=file1,
                            file2=file2,
                            repo1=api1['repo'],
                            repo2=api2['repo'],
                            overlap_type='duplicate_api',
                            similarity=similarity,
                            reason=f"Similar API surface: {intersection} shared symbols",
                            metadata={
                                'shared_symbols': list(symbols1 & symbols2),
                                'total_symbols': union
                            }
                        ))

    def _find_similar_text(self, repos: List[Dict]):
        """Find similar text blocks (for scripts, docs, etc.)"""
        text_db = []

        for repo in repos:
            repo_path = Path(repo['path'])
            repo_name = repo['name']

            for file_path in repo_path.rglob('*'):
                if not file_path.is_file():
                    continue

                if file_path.suffix in {'.py', '.sh', '.js', '.md', '.txt'}:
                    if '__pycache__' in str(file_path) or '.venv' in str(file_path):
                        continue

                    try:
                        with open(file_path) as f:
                            content = f.read()

                        # Only consider files with minimum length
                        if len(content) >= self.min_token_len:
                            text_db.append({
                                'file': str(file_path.relative_to(repo_path)),
                                'repo': repo_name,
                                'content': content
                            })

                    except Exception:
                        continue

        # Compare text similarity
        for i in range(len(text_db)):
            for j in range(i + 1, len(text_db)):
                item1, item2 = text_db[i], text_db[j]

                # Skip if same repo and same file
                if item1['repo'] == item2['repo'] and item1['file'] == item2['file']:
                    continue

                # Calculate similarity using SequenceMatcher
                similarity = difflib.SequenceMatcher(
                    None,
                    item1['content'],
                    item2['content']
                ).ratio()

                if similarity >= self.min_similarity:
                    self.findings.append(OverlapFinding(
                        file1=item1['file'],
                        file2=item2['file'],
                        repo1=item1['repo'],
                        repo2=item2['repo'],
                        overlap_type='similar_code',
                        similarity=similarity,
                        reason=f"Text similarity: {similarity:.1%}",
                        metadata={
                            'size1': len(item1['content']),
                            'size2': len(item2['content'])
                        }
                    ))


if __name__ == "__main__":
    # Test overlap detector
    detector = OverlapDetector()

    repos = [
        {'name': 'j5a', 'path': '/home/johnny5/Johny5Alive'},
        {'name': 'squirt', 'path': '/home/johnny5/Squirt'},
        {'name': 'sherlock', 'path': '/home/johnny5/Sherlock'}
    ]

    findings = detector.detect_overlaps(repos, use_ast=True)

    print(f"\n{'='*70}")
    print("JEEVES OVERLAP DETECTION RESULTS")
    print(f"{'='*70}\n")

    print(f"Total overlaps found: {len(findings)}\n")

    for finding in findings[:10]:
        print(f"[{finding.overlap_type.upper()}] {finding.similarity:.1%} similarity")
        print(f"  {finding.repo1}/{finding.file1}")
        print(f"  {finding.repo2}/{finding.file2}")
        print(f"  Reason: {finding.reason}\n")
