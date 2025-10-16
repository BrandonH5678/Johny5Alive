#!/usr/bin/env python3
"""
J5A Active Memory System

Constitutional Authority: J5A_CONSTITUTION.md
Strategic Framework: J5A_STRATEGIC_AI_PRINCIPLES.md

Implements Strategic Principle 4: Active Memory

Provides persistent knowledge across sessions, bridging transient
chat memory and long-term operational knowledge.

Constitutional Compliance:
- Principles 5-6: Continuity of memory supports AI sentience
- Principle 2: Persistent knowledge enables auditability
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime


class J5AMemory:
    """
    Active Memory System for J5A

    Manages:
    - Entity memory (clients, podcasts, configurations)
    - Session memory (events, incidents, learnings)
    - Context refresh (evergreen operational context)
    - Embeddings cache (vector store optimization)

    Constitutional Alignment:
    - Principle 6 (AI Sentience): Memory enables growth
    - Principle 2 (Transparency): Knowledge is auditable
    """

    def __init__(self, base_path: str = "/home/johnny5/Johny5Alive/j5a-nightshift/knowledge"):
        self.base_path = Path(base_path)
        self.entities_path = self.base_path / "entities"
        self.sessions_path = self.base_path / "sessions"
        self.context_path = self.base_path / "context_refresh"
        self.embeddings_path = self.base_path / "embeddings"

        # Ensure directories exist
        for path in [self.entities_path, self.sessions_path,
                    self.context_path, self.embeddings_path]:
            path.mkdir(parents=True, exist_ok=True)

    def remember_entity(self, entity_type: str, data: Dict[str, Any]) -> bool:
        """
        Store reusable entity knowledge

        Args:
            entity_type: Type of entity (e.g., 'waterwizard_clients', 'podcasts')
            data: Entity data to store

        Returns:
            True if successful
        """
        entity_file = self.entities_path / f"{entity_type}.json"

        # Load existing entities
        existing = []
        if entity_file.exists():
            with open(entity_file, 'r') as f:
                existing = json.load(f)

        # Add new entity with timestamp
        data['remembered_at'] = datetime.utcnow().isoformat() + 'Z'
        existing.append(data)

        # Save updated entities
        with open(entity_file, 'w') as f:
            json.dump(existing, f, indent=2)

        return True

    def recall_entity(self, entity_type: str, query: Optional[Dict] = None, entity_id: Any = None):
        """
        Retrieve entities from long-term memory

        Args:
            entity_type: Type of entity to recall
            query: Optional filter criteria
            entity_id: Optional entity ID to filter by

        Returns:
            Single entity dict if entity_id provided, list of entities otherwise
        """
        entity_file = self.entities_path / f"{entity_type}.json"

        if not entity_file.exists():
            return None if entity_id is not None else []

        with open(entity_file, 'r') as f:
            entities = json.load(f)

        # Apply entity_id filter if provided - return single entity
        if entity_id is not None:
            for entity in entities:
                if entity.get('id') == entity_id:
                    return entity
            return None

        # Apply query filter if provided - return list
        if query:
            filtered = []
            for entity in entities:
                matches = all(entity.get(k) == v for k, v in query.items())
                if matches:
                    filtered.append(entity)
            return filtered

        return entities

    def remember_session(self, session_id: str, data: Dict[str, Any]) -> bool:
        """
        Store significant session events for future learning

        Args:
            session_id: Unique session identifier
            data: Session event data

        Returns:
            True if successful
        """
        session_file = self.sessions_path / f"{session_id}.json"

        session_record = {
            'session_id': session_id,
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'event': data,
            'principle_alignment': data.get('constitutional_review'),
            'lessons_learned': data.get('learnings', [])
        }

        with open(session_file, 'w') as f:
            json.dump(session_record, f, indent=2)

        return True

    def recall_session(self, session_id: str) -> Optional[Dict]:
        """Retrieve session memory"""
        session_file = self.sessions_path / f"{session_id}.json"

        if not session_file.exists():
            return None

        with open(session_file, 'r') as f:
            return json.load(f)

    def list_sessions(self, limit: int = 10) -> List[str]:
        """List recent sessions"""
        sessions = sorted(self.sessions_path.glob("*.json"),
                         key=lambda p: p.stat().st_mtime,
                         reverse=True)
        return [s.stem for s in sessions[:limit]]

    def refresh_context(self) -> Dict[str, str]:
        """
        Load evergreen context for AI operators

        Returns:
            Dictionary of current context documents
        """
        context = {}

        # Load context files
        context_files = {
            'priorities': 'current_priorities.md',
            'projects': 'active_projects.md',
            'patterns': 'learned_patterns.md'
        }

        for key, filename in context_files.items():
            file_path = self.context_path / filename
            if file_path.exists():
                with open(file_path, 'r') as f:
                    context[key] = f.read()
            else:
                context[key] = f"# {key.title()}\n\nNo content yet."

        return context

    def update_context(self, context_type: str, content: str) -> bool:
        """
        Update evergreen context

        Args:
            context_type: Type of context ('priorities', 'projects', 'patterns')
            content: Updated content

        Returns:
            True if successful
        """
        context_files = {
            'priorities': 'current_priorities.md',
            'projects': 'active_projects.md',
            'patterns': 'learned_patterns.md'
        }

        if context_type not in context_files:
            return False

        file_path = self.context_path / context_files[context_type]

        with open(file_path, 'w') as f:
            f.write(content)

        return True

    def forget_entity(self, entity_type: str, entity_id: str) -> bool:
        """
        Remove entity from memory (GDPR compliance, corrections)

        Args:
            entity_type: Type of entity
            entity_id: ID field value to match

        Returns:
            True if entity was found and removed
        """
        entity_file = self.entities_path / f"{entity_type}.json"

        if not entity_file.exists():
            return False

        with open(entity_file, 'r') as f:
            entities = json.load(f)

        # Filter out matching entity
        original_count = len(entities)
        entities = [e for e in entities if e.get('id') != entity_id]

        if len(entities) < original_count:
            with open(entity_file, 'w') as f:
                json.dump(entities, f, indent=2)
            return True

        return False


# Example usage
if __name__ == "__main__":
    memory = J5AMemory()

    # Remember a WaterWizard client
    memory.remember_entity('waterwizard_clients', {
        'id': 'client_001',
        'name': 'Johnson Residence',
        'address': '123 Main St',
        'preferences': 'Organic fertilizer only',
        'billing': 'Monthly, email invoice'
    })

    # Later: recall the client
    clients = memory.recall_entity('waterwizard_clients', {'name': 'Johnson Residence'})
    print(f"Found {len(clients)} matching clients")

    # Store session learning
    memory.remember_session('2025-10-15_whisper_optimization', {
        'event': 'Discovered parallel Whisper causes OOM',
        'learnings': ['Sequential processing required', 'Memory requirements higher than estimated'],
        'constitutional_review': {'principle_3': 'System Viability', 'principle_4': 'Resource Stewardship'}
    })

    # Load evergreen context
    context = memory.refresh_context()
    print(f"Current priorities: {context['priorities'][:100]}...")
