#!/usr/bin/env python3
"""
J5A Retrieval Gateway - Unified interface for Retriever v2.1 across J5A systems
Provides high-level retrieval operations for Night Shift, Sherlock, Squirt, and Jeeves
"""

import sys
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Union

# Add retriever to path
sys.path.insert(0, str(Path(__file__).parent / "retriever"))

from retriever import (
    # v1 components
    discover_audio_from_homepage,
    RobustWebFetcher,
    # v2 core components
    APIAgent,
    MediaAgent,
    FSAgent,
    DBAgent,
    OcrAgent,
    IndexAgent,
    NLPRouter,
    QueryPlanner,
    QueueBridge,
    # v2.1 advanced extensions
    AgentChain,
    PostgreSQLAgent,
    MySQLAgent,
    MongoDBAgent,
    MLAgent,
    WebScraperAgent,
)

logger = logging.getLogger(__name__)


class J5ARetrievalGateway:
    """
    Unified retrieval gateway for all J5A systems

    Provides high-level operations that intelligently select and orchestrate
    the appropriate Retriever v2.1 agents for each task.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize J5A Retrieval Gateway

        Args:
            config: Optional configuration for database connections, etc.
        """
        self.config = config or {}

        # Initialize core agents
        self.api_agent = APIAgent()
        self.media_agent = MediaAgent()
        self.fs_agent = FSAgent()
        self.db_agent = DBAgent()
        self.ocr_agent = OcrAgent()
        self.index_agent = IndexAgent()

        # Initialize v2.1 agents (with lazy loading for optional dependencies)
        self._postgres_agent = None
        self._mysql_agent = None
        self._mongo_agent = None
        self._ml_agent = None
        self._webscraper_agent = None

        # Initialize orchestration components
        self.nlp_router = NLPRouter(use_transformers=False)  # Use regex by default
        self.query_planner = QueryPlanner()

        # Create agent registry for chaining
        self.agent_registry = {
            'api': self.api_agent,
            'media': self.media_agent,
            'fs': self.fs_agent,
            'db': self.db_agent,
            'ocr': self.ocr_agent,
            'index': self.index_agent,
        }

        logger.info("J5A Retrieval Gateway initialized")

    # =================================================================
    # High-Level Retrieval Operations (Intelligent Auto-Routing)
    # =================================================================

    def retrieve(self, query: str, **kwargs) -> Dict[str, Any]:
        """
        Intelligent retrieval based on natural language query

        Routes to appropriate agents based on query understanding

        Args:
            query: Natural language description of what to retrieve
            **kwargs: Additional parameters (paths, URLs, etc.)

        Returns:
            Retrieval result with data and metadata
        """
        logger.info(f"Intelligent retrieval: '{query}'")

        # Classify query
        classification = self.nlp_router.classify(query)
        intent = classification['intent']
        agent_types = classification['agent_types']

        logger.info(f"Classified as: intent={intent}, agents={agent_types}")

        # Route to appropriate agent
        if not agent_types:
            agent_types = [self.nlp_router.route_to_agent(query)]

        primary_agent = agent_types[0] if agent_types else 'api'
        agent = self.agent_registry.get(primary_agent)

        if not agent:
            raise ValueError(f"No agent available for: {primary_agent}")

        # Build target from query and kwargs
        target = self._build_target_from_query(query, classification, kwargs)

        # Execute retrieval
        return agent.retrieve(target)

    def retrieve_multi_step(self, query: str, **kwargs) -> Dict[str, Any]:
        """
        Multi-step retrieval using query planner and agent chaining

        Args:
            query: Natural language description of multi-step task
            **kwargs: Additional parameters

        Returns:
            Final result after executing all steps
        """
        logger.info(f"Multi-step retrieval: '{query}'")

        # Generate plan
        plan = self.query_planner.plan(query, context=kwargs)
        logger.info(f"Generated plan with {len(plan)} steps")

        # Execute plan with agent chain
        chain = AgentChain(self.agent_registry)
        result = chain.execute(plan, initial_context=kwargs)

        return {
            'data': result.get('final_result'),
            'steps': len(plan),
            'steps_completed': result['steps_completed'],
            'steps_failed': result['steps_failed'],
            'execution_time_ms': result['execution_time_ms'],
            'method': 'multi_step',
            'plan': plan
        }

    # =================================================================
    # Sherlock Integration - Intelligence Analysis
    # =================================================================

    def sherlock_discover_sources(
        self,
        topic: str,
        source_types: Optional[List[str]] = None,
        max_results: int = 10
    ) -> Dict[str, Any]:
        """
        Discover intelligence sources for Sherlock analysis

        Args:
            topic: Intelligence topic to research
            source_types: Types of sources ('web', 'pdf', 'database', etc.)
            max_results: Maximum number of sources to discover

        Returns:
            List of discovered sources with metadata
        """
        logger.info(f"Sherlock source discovery: {topic}")

        source_types = source_types or ['web', 'pdf', 'database']
        discovered_sources = []

        # Use web scraper for web sources
        if 'web' in source_types:
            try:
                scraper = self._get_webscraper_agent()
                # This would need specific URLs or search strategy
                # Placeholder for now
                logger.info("Web source discovery would go here")
            except Exception as e:
                logger.warning(f"Web source discovery failed: {e}")

        # Use FS agent for local files
        if 'file' in source_types or 'pdf' in source_types:
            try:
                result = self.fs_agent.retrieve({
                    'type': 'fs',
                    'path': '/home/johnny5/Johny5Alive/sherlock/sources',
                    'pattern': '*.pdf' if 'pdf' in source_types else '*',
                    'recursive': True
                })
                discovered_sources.extend(result.get('artifacts', []))
            except Exception as e:
                logger.warning(f"File source discovery failed: {e}")

        return {
            'sources': discovered_sources[:max_results],
            'count': len(discovered_sources),
            'topic': topic,
            'method': 'sherlock_discovery'
        }

    def sherlock_ingest_with_ocr(
        self,
        file_path: str,
        output_dir: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Ingest document with OCR support for Sherlock

        Enhances standard Sherlock ingestion with OCR for scanned documents

        Args:
            file_path: Path to document
            output_dir: Output directory for extracted text

        Returns:
            Ingestion result with extracted text path
        """
        logger.info(f"Sherlock ingest with OCR: {file_path}")

        path = Path(file_path)

        # Check if OCR needed (PDF or image)
        if path.suffix.lower() in ['.pdf', '.png', '.jpg', '.jpeg', '.tiff']:
            result = self.ocr_agent.retrieve({
                'type': 'ocr',
                'path': file_path,
                'engine': 'tesseract',
                'output_format': 'txt'
            })

            # Save extracted text
            if output_dir:
                output_path = Path(output_dir) / f"{path.stem}.txt"
                output_path.parent.mkdir(parents=True, exist_ok=True)

                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(result.get('text', ''))

                return {
                    'success': True,
                    'text_path': str(output_path),
                    'char_count': len(result.get('text', '')),
                    'method': 'ocr'
                }

        # Fall back to standard ingestion
        return {
            'success': False,
            'reason': 'File type does not require OCR or OCR failed'
        }

    def sherlock_query_database(
        self,
        query: str,
        database_type: str = 'sqlite',
        **db_params
    ) -> Dict[str, Any]:
        """
        Query database for Sherlock intelligence

        Args:
            query: SQL or NoSQL query
            database_type: 'sqlite', 'postgresql', 'mysql', 'mongodb'
            **db_params: Database connection parameters

        Returns:
            Query results with metadata
        """
        logger.info(f"Sherlock database query: {database_type}")

        if database_type == 'sqlite':
            return self.db_agent.retrieve({
                'type': 'sqlite',
                'operation': 'query',
                'query': query,
                'database': db_params.get('database'),
                'format': 'json'
            })

        elif database_type == 'postgresql':
            agent = self._get_postgres_agent()
            return agent.retrieve({
                'type': 'postgresql',
                'operation': 'query',
                'query': query,
                **db_params
            })

        elif database_type == 'mysql':
            agent = self._get_mysql_agent()
            return agent.retrieve({
                'type': 'mysql',
                'operation': 'query',
                'query': query,
                **db_params
            })

        elif database_type == 'mongodb':
            agent = self._get_mongo_agent()
            return agent.retrieve({
                'type': 'mongodb',
                'operation': 'find',
                **db_params
            })

        else:
            raise ValueError(f"Unknown database type: {database_type}")

    # =================================================================
    # Squirt Integration - Document Automation
    # =================================================================

    def squirt_extract_from_voice(
        self,
        audio_path: str,
        output_format: str = 'text'
    ) -> Dict[str, Any]:
        """
        Extract text from voice memo for Squirt processing

        Args:
            audio_path: Path to audio file
            output_format: Output format ('text', 'json')

        Returns:
            Extracted text and metadata
        """
        logger.info(f"Squirt voice extraction: {audio_path}")

        # Use media agent for audio handling
        result = self.media_agent.retrieve({
            'type': 'file',
            'path': audio_path,
            'operation': 'info'
        })

        # Note: Actual transcription would require Whisper integration
        # This is a placeholder for the architecture
        return {
            'success': True,
            'audio_file': audio_path,
            'format': result.get('format'),
            'duration': result.get('duration'),
            'method': 'squirt_voice_extraction',
            'note': 'Transcription requires Whisper integration'
        }

    def squirt_fetch_template(
        self,
        template_name: str,
        template_source: str = 'local'
    ) -> Dict[str, Any]:
        """
        Fetch document template for Squirt

        Args:
            template_name: Name of template
            template_source: 'local', 'api', 'web'

        Returns:
            Template content and metadata
        """
        logger.info(f"Squirt template fetch: {template_name}")

        if template_source == 'local':
            result = self.fs_agent.retrieve({
                'type': 'fs',
                'path': '/home/johnny5/Johny5Alive/squirt/templates',
                'pattern': f'{template_name}*',
                'recursive': False
            })

            if result.get('count', 0) > 0:
                template_path = result['artifacts'][0]['path']
                with open(template_path, 'r') as f:
                    content = f.read()

                return {
                    'success': True,
                    'template_name': template_name,
                    'template_path': template_path,
                    'content': content,
                    'method': 'local_fs'
                }

        elif template_source == 'api':
            # API-based template retrieval
            result = self.api_agent.retrieve({
                'type': 'rest',
                'url': f'https://templates.example.com/api/v1/templates/{template_name}',
                'method': 'GET'
            })
            return result

        return {'success': False, 'reason': f'Template not found: {template_name}'}

    # =================================================================
    # Jeeves Integration - Personal Assistant Operations
    # =================================================================

    def jeeves_fetch_schedule(
        self,
        calendar_source: str = 'local',
        date_range: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Fetch schedule data for Jeeves

        Args:
            calendar_source: 'local', 'api', 'web'
            date_range: Optional date range filter

        Returns:
            Schedule data
        """
        logger.info(f"Jeeves schedule fetch: {calendar_source}")

        # Placeholder for Jeeves calendar integration
        return {
            'success': True,
            'source': calendar_source,
            'method': 'jeeves_schedule',
            'note': 'Calendar integration pending'
        }

    def jeeves_research_topic(
        self,
        topic: str,
        depth: str = 'summary'
    ) -> Dict[str, Any]:
        """
        Research topic for Jeeves briefings

        Args:
            topic: Topic to research
            depth: 'summary', 'detailed', 'comprehensive'

        Returns:
            Research results
        """
        logger.info(f"Jeeves research: {topic} (depth={depth})")

        # Use multi-step retrieval for comprehensive research
        query = f"Research {topic} and gather information from multiple sources"
        return self.retrieve_multi_step(query, topic=topic, depth=depth)

    # =================================================================
    # Night Shift Integration - Podcast Intelligence
    # =================================================================

    def nightshift_discover_podcast(
        self,
        home_url: str,
        prefer_title: Optional[str] = None,
        prefer_epnum: Optional[int] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Discover podcast audio using v1 or v2.1 agents

        Args:
            home_url: Podcast homepage URL
            prefer_title: Preferred episode title
            prefer_epnum: Preferred episode number
            **kwargs: Additional discovery parameters

        Returns:
            Discovery result with media_url
        """
        logger.info(f"Night Shift podcast discovery: {home_url}")

        # Use v1 discover_audio_from_homepage (production-tested)
        try:
            fetcher = RobustWebFetcher()
            media_url, meta = discover_audio_from_homepage(
                home_url,
                prefer_title,
                prefer_epnum,
                fetcher=fetcher
            )

            return {
                'success': True,
                'media_url': media_url,
                'meta': meta,
                'method': 'v1_discovery'
            }

        except Exception as e:
            logger.error(f"Podcast discovery failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def nightshift_download_media(
        self,
        media_url: str,
        output_path: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Download media file for Night Shift

        Args:
            media_url: URL to download
            output_path: Path to save file
            **kwargs: Additional download parameters

        Returns:
            Download result with file info
        """
        logger.info(f"Night Shift media download: {media_url}")

        return self.media_agent.retrieve({
            'type': 'file',
            'url': media_url,
            'output_path': output_path,
            'operation': 'download',
            **kwargs
        })

    def nightshift_ml_inference(
        self,
        model_path: str,
        input_data: Any,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Run ML inference for Night Shift tasks

        Args:
            model_path: Path to ML model
            input_data: Input data for inference
            **kwargs: Additional inference parameters

        Returns:
            Inference results
        """
        logger.info(f"Night Shift ML inference: {model_path}")

        agent = self._get_ml_agent()
        return agent.retrieve({
            'type': 'ml',
            'model_path': model_path,
            'input_data': input_data,
            'operation': 'predict',
            **kwargs
        })

    # =================================================================
    # Lazy Loading for v2.1 Agents (Optional Dependencies)
    # =================================================================

    def _get_postgres_agent(self) -> PostgreSQLAgent:
        """Lazy load PostgreSQL agent"""
        if self._postgres_agent is None:
            self._postgres_agent = PostgreSQLAgent(
                **self.config.get('postgresql', {})
            )
            self.agent_registry['postgres'] = self._postgres_agent
        return self._postgres_agent

    def _get_mysql_agent(self) -> MySQLAgent:
        """Lazy load MySQL agent"""
        if self._mysql_agent is None:
            self._mysql_agent = MySQLAgent(
                **self.config.get('mysql', {})
            )
            self.agent_registry['mysql'] = self._mysql_agent
        return self._mysql_agent

    def _get_mongo_agent(self) -> MongoDBAgent:
        """Lazy load MongoDB agent"""
        if self._mongo_agent is None:
            self._mongo_agent = MongoDBAgent(
                **self.config.get('mongodb', {})
            )
            self.agent_registry['mongo'] = self._mongo_agent
        return self._mongo_agent

    def _get_ml_agent(self) -> MLAgent:
        """Lazy load ML agent"""
        if self._ml_agent is None:
            self._ml_agent = MLAgent(
                **self.config.get('ml', {})
            )
            self.agent_registry['ml'] = self._ml_agent
        return self._ml_agent

    def _get_webscraper_agent(self) -> WebScraperAgent:
        """Lazy load WebScraper agent"""
        if self._webscraper_agent is None:
            self._webscraper_agent = WebScraperAgent(
                **self.config.get('webscraper', {})
            )
            self.agent_registry['webscraper'] = self._webscraper_agent
        return self._webscraper_agent

    # =================================================================
    # Helper Methods
    # =================================================================

    def _build_target_from_query(
        self,
        query: str,
        classification: Dict[str, Any],
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Build agent target from query and parameters"""

        intent = classification['intent']
        agent_types = classification['agent_types']
        entities = classification.get('entities', {})

        # Start with basic target
        target = {'type': agent_types[0] if agent_types else 'api'}

        # Add entities
        if 'url' in entities and entities['url']:
            target['url'] = entities['url'][0]

        if 'path' in entities and entities['path']:
            target['path'] = entities['path'][0]

        if 'file' in entities and entities['file']:
            target['file'] = entities['file'][0]

        # Merge with provided params
        target.update(params)

        return target


# Singleton instance for easy import
_gateway_instance = None


def get_gateway(config: Optional[Dict[str, Any]] = None) -> J5ARetrievalGateway:
    """Get or create singleton gateway instance"""
    global _gateway_instance
    if _gateway_instance is None:
        _gateway_instance = J5ARetrievalGateway(config)
    return _gateway_instance


# Example usage and testing
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # Initialize gateway
    gateway = J5ARetrievalGateway()

    # Test intelligent retrieval
    print("Testing intelligent retrieval...")
    result = gateway.retrieve("Find Python files in current directory")
    print(f"Result: {result}")

    print("\n" + "="*60)
    print("J5A Retrieval Gateway initialized successfully!")
    print("="*60)
    print("\nAvailable operations:")
    print("  - retrieve(query): Intelligent single-step retrieval")
    print("  - retrieve_multi_step(query): Complex multi-step operations")
    print("  - sherlock_*: Sherlock intelligence operations")
    print("  - squirt_*: Squirt document automation")
    print("  - jeeves_*: Jeeves personal assistant")
    print("  - nightshift_*: Night Shift podcast intelligence")
