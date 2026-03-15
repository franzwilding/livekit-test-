"""Dynamic tool system for the voice agent.

Provides built-in demo tool implementations (weather, web search, reminders),
webhook-based tool execution for production integrations, and a factory for
creating tool handler functions dynamically from YAML configuration.
"""
import logging
from typing import Any

import httpx

logger = logging.getLogger("tools")


# ---------------------------------------------------------------------------
# Built-in tool implementations (demo / development)
# ---------------------------------------------------------------------------

async def _handle_get_weather(location: str) -> str:
    """Built-in weather tool (demo implementation).

    In production, replace with an actual weather API integration
    (e.g. OpenWeatherMap, WeatherAPI).
    """
    return f"The weather in {location} is currently 22\u00b0C and sunny. Humidity is 45%."


async def _handle_search_web(query: str) -> str:
    """Built-in web search tool (demo implementation).

    In production, connect to a real search API (e.g. Brave Search, SerpAPI).
    """
    return (
        f"Here are the top results for '{query}': "
        "This is a demo response. In production, connect to a search API."
    )


async def _handle_set_reminder(message: str, time: str) -> str:
    """Built-in reminder tool (demo implementation).

    In production, persist reminders to a database and schedule delivery.
    """
    return f"Reminder set: '{message}' at {time}."


# Map of built-in tool names to their async handler functions.
BUILTIN_TOOLS: dict[str, Any] = {
    "get_weather": _handle_get_weather,
    "search_web": _handle_search_web,
    "set_reminder": _handle_set_reminder,
}


# ---------------------------------------------------------------------------
# Webhook support
# ---------------------------------------------------------------------------

async def call_webhook(url: str, tool_name: str, arguments: dict[str, Any]) -> str:
    """Call an external webhook for tool execution.

    Sends a POST request with the tool name and arguments as JSON. The remote
    service is expected to return the tool result as plain text.

    Args:
        url: The webhook endpoint URL.
        tool_name: Name of the tool being invoked.
        arguments: Keyword arguments passed to the tool.

    Returns:
        The response body text from the webhook.

    Raises:
        httpx.HTTPStatusError: If the webhook returns a non-2xx status.
        httpx.TimeoutException: If the webhook does not respond within 30s.
    """
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            url,
            json={"tool": tool_name, "arguments": arguments},
            headers={"Content-Type": "application/json"},
        )
        response.raise_for_status()
        return response.text


# ---------------------------------------------------------------------------
# Dynamic tool factory
# ---------------------------------------------------------------------------

def create_tool_function(
    tool_name: str,
    tool_description: str,
    parameters: list,
    webhook_url: str = "",
):
    """Create a callable tool handler function from configuration.

    The returned coroutine first tries the *webhook_url* (if provided), then
    falls back to a built-in handler, and finally returns an informative
    error message if neither is available.

    Args:
        tool_name: Unique name for the tool.
        tool_description: Human-readable description used by the LLM.
        parameters: List of ``ToolParameter``-like objects (unused at runtime
            but kept for schema generation).
        webhook_url: Optional URL for external webhook execution.

    Returns:
        An async function ``(**kwargs) -> str`` suitable for use as a
        LiveKit function tool handler.
    """

    async def tool_handler(**kwargs: Any) -> str:
        """Dynamic tool handler."""
        # If webhook URL is configured, use it
        if webhook_url:
            try:
                result = await call_webhook(webhook_url, tool_name, kwargs)
                return result
            except Exception as e:
                logger.error(f"Webhook call failed for {tool_name}: {e}")
                return f"Error calling {tool_name}: {str(e)}"

        # Try built-in handler
        if tool_name in BUILTIN_TOOLS:
            handler = BUILTIN_TOOLS[tool_name]
            try:
                return await handler(**kwargs)
            except Exception as e:
                logger.error(f"Built-in tool {tool_name} failed: {e}")
                return f"Error in {tool_name}: {str(e)}"

        return f"Tool {tool_name} is configured but has no handler or webhook."

    tool_handler.__name__ = tool_name
    tool_handler.__doc__ = tool_description

    return tool_handler
