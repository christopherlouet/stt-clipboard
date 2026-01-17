"""Main orchestration for STT Clipboard service.

This module provides the main entry point and service orchestration for the
STT Clipboard application. It coordinates all components:

1. Audio recording with VAD
2. Speech-to-text transcription with Whisper
3. Punctuation post-processing
4. Clipboard copying
5. Optional auto-paste

The service can run in two modes:
    - **daemon**: Runs as a background service, listening for trigger events
      via Unix socket. Suitable for systemd service deployment.
    - **oneshot**: Performs a single transcription and exits. Useful for
      testing and debugging.

Example:
    Run as daemon::

        python -m src.main --daemon
        python -m src.main --mode daemon

    Run single transcription::

        python -m src.main --mode oneshot

    With custom config::

        python -m src.main --config /path/to/config.yaml --log-level DEBUG

Trigger modes (daemon only):
    - TRIGGER_COPY: Transcribe and copy to clipboard
    - TRIGGER_PASTE: Transcribe, copy, and auto-paste (Ctrl+V)
    - TRIGGER_PASTE_TERMINAL: Transcribe, copy, and paste for terminals (Ctrl+Shift+V)

Architecture:
    The STTService class orchestrates the pipeline:

    Trigger → Audio Recording → VAD → Transcription → Punctuation → Clipboard → [Paste]
"""

import argparse
import asyncio
import sys
import time
from pathlib import Path

from loguru import logger

from src.audio_capture import AudioRecorder
from src.autopaste import create_autopaster
from src.clipboard import copy_to_clipboard
from src.config import Config
from src.hotkey import TriggerServer, TriggerType
from src.notifications import notify_recording_started, notify_text_copied
from src.punctuation import PunctuationProcessor
from src.transcription import WhisperTranscriber
from src.warmup import warmup_transcriber


