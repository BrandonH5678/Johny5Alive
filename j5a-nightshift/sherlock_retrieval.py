#!/usr/bin/env python3
"""
Sherlock Retrieval - Enhanced intelligence source discovery and ingestion
Integrates Retriever v2.1 agents for comprehensive intelligence gathering
"""

import sys
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

# Import existing Sherlock components
from sherlock_ingest import ingest
from sherlock_chunk import chunk, select_excerpts

# Import J5A Retrieval Gateway
sys.path.append('ops/fetchers')
from j5a_retrieval_gateway import J5ARetrievalGateway

logger = logging.getLogger(__name__)


class SherlockRetrieval:
    """
    Enhanced Sherlock intelligence retrieval using Retriever v2.1

    Extends base Sherlock ingestion with:
    - Multi-source discovery (web, databases, APIs)
    - OCR for scanned documents
    - Structured data extraction
    - Intelligence indexing and search
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize Sherlock Retrieval with gateway"""
        self.gateway = J5ARetrievalGateway(config)
        self.base_path = Path("/home/johnny5/Johny5Alive/j5a-nightshift")
        self.processed_dir = self.base_path / "ops" / "processed"
        self.processed_dir.mkdir(parents=True, exist_ok=True)

        logger.info("Sherlock Retrieval initialized with v2.1 capabilities")

    def discover_intelligence_sources(
        self,
        topic: str,
        source_types: Optional[List[str]] = None,
        search_depth: str = 'standard'
    ) -> Dict[str, Any]:
        """
        Discover intelligence sources across multiple channels

        Args:
            topic: Intelligence topic/query
            source_types: Types to search ['files', 'web', 'databases', 'apis']
            search_depth: 'quick', 'standard', 'comprehensive'

        Returns:
            Discovered sources with metadata
        """
        logger.info(f"Discovering intelligence sources for: {topic}")

        source_types = source_types or ['files', 'web', 'databases']
        discovered = []

        # File system search
        if 'files' in source_types:
            logger.info("Searching local file sources...")
            file_sources = self._discover_file_sources(topic)
            discovered.extend(file_sources)

        # Web search (if webscraper available)
        if 'web' in source_types:
            logger.info("Searching web sources...")
            web_sources = self._discover_web_sources(topic, search_depth)
            discovered.extend(web_sources)

        # Database search
        if 'databases' in source_types:
            logger.info("Searching database sources...")
            db_sources = self._discover_database_sources(topic)
            discovered.extend(db_sources)

        # API search
        if 'apis' in source_types:
            logger.info("Searching API sources...")
            api_sources = self._discover_api_sources(topic)
            discovered.extend(api_sources)

        return {
            'topic': topic,
            'sources_found': len(discovered),
            'sources': discovered,
            'search_depth': search_depth,
            'method': 'sherlock_v2_discovery'
        }

    def ingest_with_intelligence(
        self,
        source: str,
        extract_structured: bool = True,
        use_ocr: bool = True
    ) -> Dict[str, Any]:
        """
        Ingest source with enhanced intelligence extraction

        Args:
            source: Path or URL to source
            extract_structured: Extract structured data (tables, lists)
            use_ocr: Use OCR for scanned documents

        Returns:
            Ingestion result with extracted content
        """
        logger.info(f"Ingesting with intelligence: {source}")

        source_path = Path(source)

        # Determine if OCR needed
        needs_ocr = use_ocr and source_path.suffix.lower() in ['.pdf', '.png', '.jpg', '.jpeg', '.tiff']

        if needs_ocr:
            logger.info("Using OCR for text extraction...")
            ocr_result = self.gateway.sherlock_ingest_with_ocr(
                source,
                output_dir=str(self.processed_dir)
            )

            if ocr_result.get('success'):
                txt_path = ocr_result['text_path']
            else:
                # Fall back to standard ingestion
                txt_path = ingest(source, output_dir=str(self.processed_dir))
        else:
            # Standard ingestion
            txt_path = ingest(source, output_dir=str(self.processed_dir))

        # Extract structured data if requested
        structured_data = None
        if extract_structured:
            structured_data = self._extract_structured_data(txt_path)

        return {
            'success': True,
            'text_path': txt_path,
            'source': source,
            'ocr_used': needs_ocr,
            'structured_data': structured_data,
            'method': 'sherlock_intelligence_ingest'
        }

    def query_intelligence_database(
        self,
        query: str,
        database_type: str = 'sqlite',
        database_path: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Query Sherlock intelligence database

        Args:
            query: SQL/NoSQL query
            database_type: 'sqlite', 'postgresql', 'mysql', 'mongodb'
            database_path: Path to database file (for SQLite)
            **kwargs: Database connection parameters

        Returns:
            Query results
        """
        logger.info(f"Querying intelligence database: {database_type}")

        # Default to Sherlock database
        if database_type == 'sqlite' and not database_path:
            database_path = str(self.base_path / "sherlock_intelligence.db")

        return self.gateway.sherlock_query_database(
            query,
            database_type=database_type,
            database=database_path,
            **kwargs
        )

    def index_intelligence(
        self,
        documents: List[Dict[str, Any]],
        index_name: str = 'sherlock_main'
    ) -> Dict[str, Any]:
        """
        Index intelligence documents for fast retrieval

        Args:
            documents: List of documents to index
            index_name: Name of the index

        Returns:
            Indexing result
        """
        logger.info(f"Indexing {len(documents)} documents...")

        result = self.gateway.index_agent.retrieve({
            'type': 'index',
            'operation': 'index',
            'documents': documents,
            'index_name': index_name
        })

        return {
            'success': True,
            'indexed_count': result.get('indexed', 0),
            'index_name': index_name,
            'method': 'sherlock_indexing'
        }

    def search_intelligence(
        self,
        query: str,
        index_name: str = 'sherlock_main',
        top_k: int = 10
    ) -> Dict[str, Any]:
        """
        Search indexed intelligence

        Args:
            query: Search query
            index_name: Index to search
            top_k: Number of results to return

        Returns:
            Search results with relevance scores
        """
        logger.info(f"Searching intelligence: '{query}'")

        result = self.gateway.index_agent.retrieve({
            'type': 'index',
            'operation': 'search',
            'query': query,
            'index_name': index_name,
            'top_k': top_k
        })

        return {
            'query': query,
            'results': result.get('results', []),
            'count': result.get('count', 0),
            'method': 'sherlock_search'
        }

    def analyze_source_patterns(
        self,
        sources: List[str],
        pattern_type: str = 'connections'
    ) -> Dict[str, Any]:
        """
        Analyze patterns across multiple intelligence sources

        Args:
            sources: List of source paths
            pattern_type: 'connections', 'timeline', 'entities'

        Returns:
            Pattern analysis results
        """
        logger.info(f"Analyzing patterns: {pattern_type}")

        # Ingest all sources
        ingested = []
        for source in sources:
            try:
                result = self.ingest_with_intelligence(source)
                if result.get('success'):
                    ingested.append(result['text_path'])
            except Exception as e:
                logger.warning(f"Failed to ingest {source}: {e}")

        # Chunk all sources
        all_chunks = []
        for txt_path in ingested:
            chunks_path = chunk(txt_path)
            # Load chunks
            import json
            with open(chunks_path, 'r') as f:
                chunks_data = json.load(f)
                all_chunks.extend(chunks_data.get('chunks', []))

        # Analyze patterns
        analysis = {
            'pattern_type': pattern_type,
            'sources_analyzed': len(ingested),
            'total_chunks': len(all_chunks),
            'patterns': []
        }

        # Pattern detection logic would go here
        # This is a placeholder for the architecture

        return analysis

    # =================================================================
    # Private Helper Methods
    # =================================================================

    def _discover_file_sources(self, topic: str) -> List[Dict[str, Any]]:
        """Discover file-based sources"""
        sources = []

        # Search common Sherlock directories
        search_dirs = [
            self.base_path / "ops" / "inbox",
            self.base_path / "ops" / "processed",
            Path("/home/johnny5/Johny5Alive/sherlock/sources"),
        ]

        for search_dir in search_dirs:
            if not search_dir.exists():
                continue

            try:
                result = self.gateway.fs_agent.retrieve({
                    'type': 'fs',
                    'path': str(search_dir),
                    'pattern': '*',
                    'recursive': True
                })

                for artifact in result.get('artifacts', []):
                    sources.append({
                        'type': 'file',
                        'path': artifact['path'],
                        'name': artifact['name'],
                        'size': artifact.get('size'),
                        'modified': artifact.get('modified')
                    })

            except Exception as e:
                logger.warning(f"Failed to search {search_dir}: {e}")

        return sources

    def _discover_web_sources(self, topic: str, depth: str) -> List[Dict[str, Any]]:
        """Discover web-based sources"""
        sources = []

        # This would integrate with web search APIs or scrapers
        # Placeholder for architecture
        logger.info("Web source discovery: Architecture placeholder")

        return sources

    def _discover_database_sources(self, topic: str) -> List[Dict[str, Any]]:
        """Discover database sources"""
        sources = []

        # Check Sherlock SQLite database
        db_path = self.base_path / "sherlock_intelligence.db"
        if db_path.exists():
            try:
                result = self.gateway.db_agent.retrieve({
                    'type': 'sqlite',
                    'operation': 'tables',
                    'database': str(db_path)
                })

                sources.append({
                    'type': 'database',
                    'database_type': 'sqlite',
                    'path': str(db_path),
                    'tables': result.get('tables', [])
                })

            except Exception as e:
                logger.warning(f"Failed to query database: {e}")

        return sources

    def _discover_api_sources(self, topic: str) -> List[Dict[str, Any]]:
        """Discover API-based sources"""
        sources = []

        # This would integrate with intelligence APIs
        # Placeholder for architecture
        logger.info("API source discovery: Architecture placeholder")

        return sources

    def _extract_structured_data(self, txt_path: str) -> Optional[Dict[str, Any]]:
        """Extract structured data from text"""

        # This would use NLP/ML to extract:
        # - Named entities
        # - Dates/times
        # - Locations
        # - Organizations
        # Placeholder for future implementation

        return {
            'entities': [],
            'dates': [],
            'locations': [],
            'organizations': []
        }


def discover_and_ingest(
    topic: str,
    source_types: Optional[List[str]] = None,
    max_sources: int = 10
) -> List[str]:
    """
    Convenience function: Discover and ingest intelligence sources

    Args:
        topic: Intelligence topic
        source_types: Types of sources to discover
        max_sources: Maximum sources to ingest

    Returns:
        List of ingested text file paths
    """
    retrieval = SherlockRetrieval()

    # Discover sources
    discovery = retrieval.discover_intelligence_sources(topic, source_types)

    # Ingest discovered sources
    ingested_paths = []
    for source in discovery['sources'][:max_sources]:
        try:
            result = retrieval.ingest_with_intelligence(source['path'])
            if result.get('success'):
                ingested_paths.append(result['text_path'])
        except Exception as e:
            logger.warning(f"Failed to ingest {source.get('path')}: {e}")

    logger.info(f"Ingested {len(ingested_paths)} sources for topic: {topic}")
    return ingested_paths


# Example usage and testing
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # Initialize Sherlock Retrieval
    sherlock = SherlockRetrieval()

    # Test source discovery
    print("Testing Sherlock intelligence source discovery...")
    result = sherlock.discover_intelligence_sources(
        topic="UAP intelligence reports",
        source_types=['files', 'databases']
    )

    print(f"\nDiscovered {result['sources_found']} sources")
    for source in result['sources'][:5]:
        print(f"  - {source.get('type')}: {source.get('path') or source.get('name')}")

    print("\n" + "="*60)
    print("Sherlock Retrieval with v2.1 integration ready!")
    print("="*60)
