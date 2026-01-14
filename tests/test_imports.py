#!/usr/bin/env python3
"""Test that all modules can be imported successfully."""

import sys


def test_imports():
    """Test all imports."""
    print("Testing module imports...")
    print()

    tests = [
        ("Config", "from src.config import Config"),
        ("AudioRecorder", "from src.audio_capture import AudioRecorder"),
        ("WhisperTranscriber", "from src.transcription import WhisperTranscriber"),
        ("PunctuationProcessor", "from src.punctuation import PunctuationProcessor"),
        ("ClipboardManager", "from src.clipboard import ClipboardManager"),
        ("TriggerServer", "from src.hotkey import TriggerServer"),
        ("TriggerType", "from src.hotkey import TriggerType"),
        ("BaseAutoPaster", "from src.autopaste import BaseAutoPaster"),
        ("create_autopaster", "from src.autopaste import create_autopaster"),
    ]

    passed = 0
    failed = 0
    failed_imports = []

    for name, import_stmt in tests:
        try:
            exec(import_stmt)
            print(f"✓ {name}")
            passed += 1
        except Exception as e:
            print(f"✗ {name}: {e}")
            failed += 1
            failed_imports.append((name, str(e)))

    print()
    print("=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)

    assert failed == 0, f"Failed imports: {', '.join([name for name, _ in failed_imports])}"


if __name__ == "__main__":
    try:
        test_imports()
        print("\n✓ All imports successful!")
        sys.exit(0)
    except AssertionError as e:
        print(f"\n✗ Import test failed: {e}")
        sys.exit(1)
