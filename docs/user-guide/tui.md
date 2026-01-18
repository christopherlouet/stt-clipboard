# Text User Interface (TUI)

STT Clipboard includes a modern terminal-based interface built with [Textual](https://github.com/Textualize/textual) for easy operation and configuration.

## Launch

### From Project Directory

```bash
# Using Python module
uv run python -m src.main --tui

# Using Makefile
make tui
```

### Global Command

After running `./scripts/install_global.sh`:

```bash
stt-tui
```

!!! note "PATH Configuration"
    If `stt-tui` is not found, add `~/.local/bin` to your PATH:

    === "Bash"
        ```bash
        echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
        source ~/.bashrc
        ```

    === "Zsh"
        ```bash
        echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc
        source ~/.zshrc
        ```

## Interface Overview

The TUI provides a complete interface for:

- Recording and transcription
- Viewing transcription history
- Editing settings with hot-reload
- Monitoring performance statistics

```
┌─────────────────────────────────────────────────────────────────┐
│ STT Clipboard                                      [READY]      │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Transcription Log                                              │
│  ─────────────────                                              │
│  [2025-01-18 12:30:45] Bonjour, comment allez-vous ?           │
│  [2025-01-18 12:31:02] Hello, this is a test.                  │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│  [Record]  [Continuous]  [Stop]  [History]  [Settings]         │
├─────────────────────────────────────────────────────────────────┤
│  Total: 2 | Success: 2 | Failed: 0 | Audio: 8.5s | RTF: 0.25   │
└─────────────────────────────────────────────────────────────────┘
```

## Keyboard Shortcuts

| Key | Action | Description |
|-----|--------|-------------|
| ++r++ | Record | Start single recording |
| ++c++ | Continuous | Start continuous dictation mode |
| ++s++ | Stop | Stop current recording |
| ++h++ | History | View transcription history |
| ++o++ | Options | Open settings editor |
| ++q++ | Quit | Exit the application |

## Recording Modes

### Single Recording (++r++)

1. Press ++r++ to start recording
2. Speak into your microphone
3. Recording stops automatically after 1.2s of silence
4. Text is transcribed and copied to clipboard

### Continuous Mode (++c++)

1. Press ++c++ to start continuous mode
2. Speak in segments
3. Each pause triggers transcription and clipboard copy
4. Press ++s++ to stop

## Transcription History

Press ++h++ to view your transcription history.

Features:

- View all past transcriptions with timestamps
- See detected language for each entry
- Copy individual entries to clipboard
- Filter by date or language
- Persistent storage (survives restarts)

### History Configuration

In `config/config.yaml`:

```yaml
history:
  enabled: true                # Enable/disable history
  file: ./data/history.json    # Storage location
  max_entries: 100             # Maximum entries to keep
  auto_save: true              # Save after each transcription
```

## Settings Editor

Press ++o++ to open the settings editor.

### Features

- **Tabbed Interface**: Organized by category (Audio, Transcription, Output, System)
- **Hot-Reload**: Many settings apply immediately without restart
- **Validation**: Invalid values are rejected with clear error messages
- **Restart Indicators**: Settings requiring restart are marked with `[*]`

### Settings Categories

#### Audio Tab

| Setting | Description | Restart Required |
|---------|-------------|------------------|
| Sample Rate | Audio sampling rate (Hz) | Yes |
| Channels | Mono (1) or Stereo (2) | Yes |
| Silence Duration | Seconds of silence to stop recording | No |
| Min Speech Duration | Minimum speech to avoid false starts | No |
| Max Recording Duration | Maximum recording length | No |
| Block Size | Audio buffer size | Yes |

#### Transcription Tab

| Setting | Description | Restart Required |
|---------|-------------|------------------|
| Model Size | Whisper model (tiny/base/small/medium) | Yes |
| Language | Auto-detect, French, or English | No |
| Device | CPU or CUDA | Yes |
| Compute Type | int8/int16/float16/float32 | Yes |
| Beam Size | Decoding beam size (1-10) | No |

#### Output Tab

| Setting | Description | Restart Required |
|---------|-------------|------------------|
| Clipboard Enabled | Enable clipboard copy | No |
| Clipboard Timeout | Clipboard operation timeout | No |
| Paste Enabled | Enable auto-paste | No |
| Paste Tool | xdotool/ydotool/wtype/auto | No |
| Punctuation Enabled | Enable post-processing | No |
| French Spacing | Apply French typography rules | No |

#### System Tab

| Setting | Description | Restart Required |
|---------|-------------|------------------|
| Log Level | DEBUG/INFO/WARNING/ERROR | No |
| History Enabled | Enable transcription history | No |
| History Max Entries | Maximum history entries | No |

### Saving Changes

- Press ++ctrl+s++ to save changes
- Press ++escape++ to cancel (prompts if unsaved changes)
- Press ++ctrl+r++ to reset to original values

## Statistics Panel

The bottom panel shows real-time statistics:

| Metric | Description |
|--------|-------------|
| Total | Total transcription requests |
| Success | Successful transcriptions |
| Failed | Failed transcriptions |
| Audio | Total audio processed (seconds) |
| RTF | Real-Time Factor (lower is better) |

## Configuration Location

The TUI looks for configuration in this order:

1. `STT_CONFIG` environment variable
2. `./config/config.yaml` (current directory)
3. `~/.config/stt-clipboard/config.yaml` (user config)

For global installation, the config is automatically copied to `~/.config/stt-clipboard/`.

## Troubleshooting

### TUI doesn't start

```bash
# Check if Textual is installed
uv run python -c "import textual; print(textual.__version__)"

# Try reinstalling dependencies
uv sync
```

### Display issues

If the TUI looks wrong:

1. Ensure your terminal supports 256 colors
2. Try a different terminal emulator (kitty, alacritty, wezterm)
3. Check terminal dimensions (minimum 80x24)

### Settings not saving

1. Check file permissions on `config/config.yaml`
2. Ensure the config directory exists
3. Check for YAML syntax errors in existing config
