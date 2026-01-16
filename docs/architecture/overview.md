# Architecture Overview

## System Flow

```
┌─────────────────────────────────────────────────────────┐
│                    User Presses Hotkey                  │
└─────────────────────┬───────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────────┐
│  trigger.sh / trigger_paste.sh / trigger_paste_terminal.sh │
│  → Unix Socket → TriggerServer (hotkey.py)              │
└─────────────────────┬───────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────────┐
│          STTService.process_request() (main.py)         │
└─────────────────────┬───────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────────┐
│  Step 1: AudioRecorder records until silence (1.2s)    │
│          - sounddevice captures audio                   │
│          - silero-vad detects speech/silence            │
│          (audio_capture.py)                             │
└─────────────────────┬───────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────────┐
│  Step 2: WhisperTranscriber transcribes audio           │
│          - faster-whisper (CTranslate2)                 │
│          - Optimized for CPU, French/English            │
│          (transcription.py)                             │
└─────────────────────┬───────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────────┐
│  Step 3: PunctuationProcessor post-processes            │
│          - Language-aware typography (FR/EN)            │
│          - Capitalize sentences                         │
│          (punctuation.py)                               │
└─────────────────────┬───────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────────┐
│  Step 4: ClipboardManager copies to clipboard           │
│          - Wayland (wl-copy) / X11 (xclip) / macOS      │
│          (clipboard.py)                                 │
└─────────────────────┬───────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────────┐
│  Step 5 (Optional): Auto-paste                          │
│          - Ctrl+V / Ctrl+Shift+V / Cmd+V                │
│          (autopaste.py)                                 │
└─────────────────────┬───────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────────┐
│              Text appears in application                │
└─────────────────────────────────────────────────────────┘
```

## Design Principles

### Privacy First

- **100% Offline**: No network calls after model download
- **No Logging of Content**: Audio/text never logged
- **In-Memory Processing**: Audio never saved to disk

### Low Latency

- **Silence Detection**: Stops recording after 1.2s silence
- **Optimized Model**: int8 quantization for faster inference
- **Pre-loaded Model**: Model stays in memory

### Universal Compatibility

- **Multi-Platform**: Linux (Wayland/X11) and macOS
- **Auto-Detection**: Automatically selects best tools
- **Fallback Chain**: Multiple options for each function

## Key Technologies

| Component | Technology | Purpose |
|-----------|------------|---------|
| STT Engine | faster-whisper | Speech-to-text |
| VAD | Silero VAD | Speech detection |
| Audio | sounddevice | Audio capture |
| ML Runtime | CTranslate2 | Optimized inference |
| IPC | Unix Sockets | Hotkey triggering |
