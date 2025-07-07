import requests
import aiohttp
import asyncio
import os
import json
import time

from typing import Dict, Optional
from langchain.tools import BaseTool


class WebSearchTool(BaseTool):
    name: str = "web_search"
    description: str = (
        "Useful for searching the web for current information. "
        "Input should be a search query."
    )

    # Class-level session for connection pooling
    _session: Optional[requests.Session] = None
    _async_session: Optional[aiohttp.ClientSession] = None

    # Simple rate limiting: track last request times
    _last_requests: Dict[str, float] = {}
    _min_interval = 1.0  # Reduced from 2.0 seconds
    _max_requests_per_minute = 15  # Increased from 10

    @classmethod
    def get_session(cls) -> requests.Session:
        """Get or create a reusable session for HTTP requests."""
        if cls._session is None:
            cls._session = requests.Session()
            # Configure session for better performance
            cls._session.headers.update(
                {
                    "User-Agent": "LocalCodingAgent/1.0",
                    "Accept": "application/json",
                    "Connection": "keep-alive",
                }
            )
            # Configure connection pooling
            from requests.adapters import HTTPAdapter

            adapter = HTTPAdapter(pool_connections=5, pool_maxsize=10, max_retries=3)
            cls._session.mount("http://", adapter)
            cls._session.mount("https://", adapter)
        return cls._session

    @classmethod
    async def get_async_session(cls) -> aiohttp.ClientSession:
        """Get or create a reusable async session for HTTP requests."""
        if cls._async_session is None or cls._async_session.closed:
            connector = aiohttp.TCPConnector(
                limit=10,
                limit_per_host=5,
                keepalive_timeout=30,
                enable_cleanup_closed=True,
            )
            timeout = aiohttp.ClientTimeout(total=10, connect=5)
            cls._async_session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                headers={
                    "User-Agent": "LocalCodingAgent/1.0",
                    "Accept": "application/json",
                    "Connection": "keep-alive",
                },
            )
        return cls._async_session

    def _run(self, query: str) -> str:
        """Search the web for information using SearXNG with optimized sync method."""
        try:
            # Quick rate limiting check
            current_time = time.time()
            if not self._check_rate_limit(current_time):
                return "Rate limit exceeded. Please wait before making another search request."

            # Record this request
            self._last_requests[str(current_time)] = current_time
            self._cleanup_old_requests(current_time)

            # Use persistent session for better performance
            session = self.get_session()
            searxng_base_url = os.getenv("SEARXNG_BASE_URL", "http://searxng:8080")

            # Optimized search parameters
            params = {
                "q": query,
                "format": "json",
                "categories": "general",
                "engines": "!google,!bing,!duckduckgo",  # Limit to faster engines
                "time_range": "",  # Don't filter by time for speed
                "safesearch": "0",  # Disable safe search for speed
            }

            # Make request with persistent connection
            search_url = f"{searxng_base_url}/search"
            response = session.get(
                search_url, params=params, timeout=8
            )  # Reduced timeout

            if response.status_code != 200:
                return f"Error: SearXNG returned status code {response.status_code}"

            # Parse JSON response
            data = response.json()
            results = data.get("results", [])

            if not results:
                return "No search results found."

            # Format results with reduced processing
            return self._format_results(results[:4])  # Reduced from 5 to 4 results

        except requests.exceptions.RequestException as e:
            return f"Error connecting to SearXNG: {str(e)}"
        except json.JSONDecodeError as e:
            return f"Error parsing SearXNG response: {str(e)}"
        except Exception as e:
            return f"Error performing web search: {str(e)}"

    async def _arun(self, query: str) -> str:
        """Async search method for better performance."""
        try:
            # Quick rate limiting check
            current_time = time.time()
            if not self._check_rate_limit(current_time):
                return "Rate limit exceeded. Please wait before making another search request."

            # Record this request
            self._last_requests[str(current_time)] = current_time
            self._cleanup_old_requests(current_time)

            # Use async session for better performance
            session = await self.get_async_session()
            searxng_base_url = os.getenv("SEARXNG_BASE_URL", "http://searxng:8080")

            # Optimized search parameters
            params = {
                "q": query,
                "format": "json",
                "categories": "general",
                "engines": "!google,!bing,!duckduckgo",
                "time_range": "",
                "safesearch": "0",
            }

            # Make async request
            search_url = f"{searxng_base_url}/search"
            async with session.get(search_url, params=params) as response:
                if response.status != 200:
                    return f"Error: SearXNG returned status code {response.status}"

                data = await response.json()
                results = data.get("results", [])

                if not results:
                    return "No search results found."

                return self._format_results(results[:4])

        except asyncio.TimeoutError:
            return "Search request timed out."
        except Exception as e:
            return f"Error performing async web search: {str(e)}"

    def _check_rate_limit(self, current_time: float) -> bool:
        """Optimized rate limiting check."""
        # Check requests per minute
        recent_requests = [
            t for t in self._last_requests.values() if current_time - t < 60
        ]
        if len(recent_requests) >= self._max_requests_per_minute:
            return False

        # Check minimum interval
        if self._last_requests:
            min_time_diff = min(current_time - t for t in self._last_requests.values())
            if min_time_diff < self._min_interval:
                return False

        return True

    def _cleanup_old_requests(self, current_time: float) -> None:
        """Clean old entries to prevent memory buildup."""
        self._last_requests = {
            k: v for k, v in self._last_requests.items() if current_time - v < 60
        }

    def _format_results(self, results: list) -> str:
        """Optimized result formatting."""
        formatted_results = []
        for result in results:
            title = result.get("title", "").strip()
            content = result.get("content", "").strip()
            url = result.get("url", "").strip()

            # Simplified formatting for speed
            result_parts = [f"Title: {title}"]
            if content:
                # Truncate content for faster processing
                content = content[:200] + "..." if len(content) > 200 else content
                result_parts.append(f"Content: {content}")
            result_parts.append(f"URL: {url}")

            formatted_results.append("\n".join(result_parts))

        return "\n---\n".join(formatted_results)
