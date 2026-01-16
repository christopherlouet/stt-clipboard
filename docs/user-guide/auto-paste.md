# Auto-Paste

Auto-paste automatically types the transcribed text into the active application.

## Overview

| Platform | Tool | Shortcut |
|----------|------|----------|
| Linux (X11) | xdotool | Ctrl+V |
| Linux (Wayland) | ydotool | Ctrl+V |
| Linux (Wayland) | wtype | Direct typing |
| macOS | osascript | Cmd+V |

## Setup

### Linux (X11)

xdotool is usually installed automatically:

```bash
sudo apt install xdotool  # Debian/Ubuntu
sudo dnf install xdotool  # Fedora
sudo pacman -S xdotool    # Arch
```

### Linux (Wayland)

ydotool requires the daemon to be running:

```bash
# Install
sudo apt install ydotool  # Debian/Ubuntu
sudo dnf install ydotool  # Fedora
sudo pacman -S ydotool    # Arch

# Enable daemon
sudo systemctl enable --now ydotool
```

### macOS

!!! warning "Accessibility Permissions Required"
    macOS requires Accessibility permissions for auto-paste to work.

1. Go to **System Settings** → **Privacy & Security** → **Accessibility**
2. Enable access for your terminal application (e.g., Terminal, iTerm2)
3. If using a launcher app, enable it too

## Configuration

Edit `config/config.yaml`:

```yaml
paste:
  enabled: true
  timeout: 2.0
  delay_ms: 100
  preferred_tool: auto  # or "osascript", "xdotool", "ydotool", "wtype"
```

## Trigger Scripts

### Copy Only (Default)

```bash
./scripts/trigger.sh
```

Text is copied to clipboard. Manual paste required.

### Auto-Paste (Standard Apps)

```bash
./scripts/trigger_paste.sh
```

Text is copied and automatically pasted with ++ctrl+v++ (++cmd+v++ on macOS).

### Terminal Paste

```bash
./scripts/trigger_paste_terminal.sh
```

Text is copied and pasted with ++ctrl+shift+v++ (for terminal emulators).

## Keyboard Shortcuts

Configure multiple shortcuts for different modes:

| Shortcut | Script | Use Case |
|----------|--------|----------|
| ++super+shift+s++ | `trigger.sh` | Copy only |
| ++super+shift+v++ | `trigger_paste.sh` | Auto-paste in apps |
| ++super+shift+t++ | `trigger_paste_terminal.sh` | Auto-paste in terminals |

## Troubleshooting

### xdotool not working

```bash
# Check if DISPLAY is set
echo $DISPLAY

# Test xdotool
xdotool key ctrl+v
```

### ydotool not working

```bash
# Check if daemon is running
systemctl status ydotool

# Start daemon
sudo systemctl start ydotool
```

### macOS paste not working

1. Check Accessibility permissions
2. Try running the script directly:
   ```bash
   osascript -e 'tell application "System Events" to keystroke "v" using command down'
   ```
