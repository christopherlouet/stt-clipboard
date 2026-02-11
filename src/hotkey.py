"""Unix socket trigger server for hotkey integration."""

import asyncio
import os
import threading
import time
from collections import deque
from collections.abc import Awaitable, Callable
from enum import Enum
from pathlib import Path

from loguru import logger


class TriggerType(Enum):
    """Type of trigger received."""

    COPY = "TRIGGER_COPY"
    PASTE = "TRIGGER_PASTE"
    PASTE_TERMINAL = "TRIGGER_PASTE_TERMINAL"  # Ctrl+Shift+V for terminals
    UNKNOWN = "TRIGGER"  # Legacy support


VALID_COMMANDS: frozenset[str] = frozenset(
    {
        "TRIGGER_COPY",
        "TRIGGER_PASTE",
        "TRIGGER_PASTE_TERMINAL",
        "TRIGGER",
    }
)


class RateLimiter:
    """Sliding window rate limiter for trigger requests."""

    def __init__(self, max_requests: int = 5, window_seconds: float = 10.0):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._timestamps: deque[float] = deque()
        self._lock = threading.Lock()

    def allow(self) -> bool:
        """Check if a request is allowed under the rate limit."""
        now = time.monotonic()
        with self._lock:
            # Evict expired timestamps
            cutoff = now - self.window_seconds
            while self._timestamps and self._timestamps[0] <= cutoff:
                self._timestamps.popleft()

            if len(self._timestamps) >= self.max_requests:
                return False

            self._timestamps.append(now)
            return True


