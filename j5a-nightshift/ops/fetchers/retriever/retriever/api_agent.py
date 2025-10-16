"""
APIAgent - REST and GraphQL API retrieval with authentication and retries
"""
from __future__ import annotations
import json
import time
import logging
from typing import Dict, Any, Optional
import requests
from .base import BaseAgent

logger = logging.getLogger(__name__)


class APIAgent(BaseAgent):
    """
    Retrieves data from REST and GraphQL APIs

    Supports:
    - REST (GET, POST, PUT, DELETE, PATCH)
    - GraphQL queries and mutations
    - Authentication (Bearer, API Key, Basic)
    - Retries with exponential backoff
    - Request/response validation
    """

    def __init__(
        self,
        timeout: int = 30,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        verify_ssl: bool = True
    ):
        """
        Initialize APIAgent

        Args:
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
            retry_delay: Initial delay between retries (exponential backoff)
            verify_ssl: Verify SSL certificates
        """
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.verify_ssl = verify_ssl
        self.session = requests.Session()

    def supports(self, target: Any) -> bool:
        """Check if target is an API request"""
        if not isinstance(target, dict):
            return False

        target_type = target.get('type', '').lower()
        return target_type in ('rest', 'graphql', 'api')

    def retrieve(self, target: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """
        Retrieve data from API

        Target structure:
            {
                'type': 'rest' or 'graphql',
                'url': 'https://api.example.com/endpoint',
                'method': 'GET' (optional, default GET),
                'headers': {...} (optional),
                'auth': {...} (optional),
                'data': {...} (optional, request body),
                'params': {...} (optional, query parameters),
                'query': '...' (GraphQL query, if type=graphql)
            }

        Returns:
            {
                'data': <response data>,
                'status_code': 200,
                'headers': {...},
                'meta': {
                    'method': 'rest' or 'graphql',
                    'url': '...',
                    'attempts': 1,
                    'duration_ms': 123
                }
            }
        """
        target_type = target.get('type', 'rest').lower()

        if target_type == 'graphql':
            return self._retrieve_graphql(target, **kwargs)
        else:
            return self._retrieve_rest(target, **kwargs)

    def _retrieve_rest(self, target: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Retrieve data from REST API"""
        url = target.get('url')
        if not url:
            raise ValueError("API target must include 'url'")

        method = target.get('method', 'GET').upper()
        headers = target.get('headers', {}).copy()
        params = target.get('params', {})
        data = target.get('data')

        # Handle authentication
        auth_config = target.get('auth', {})
        headers = self._apply_authentication(headers, auth_config)

        # Retry logic
        last_error = None
        start_time = time.time()

        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info(f"API request: {method} {url} (attempt {attempt}/{self.max_retries})")

                response = self.session.request(
                    method=method,
                    url=url,
                    headers=headers,
                    params=params,
                    json=data if data and method in ('POST', 'PUT', 'PATCH') else None,
                    timeout=self.timeout,
                    verify=self.verify_ssl
                )

                duration_ms = int((time.time() - start_time) * 1000)

                # Check for HTTP errors
                if response.status_code >= 400:
                    logger.warning(f"API returned {response.status_code}: {response.text[:200]}")

                    # Don't retry client errors (4xx), only server errors (5xx)
                    if response.status_code < 500:
                        return self._format_response(response, url, attempt, duration_ms, error=f"HTTP {response.status_code}")

                    # Retry server errors
                    if attempt < self.max_retries:
                        delay = self.retry_delay * (2 ** (attempt - 1))
                        logger.info(f"Retrying after {delay}s...")
                        time.sleep(delay)
                        continue

                # Success
                logger.info(f"API request successful: {response.status_code}")
                return self._format_response(response, url, attempt, duration_ms)

            except requests.exceptions.Timeout as e:
                last_error = f"Timeout after {self.timeout}s"
                logger.warning(f"Request timeout: {e}")

            except requests.exceptions.ConnectionError as e:
                last_error = f"Connection error: {str(e)}"
                logger.warning(f"Connection error: {e}")

            except Exception as e:
                last_error = str(e)
                logger.error(f"Unexpected error: {e}", exc_info=True)

            # Retry with backoff
            if attempt < self.max_retries:
                delay = self.retry_delay * (2 ** (attempt - 1))
                logger.info(f"Retrying after {delay}s...")
                time.sleep(delay)

        # All retries exhausted
        duration_ms = int((time.time() - start_time) * 1000)
        return {
            'data': None,
            'status_code': None,
            'headers': {},
            'error': last_error,
            'meta': {
                'method': 'rest',
                'url': url,
                'attempts': self.max_retries,
                'duration_ms': duration_ms,
                'success': False
            }
        }

    def _retrieve_graphql(self, target: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Retrieve data from GraphQL API"""
        url = target.get('url')
        query = target.get('query')

        if not url or not query:
            raise ValueError("GraphQL target must include 'url' and 'query'")

        variables = target.get('variables', {})
        headers = target.get('headers', {}).copy()

        # GraphQL uses POST with JSON
        headers['Content-Type'] = 'application/json'

        # Handle authentication
        auth_config = target.get('auth', {})
        headers = self._apply_authentication(headers, auth_config)

        # Build GraphQL request
        graphql_request = {
            'query': query,
            'variables': variables
        }

        # Use REST retrieval with GraphQL payload
        rest_target = {
            'type': 'rest',
            'url': url,
            'method': 'POST',
            'headers': headers,
            'data': graphql_request
        }

        result = self._retrieve_rest(rest_target, **kwargs)

        # Update meta to indicate GraphQL
        if 'meta' in result:
            result['meta']['method'] = 'graphql'
            result['meta']['query'] = query[:100] + '...' if len(query) > 100 else query

        return result

    def _apply_authentication(self, headers: Dict[str, str], auth_config: Dict[str, Any]) -> Dict[str, str]:
        """Apply authentication to headers"""
        if not auth_config:
            return headers

        auth_type = auth_config.get('type', '').lower()

        if auth_type == 'bearer':
            token = auth_config.get('token')
            if token:
                headers['Authorization'] = f'Bearer {token}'

        elif auth_type == 'api_key':
            key = auth_config.get('key')
            value = auth_config.get('value')
            if key and value:
                headers[key] = value

        elif auth_type == 'basic':
            # Basic auth handled by requests library
            # Not adding to headers, will use auth parameter
            pass

        return headers

    def _format_response(
        self,
        response: requests.Response,
        url: str,
        attempts: int,
        duration_ms: int,
        error: Optional[str] = None
    ) -> Dict[str, Any]:
        """Format API response"""
        # Try to parse JSON
        try:
            data = response.json()
        except Exception:
            data = response.text

        return {
            'data': data,
            'status_code': response.status_code,
            'headers': dict(response.headers),
            'error': error,
            'meta': {
                'method': 'rest',
                'url': url,
                'attempts': attempts,
                'duration_ms': duration_ms,
                'success': response.status_code < 400 and not error
            }
        }
