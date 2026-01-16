#!/usr/bin/env python3
"""Test hotkey/trigger system."""

import asyncio

import pytest

from src.hotkey import TriggerClient, TriggerServer, TriggerType


def test_trigger_type_enum():
    """Test TriggerType enum values."""
    assert TriggerType.COPY.value == "TRIGGER_COPY"
    assert TriggerType.PASTE.value == "TRIGGER_PASTE"
    assert TriggerType.PASTE_TERMINAL.value == "TRIGGER_PASTE_TERMINAL"
    assert TriggerType.UNKNOWN.value == "TRIGGER"


def test_trigger_server_initialization():
    """Test TriggerServer initialization."""
    server = TriggerServer(socket_path="/tmp/test-stt.sock")
    assert server.socket_path == "/tmp/test-stt.sock"
    assert server.is_running is False
    assert server.on_trigger is None


def test_trigger_client_initialization():
    """Test TriggerClient initialization."""
    client = TriggerClient(socket_path="/tmp/test-stt.sock")
    assert client.socket_path == "/tmp/test-stt.sock"


@pytest.mark.asyncio
async def test_trigger_server_lifecycle():
    """Test trigger server start and stop."""
    socket_path = "/tmp/test-stt-lifecycle.sock"
    server = TriggerServer(socket_path=socket_path)

    # Start server
    await server.start()
    assert server.is_running is True

    # Stop server
    await server.stop()
    assert server.is_running is False


@pytest.mark.asyncio
async def test_trigger_server_callback():
    """Test trigger server callback execution."""
    socket_path = "/tmp/test-stt-callback.sock"
    received_trigger = None

    async def callback(trigger_type: TriggerType):
        nonlocal received_trigger
        received_trigger = trigger_type

    server = TriggerServer(socket_path=socket_path, on_trigger=callback)

    try:
        await server.start()

        # Send trigger
        client = TriggerClient(socket_path=socket_path)
        success = await client.send_trigger(trigger_type="TRIGGER_COPY", timeout=2.0)

        # Give callback time to execute
        await asyncio.sleep(0.1)

        assert success is True
        assert received_trigger == TriggerType.COPY

    finally:
        await server.stop()


@pytest.mark.asyncio
async def test_trigger_types():
    """Test all trigger types are correctly parsed."""
    socket_path = "/tmp/test-stt-types.sock"
    received_triggers = []

    async def callback(trigger_type: TriggerType):
        received_triggers.append(trigger_type)

    server = TriggerServer(socket_path=socket_path, on_trigger=callback)

    try:
        await server.start()
        client = TriggerClient(socket_path=socket_path)

        # Test COPY
        await client.send_trigger(trigger_type="TRIGGER_COPY", timeout=2.0)
        await asyncio.sleep(0.1)

        # Test PASTE
        await client.send_trigger(trigger_type="TRIGGER_PASTE", timeout=2.0)
        await asyncio.sleep(0.1)

        # Test PASTE_TERMINAL
        await client.send_trigger(trigger_type="TRIGGER_PASTE_TERMINAL", timeout=2.0)
        await asyncio.sleep(0.1)

        # Test UNKNOWN (legacy)
        await client.send_trigger(trigger_type="TRIGGER", timeout=2.0)
        await asyncio.sleep(0.1)

        assert len(received_triggers) == 4
        assert received_triggers[0] == TriggerType.COPY
        assert received_triggers[1] == TriggerType.PASTE
        assert received_triggers[2] == TriggerType.PASTE_TERMINAL
        assert received_triggers[3] == TriggerType.UNKNOWN

    finally:
        await server.stop()


@pytest.mark.asyncio
async def test_client_connection_failure():
    """Test client behavior when server is not running."""
    client = TriggerClient(socket_path="/tmp/nonexistent-stt.sock")
    success = await client.send_trigger(trigger_type="TRIGGER_COPY", timeout=1.0)
    assert success is False


