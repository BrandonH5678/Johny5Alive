#!/usr/bin/env python3
"""
Sherlock Research Executor - Implements Actual Research Package Execution

Takes research packages from J5A queue and performs:
1. Content collection (web scraping, document download)
2. Content processing (text extraction, chunking)
3. AI analysis (claim extraction, entity recognition)
4. Evidence generation (create evidence cards)
5. Output creation (JSON files with research results)
"""

import os
import json
import time
import requests
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import logging

# Claude API (will need to install: pip install anthropic)
try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    print("⚠️  Anthropic library not installed. Run: pip install anthropic")

# Web scraping
try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False
    print("⚠️  BeautifulSoup not installed. Run: pip install beautifulsoup4")


@dataclass
class ResearchResult:
    """Research execution result"""
    success: bool
    claims_extracted: int
    entities_found: int
    outputs_generated: List[str]
    token_usage: Dict[str, int]
    processing_time: float
    error_message: Optional[str] = None


class SherlockResearchExecutor:
    """
    Executes Sherlock research packages with full pipeline.

    Pipeline:
    1. Load package definition
    2. Collect content from URLs
    3. Process and chunk content
    4. Analyze with Claude API
    5. Generate evidence cards
    6. Create output files
    7. Store in Sherlock database
    """

    def __init__(
        self,
        sherlock_db_path: str = "/home/johnny5/Sherlock/evidence.db",
        output_base_dir: str = "/home/johnny5/Sherlock/research_outputs"
    ):
        """
        Initialize research executor.

        Args:
            sherlock_db_path: Path to Sherlock evidence database
            output_base_dir: Base directory for research outputs
        """
        self.sherlock_db = Path(sherlock_db_path)
        self.output_base = Path(output_base_dir)
        self.output_base.mkdir(parents=True, exist_ok=True)

        self.logger = logging.getLogger("SherlockResearchExecutor")

        # Initialize Claude API
        self.claude_client = None
        if ANTHROPIC_AVAILABLE:
            api_key = os.getenv("ANTHROPIC_API_KEY")
            if api_key:
                self.claude_client = anthropic.Anthropic(api_key=api_key)
            else:
                self.logger.warning("ANTHROPIC_API_KEY not set in environment")

        # Token tracking
        self.total_input_tokens = 0
        self.total_output_tokens = 0

    def execute_package(self, package_data: Dict) -> ResearchResult:
        """
        Execute complete research package.

        Args:
            package_data: Package definition from queue

        Returns:
            ResearchResult with execution details
        """
        start_time = time.time()
        self.total_input_tokens = 0
        self.total_output_tokens = 0

        try:
            package_id = package_data['package_id']
            package_type = package_data['package_type']
            target_name = package_data['target_name']
            collection_urls = package_data['collection_urls']

            self.logger.info(f"🔬 Executing research package {package_id}: {target_name}")

            # Step 1: Collect content
            raw_content = self._collect_content(collection_urls, package_type)
            if not raw_content:
                return ResearchResult(
                    success=False,
                    claims_extracted=0,
                    entities_found=0,
                    outputs_generated=[],
                    token_usage={"input": 0, "output": 0},
                    processing_time=time.time() - start_time,
                    error_message="No content collected from URLs"
                )

            # Step 2: Process and chunk content
            chunks = self._process_content(raw_content)
            self.logger.info(f"📄 Processed into {len(chunks)} chunks")

            # Step 3: Extract claims and entities with Claude
            claims = self._extract_claims(chunks, target_name)
            entities = self._extract_entities(chunks, target_name)

            self.logger.info(f"✅ Extracted {len(claims)} claims, {len(entities)} entities")

            # Step 4: Analyze relationships
            relationships = self._analyze_relationships(entities, target_name)

            # Step 5: Generate evidence cards
            evidence_cards = self._generate_evidence_cards(
                claims=claims,
                entities=entities,
                target_name=target_name,
                source_urls=collection_urls
            )

            # Step 6: Store in Sherlock database
            self._store_evidence(evidence_cards)

            # Step 7: Create output files
            outputs = self._create_outputs(
                package_id=package_id,
                target_name=target_name,
                claims=claims,
                entities=entities,
                relationships=relationships,
                evidence_cards=evidence_cards
            )

            processing_time = time.time() - start_time

            return ResearchResult(
                success=True,
                claims_extracted=len(claims),
                entities_found=len(entities),
                outputs_generated=outputs,
                token_usage={
                    "input": self.total_input_tokens,
                    "output": self.total_output_tokens
                },
                processing_time=processing_time
            )

        except Exception as e:
            self.logger.error(f"❌ Research execution failed: {e}")
            return ResearchResult(
                success=False,
                claims_extracted=0,
                entities_found=0,
                outputs_generated=[],
                token_usage={
                    "input": self.total_input_tokens,
                    "output": self.total_output_tokens
                },
                processing_time=time.time() - start_time,
                error_message=str(e)
            )

    def _collect_content(self, urls: List[str], package_type: str) -> List[Dict]:
        """
        Collect content from URLs.

        Args:
            urls: List of URLs to scrape
            package_type: Type of package (youtube, document, composite)

        Returns:
            List of content dictionaries
        """
        content = []

        for url in urls:
            try:
                if 'wikipedia.org' in url:
                    text = self._scrape_wikipedia(url)
                elif 'books.google.com' in url:
                    text = self._scrape_google_books(url)
                elif 'youtube.com' in url:
                    text = self._get_youtube_info(url)
                else:
                    text = self._scrape_generic_web(url)

                if text:
                    content.append({
                        'url': url,
                        'text': text,
                        'type': package_type
                    })
                    self.logger.info(f"✅ Collected {len(text)} chars from {url[:50]}...")

            except Exception as e:
                self.logger.warning(f"⚠️  Failed to collect from {url}: {e}")
                continue

        return content

    def _scrape_wikipedia(self, url: str) -> str:
        """Scrape Wikipedia article"""
        if not BS4_AVAILABLE:
            return f"Wikipedia URL: {url} (scraping not available - BeautifulSoup not installed)"

        try:
            response = requests.get(url, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')

            # Get main content
            content = soup.find('div', {'id': 'mw-content-text'})
            if content:
                # Remove unwanted elements
                for element in content.find_all(['script', 'style', 'table', 'sup']):
                    element.decompose()

                text = content.get_text(separator=' ', strip=True)
                # Clean up whitespace
                text = ' '.join(text.split())
                return text[:15000]  # Limit to ~15K chars

        except Exception as e:
            self.logger.warning(f"Wikipedia scraping failed: {e}")

        return f"Wikipedia reference: {url}"

    def _scrape_google_books(self, url: str) -> str:
        """Get Google Books info (limited preview)"""
        # Google Books requires special handling - for now, just note the reference
        return f"Book reference: {url} (full text retrieval requires Google Books API key)"

    def _get_youtube_info(self, url: str) -> str:
        """Get YouTube video info"""
        # YouTube scraping would need youtube-dl or API
        return f"YouTube video: {url} (transcript retrieval requires YouTube API or youtube-dl)"

    def _scrape_generic_web(self, url: str) -> str:
        """Scrape generic web page"""
        if not BS4_AVAILABLE:
            return f"Web reference: {url} (scraping not available)"

        try:
            response = requests.get(url, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')

            # Remove unwanted elements
            for element in soup.find_all(['script', 'style', 'nav', 'footer', 'header']):
                element.decompose()

            text = soup.get_text(separator=' ', strip=True)
            text = ' '.join(text.split())
            return text[:15000]

        except Exception as e:
            self.logger.warning(f"Generic scraping failed: {e}")
            return f"Web reference: {url}"

    def _process_content(self, raw_content: List[Dict]) -> List[Dict]:
        """
        Process and chunk content.

        Args:
            raw_content: List of content dictionaries

        Returns:
            List of text chunks with metadata
        """
        chunks = []

        for content_item in raw_content:
            text = content_item['text']
            url = content_item['url']

            # Simple chunking by character count (~1500 chars = ~375 tokens)
            chunk_size = 1500
            for i in range(0, len(text), chunk_size):
                chunk_text = text[i:i + chunk_size]
                chunks.append({
                    'text': chunk_text,
                    'source_url': url,
                    'chunk_index': i // chunk_size
                })

        return chunks

    def _extract_claims(self, chunks: List[Dict], target_name: str) -> List[Dict]:
        """
        Extract claims from chunks using Claude API.

        Args:
            chunks: Text chunks to analyze
            target_name: Research target name

        Returns:
            List of claim dictionaries
        """
        if not self.claude_client:
            self.logger.warning("Claude API not available - using mock claims")
            return [{
                'claim_text': f"Mock claim about {target_name}",
                'confidence': 0.5,
                'source_chunk': 0
            }]

        claims = []

        # Limit to first 10 chunks to control token usage
        for chunk in chunks[:10]:
            try:
                response = self.claude_client.messages.create(
                    model="claude-3-haiku-20240307",
                    max_tokens=500,
                    messages=[{
                        "role": "user",
                        "content": f"""Extract factual claims about {target_name} from this text.

Text: {chunk['text']}

Return claims as a JSON list: [{{"claim": "...", "confidence": 0.0-1.0}}]"""
                    }]
                )

                # Track tokens
                self.total_input_tokens += response.usage.input_tokens
                self.total_output_tokens += response.usage.output_tokens

                # Parse response
                try:
                    parsed_claims = json.loads(response.content[0].text)
                    for claim in parsed_claims:
                        claims.append({
                            'claim_text': claim['claim'],
                            'confidence': claim.get('confidence', 0.7),
                            'source_chunk': chunk['chunk_index'],
                            'source_url': chunk['source_url']
                        })
                except json.JSONDecodeError:
                    # Fallback: treat whole response as one claim
                    claims.append({
                        'claim_text': response.content[0].text,
                        'confidence': 0.6,
                        'source_chunk': chunk['chunk_index'],
                        'source_url': chunk['source_url']
                    })

            except Exception as e:
                self.logger.warning(f"Claim extraction failed for chunk {chunk['chunk_index']}: {e}")
                continue

        return claims

    def _extract_entities(self, chunks: List[Dict], target_name: str) -> List[Dict]:
        """Extract named entities from chunks"""
        if not self.claude_client:
            return [{'name': target_name, 'type': 'person', 'confidence': 0.8}]

        entities = []

        # Process first 10 chunks
        for chunk in chunks[:10]:
            try:
                response = self.claude_client.messages.create(
                    model="claude-3-haiku-20240307",
                    max_tokens=300,
                    messages=[{
                        "role": "user",
                        "content": f"""Extract named entities from this text about {target_name}.

Text: {chunk['text']}

Return as JSON list: [{{"name": "...", "type": "person|org|location|event", "confidence": 0.0-1.0}}]"""
                    }]
                )

                self.total_input_tokens += response.usage.input_tokens
                self.total_output_tokens += response.usage.output_tokens

                try:
                    parsed_entities = json.loads(response.content[0].text)
                    entities.extend(parsed_entities)
                except json.JSONDecodeError:
                    pass

            except Exception as e:
                self.logger.warning(f"Entity extraction failed: {e}")
                continue

        return entities

    def _analyze_relationships(self, entities: List[Dict], target_name: str) -> List[Dict]:
        """Analyze relationships between entities"""
        if not self.claude_client or not entities:
            return []

        try:
            entity_names = [e['name'] for e in entities[:20]]  # Limit to 20

            response = self.claude_client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=800,
                messages=[{
                    "role": "user",
                    "content": f"""Analyze relationships between these entities related to {target_name}:

Entities: {', '.join(entity_names)}

Return as JSON list: [{{"entity1": "...", "relationship": "...", "entity2": "...", "confidence": 0.0-1.0}}]"""
                }]
            )

            self.total_input_tokens += response.usage.input_tokens
            self.total_output_tokens += response.usage.output_tokens

            try:
                return json.loads(response.content[0].text)
            except json.JSONDecodeError:
                return []

        except Exception as e:
            self.logger.warning(f"Relationship analysis failed: {e}")
            return []

    def _generate_evidence_cards(
        self,
        claims: List[Dict],
        entities: List[Dict],
        target_name: str,
        source_urls: List[str]
    ) -> List[Dict]:
        """Generate evidence cards for Sherlock database"""
        evidence_cards = []

        for i, claim in enumerate(claims):
            card = {
                'evidence_id': f"{target_name.lower().replace(' ', '_')}_{i}",
                'claim_text': claim['claim_text'],
                'confidence': claim['confidence'],
                'source_urls': [claim.get('source_url', source_urls[0])],
                'target_name': target_name,
                'entities_mentioned': [e['name'] for e in entities if e['name'].lower() in claim['claim_text'].lower()][:5],
                'created_at': datetime.now().isoformat()
            }
            evidence_cards.append(card)

        return evidence_cards

    def _store_evidence(self, evidence_cards: List[Dict]):
        """Store evidence cards in Sherlock database"""
        if not self.sherlock_db.exists():
            self.logger.warning("Sherlock database not found - skipping storage")
            return

        try:
            conn = sqlite3.connect(self.sherlock_db)
            cursor = conn.cursor()

            for card in evidence_cards:
                # Generate unique claim_id
                claim_id = f"claim_{card['evidence_id']}"

                # Convert entities list to JSON string
                entities_json = json.dumps(card.get('entities_mentioned', []))

                cursor.execute('''
                    INSERT OR REPLACE INTO evidence_claims
                    (claim_id, source_id, claim_type, text, confidence,
                     entities, context, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    claim_id,
                    card.get('source_url', 'unknown'),
                    'factual',  # Default claim type
                    card['claim_text'],
                    card['confidence'],
                    entities_json,
                    '',  # Empty context for now
                    card['created_at']
                ))

            conn.commit()
            conn.close()
            self.logger.info(f"✅ Stored {len(evidence_cards)} evidence cards to evidence_claims table")

        except Exception as e:
            self.logger.error(f"❌ Evidence storage failed: {e}")

    def _create_outputs(
        self,
        package_id: int,
        target_name: str,
        claims: List[Dict],
        entities: List[Dict],
        relationships: List[Dict],
        evidence_cards: List[Dict]
    ) -> List[str]:
        """Create output JSON files matching queue expected paths"""
        outputs = []

        # Create filename-safe version of target name
        safe_name = target_name.lower().replace(' ', '_').replace('—', '-').replace('  ', '_')

        # Create output directories (documents/, evidence/, analysis/)
        docs_dir = self.output_base / 'documents'
        evidence_dir = self.output_base / 'evidence'
        analysis_dir = self.output_base / 'analysis'

        docs_dir.mkdir(parents=True, exist_ok=True)
        evidence_dir.mkdir(parents=True, exist_ok=True)
        analysis_dir.mkdir(parents=True, exist_ok=True)

        # 1. Documents text file (raw collected text)
        docs_file = docs_dir / f"{safe_name}_text.txt"
        with open(docs_file, 'w') as f:
            f.write(f"Research Document: {target_name}\n")
            f.write("=" * 70 + "\n\n")
            f.write(f"Package ID: {package_id}\n")
            f.write(f"Created: {datetime.now().isoformat()}\n\n")
            f.write(f"Total Claims: {len(claims)}\n")
            f.write(f"Total Entities: {len(entities)}\n\n")
            f.write("=" * 70 + "\n")
        outputs.append(str(docs_file))

        # 2. Evidence claims JSON
        claims_file = evidence_dir / f"{safe_name}_claims.json"
        with open(claims_file, 'w') as f:
            json.dump({
                'target_name': target_name,
                'package_id': package_id,
                'claims': claims,
                'total_claims': len(claims),
                'created_at': datetime.now().isoformat()
            }, f, indent=2)
        outputs.append(str(claims_file))

        # 3. Analysis summary JSON
        summary_file = analysis_dir / f"{safe_name}_summary.json"
        with open(summary_file, 'w') as f:
            json.dump({
                'target_name': target_name,
                'package_id': package_id,
                'summary': f"Research analysis of {target_name}",
                'total_claims': len(claims),
                'total_entities': len(entities),
                'total_relationships': len(relationships),
                'entities': entities,
                'relationships': relationships,
                'created_at': datetime.now().isoformat()
            }, f, indent=2)
        outputs.append(str(summary_file))

        self.logger.info(f"✅ Created {len(outputs)} output files")
        return outputs


if __name__ == "__main__":
    # Test executor
    logging.basicConfig(level=logging.INFO)

    executor = SherlockResearchExecutor()

    # Test package
    test_package = {
        'package_id': 999,
        'target_name': 'Test Target',
        'package_type': 'composite',
        'collection_urls': [
            'https://en.wikipedia.org/wiki/Hal_Puthoff'
        ]
    }

    result = executor.execute_package(test_package)

    print("\n" + "=" * 70)
    print("EXECUTION RESULT")
    print("=" * 70)
    print(f"Success: {result.success}")
    print(f"Claims: {result.claims_extracted}")
    print(f"Entities: {result.entities_found}")
    print(f"Outputs: {len(result.outputs_generated)}")
    print(f"Tokens: {result.token_usage['input']} in, {result.token_usage['output']} out")
    print(f"Time: {result.processing_time:.1f}s")
    if result.error_message:
        print(f"Error: {result.error_message}")
