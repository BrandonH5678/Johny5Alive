"""
IndexAgent - Full-text search index creation and querying with ranking
"""
from __future__ import annotations
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from collections import defaultdict
import math
from .base import BaseAgent

logger = logging.getLogger(__name__)


class IndexAgent(BaseAgent):
    """
    Creates and queries full-text search indexes

    Supports:
    - Document indexing with TF-IDF weighting
    - Fast keyword search
    - Ranked result retrieval
    - Index persistence (save/load)
    - Multiple index types (simple, weighted)
    """

    def __init__(
        self,
        index_path: Optional[str] = None,
        min_term_length: int = 2,
        max_results: int = 100
    ):
        """
        Initialize IndexAgent

        Args:
            index_path: Path to persist index (optional)
            min_term_length: Minimum term length for indexing
            max_results: Maximum search results to return
        """
        self.index_path = Path(index_path) if index_path else None
        self.min_term_length = min_term_length
        self.max_results = max_results

        # In-memory index structures
        self.documents: Dict[str, Dict[str, Any]] = {}  # doc_id -> document
        self.term_index: Dict[str, set] = defaultdict(set)  # term -> {doc_ids}
        self.term_freq: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))  # term -> {doc_id -> count}
        self.doc_lengths: Dict[str, int] = {}  # doc_id -> term count

        # Load existing index if available
        if self.index_path and self.index_path.exists():
            self._load_index()

    def supports(self, target: Any) -> bool:
        """Check if target is an index operation"""
        if not isinstance(target, dict):
            return False

        target_type = target.get('type', '').lower()
        return target_type in ('index', 'search', 'fulltext')

    def retrieve(self, target: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """
        Create or query search index

        Target structure:
            {
                'type': 'index',
                'operation': 'index' | 'search' | 'delete' | 'stats',

                # For indexing:
                'documents': [
                    {'id': 'doc1', 'text': 'Document text...', 'metadata': {...}},
                    ...
                ],

                # For searching:
                'query': 'search terms',
                'max_results': 10,
                'ranking': 'tfidf' | 'count' (default 'tfidf'),

                # For deletion:
                'doc_id': 'doc1' or 'doc_ids': ['doc1', 'doc2'],

                # General:
                'save': True (optional, save index to disk)
            }

        Returns:
            {
                'results': [
                    {
                        'doc_id': 'doc1',
                        'score': 0.92,
                        'text': 'Document text...',
                        'metadata': {...}
                    },
                    ...
                ],
                'count': 42,
                'meta': {
                    'method': 'index',
                    'operation': 'search',
                    'query': 'search terms',
                    'index_size': 1000,
                    'search_time_ms': 12
                }
            }
        """
        import time

        start_time = time.time()

        operation = target.get('operation', 'search').lower()

        if operation == 'index':
            result = self._index_documents(target)
        elif operation == 'search':
            result = self._search(target)
        elif operation == 'delete':
            result = self._delete_documents(target)
        elif operation == 'stats':
            result = self._get_stats()
        else:
            raise ValueError(f"Unknown index operation: {operation}")

        # Save index if requested
        if target.get('save') and self.index_path:
            self._save_index()

        # Add timing metadata
        search_time_ms = int((time.time() - start_time) * 1000)
        if 'meta' not in result:
            result['meta'] = {}
        result['meta']['search_time_ms'] = search_time_ms

        return result

    def _index_documents(self, target: Dict[str, Any]) -> Dict[str, Any]:
        """Index documents for search"""
        documents = target.get('documents', [])

        if not documents:
            raise ValueError("Index operation requires 'documents' list")

        indexed_count = 0

        for doc in documents:
            doc_id = doc.get('id')
            text = doc.get('text', '')
            metadata = doc.get('metadata', {})

            if not doc_id:
                logger.warning("Skipping document without 'id' field")
                continue

            # Store document
            self.documents[doc_id] = {
                'id': doc_id,
                'text': text,
                'metadata': metadata
            }

            # Tokenize and index terms
            terms = self._tokenize(text)
            self.doc_lengths[doc_id] = len(terms)

            for term in terms:
                if len(term) < self.min_term_length:
                    continue

                # Add to term index
                if doc_id not in self.term_index[term]:
                    self.term_index[term].add(doc_id)

                # Track term frequency
                self.term_freq[term][doc_id] += 1

            indexed_count += 1

        logger.info(f"Indexed {indexed_count} documents")

        return {
            'indexed': indexed_count,
            'total_documents': len(self.documents),
            'meta': {
                'method': 'index',
                'operation': 'index',
                'index_size': len(self.documents)
            }
        }

    def _search(self, target: Dict[str, Any]) -> Dict[str, Any]:
        """Search indexed documents"""
        query = target.get('query')
        if not query:
            raise ValueError("Search operation requires 'query'")

        max_results = target.get('max_results', self.max_results)
        ranking_method = target.get('ranking', 'tfidf').lower()

        logger.info(f"Searching: '{query}' (ranking={ranking_method})")

        # Tokenize query
        query_terms = self._tokenize(query)

        # Find matching documents
        if ranking_method == 'tfidf':
            results = self._search_tfidf(query_terms, max_results)
        else:  # count
            results = self._search_count(query_terms, max_results)

        return {
            'results': results,
            'count': len(results),
            'meta': {
                'method': 'index',
                'operation': 'search',
                'query': query,
                'ranking': ranking_method,
                'index_size': len(self.documents)
            }
        }

    def _search_tfidf(self, query_terms: List[str], max_results: int) -> List[Dict[str, Any]]:
        """Search with TF-IDF ranking"""
        # Calculate TF-IDF scores for each document
        doc_scores: Dict[str, float] = defaultdict(float)

        total_docs = len(self.documents)

        for term in query_terms:
            if term not in self.term_index:
                continue

            # Calculate IDF
            doc_freq = len(self.term_index[term])
            idf = math.log(total_docs / (1 + doc_freq))

            # Add TF-IDF score for each document containing this term
            for doc_id in self.term_index[term]:
                tf = self.term_freq[term][doc_id] / self.doc_lengths.get(doc_id, 1)
                doc_scores[doc_id] += tf * idf

        # Sort by score
        sorted_docs = sorted(
            doc_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )[:max_results]

        # Build result list
        results = []
        for doc_id, score in sorted_docs:
            doc = self.documents.get(doc_id)
            if doc:
                results.append({
                    'doc_id': doc_id,
                    'score': round(score, 4),
                    'text': doc['text'],
                    'metadata': doc.get('metadata', {})
                })

        return results

    def _search_count(self, query_terms: List[str], max_results: int) -> List[Dict[str, Any]]:
        """Search with simple term count ranking"""
        # Count matching terms in each document
        doc_scores: Dict[str, int] = defaultdict(int)

        for term in query_terms:
            if term not in self.term_index:
                continue

            for doc_id in self.term_index[term]:
                doc_scores[doc_id] += self.term_freq[term][doc_id]

        # Sort by count
        sorted_docs = sorted(
            doc_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )[:max_results]

        # Build result list
        results = []
        for doc_id, count in sorted_docs:
            doc = self.documents.get(doc_id)
            if doc:
                results.append({
                    'doc_id': doc_id,
                    'score': count,
                    'text': doc['text'],
                    'metadata': doc.get('metadata', {})
                })

        return results

    def _delete_documents(self, target: Dict[str, Any]) -> Dict[str, Any]:
        """Delete documents from index"""
        doc_id = target.get('doc_id')
        doc_ids = target.get('doc_ids', [])

        if doc_id:
            doc_ids = [doc_id]

        if not doc_ids:
            raise ValueError("Delete operation requires 'doc_id' or 'doc_ids'")

        deleted_count = 0

        for did in doc_ids:
            if did in self.documents:
                # Remove document
                del self.documents[did]
                del self.doc_lengths[did]

                # Remove from term indexes
                terms_to_clean = []
                for term, doc_list in self.term_index.items():
                    if did in doc_list:
                        doc_list.remove(did)
                        if not doc_list:  # No more documents for this term
                            terms_to_clean.append(term)

                    if did in self.term_freq[term]:
                        del self.term_freq[term][did]

                # Clean up empty term entries
                for term in terms_to_clean:
                    del self.term_index[term]
                    del self.term_freq[term]

                deleted_count += 1

        logger.info(f"Deleted {deleted_count} documents")

        return {
            'deleted': deleted_count,
            'remaining_documents': len(self.documents),
            'meta': {
                'method': 'index',
                'operation': 'delete',
                'index_size': len(self.documents)
            }
        }

    def _get_stats(self) -> Dict[str, Any]:
        """Get index statistics"""
        return {
            'total_documents': len(self.documents),
            'total_terms': len(self.term_index),
            'avg_doc_length': sum(self.doc_lengths.values()) / len(self.doc_lengths) if self.doc_lengths else 0,
            'meta': {
                'method': 'index',
                'operation': 'stats',
                'index_size': len(self.documents)
            }
        }

    def _tokenize(self, text: str) -> List[str]:
        """Tokenize text into searchable terms"""
        import re

        # Convert to lowercase
        text = text.lower()

        # Extract alphanumeric tokens
        tokens = re.findall(r'\b\w+\b', text)

        # Filter by min length
        tokens = [t for t in tokens if len(t) >= self.min_term_length]

        return tokens

    def _save_index(self):
        """Save index to disk"""
        if not self.index_path:
            return

        try:
            # Convert defaultdicts to regular dicts for JSON serialization
            index_data = {
                'documents': self.documents,
                'term_index': {k: list(v) for k, v in self.term_index.items()},
                'term_freq': {k: dict(v) for k, v in self.term_freq.items()},
                'doc_lengths': self.doc_lengths
            }

            self.index_path.parent.mkdir(parents=True, exist_ok=True)

            with open(self.index_path, 'w') as f:
                json.dump(index_data, f, indent=2)

            logger.info(f"Index saved to {self.index_path}")

        except Exception as e:
            logger.error(f"Failed to save index: {e}")

    def _load_index(self):
        """Load index from disk"""
        if not self.index_path or not self.index_path.exists():
            return

        try:
            with open(self.index_path, 'r') as f:
                index_data = json.load(f)

            self.documents = index_data.get('documents', {})
            self.term_index = defaultdict(list, {k: set(v) for k, v in index_data.get('term_index', {}).items()})
            self.term_freq = defaultdict(lambda: defaultdict(int), {
                k: defaultdict(int, v) for k, v in index_data.get('term_freq', {}).items()
            })
            self.doc_lengths = index_data.get('doc_lengths', {})

            logger.info(f"Index loaded from {self.index_path} ({len(self.documents)} documents)")

        except Exception as e:
            logger.error(f"Failed to load index: {e}")
