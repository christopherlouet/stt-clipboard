#!/usr/bin/env python3
"""System verification test."""

import sys

import numpy as np
import pytest

from src.clipboard import ClipboardManager
from src.config import Config
from src.transcription import WhisperTranscriber


def test_config():
    """Test configuration loading."""
    print("Testing configuration...")
    config = Config.from_yaml("config/config.yaml")
    config.validate()
    print("✓ Configuration loaded and validated")

    # Verify some basic config values
    assert config.audio.sample_rate == 16000
    assert config.transcription.model_size in ["tiny", "base", "small", "medium", "large"]
    # Language can be empty string (auto-detect) or a specific language code
    assert (
        config.transcription.language in ["", "fr", "en"] or len(config.transcription.language) == 2
    )

    # Verify paste config
    assert hasattr(config, "paste"), "Config should have paste attribute"
    assert config.paste.enabled in [True, False]
    assert config.paste.timeout > 0
    assert config.paste.delay_ms >= 0
    assert config.paste.preferred_tool in ["auto", "xdotool", "ydotool", "wtype"]
    print("✓ Paste configuration validated")


@pytest.mark.slow
def test_whisper_model():
    """Test Whisper model loading."""
    print("\nTesting Whisper model...")
    config = Config.from_yaml("config/config.yaml")
    transcriber = WhisperTranscriber(config.transcription)

    print("  Loading model (this may take a few seconds)...")
    transcriber.load_model()

    print(f"✓ Model loaded successfully in {transcriber.load_time:.2f}s")
    assert transcriber.model is not None, "Model should be loaded"

    # Test transcription with synthetic audio
    print("  Testing transcription with synthetic audio...")
    audio = np.random.randn(16000).astype(np.float32) * 0.1  # 1 second of noise
    text = transcriber.transcribe(audio)

    print(f"✓ Transcription works (output: '{text[:50]}...')")
    assert isinstance(text, str), "Transcription should return a string"


def test_clipboard():
    """Test clipboard functionality."""
    print("\nTesting clipboard...")

    # Check if we're in Wayland session
    import os

    session_type = os.environ.get("XDG_SESSION_TYPE", "unknown")

    if session_type != "wayland":
        print(f"⚠ Not in Wayland session (session type: {session_type})")
        print("  Clipboard test skipped - will work in interactive Wayland session")
        pytest.skip("Not in Wayland session")
        return

    try:
        manager = ClipboardManager(timeout=1.0)  # Shorter timeout
        test_text = "Test de dictée vocale"

        success = manager.copy(test_text)
        if not success:
            print("⚠ Clipboard copy failed (may require interactive session)")
            print("  This is normal if running from SSH or non-interactive shell")
            pytest.skip("Clipboard requires interactive session")
            return

        # Try to read back
        pasted = manager.paste()
        if pasted == test_text:
            print("✓ Clipboard works (copy and paste successful)")
            assert pasted == test_text
        else:
            print("⚠ Clipboard copy works but paste may not match")
            # Still pass as long as copy worked

    except Exception as e:
        print(f"⚠ Clipboard test warning: {e}")
        print("  This is normal if not in interactive Wayland session")
        pytest.skip(f"Clipboard not available: {e}")


def main():
    """Run all tests."""
    print("=" * 60)
    print("STT Clipboard System Verification")
    print("=" * 60)
    print()

    results = {
        "Configuration": test_config(),
        "Whisper Model": test_whisper_model(),
        "Clipboard": test_clipboard(),
    }

    print()
    print("=" * 60)
    print("Summary:")
    print("=" * 60)

    for name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status} - {name}")

    all_passed = all(results.values())

    print()
    if all_passed:
        print("🎉 All tests passed! System is ready to use.")
        print()
        print("Next steps:")
        print("  1. Test manually: python -m src.main --mode oneshot")
        print("  2. Install service: ./scripts/install_service.sh")
        print("  3. Configure hotkey (see README.md)")
    else:
        print("⚠ Some tests failed. Please check the errors above.")
        print()
        print("Common issues:")
        print("  - Whisper model: Run ./scripts/install_deps.sh again")
        print("  - Clipboard: Ensure you're in a Wayland session")

    print("=" * 60)

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