class TestTriggerServerExtended:
    """Extended tests for TriggerServer."""

    @pytest.mark.asyncio
    async def test_server_already_running_warning(self):
        """Test that starting an already running server logs warning."""
        socket_path = "/tmp/test-stt-already-running.sock"
        server = TriggerServer(socket_path=socket_path)

        try:
            await server.start()
            assert server.is_running is True

            # Start again - should just warn, not fail
            await server.start()
            assert server.is_running is True

        finally:
            await server.stop()

    @pytest.mark.asyncio
    async def test_stop_when_not_running(self):
        """Test that stopping a non-running server is safe."""
        socket_path = "/tmp/test-stt-not-running.sock"
        server = TriggerServer(socket_path=socket_path)

        # Should not raise
        await server.stop()
        assert server.is_running is False

    @pytest.mark.asyncio
    async def test_callback_error_handling(self):
        """Test that server handles callback errors gracefully."""
        socket_path = "/tmp/test-stt-callback-error.sock"

        async def failing_callback(trigger_type: TriggerType):
            raise RuntimeError("Callback failed")

        server = TriggerServer(socket_path=socket_path, on_trigger=failing_callback)

        try:
            await server.start()

            client = TriggerClient(socket_path=socket_path)
            success = await client.send_trigger(trigger_type="TRIGGER_COPY", timeout=2.0)

            # Should return False because callback failed
            assert success is False

        finally:
            await server.stop()

    @pytest.mark.asyncio
    async def test_no_handler_response(self):
        """Test server response when no handler is set."""
        socket_path = "/tmp/test-stt-no-handler.sock"
        server = TriggerServer(socket_path=socket_path, on_trigger=None)

        try:
            await server.start()

            client = TriggerClient(socket_path=socket_path)
            success = await client.send_trigger(trigger_type="TRIGGER_COPY", timeout=2.0)

            # Should return False because no handler
            assert success is False

        finally:
            await server.stop()

    @pytest.mark.asyncio
    async def test_wait_for_trigger_with_timeout(self):
        """Test wait_for_trigger with timeout."""
        socket_path = "/tmp/test-stt-wait-timeout.sock"
        server = TriggerServer(socket_path=socket_path)

        try:
            await server.start()

            # Should timeout because no trigger sent
            result = await server.wait_for_trigger(timeout=0.1)
            assert result is False

        finally:
            await server.stop()

    @pytest.mark.asyncio
    async def test_wait_for_trigger_success(self):
        """Test wait_for_trigger with successful trigger."""
        socket_path = "/tmp/test-stt-wait-success.sock"
        server = TriggerServer(socket_path=socket_path)

        try:
            await server.start()

            # Send trigger in background
            async def send_delayed():
                await asyncio.sleep(0.1)
                client = TriggerClient(socket_path=socket_path)
                await client.send_trigger(trigger_type="TRIGGER_COPY", timeout=2.0)

            asyncio.create_task(send_delayed())

            # Wait for trigger
            result = await server.wait_for_trigger(timeout=2.0)
            assert result is True

        finally:
            await server.stop()

    @pytest.mark.asyncio
    async def test_removes_existing_socket(self):
        """Test server removes existing socket file."""
        from pathlib import Path

        socket_path = "/tmp/test-stt-remove-socket.sock"
        socket_file = Path(socket_path)

        # Create a fake socket file
        socket_file.write_text("fake")
        assert socket_file.exists()

        server = TriggerServer(socket_path=socket_path)

        try:
            await server.start()
            assert server.is_running is True

        finally:
            await server.stop()
            # File should be removed after stop
            assert not socket_file.exists()

    @pytest.mark.asyncio
    async def test_unknown_trigger_message(self):
        """Test handling of unknown trigger messages."""
        socket_path = "/tmp/test-stt-unknown-msg.sock"
        received_trigger = None

        async def callback(trigger_type: TriggerType):
            nonlocal received_trigger
            received_trigger = trigger_type

        server = TriggerServer(socket_path=socket_path, on_trigger=callback)

        try:
            await server.start()

            client = TriggerClient(socket_path=socket_path)
            await client.send_trigger(trigger_type="UNKNOWN_MESSAGE", timeout=2.0)
            await asyncio.sleep(0.1)

            assert received_trigger == TriggerType.UNKNOWN

        finally:
            await server.stop()


class TestTriggerClientExtended:
    """Extended tests for TriggerClient."""

    def test_send_trigger_sync(self):
        """Test synchronous trigger sending."""
        client = TriggerClient(socket_path="/tmp/nonexistent-sync.sock")
        success = client.send_trigger_sync(trigger_type="TRIGGER_COPY", timeout=0.5)
        assert success is False

    @pytest.mark.asyncio
    async def test_client_timeout(self):
        """Test client timeout handling."""
        socket_path = "/tmp/test-stt-client-timeout.sock"

        async def slow_callback(trigger_type: TriggerType):
            await asyncio.sleep(5)  # Very slow callback

        server = TriggerServer(socket_path=socket_path, on_trigger=slow_callback)

        try:
            await server.start()

            client = TriggerClient(socket_path=socket_path)
            # Very short timeout
            success = await client.send_trigger(trigger_type="TRIGGER_COPY", timeout=0.1)

            # Should timeout
            assert success is False

        finally:
            await server.stop()


