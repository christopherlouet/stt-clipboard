# Basic Usage

## Workflow

```
Press Hotkey → Speak → Pause (1.2s) → Text in Clipboard → Paste
```

## Using the Service

### Start the Service

```bash
systemctl --user start stt-clipboard
```

### Trigger Dictation

Press your configured hotkey (e.g., ++super+shift+s++), then:

1. **Speak** clearly into your microphone
2. **Pause** for about 1.2 seconds
3. **Paste** with ++ctrl+v++ (or ++cmd+v++ on macOS)

### View Logs

```bash
# Real-time logs
journalctl --user -u stt-clipboard -f

# Recent logs
journalctl --user -u stt-clipboard -n 50

# File logs
tail -f logs/stt-clipboard.log
```

## One-Shot Mode

For testing without the service:

```bash
uv run python -m src.main --mode oneshot
```

## Debug Mode

For verbose output:

```bash
uv run python -m src.main --daemon --log-level DEBUG
```

## Tips for Best Results

### Speaking

- Speak clearly at a natural pace
- Avoid speaking too fast
- Pause briefly between sentences for better punctuation

### Environment

- Use in a quiet environment
- Position microphone close to your mouth
- Avoid background noise

### Language

- The system auto-detects: French, English, German, Spanish, Italian
- Each language has specific punctuation rules
- French text gets French spacing (space before ? ! : ;)

## Module Testing

Test individual components:

```bash
# Test audio recording
uv run python -m src.audio_capture

# Test transcription
uv run python -m src.transcription

# Test clipboard
uv run python -m src.clipboard

# Test punctuation
uv run python -m src.punctuation
```