class STTService:
    """Main STT service orchestrator."""

    def __init__(self, config: Config):
        """Initialize STT service.

        Args:
            config: Service configuration
        """
        self.config = config

        # Initialize components (transcriber loaded at startup)
        self.transcriber = WhisperTranscriber(config.transcription)
        self.audio_recorder = AudioRecorder(config.audio, config.vad)
        self.punctuation_processor = PunctuationProcessor(
            enable_french_spacing=config.punctuation.french_spacing,
            clean_artifacts=True,
            capitalize=True,
        )

        # Auto-paster (if enabled)
        self.autopaster = None
        self.autopaster_terminal = None
        if config.paste.enabled:
            try:
                self.autopaster = create_autopaster(
                    preferred_tool=config.paste.preferred_tool, timeout=config.paste.timeout
                )
                logger.info(f"Auto-paste enabled: {self.autopaster.__class__.__name__}")

                # Create terminal paster (with Shift for Ctrl+Shift+V)
                if config.paste.preferred_tool == "ydotool":
                    from src.autopaste import YdotoolPaster

                    self.autopaster_terminal = YdotoolPaster(
                        timeout=config.paste.timeout, use_shift=True
                    )
                    logger.info("Auto-paste terminal mode enabled (Ctrl+Shift+V)")
            except Exception as e:
                logger.warning(f"Auto-paste initialization failed: {e}")
                logger.warning("Auto-paste will be disabled")

        # Trigger server (if enabled)
        self.trigger_server: TriggerServer | None = None

        # Stats
        self.stats = {
            "total_requests": 0,
            "successful_transcriptions": 0,
            "failed_transcriptions": 0,
            "total_transcription_time": 0.0,
            "total_audio_duration": 0.0,
        }

        logger.info("STTService initialized")

    async def initialize(self):
        """Initialize service (load models, etc.)."""
        logger.info("Initializing STT service...")

        # Load Whisper model
        logger.info("Loading Whisper model (this may take a few seconds)...")
        self.transcriber.load_model()

        # Pre-load VAD model
        logger.info("Pre-loading VAD model...")
        self.audio_recorder._load_vad_model()

        # Warmup transcription model if enabled
        if self.config.transcription.warmup_enabled:
            logger.info("Warming up transcription model...")
            warmup_result = warmup_transcriber(self.transcriber)
            if warmup_result.success:
                logger.info(f"✓ Model warmup completed in {warmup_result.duration_seconds:.2f}s")
            else:
                logger.warning(f"Model warmup failed: {warmup_result.error_message}")

        logger.info("✓ Service initialization complete")

    async def process_request(self, trigger_type: TriggerType = TriggerType.UNKNOWN) -> str | None:
        """Process a single STT request (record → transcribe → clipboard → optional paste).

        Args:
            trigger_type: Type of trigger (COPY, PASTE, or UNKNOWN)

        Returns:
            Transcribed text, or None if failed
        """
        self.stats["total_requests"] += 1
        request_start = time.time()

        logger.info(f"Processing request #{self.stats['total_requests']}")

        try:
            # Step 1: Record audio
            logger.info("Recording audio...")
            # Send notification that recording has started
            notify_recording_started()
            audio = await asyncio.to_thread(self.audio_recorder.record_until_silence)

            if audio is None:
                logger.error("Audio recording failed")
                self.stats["failed_transcriptions"] += 1
                return None

            audio_duration = len(audio) / self.config.audio.sample_rate
            self.stats["total_audio_duration"] += audio_duration

            # Step 2: Transcribe
            logger.info("Transcribing audio...")
            transcription_start = time.time()

            text = await asyncio.to_thread(self.transcriber.transcribe, audio)

            transcription_time = time.time() - transcription_start
            self.stats["total_transcription_time"] += transcription_time

            if not text or not text.strip():
                logger.warning("Transcription returned empty text")
                self.stats["failed_transcriptions"] += 1
                return None

            logger.info(f"Transcription: '{text}'")

            # Step 3: Post-process punctuation (language-aware)
            if self.config.punctuation.enabled:
                detected_lang = self.transcriber.detected_language
                logger.debug(f"Applying punctuation rules (detected: {detected_lang})...")
                text = self.punctuation_processor.process(text, detected_language=detected_lang)
                logger.info(f"After punctuation: '{text}'")

            # Step 4: Copy to clipboard
            if self.config.clipboard.enabled:
                logger.info("Copying to clipboard...")
                success = await asyncio.to_thread(
                    copy_to_clipboard, text, self.config.clipboard.timeout
                )

                if not success:
                    logger.error("Failed to copy to clipboard")
                    self.stats["failed_transcriptions"] += 1
                    return None

                logger.info("✓ Text copied to clipboard")
                # Send notification that text has been copied
                notify_text_copied(text)

            # Step 5: Auto-paste (if requested and enabled)
            if trigger_type == TriggerType.PASTE and self.autopaster:
                logger.info("Auto-pasting text...")

                # Small delay to ensure clipboard is ready
                await asyncio.sleep(self.config.paste.delay_ms / 1000.0)

                try:
                    success = await asyncio.to_thread(self.autopaster.paste)

                    if success:
                        logger.info("✓ Text auto-pasted")
                    else:
                        logger.warning("Auto-paste failed")
                except Exception as e:
                    logger.error(f"Auto-paste error: {e}")

            elif trigger_type == TriggerType.PASTE_TERMINAL and self.autopaster_terminal:
                logger.info("Auto-pasting text (terminal mode with Ctrl+Shift+V)...")

                # Small delay to ensure clipboard is ready
                await asyncio.sleep(self.config.paste.delay_ms / 1000.0)

                try:
                    success = await asyncio.to_thread(self.autopaster_terminal.paste)

                    if success:
                        logger.info("✓ Text auto-pasted (terminal)")
                    else:
                        logger.warning("Auto-paste (terminal) failed")
                except Exception as e:
                    logger.error(f"Auto-paste (terminal) error: {e}")

            # Stats
            total_time = time.time() - request_start
            rtf = transcription_time / audio_duration if audio_duration > 0 else 0

            logger.info(
                f"Request complete: {total_time:.2f}s total "
                f"(audio: {audio_duration:.2f}s, "
                f"transcription: {transcription_time:.2f}s, "
                f"RTF: {rtf:.2f}x)"
            )

            self.stats["successful_transcriptions"] += 1

            return text

        except Exception as e:
            logger.error(f"Request processing failed: {e}")
            self.stats["failed_transcriptions"] += 1
            return None

    async def run_daemon(self):
        """Run service in daemon mode (wait for triggers)."""
        logger.info("Starting STT service in daemon mode...")

        # Initialize
        await self.initialize()

        # Create callback that passes trigger type
        async def trigger_callback(trigger_type: TriggerType):
            await self.process_request(trigger_type)

        # Create trigger server
        self.trigger_server = TriggerServer(
            socket_path=self.config.hotkey.socket_path, on_trigger=trigger_callback
        )

        await self.trigger_server.start()

        logger.info(f"✓ Service ready! Listening for triggers on {self.config.hotkey.socket_path}")
        logger.info("Press Ctrl+C to stop")

        try:
            # Run server forever
            await self.trigger_server.serve_forever()

        except KeyboardInterrupt:
            logger.info("Received interrupt signal")

        finally:
            await self.shutdown()

    async def run_oneshot(self):
        """Run service in one-shot mode (single transcription)."""
        logger.info("Running in one-shot mode...")

        # Initialize
        await self.initialize()

        logger.info("\n" + "=" * 60)
        logger.info("Ready to record! Speak into your microphone...")
        logger.info("Recording will stop after 1.2s of silence")
        logger.info("=" * 60 + "\n")

        # Process single request
        text = await self.process_request()

        if text:
            logger.info("\n" + "=" * 60)
            logger.info("SUCCESS!")
            logger.info(f"Transcribed: {text}")
            logger.info(f"Characters: {len(text)}")
            logger.info("Text is now in your clipboard (Ctrl+V to paste)")
            logger.info("=" * 60)

            return 0
        else:
            logger.error("\n" + "=" * 60)
            logger.error("FAILED!")
            logger.error("Transcription failed, please try again")
            logger.error("=" * 60)

            return 1

    async def shutdown(self):
        """Shutdown service gracefully."""
        logger.info("Shutting down service...")

        # Stop trigger server
        if self.trigger_server:
            await self.trigger_server.stop()

        # Print stats
        logger.info("\n" + "=" * 60)
        logger.info("Session Statistics:")
        logger.info(f"  Total requests: {self.stats['total_requests']}")
        logger.info(f"  Successful: {self.stats['successful_transcriptions']}")
        logger.info(f"  Failed: {self.stats['failed_transcriptions']}")

        if self.stats["total_audio_duration"] > 0:
            logger.info(f"  Total audio processed: {self.stats['total_audio_duration']:.1f}s")
            logger.info(
                f"  Total transcription time: {self.stats['total_transcription_time']:.1f}s"
            )
            avg_rtf = self.stats["total_transcription_time"] / self.stats["total_audio_duration"]
            logger.info(f"  Average RTF: {avg_rtf:.2f}x")

        logger.info("=" * 60)

        logger.info("Goodbye!")