class TestSendTriggerFunction:
    """Tests for send_trigger convenience function."""

    def test_send_trigger_to_nonexistent_socket(self):
        """Test send_trigger function with nonexistent socket."""
        from src.hotkey import send_trigger

        success = send_trigger(
            socket_path="/tmp/nonexistent-trigger.sock",
            trigger_type="TRIGGER_COPY",
            timeout=0.5,
        )
        assert success is False


class TestServerStartErrors:
    """Tests for server start error handling."""

    @pytest.mark.asyncio
    async def test_server_start_failure_raises_error(self):
        """Test that server start failure raises RuntimeError."""
        from unittest.mock import patch

        socket_path = "/tmp/test-stt-start-fail.sock"
        server = TriggerServer(socket_path=socket_path)

        with patch("asyncio.start_unix_server", side_effect=OSError("Permission denied")):
            with pytest.raises(RuntimeError, match="Server start failed"):
                await server.start()

    @pytest.mark.asyncio
    async def test_serve_forever_starts_server_if_not_started(self):
        """Test that serve_forever starts the server if not already started."""
        socket_path = "/tmp/test-stt-serve-forever.sock"
        server = TriggerServer(socket_path=socket_path)

        async def cancel_after_delay():
            await asyncio.sleep(0.2)
            server.server.close()

        try:
            # Start a background task to cancel the server
            cancel_task = asyncio.create_task(cancel_after_delay())

            # serve_forever should start the server automatically
            assert server.server is None
            await asyncio.wait_for(server.serve_forever(), timeout=1.0)

        except asyncio.TimeoutError:
            pass  # Expected if cancellation didn't work
        except asyncio.CancelledError:
            pass  # Expected

        finally:
            cancel_task.cancel()
            await server.stop()


class TestWaitForTriggerNoTimeout:
    """Tests for wait_for_trigger without timeout."""

    @pytest.mark.asyncio
    async def test_wait_for_trigger_no_timeout(self):
        """Test wait_for_trigger without timeout parameter."""
        socket_path = "/tmp/test-stt-wait-no-timeout.sock"
        server = TriggerServer(socket_path=socket_path)

        try:
            await server.start()

            # Send trigger in background quickly
            async def send_delayed():
                await asyncio.sleep(0.05)
                client = TriggerClient(socket_path=socket_path)
                await client.send_trigger(trigger_type="TRIGGER_COPY", timeout=2.0)

            asyncio.create_task(send_delayed())

            # Wait for trigger with no timeout (will be cancelled by actual trigger)
            result = await asyncio.wait_for(server.wait_for_trigger(timeout=None), timeout=2.0)
            assert result is True

        finally:
            await server.stop()


class TestClientExceptionHandling:
    """Tests for client exception handling."""

    @pytest.mark.asyncio
    async def test_client_send_trigger_exception(self):
        """Test client handling of general exceptions during send."""
        from unittest.mock import patch

        client = TriggerClient(socket_path="/tmp/test-exception.sock")

        # Patch to raise a general exception
        with patch(
            "asyncio.open_unix_connection",
            side_effect=OSError("Connection refused"),
        ):
            success = await client.send_trigger(trigger_type="TRIGGER_COPY", timeout=1.0)
            assert success is False


class TestHandleClientErrors:
    """Tests for _handle_client error handling."""

    @pytest.mark.asyncio
    async def test_handle_client_close_error(self):
        """Test that errors during client close are handled gracefully."""
        socket_path = "/tmp/test-stt-close-error.sock"
        received_triggers = []

        async def callback(trigger_type: TriggerType):
            received_triggers.append(trigger_type)

        server = TriggerServer(socket_path=socket_path, on_trigger=callback)

        try:
            await server.start()

            # Connect and send a trigger, then disconnect abruptly
            # This simulates the case where writer.close() might raise
            client = TriggerClient(socket_path=socket_path)
            success = await client.send_trigger(trigger_type="TRIGGER_COPY", timeout=2.0)

            await asyncio.sleep(0.1)

            assert success is True
            assert len(received_triggers) == 1

        finally:
            await server.stop()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
