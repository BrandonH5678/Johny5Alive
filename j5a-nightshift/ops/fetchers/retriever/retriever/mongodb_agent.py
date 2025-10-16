"""
MongoDBAgent - MongoDB document database query and extraction
"""
from __future__ import annotations
import logging
import json
from typing import Dict, Any, List, Optional
from .base import BaseAgent

logger = logging.getLogger(__name__)


class MongoDBAgent(BaseAgent):
    """
    Retrieves data from MongoDB databases

    Supports:
    - Document queries with filters
    - Aggregation pipelines
    - Collection introspection
    - Index management
    - Multiple output formats
    """

    def __init__(
        self,
        host: str = 'localhost',
        port: int = 27017,
        database: Optional[str] = None,
        user: Optional[str] = None,
        password: Optional[str] = None,
        timeout: int = 30,
        max_docs: int = 10000
    ):
        """
        Initialize MongoDBAgent

        Args:
            host: Database host
            port: Database port
            database: Database name
            user: Username
            password: Password
            timeout: Query timeout in seconds
            max_docs: Maximum number of documents to return
        """
        self.host = host
        self.port = port
        self.database = database
        self.user = user
        self.password = password
        self.timeout = timeout
        self.max_docs = max_docs
        self._check_pymongo()

    def _check_pymongo(self):
        """Check if pymongo is available"""
        try:
            import pymongo
            self.pymongo = pymongo
            logger.info("pymongo available")
        except ImportError:
            self.pymongo = None
            logger.warning("pymongo not installed - install with: pip install pymongo")

    def supports(self, target: Any) -> bool:
        """Check if target is a MongoDB operation"""
        if not isinstance(target, dict):
            return False

        target_type = target.get('type', '').lower()
        return target_type in ('mongodb', 'mongo')

    def retrieve(self, target: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """
        Retrieve data from MongoDB database

        Target structure:
            {
                'type': 'mongodb',
                'host': 'localhost' (optional),
                'port': 27017 (optional),
                'database': 'mydb',
                'user': 'username' (optional),
                'password': 'password' (optional),
                'operation': 'find' | 'aggregate' | 'collections' | 'indexes',
                'collection': 'users',
                'filter': {'age': {'$gt': 18}} (for find),
                'pipeline': [...] (for aggregate),
                'projection': {'name': 1, 'age': 1} (optional),
                'sort': [('age', -1)] (optional),
                'limit': 100 (optional)
            }

        Returns:
            {
                'data': [doc1, doc2, ...],
                'count': 42,
                'meta': {
                    'method': 'mongodb',
                    'database': 'mydb',
                    'collection': 'users',
                    'operation': 'find',
                    'query_time_ms': 123
                }
            }
        """
        if not self.pymongo:
            raise ImportError("pymongo not installed")

        import time

        start_time = time.time()

        # Get connection parameters
        host = target.get('host', self.host)
        port = target.get('port', self.port)
        database = target.get('database', self.database)
        user = target.get('user', self.user)
        password = target.get('password', self.password)

        if not database:
            raise ValueError("Database name required")

        operation = target.get('operation', 'find').lower()

        # Build connection string
        if user and password:
            connection_string = f"mongodb://{user}:{password}@{host}:{port}/"
        else:
            connection_string = f"mongodb://{host}:{port}/"

        # Connect to database
        client = self.pymongo.MongoClient(
            connection_string,
            serverSelectionTimeoutMS=self.timeout * 1000
        )

        try:
            db = client[database]

            if operation == 'collections':
                result = self._list_collections(db, target)
            elif operation == 'indexes':
                result = self._list_indexes(db, target)
            elif operation == 'aggregate':
                result = self._execute_aggregate(db, target)
            else:  # find
                result = self._execute_find(db, target)

            query_time_ms = int((time.time() - start_time) * 1000)

            result['meta'] = result.get('meta', {})
            result['meta'].update({
                'method': 'mongodb',
                'database': database,
                'host': host,
                'query_time_ms': query_time_ms
            })

            return result

        finally:
            client.close()

    def _execute_find(self, db, target: Dict[str, Any]) -> Dict[str, Any]:
        """Execute find query"""
        collection_name = target.get('collection')
        if not collection_name:
            raise ValueError("Collection name required for find operation")

        collection = db[collection_name]

        # Query parameters
        filter_query = target.get('filter', {})
        projection = target.get('projection')
        sort = target.get('sort')
        limit = target.get('limit', self.max_docs)

        # Execute query
        cursor = collection.find(filter_query, projection)

        if sort:
            cursor = cursor.sort(sort)

        cursor = cursor.limit(min(limit, self.max_docs))

        # Fetch documents
        documents = list(cursor)

        # Convert ObjectId to string for JSON serialization
        for doc in documents:
            if '_id' in doc:
                doc['_id'] = str(doc['_id'])

        return {
            'data': documents,
            'count': len(documents),
            'meta': {
                'operation': 'find',
                'collection': collection_name,
                'filter': filter_query,
                'truncated': len(documents) >= self.max_docs
            }
        }

    def _execute_aggregate(self, db, target: Dict[str, Any]) -> Dict[str, Any]:
        """Execute aggregation pipeline"""
        collection_name = target.get('collection')
        if not collection_name:
            raise ValueError("Collection name required for aggregate operation")

        pipeline = target.get('pipeline')
        if not pipeline:
            raise ValueError("Pipeline required for aggregate operation")

        collection = db[collection_name]

        # Execute aggregation
        cursor = collection.aggregate(pipeline)
        documents = list(cursor)

        # Convert ObjectId to string
        for doc in documents:
            if '_id' in doc:
                doc['_id'] = str(doc['_id'])

        return {
            'data': documents,
            'count': len(documents),
            'meta': {
                'operation': 'aggregate',
                'collection': collection_name,
                'pipeline_stages': len(pipeline)
            }
        }

    def _list_collections(self, db, target: Dict[str, Any]) -> Dict[str, Any]:
        """List all collections in database"""
        collection_names = db.list_collection_names()

        collections = []
        for name in collection_names:
            collection = db[name]

            # Get document count
            count = collection.count_documents({})

            # Get indexes
            indexes = list(collection.list_indexes())

            collections.append({
                'name': name,
                'document_count': count,
                'index_count': len(indexes)
            })

        return {
            'data': collections,
            'collection_count': len(collections),
            'meta': {'operation': 'collections'}
        }

    def _list_indexes(self, db, target: Dict[str, Any]) -> Dict[str, Any]:
        """List indexes for a collection"""
        collection_name = target.get('collection')
        if not collection_name:
            raise ValueError("Collection name required for indexes operation")

        collection = db[collection_name]
        indexes = list(collection.list_indexes())

        # Convert ObjectId to string
        for idx in indexes:
            if '_id' in idx:
                idx['_id'] = str(idx['_id'])

        return {
            'data': indexes,
            'index_count': len(indexes),
            'meta': {
                'operation': 'indexes',
                'collection': collection_name
            }
        }
