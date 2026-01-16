# Configuration

STT Clipboard is configured via `config/config.yaml`.

## Configuration File

```yaml
audio:
  sample_rate: 16000
  channels: 1
  silence_duration: 1.2
  min_speech_duration: 0.3
  max_recording_duration: 30
  blocksize: 512

vad:
  threshold: 0.5
  min_silence_duration_ms: 300
  speech_pad_ms: 300

transcription:
  model_size: base
  language: ""
  device: cpu
  compute_type: int8
  beam_size: 1
  best_of: 1
  temperature: 0.0
  download_root: ./models

punctuation:
  enabled: true
  french_spacing: true

clipboard:
  enabled: true
  timeout: 2.0

paste:
  enabled: true
  timeout: 2.0
  delay_ms: 100
  preferred_tool: auto

logging:
  level: INFO
  file: ./logs/stt-clipboard.log

hotkey:
  enabled: false
  socket_path: /tmp/stt-clipboard.sock
```

## Audio Settings

| Option | Default | Description |
|--------|---------|-------------|
| `sample_rate` | 16000 | Audio sample rate in Hz |
| `silence_duration` | 1.2 | Seconds of silence to stop recording |
| `min_speech_duration` | 0.3 | Minimum speech duration to process |
| `max_recording_duration` | 30 | Maximum recording length (safety limit) |

## Transcription Settings

| Option | Default | Description |
|--------|---------|-------------|
| `model_size` | base | Whisper model: `tiny`, `base`, `small`, `medium` |
| `language` | "" | Empty = auto-detect FR/EN, or force `"fr"` / `"en"` |
| `compute_type` | int8 | Quantization: `int8`, `int16`, `float16`, `float32` |
| `beam_size` | 1 | Higher = more accurate but slower |

### Model Selection

| Model | Size | Speed (5s audio) | Accuracy |
|-------|------|------------------|----------|
| tiny | 75MB | ~0.8s | Good |
| base | 140MB | ~1.2s | Better |
| small | 460MB | ~3s | Excellent |
| medium | 1.5GB | ~8s | Best |

## Auto-Paste Settings

| Option | Default | Description |
|--------|---------|-------------|
| `enabled` | true | Enable/disable auto-paste |
| `timeout` | 2.0 | Timeout for paste operations |
| `delay_ms` | 100 | Delay between copy and paste |
| `preferred_tool` | auto | `"auto"`, `"osascript"`, `"xdotool"`, `"ydotool"`, `"wtype"` |

## Language Settings

### Auto-Detection (Recommended)

```yaml
transcription:
  language: ""  # Auto-detect French/English
```

### Force Single Language

```yaml
transcription:
  language: "fr"  # French only (slightly faster)
```

## Applying Changes

After modifying the configuration:

```bash
systemctl --user restart stt-clipboard
```

## Environment Variables

You can override some settings via environment variables:

```bash
export STT_LOG_LEVEL=DEBUG
export STT_MODEL_SIZE=small
```
