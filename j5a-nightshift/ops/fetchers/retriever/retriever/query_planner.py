"""
QueryPlanner - Multi-step retrieval plan generation and orchestration
"""
from __future__ import annotations
import logging
from typing import Dict, Any, List, Optional
from .nlp_router import NLPRouter

logger = logging.getLogger(__name__)


class QueryPlanner:
    """
    Generates multi-step retrieval plans from natural language instructions

    Supports:
    - Natural language query understanding
    - Multi-step plan generation
    - Agent coordination
    - Task decomposition
    - Plan optimization
    """

    def __init__(self, nlp_router: Optional[NLPRouter] = None):
        """
        Initialize QueryPlanner

        Args:
            nlp_router: NLPRouter instance for query classification (optional)
        """
        self.nlp_router = nlp_router or NLPRouter()

        # Plan templates for common task patterns
        self.plan_templates = {
            'download_and_extract': [
                {'agent': 'media', 'operation': 'download'},
                {'agent': 'ocr', 'operation': 'extract_text'},
            ],
            'search_and_retrieve': [
                {'agent': 'index', 'operation': 'search'},
                {'agent': 'fs', 'operation': 'retrieve_files'},
            ],
            'query_and_export': [
                {'agent': 'db', 'operation': 'query'},
                {'agent': 'fs', 'operation': 'save_results'},
            ],
            'crawl_and_index': [
                {'agent': 'api', 'operation': 'fetch_pages'},
                {'agent': 'ocr', 'operation': 'extract_text'},
                {'agent': 'index', 'operation': 'index_documents'},
            ],
        }

    def plan(self, instruction: str, context: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Generate execution plan from natural language instruction

        Args:
            instruction: Natural language task description
            context: Optional context (previous results, configuration, etc.)

        Returns:
            List of plan steps:
            [
                {
                    'agent': 'media',
                    'target': {
                        'type': 'media',
                        'url': 'https://example.com/file.mp3',
                        'output_dir': '/tmp/downloads'
                    },
                    'description': 'Download audio file from URL'
                },
                {
                    'agent': 'ocr',
                    'target': {
                        'type': 'ocr',
                        'path': '/tmp/downloads/file.mp3'
                    },
                    'description': 'Extract text from downloaded file',
                    'depends_on': 0  # Step index this depends on
                },
                ...
            ]
        """
        logger.info(f"Planning: '{instruction[:100]}...'")

        context = context or {}

        # Classify the instruction
        classification = self.nlp_router.classify(instruction)

        intent = classification['intent']
        agent_types = classification['agent_types']
        entities = classification['entities']
        keywords = classification['keywords']

        logger.info(f"Classified: intent={intent}, agents={agent_types}")

        # Check for multi-step patterns
        plan_steps = []

        # Pattern matching for complex workflows
        if self._matches_pattern(keywords, ['download', 'extract', 'text']):
            plan_steps = self._plan_download_and_extract(entities, context)

        elif self._matches_pattern(keywords, ['search', 'find', 'retrieve']):
            plan_steps = self._plan_search_and_retrieve(entities, context)

        elif self._matches_pattern(keywords, ['query', 'database', 'export']):
            plan_steps = self._plan_query_and_export(entities, context)

        elif self._matches_pattern(keywords, ['crawl', 'index', 'website']):
            plan_steps = self._plan_crawl_and_index(entities, context)

        # Fallback: single-step plan
        if not plan_steps:
            plan_steps = self._plan_single_step(classification, entities, context)

        logger.info(f"Generated plan with {len(plan_steps)} steps")

        return plan_steps

    def _plan_single_step(
        self,
        classification: Dict[str, Any],
        entities: Dict[str, List[str]],
        context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate single-step plan for simple tasks"""

        agent_types = classification['agent_types']
        agent = agent_types[0] if agent_types else 'api'

        # Build target based on entities and agent type
        target = {'type': agent}

        if agent == 'media':
            if 'url' in entities:
                target['url'] = entities['url'][0]
            if 'file' in entities:
                target['output_filename'] = entities['file'][0]
            target['output_dir'] = context.get('output_dir', '.')

        elif agent == 'fs':
            if 'path' in entities:
                target['path'] = entities['path'][0]
            else:
                target['path'] = context.get('base_path', '.')

            # Add pattern if mentioned
            if 'file' in entities:
                file_ext = entities['file'][0].split('.')[-1]
                target['pattern'] = f'*.{file_ext}'

        elif agent == 'db':
            if 'path' in entities:
                target['path'] = entities['path'][0]
            else:
                target['path'] = context.get('db_path', 'data.db')

            target['operation'] = 'tables'  # Default: list tables

        elif agent == 'ocr':
            if 'path' in entities:
                target['path'] = entities['path'][0]
            elif 'file' in entities:
                target['path'] = entities['file'][0]

        elif agent == 'index':
            target['operation'] = 'search'
            # Extract query from instruction (simple heuristic)
            query_words = classification['keywords']
            target['query'] = ' '.join(query_words[:5])

        elif agent == 'api':
            if 'url' in entities:
                target['url'] = entities['url'][0]
                target['method'] = 'GET'

        return [{
            'agent': agent,
            'target': target,
            'description': f'{classification["intent"].capitalize()} using {agent} agent'
        }]

    def _plan_download_and_extract(
        self,
        entities: Dict[str, List[str]],
        context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Plan for downloading media and extracting text"""

        url = entities.get('url', [None])[0]
        if not url:
            return []

        output_dir = context.get('output_dir', '/tmp/retriever_downloads')
        filename = entities.get('file', ['downloaded_file'])[0]

        steps = [
            {
                'agent': 'media',
                'target': {
                    'type': 'media',
                    'url': url,
                    'output_dir': output_dir,
                    'output_filename': filename
                },
                'description': f'Download file from {url}'
            },
            {
                'agent': 'ocr',
                'target': {
                    'type': 'ocr',
                    'path': f'{output_dir}/{filename}'
                },
                'description': 'Extract text from downloaded file',
                'depends_on': 0
            }
        ]

        return steps

    def _plan_search_and_retrieve(
        self,
        entities: Dict[str, List[str]],
        context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Plan for searching and retrieving files"""

        search_path = entities.get('path', ['.'])[0]
        file_pattern = context.get('pattern', '*')

        if 'file' in entities:
            ext = entities['file'][0].split('.')[-1]
            file_pattern = f'*.{ext}'

        steps = [
            {
                'agent': 'fs',
                'target': {
                    'type': 'fs',
                    'path': search_path,
                    'pattern': file_pattern,
                    'recursive': True
                },
                'description': f'Search for {file_pattern} in {search_path}'
            }
        ]

        return steps

    def _plan_query_and_export(
        self,
        entities: Dict[str, List[str]],
        context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Plan for querying database and exporting results"""

        db_path = entities.get('path', [context.get('db_path', 'data.db')])[0]
        export_format = context.get('export_format', 'csv')

        steps = [
            {
                'agent': 'db',
                'target': {
                    'type': 'sqlite',
                    'path': db_path,
                    'operation': 'query',
                    'query': context.get('query', 'SELECT * FROM main_table LIMIT 100'),
                    'format': export_format
                },
                'description': f'Query database at {db_path}'
            }
        ]

        # Add export step if requested
        if context.get('export_path'):
            steps.append({
                'agent': 'fs',
                'target': {
                    'type': 'fs',
                    'operation': 'save',
                    'path': context['export_path']
                },
                'description': f'Export results to {context["export_path"]}',
                'depends_on': 0
            })

        return steps

    def _plan_crawl_and_index(
        self,
        entities: Dict[str, List[str]],
        context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Plan for crawling website and indexing content"""

        url = entities.get('url', [None])[0]
        if not url:
            return []

        steps = [
            {
                'agent': 'api',
                'target': {
                    'type': 'rest',
                    'url': url,
                    'method': 'GET'
                },
                'description': f'Fetch content from {url}'
            },
            {
                'agent': 'index',
                'target': {
                    'type': 'index',
                    'operation': 'index',
                    'documents': []  # Will be populated from previous step
                },
                'description': 'Index fetched content',
                'depends_on': 0
            }
        ]

        return steps

    def _matches_pattern(self, keywords: List[str], pattern_words: List[str]) -> bool:
        """Check if keywords match a pattern"""
        matches = sum(1 for word in pattern_words if word in keywords)
        return matches >= len(pattern_words) // 2  # Match at least half

    def optimize_plan(self, plan: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Optimize plan by removing redundant steps and reordering"""

        # Remove duplicate steps
        seen_targets = set()
        optimized = []

        for step in plan:
            target_key = f"{step['agent']}:{step['target'].get('type')}:{step['target'].get('path', step['target'].get('url', ''))}"

            if target_key not in seen_targets:
                seen_targets.add(target_key)
                optimized.append(step)

        logger.info(f"Plan optimized: {len(plan)} -> {len(optimized)} steps")

        return optimized
