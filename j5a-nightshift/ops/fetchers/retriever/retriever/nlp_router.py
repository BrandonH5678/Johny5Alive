"""
NLPRouter - Natural language query classification and intent detection
"""
from __future__ import annotations
import re
import logging
from typing import Dict, Any, List, Optional, Tuple
from collections import Counter

logger = logging.getLogger(__name__)


class NLPRouter:
    """
    Routes natural language queries to appropriate agents

    Supports:
    - Query intent detection
    - Agent type classification
    - Keyword extraction
    - Entity recognition (basic)
    - Confidence scoring
    """

    def __init__(self, use_transformers: bool = False, model_name: str = 'all-MiniLM-L6-v2'):
        """
        Initialize NLPRouter with classification patterns

        Args:
            use_transformers: Use transformer models for semantic similarity (requires sentence-transformers)
            model_name: Name of sentence-transformer model to use
        """
        self.use_transformers = use_transformers
        self.model_name = model_name
        self.model = None

        # Try to load transformer model if requested
        if self.use_transformers:
            self._load_transformer_model()

        # Intent patterns (regex patterns mapped to intents)
        self.intent_patterns = {
            'search': [
                r'\b(find|search|lookup|locate|get|fetch)\b',
                r'\b(where|what|show me)\b',
                r'\b(list|display)\b.*\b(all|files|documents)\b',
            ],
            'download': [
                r'\b(download|fetch|retrieve|pull)\b',
                r'\b(get|grab)\b.*\b(file|audio|video|media|pdf)\b',
            ],
            'analyze': [
                r'\b(analyze|examine|inspect|investigate)\b',
                r'\b(extract|parse|process)\b.*\b(text|data)\b',
                r'\b(what does|what is)\b',
            ],
            'query': [
                r'\b(query|select|get)\b.*\b(database|db|table)\b',
                r'\bsql\b',
                r'\b(count|sum|average)\b.*\b(records|rows)\b',
            ],
            'index': [
                r'\b(index|catalog|organize)\b',
                r'\b(build|create)\b.*\bindex\b',
            ],
        }

        # Agent type patterns
        self.agent_patterns = {
            'api': [
                r'\bapi\b',
                r'\b(rest|graphql|endpoint)\b',
                r'\b(http|https)://\S+',
            ],
            'media': [
                r'\b(audio|video|media|image|podcast|mp3|mp4)\b',
                r'\.(mp3|mp4|avi|wav|jpg|png|pdf)\b',
            ],
            'fs': [
                r'\b(file|directory|folder|path)\b',
                r'\b(filesystem|disk)\b',
                r'/[\w/]+',
            ],
            'db': [
                r'\b(database|sqlite|sql|table|query)\b',
                r'\.db\b',
            ],
            'ocr': [
                r'\b(ocr|scan|extract text|read)\b.*\b(image|pdf|document)\b',
                r'\b(tesseract|text extraction)\b',
            ],
            'index': [
                r'\b(search|index|fulltext)\b',
                r'\b(find|lookup)\b.*\b(documents|text)\b',
            ],
        }

        # Entity patterns
        self.entity_patterns = {
            'url': r'https?://[^\s]+',
            'path': r'/[\w/\.\-]+',
            'file': r'[\w\-]+\.(mp3|mp4|pdf|txt|json|csv|db|png|jpg)',
            'number': r'\b\d+\b',
        }

    def classify(self, text: str) -> Dict[str, Any]:
        """
        Classify query and detect intent

        Args:
            text: Natural language query text

        Returns:
            {
                'intent': 'search',
                'confidence': 0.85,
                'agent_types': ['api', 'media'],
                'entities': {
                    'url': ['https://example.com'],
                    'file': ['audio.mp3']
                },
                'keywords': ['download', 'podcast', 'episode'],
                'labels': ['search', 'media']
            }
        """
        logger.info(f"Classifying query: '{text[:100]}...'")

        text_lower = text.lower()

        # Detect intent
        intent, intent_confidence = self._detect_intent(text_lower)

        # Detect agent types
        agent_types = self._detect_agent_types(text_lower)

        # Extract entities
        entities = self._extract_entities(text)

        # Extract keywords
        keywords = self._extract_keywords(text_lower)

        # Build labels list (combines intent and agent types)
        labels = [intent] + agent_types

        result = {
            'intent': intent,
            'confidence': round(intent_confidence, 2),
            'agent_types': agent_types,
            'entities': entities,
            'keywords': keywords,
            'labels': labels
        }

        logger.info(f"Classification: intent={intent}, agents={agent_types}, confidence={intent_confidence:.2f}")

        return result

    def route_to_agent(self, text: str) -> str:
        """
        Determine best agent for query

        Args:
            text: Natural language query

        Returns:
            Agent type name ('api', 'media', 'fs', 'db', 'ocr', 'index')
        """
        classification = self.classify(text)

        # Priority order: use most specific agent type
        agent_types = classification['agent_types']

        if agent_types:
            return agent_types[0]  # Return highest confidence agent

        # Fallback based on intent
        intent = classification['intent']
        intent_to_agent = {
            'search': 'index',
            'download': 'media',
            'analyze': 'ocr',
            'query': 'db',
            'index': 'index',
        }

        return intent_to_agent.get(intent, 'api')  # Default to API

    def _detect_intent(self, text: str) -> Tuple[str, float]:
        """Detect query intent with confidence score"""
        intent_scores: Dict[str, int] = Counter()

        # Match patterns for each intent
        for intent, patterns in self.intent_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    intent_scores[intent] += 1

        # Get highest scoring intent
        if intent_scores:
            most_common = intent_scores.most_common(1)[0]
            intent = most_common[0]
            matches = most_common[1]

            # Calculate confidence (normalized by max possible matches)
            max_matches = len(self.intent_patterns[intent])
            confidence = min(matches / max_matches, 1.0)

            return intent, confidence

        # Default intent
        return 'search', 0.5

    def _detect_agent_types(self, text: str) -> List[str]:
        """Detect applicable agent types"""
        agent_scores: Dict[str, int] = Counter()

        # Match patterns for each agent type
        for agent_type, patterns in self.agent_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    agent_scores[agent_type] += 1

        # Return agents sorted by score (most relevant first)
        sorted_agents = [agent for agent, score in agent_scores.most_common()]

        return sorted_agents

    def _extract_entities(self, text: str) -> Dict[str, List[str]]:
        """Extract entities from text"""
        entities: Dict[str, List[str]] = {}

        for entity_type, pattern in self.entity_patterns.items():
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                entities[entity_type] = list(set(matches))  # Deduplicate

        return entities

    def _extract_keywords(self, text: str) -> List[str]:
        """Extract important keywords from text"""
        # Remove common stopwords
        stopwords = {
            'a', 'an', 'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'be',
            'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
            'would', 'should', 'could', 'may', 'might', 'must', 'can', 'this',
            'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they'
        }

        # Extract words
        words = re.findall(r'\b\w+\b', text.lower())

        # Filter stopwords and short words
        keywords = [w for w in words if w not in stopwords and len(w) > 3]

        # Return unique keywords (preserving order)
        seen = set()
        unique_keywords = []
        for kw in keywords:
            if kw not in seen:
                seen.add(kw)
                unique_keywords.append(kw)

        return unique_keywords[:10]  # Limit to top 10 keywords

    def _load_transformer_model(self):
        """Load transformer model for semantic similarity"""
        try:
            from sentence_transformers import SentenceTransformer
            logger.info(f"Loading transformer model: {self.model_name}")
            self.model = SentenceTransformer(self.model_name)
            logger.info("Transformer model loaded successfully")
        except ImportError:
            logger.warning("sentence-transformers not installed - install with: pip install sentence-transformers")
            logger.warning("Falling back to regex-based classification")
            self.use_transformers = False
        except Exception as e:
            logger.warning(f"Failed to load transformer model: {e}")
            logger.warning("Falling back to regex-based classification")
            self.use_transformers = False

    def classify_semantic(self, text: str) -> Dict[str, Any]:
        """
        Classify query using semantic similarity with transformers

        Args:
            text: Natural language query text

        Returns:
            Same format as classify() but with semantic similarity scores
        """
        if not self.use_transformers or not self.model:
            # Fallback to regex-based classification
            return self.classify(text)

        logger.info(f"Semantic classification: '{text[:100]}...'")

        # Example queries for each intent (for semantic similarity)
        intent_examples = {
            'search': [
                "find files in the directory",
                "search for documents",
                "lookup database records",
                "show me all images"
            ],
            'download': [
                "download audio file from URL",
                "fetch video from website",
                "retrieve PDF document",
                "pull media files"
            ],
            'analyze': [
                "analyze the data",
                "extract text from image",
                "process the document",
                "examine the content"
            ],
            'query': [
                "query the database",
                "select from SQL table",
                "get records from database",
                "count rows in table"
            ],
            'index': [
                "index the documents",
                "build search index",
                "catalog the files",
                "create fulltext index"
            ]
        }

        # Agent examples
        agent_examples = {
            'api': ["call REST API", "fetch from GraphQL endpoint", "HTTP request"],
            'media': ["download audio file", "process video", "extract from PDF"],
            'fs': ["search filesystem", "find files in directory", "scan folders"],
            'db': ["query database", "SELECT from table", "database query"],
            'ocr': ["extract text from image", "OCR scan document", "read PDF"],
            'index': ["search documents", "fulltext search", "query index"]
        }

        # Encode query
        query_embedding = self.model.encode([text])[0]

        # Find best matching intent
        best_intent = None
        best_intent_score = 0

        for intent, examples in intent_examples.items():
            example_embeddings = self.model.encode(examples)
            # Calculate cosine similarity
            similarities = self.model.similarity(query_embedding, example_embeddings)
            max_similarity = float(similarities.max())

            if max_similarity > best_intent_score:
                best_intent_score = max_similarity
                best_intent = intent

        # Find best matching agents
        agent_scores = []

        for agent_type, examples in agent_examples.items():
            example_embeddings = self.model.encode(examples)
            similarities = self.model.similarity(query_embedding, example_embeddings)
            max_similarity = float(similarities.max())
            agent_scores.append((agent_type, max_similarity))

        # Sort by score and filter above threshold
        agent_scores.sort(key=lambda x: x[1], reverse=True)
        agent_types = [agent for agent, score in agent_scores if score > 0.3]

        # Extract entities and keywords (still use regex)
        entities = self._extract_entities(text)
        keywords = self._extract_keywords(text.lower())

        # Build labels
        labels = [best_intent] + agent_types

        result = {
            'intent': best_intent or 'search',
            'confidence': round(best_intent_score, 2),
            'agent_types': agent_types,
            'entities': entities,
            'keywords': keywords,
            'labels': labels,
            'method': 'transformer'
        }

        logger.info(f"Semantic classification: intent={best_intent}, agents={agent_types}, confidence={best_intent_score:.2f}")

        return result
