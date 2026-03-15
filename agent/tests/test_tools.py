"""Tests for the dynamic tool system."""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from src.tools import (
    BUILTIN_TOOLS,
    _handle_get_weather,
    _handle_search_web,
    _handle_set_reminder,
    call_webhook,
    create_tool_function,
)


# ---------------------------------------------------------------------------
# Built-in tool handlers
# ---------------------------------------------------------------------------

class TestBuiltinWeather:
    """Test the built-in weather tool."""

    async def test_returns_weather_string(self):
        result = await _handle_get_weather(location="Paris")
        assert "Paris" in result
        assert "22" in result  # temperature
        assert isinstance(result, str)

    async def test_different_locations(self):
        r1 = await _handle_get_weather(location="London")
        r2 = await _handle_get_weather(location="Tokyo")
        assert "London" in r1
        assert "Tokyo" in r2


class TestBuiltinSearchWeb:
    """Test the built-in web search tool."""

    async def test_returns_search_results(self):
        result = await _handle_search_web(query="Python tutorials")
        assert "Python tutorials" in result
        assert isinstance(result, str)

    async def test_demo_indicator(self):
        result = await _handle_search_web(query="test")
        assert "demo" in result.lower()


class TestBuiltinSetReminder:
    """Test the built-in reminder tool."""

    async def test_returns_confirmation(self):
        result = await _handle_set_reminder(message="Buy milk", time="tomorrow at 9am")
        assert "Buy milk" in result
        assert "tomorrow at 9am" in result
        assert "Reminder set" in result


class TestBuiltinToolsRegistry:
    """Verify the BUILTIN_TOOLS mapping is complete."""

    def test_contains_expected_tools(self):
        assert "get_weather" in BUILTIN_TOOLS
        assert "search_web" in BUILTIN_TOOLS
        assert "set_reminder" in BUILTIN_TOOLS

    def test_all_handlers_are_callable(self):
        for name, handler in BUILTIN_TOOLS.items():
            assert callable(handler), f"Handler for {name} is not callable"


# ---------------------------------------------------------------------------
# Webhook calling
# ---------------------------------------------------------------------------

class TestCallWebhook:
    """Test the webhook integration."""

    async def test_successful_webhook_call(self):
        mock_response = MagicMock()
        mock_response.text = '{"result": "sunny"}'
        mock_response.raise_for_status = MagicMock()

        with patch("src.tools.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.post.return_value = mock_response
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client

            result = await call_webhook(
                url="https://api.example.com/weather",
                tool_name="get_weather",
                arguments={"location": "Berlin"},
            )

            assert result == '{"result": "sunny"}'
            mock_client.post.assert_called_once_with(
                "https://api.example.com/weather",
                json={"tool": "get_weather", "arguments": {"location": "Berlin"}},
                headers={"Content-Type": "application/json"},
            )

    async def test_webhook_http_error_propagates(self):
        import httpx

        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Server Error", request=MagicMock(), response=MagicMock()
        )

        with patch("src.tools.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.post.return_value = mock_response
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client

            with pytest.raises(httpx.HTTPStatusError):
                await call_webhook(
                    url="https://api.example.com/fail",
                    tool_name="test",
                    arguments={},
                )


# ---------------------------------------------------------------------------
# Dynamic tool creation
# ---------------------------------------------------------------------------

class TestCreateToolFunction:
    """Test the dynamic tool factory."""

    async def test_creates_callable_with_correct_name(self):
        fn = create_tool_function(
            tool_name="my_tool",
            tool_description="A test tool",
            parameters=[],
        )
        assert callable(fn)
        assert fn.__name__ == "my_tool"
        assert fn.__doc__ == "A test tool"

    async def test_uses_builtin_handler(self):
        fn = create_tool_function(
            tool_name="get_weather",
            tool_description="Get weather",
            parameters=[],
        )
        result = await fn(location="NYC")
        assert "NYC" in result

    async def test_uses_webhook_when_configured(self):
        mock_response = MagicMock()
        mock_response.text = "webhook result"
        mock_response.raise_for_status = MagicMock()

        with patch("src.tools.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.post.return_value = mock_response
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client

            fn = create_tool_function(
                tool_name="custom",
                tool_description="Custom tool",
                parameters=[],
                webhook_url="https://api.example.com/custom",
            )
            result = await fn(data="test")
            assert result == "webhook result"

    async def test_webhook_failure_returns_error_string(self):
        with patch("src.tools.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.post.side_effect = Exception("Connection refused")
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client

            fn = create_tool_function(
                tool_name="failing_tool",
                tool_description="Will fail",
                parameters=[],
                webhook_url="https://broken.example.com",
            )
            result = await fn()
            assert "Error calling failing_tool" in result

    async def test_no_handler_or_webhook_returns_message(self):
        fn = create_tool_function(
            tool_name="unknown_tool",
            tool_description="No handler",
            parameters=[],
        )
        result = await fn()
        assert "no handler or webhook" in result.lower()

    async def test_builtin_handler_exception_returns_error(self):
        """If a built-in handler raises, the error is caught gracefully."""
        original = BUILTIN_TOOLS.get("get_weather")
        try:
            async def broken_handler(**kwargs):
                raise RuntimeError("API down")

            BUILTIN_TOOLS["get_weather"] = broken_handler

            fn = create_tool_function(
                tool_name="get_weather",
                tool_description="Weather",
                parameters=[],
            )
            result = await fn(location="test")
            assert "Error in get_weather" in result
        finally:
            if original is not None:
                BUILTIN_TOOLS["get_weather"] = original

    async def test_webhook_takes_priority_over_builtin(self):
        """When both webhook and builtin exist, webhook is used first."""
        mock_response = MagicMock()
        mock_response.text = "from webhook"
        mock_response.raise_for_status = MagicMock()

        with patch("src.tools.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.post.return_value = mock_response
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client

            fn = create_tool_function(
                tool_name="get_weather",
                tool_description="Weather via webhook",
                parameters=[],
                webhook_url="https://api.example.com/weather",
            )
            result = await fn(location="Berlin")
            assert result == "from webhook"