def setup_logging(config: Config):
    """Setup logging configuration.

    Args:
        config: Configuration object
    """
    # Remove default logger
    logger.remove()

    # Add console logger
    logger.add(
        sys.stderr,
        format=config.logging.format,
        level=config.logging.level,
        colorize=True,
    )

    # Add file logger
    if config.logging.file:
        log_file = Path(config.logging.file)
        log_file.parent.mkdir(parents=True, exist_ok=True)

        logger.add(
            config.logging.file,
            format=config.logging.format,
            level=config.logging.level,
            rotation="10 MB",
            retention="7 days",
            compression="zip",
        )

    logger.info(f"Logging configured: level={config.logging.level}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="STT Clipboard - Offline Speech-to-Text (French/English)"
    )

    parser.add_argument(
        "--mode",
        choices=["daemon", "oneshot"],
        default="daemon",
        help="Run mode: daemon (service) or oneshot (single transcription)",
    )

    parser.add_argument(
        "--config", type=str, default="config/config.yaml", help="Path to config file"
    )

    parser.add_argument(
        "--daemon",
        action="store_true",
        help="Run in daemon mode (equivalent to --mode daemon)",
    )

    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Override log level from config",
    )

    args = parser.parse_args()

    # Determine mode
    if args.daemon:
        args.mode = "daemon"

    try:
        # Load configuration
        config = Config.from_yaml(args.config)

        # Override log level if specified
        if args.log_level:
            config.logging.level = args.log_level

        # Validate config
        config.validate()

        # Setup logging
        setup_logging(config)

        logger.info("=" * 60)
        logger.info("STT Clipboard - Offline Speech-to-Text")
        logger.info("=" * 60)
        logger.info(f"Mode: {args.mode}")
        logger.info(f"Config: {args.config}")
        logger.info(f"Model: {config.transcription.model_size}")
        lang_display = config.transcription.language or "auto-detect"
        logger.info(f"Language: {lang_display}")
        logger.info("=" * 60)

        # Create service
        service = STTService(config)

        # Run service
        if args.mode == "daemon":
            asyncio.run(service.run_daemon())
        else:
            exit_code = asyncio.run(service.run_oneshot())
            sys.exit(exit_code)

    except KeyboardInterrupt:
        logger.info("\nInterrupted by user")
        sys.exit(0)

    except Exception as e:
        logger.error(f"Fatal error: {e}")
        logger.exception("Traceback:")
        sys.exit(1)


if __name__ == "__main__":
    main()
