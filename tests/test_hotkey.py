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


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