class TriggerServer:
    """Unix socket server for receiving trigger events from hotkey."""

    def __init__(
        self,
        socket_path: str = "/tmp/stt-clipboard.sock",  # nosec B108
        on_trigger: Callable[[TriggerType], Awaitable[None]] | None = None,
    ):
        """Initialize trigger server.

        Args:
            socket_path: Path to Unix socket
            on_trigger: Async callback when trigger received (receives TriggerType)
        """
        self.socket_path = socket_path
        self.on_trigger = on_trigger
        self.server: asyncio.Server | None = None
        self.is_running = False
        self._rate_limiter = RateLimiter()

        logger.info(f"TriggerServer initialized: socket={socket_path}")

    async def _handle_client(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> None:
        """Handle client connection.

        Args:
            reader: Stream reader
            writer: Stream writer
        """
        addr = writer.get_extra_info("peername")
        logger.debug(f"Client connected: {addr}")

        try:
            # Rate limiting check
            if not self._rate_limiter.allow():
                logger.warning("Rate limit exceeded, rejecting request")
                writer.write(b"RATE_LIMITED\n")
                await writer.drain()
                return

            # Read data (up to 1024 bytes to detect oversized messages)
            data = await reader.read(1024)

            # Reject oversized messages (> 100 bytes)
            if len(data) > 100:
                logger.warning(f"Rejecting oversized message: {len(data)} bytes")
                writer.write(b"REJECTED\n")
                await writer.drain()
                return

            # Decode UTF-8 safely
            try:
                message = data.decode("utf-8").strip()
            except UnicodeDecodeError:
                logger.warning("Rejecting non-UTF8 data")
                writer.write(b"REJECTED\n")
                await writer.drain()
                return

            logger.debug(f"Received trigger: {message}")

            # Reject empty messages
            if not message:
                logger.warning("Rejecting empty message")
                writer.write(b"REJECTED\n")
                await writer.drain()
                return

            # Validate command against whitelist
            if message not in VALID_COMMANDS:
                logger.warning(f"Rejecting unknown command: {message}")
                writer.write(b"REJECTED\n")
                await writer.drain()
                return

            # Parse trigger type
            if message == "TRIGGER_COPY":
                trigger_type = TriggerType.COPY
            elif message == "TRIGGER_PASTE":
                trigger_type = TriggerType.PASTE
            elif message == "TRIGGER_PASTE_TERMINAL":
                trigger_type = TriggerType.PASTE_TERMINAL
            else:
                # "TRIGGER" legacy support
                trigger_type = TriggerType.UNKNOWN

            # Call trigger callback with type
            if self.on_trigger:
                try:
                    await self.on_trigger(trigger_type)
                    # Send success response
                    writer.write(b"OK\n")
                except Exception as e:
                    logger.error(f"Trigger callback failed: {e}")
                    writer.write(f"ERROR: {e}\n".encode())
            else:
                writer.write(b"NO_HANDLER\n")

            await writer.drain()

        except Exception as e:
            logger.error(f"Error handling client: {e}")

        finally:
            try:
                writer.close()
                await writer.wait_closed()
            except (BrokenPipeError, ConnectionResetError):
                # Client disconnected early (normal with netcat)
                pass
            except Exception as e:
                logger.debug(f"Error closing connection: {e}")
            logger.debug("Client disconnected")

    async def start(self) -> None:
        """Start the trigger server."""
        if self.is_running:
            logger.warning("Server already running")
            return

        # Remove existing socket if present
        socket_file = Path(self.socket_path)
        if socket_file.exists():
            logger.info(f"Removing existing socket: {self.socket_path}")
            socket_file.unlink()

        # Ensure parent directory exists
        socket_file.parent.mkdir(parents=True, exist_ok=True)

        try:
            # Create Unix socket server
            self.server = await asyncio.start_unix_server(
                self._handle_client, path=self.socket_path
            )

            # Set socket permissions (readable/writable by user)
            os.chmod(self.socket_path, 0o600)

            self.is_running = True
            logger.info(f"Trigger server started on {self.socket_path}")

        except Exception as e:
            logger.error(f"Failed to start trigger server: {e}")
            raise RuntimeError(f"Server start failed: {e}")

    async def serve_forever(self) -> None:
        """Serve forever (run until cancelled)."""
        if not self.server:
            await self.start()

        assert self.server is not None
        async with self.server:
            await self.server.serve_forever()

    async def stop(self) -> None:
        """Stop the trigger server."""
        if not self.is_running:
            return

        logger.info("Stopping trigger server...")

        if self.server:
            self.server.close()
            await self.server.wait_closed()

        # Remove socket file
        socket_file = Path(self.socket_path)
        if socket_file.exists():
            socket_file.unlink()

        self.is_running = False
        logger.info("Trigger server stopped")

    async def wait_for_trigger(self, timeout: float | None = None) -> bool:
        """Wait for a single trigger event.

        Args:
            timeout: Timeout in seconds, or None for no timeout

        Returns:
            True if trigger received, False if timeout
        """
        trigger_event = asyncio.Event()

        async def trigger_handler(trigger_type: TriggerType) -> None:
            trigger_event.set()

        # Set temporary handler
        old_handler = self.on_trigger
        self.on_trigger = trigger_handler

        try:
            # Wait for trigger
            if timeout:
                await asyncio.wait_for(trigger_event.wait(), timeout=timeout)
            else:
                await trigger_event.wait()

            return True

        except asyncio.TimeoutError:
            logger.debug("Trigger wait timeout")
            return False

        finally:
            # Restore original handler
            self.on_trigger = old_handler


class TriggerClient:
    """Client for sending trigger events to the server."""

    def __init__(self, socket_path: str = "/tmp/stt-clipboard.sock"):  # nosec B108
        """Initialize trigger client.

        Args:
            socket_path: Path to Unix socket
        """
        self.socket_path = socket_path

    async def send_trigger(self, trigger_type: str = "TRIGGER", timeout: float = 2.0) -> bool:
        """Send trigger event to server.

        Args:
            trigger_type: Type of trigger to send ("TRIGGER", "TRIGGER_COPY", "TRIGGER_PASTE")
            timeout: Connection timeout

        Returns:
            True if successful, False otherwise
        """
        try:
            # Connect to Unix socket
            reader, writer = await asyncio.wait_for(
                asyncio.open_unix_connection(self.socket_path), timeout=timeout
            )

            # Send trigger message
            writer.write(f"{trigger_type}\n".encode())
            await writer.drain()

            # Wait for response
            response = await asyncio.wait_for(reader.read(100), timeout=timeout)
            response_text = response.decode("utf-8").strip()

            logger.debug(f"Server response: {response_text}")

            # Close connection
            writer.close()
            await writer.wait_closed()

            return response_text == "OK"

        except FileNotFoundError:
            logger.error(f"Socket not found: {self.socket_path}")
            logger.error("Is the STT service running?")
            return False

        except asyncio.TimeoutError:
            logger.error(f"Connection timeout after {timeout}s")
            return False

        except Exception as e:
            logger.error(f"Failed to send trigger: {e}")
            return False

    def send_trigger_sync(self, trigger_type: str = "TRIGGER", timeout: float = 2.0) -> bool:
        """Send trigger synchronously (for use in scripts).

        Args:
            trigger_type: Type of trigger to send ("TRIGGER", "TRIGGER_COPY", "TRIGGER_PASTE")
            timeout: Connection timeout

        Returns:
            True if successful, False otherwise
        """
        return asyncio.run(self.send_trigger(trigger_type, timeout))


# Convenience functions
def send_trigger(
    socket_path: str = "/tmp/stt-clipboard.sock",
    trigger_type: str = "TRIGGER",
    timeout: float = 2.0,
) -> bool:  # nosec B108
    """Send trigger event (convenience function).

    Args:
        socket_path: Path to Unix socket
        trigger_type: Type of trigger to send
        timeout: Connection timeout

    Returns:
        True if successful, False otherwise
    """
    client = TriggerClient(socket_path)
    return client.send_trigger_sync(trigger_type, timeout)


# Example usage and testing
if __name__ == "__main__":
    import sys

    async def test_server() -> None:
        """Test the trigger server."""
        print("Trigger Server Test")
        print("=" * 60)

        trigger_count = [0]  # Use list for closure

        async def handle_trigger(trigger_type: TriggerType) -> None:
            trigger_count[0] += 1
            print(f"\n🎯 Trigger received! Type: {trigger_type.value} (count: {trigger_count[0]})")

        # Create server
        server = TriggerServer(
            socket_path="/tmp/stt-clipboard-test.sock",
            on_trigger=handle_trigger,  # nosec B108
        )

        # Start server
        await server.start()

        print("\nServer started. Waiting for triggers...")
        print("Run this in another terminal to trigger:")
        print(
            "  python -c 'from src.hotkey import send_trigger; send_trigger(\"/tmp/stt-clipboard-test.sock\")'"
        )
        print("\nPress Ctrl+C to stop\n")

        try:
            # Run server
            await server.serve_forever()

        except KeyboardInterrupt:
            print("\n\nShutting down...")

        finally:
            await server.stop()
            print(f"Total triggers received: {trigger_count[0]}")

    async def test_client() -> None:
        """Test the trigger client."""
        print("Trigger Client Test")
        print("=" * 60)

        client = TriggerClient("/tmp/stt-clipboard-test.sock")  # nosec B108

        print("\nSending trigger...")
        success = await client.send_trigger()

        if success:
            print("✓ Trigger sent successfully")
        else:
            print("✗ Failed to send trigger")
            sys.exit(1)

    # Run test
    if len(sys.argv) > 1 and sys.argv[1] == "client":
        # Test client
        asyncio.run(test_client())
    else:
        # Test server
        asyncio.run(test_server())
