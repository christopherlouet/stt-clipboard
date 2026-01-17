"""Main orchestration for STT Clipboard service."""

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
from src.history import TranscriptionHistory
from src.hotkey import TriggerServer, TriggerType
from src.notifications import (
    notify_no_speech_detected,
    notify_recording_started,
    notify_text_copied,
)
from src.punctuation import PunctuationProcessor
from src.transcription import WhisperTranscriber


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

        # History (if enabled)
        self.history: TranscriptionHistory | None = None
        if config.history.enabled:
            self.history = TranscriptionHistory(
                history_file=config.history.file,
                max_entries=config.history.max_entries,
                auto_save=config.history.auto_save,
            )
            logger.info(
                f"History enabled: {config.history.file} (max {config.history.max_entries})"
            )

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
                logger.warning("No speech detected or recording failed")
                notify_no_speech_detected(timeout_seconds=self.config.audio.max_recording_duration)
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

            # Add to history (if enabled)
            if self.history:
                self.history.add(
                    text=text,
                    language=self.transcriber.detected_language,
                    audio_duration=audio_duration,
                    transcription_time=transcription_time,
                )

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

    async def run_continuous(self):
        """Run service in continuous dictation mode.

        Continuously records and transcribes audio segments, copying each
        to the clipboard. Press Ctrl+C to stop.
        """
        logger.info("Running in continuous dictation mode...")

        # Initialize
        await self.initialize()

        logger.info("\n" + "=" * 60)
        logger.info("Continuous Dictation Mode")
        logger.info("Speak into your microphone...")
        logger.info("Each pause will trigger transcription and clipboard copy")
        logger.info("Press Ctrl+C to stop")
        logger.info("=" * 60 + "\n")

        try:
            segment_count = 0

            for audio in self.audio_recorder.record_continuous():
                segment_count += 1
                self.stats["total_requests"] += 1

                audio_duration = len(audio) / self.config.audio.sample_rate
                self.stats["total_audio_duration"] += audio_duration

                logger.info(f"\n--- Segment #{segment_count} ---")

                # Transcribe
                logger.info("Transcribing...")
                transcription_start = time.time()
                text = await asyncio.to_thread(self.transcriber.transcribe, audio)
                transcription_time = time.time() - transcription_start
                self.stats["total_transcription_time"] += transcription_time

                if not text or not text.strip():
                    logger.warning("Empty transcription, skipping")
                    self.stats["failed_transcriptions"] += 1
                    continue

                # Post-process
                if self.config.punctuation.enabled:
                    detected_lang = self.transcriber.detected_language
                    text = self.punctuation_processor.process(text, detected_language=detected_lang)

                logger.info(f"Transcribed: {text}")

                # Copy to clipboard
                if self.config.clipboard.enabled:
                    success = await asyncio.to_thread(
                        copy_to_clipboard, text, self.config.clipboard.timeout
                    )
                    if success:
                        logger.info("✓ Copied to clipboard")
                        notify_text_copied(text)
                    else:
                        logger.error("Failed to copy to clipboard")
                        self.stats["failed_transcriptions"] += 1
                        continue

                self.stats["successful_transcriptions"] += 1

                # Add to history
                if self.history:
                    self.history.add(
                        text=text,
                        language=self.transcriber.detected_language,
                        audio_duration=audio_duration,
                        transcription_time=transcription_time,
                    )

                rtf = transcription_time / audio_duration if audio_duration > 0 else 0
                logger.info(
                    f"Segment complete (audio: {audio_duration:.2f}s, "
                    f"transcription: {transcription_time:.2f}s, RTF: {rtf:.2f}x)"
                )

        except KeyboardInterrupt:
            logger.info("\nStopping continuous mode...")
            self.audio_recorder.stop_continuous()

        finally:
            await self.shutdown()

        return 0

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
        choices=["daemon", "oneshot", "continuous", "tui"],
        default="daemon",
        help="Run mode: daemon (service), oneshot (single), continuous (dictation), or tui (text interface)",
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
        "--continuous",
        action="store_true",
        help="Run in continuous dictation mode (equivalent to --mode continuous)",
    )

    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Override log level from config",
    )

    parser.add_argument(
        "--tui",
        action="store_true",
        help="Run in TUI mode (equivalent to --mode tui)",
    )

    args = parser.parse_args()

    # Determine mode
    if args.tui:
        args.mode = "tui"
    elif args.daemon:
        args.mode = "daemon"
    elif args.continuous:
        args.mode = "continuous"

    try:
        # Load configuration
        config = Config.from_yaml(args.config)

        # Override log level if specified
        if args.log_level:
            config.logging.level = args.log_level

        # Validate config
        config.validate()

        # Validate system tools
        tools_result = config.validate_system_tools()
        if not tools_result.is_valid:
            for error in tools_result.errors:
                print(f"ERROR: {error}", file=sys.stderr)  # noqa: T201
            sys.exit(1)

        # Setup logging
        setup_logging(config)

        # Log warnings about optional tools
        for warning in tools_result.warnings:
            logger.warning(warning)

        logger.info("=" * 60)
        logger.info("STT Clipboard - Offline Speech-to-Text")
        logger.info("=" * 60)
        logger.info(f"Mode: {args.mode}")
        logger.info(f"Config: {args.config}")
        logger.info(f"Model: {config.transcription.model_size}")
        lang_display = config.transcription.language or "auto-detect"
        logger.info(f"Language: {lang_display}")
        logger.info("=" * 60)

        # Run TUI mode (separate from service modes)
        if args.mode == "tui":
            from src.tui import run_tui

            run_tui(config)
            return

        # Create service
        service = STTService(config)

        # Run service
        if args.mode == "daemon":
            asyncio.run(service.run_daemon())
        elif args.mode == "continuous":
            exit_code = asyncio.run(service.run_continuous())
            sys.exit(exit_code)
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
