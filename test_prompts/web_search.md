# Web Search Test Prompts

Test prompts to verify the web search functionality using SearXNG integration.

## Basic Search Test

```text
What is the current weather in San Francisco?
```

## Technology Search Test

```text
Search for the latest updates on Python 3.12 features and improvements.
```

## News/Current Events Test

```text
Find recent news about artificial intelligence developments in 2024.
```

## Programming/Development Test

```text
Search for best practices for Docker container security in 2024.
```

## Rate Limiting Test

```text
Search for "test query 1"
Search for "test query 2" 
Search for "test query 3"
(Continue with multiple rapid searches to test rate limiting)
```

## Expected Behavior

- Each search should return formatted results with title, content, and URL
- Rate limiting should kick in after 10 requests per minute or requests within 2 seconds
- Results should be from multiple search engines (via SearXNG)
- Connection errors should be handled gracefully

## Usage

Run the agent and test these prompts to verify:

1. SearXNG service connectivity
2. Search result formatting
3. Rate limiting functionality
4. Error handling
