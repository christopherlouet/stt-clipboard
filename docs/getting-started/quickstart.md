# Quick Start

## 1. Install Dependencies

```bash
./scripts/install_deps.sh
```

## 2. Test One-Shot Mode

```bash
uv run python -m src.main --mode oneshot
```

Speak into your microphone, pause for 1.2 seconds, and the text will appear in your clipboard.

## 3. Install as Service

```bash
./scripts/install_service.sh
```

This installs and enables the service to start automatically on login.

## 4. Configure Keyboard Shortcut

### Ubuntu GNOME

1. Open **Settings** → **Keyboard** → **Keyboard Shortcuts**
2. Click **"+"** to add custom shortcut
3. Set:
    - **Name**: STT Dictation
    - **Command**: `/path/to/stt-clipboard/scripts/trigger.sh`
    - **Shortcut**: e.g., ++super+shift+s++

### KDE Plasma

1. Open **System Settings** → **Shortcuts** → **Custom Shortcuts**
2. Right-click → **New** → **Global Shortcut** → **Command/URL**
3. Set command to: `/path/to/stt-clipboard/scripts/trigger.sh`
4. Assign hotkey: e.g., ++meta+shift+s++

### macOS

1. Use a tool like **BetterTouchTool**, **Karabiner-Elements**, or **Hammerspoon**
2. Set command to: `/path/to/stt-clipboard/scripts/trigger.sh`
3. Assign hotkey: e.g., ++ctrl+option+s++

## 5. Usage

1. Press your configured hotkey
2. Speak (you'll see a notification)
3. Pause for 1.2 seconds
4. Text is automatically copied to clipboard
5. Paste with ++ctrl+v++ (or ++cmd+v++ on macOS)

## Trigger Modes

| Mode | Script | Behavior |
|------|--------|----------|
| Copy Only | `trigger.sh` | Text copied to clipboard |
| Auto-Paste | `trigger_paste.sh` | Text copied and pasted (Ctrl+V) |
| Terminal Paste | `trigger_paste_terminal.sh` | Text copied and pasted (Ctrl+Shift+V) |

## Next Steps

- [Configuration Guide](configuration.md)
- [Auto-Paste Setup](../user-guide/auto-paste.md)
- [Troubleshooting](../user-guide/troubleshooting.md)
