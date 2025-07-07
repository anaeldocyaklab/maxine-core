import os
import json
import aiofiles

from langchain.tools import BaseTool


class DiskOperationsTool(BaseTool):
    name: str = "disk_operations"
    description: str = (
        "Useful for reading from or writing to files. "
        "Input should be a JSON string with 'operation' ('read' or 'write'), "
        "'path', and 'content' (for write operations). "
        'Example: {"operation": "read", "path": "example.txt"} or '
        '{"operation": "write", "path": "example.txt", "content": "Hello world"}'
    )

    # Cache for recently read files to avoid repeated I/O
    _file_cache = {}
    _cache_size_limit = 50

    def _run(self, query: str) -> str:
        """Read from or write to a file with optimized I/O."""
        try:
            params = json.loads(query)
            operation = params.get("operation", "").lower()
            path = params.get("path", "")

            if not path:
                return "Error: A file path must be provided."

            path = os.path.normpath(path)

            if operation == "read":
                return self._read_file(path)
            elif operation == "write":
                content = params.get("content", "")
                return self._write_file(path, content)
            else:
                return "Error: Invalid operation. Use 'read' or 'write'."

        except json.JSONDecodeError:
            return (
                "Error: Input must be a valid JSON string with the required parameters."
            )
        except Exception as e:
            return f"Error performing file operation: {str(e)}"

    async def _arun(self, query: str) -> str:
        """Async version for better performance."""
        try:
            params = json.loads(query)
            operation = params.get("operation", "").lower()
            path = params.get("path", "")

            if not path:
                return "Error: A file path must be provided."

            path = os.path.normpath(path)

            if operation == "read":
                return await self._read_file_async(path)
            elif operation == "write":
                content = params.get("content", "")
                return await self._write_file_async(path, content)
            else:
                return "Error: Invalid operation. Use 'read' or 'write'."

        except json.JSONDecodeError:
            return (
                "Error: Input must be a valid JSON string with the required parameters."
            )
        except Exception as e:
            return f"Error performing async file operation: {str(e)}"

    def _read_file(self, path: str) -> str:
        """Optimized synchronous file reading with caching."""
        # Check cache first
        if path in self._file_cache:
            return f"File content (cached):\n{self._file_cache[path]}"

        if not os.path.exists(path):
            return f"Error: The file at '{path}' does not exist."

        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()

            # Cache the content (with size limit)
            if len(self._file_cache) >= self._cache_size_limit:
                # Remove oldest entry
                self._file_cache.pop(next(iter(self._file_cache)))
            self._file_cache[path] = content

            return f"File content:\n{content}"
        except Exception as e:
            return f"Error reading file: {str(e)}"

    async def _read_file_async(self, path: str) -> str:
        """Async file reading with caching."""
        # Check cache first
        if path in self._file_cache:
            return f"File content (cached):\n{self._file_cache[path]}"

        if not os.path.exists(path):
            return f"Error: The file at '{path}' does not exist."

        try:
            async with aiofiles.open(path, "r", encoding="utf-8") as f:
                content = await f.read()

            # Cache the content (with size limit)
            if len(self._file_cache) >= self._cache_size_limit:
                # Remove oldest entry
                self._file_cache.pop(next(iter(self._file_cache)))
            self._file_cache[path] = content

            return f"File content:\n{content}"
        except Exception as e:
            return f"Error reading file async: {str(e)}"

    def _write_file(self, path: str, content: str) -> str:
        """Optimized synchronous file writing."""
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(path), exist_ok=True)

            with open(path, "w", encoding="utf-8") as f:
                f.write(content)

            # Update cache
            if path in self._file_cache:
                self._file_cache[path] = content

            return f"Successfully wrote to '{path}'."
        except Exception as e:
            return f"Error writing file: {str(e)}"

    async def _write_file_async(self, path: str, content: str) -> str:
        """Async file writing."""
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(path), exist_ok=True)

            async with aiofiles.open(path, "w", encoding="utf-8") as f:
                await f.write(content)

            # Update cache
            if path in self._file_cache:
                self._file_cache[path] = content

            return f"Successfully wrote to '{path}'."
        except Exception as e:
            return f"Error writing file async: {str(e)}"
