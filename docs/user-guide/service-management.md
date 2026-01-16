# Service Management

STT Clipboard runs as a systemd user service for automatic startup.

## Installation

```bash
./scripts/install_service.sh
```

## Commands

### Start Service

```bash
systemctl --user start stt-clipboard
```

### Stop Service

```bash
systemctl --user stop stt-clipboard
```

### Restart Service

```bash
systemctl --user restart stt-clipboard
```

### Check Status

```bash
systemctl --user status stt-clipboard
```

### Enable Auto-Start

```bash
systemctl --user enable stt-clipboard
```

### Disable Auto-Start

```bash
systemctl --user disable stt-clipboard
```

## Viewing Logs

### Real-time Logs

```bash
journalctl --user -u stt-clipboard -f
```

### Recent Logs

```bash
journalctl --user -u stt-clipboard -n 50
```

### File Logs

```bash
tail -f logs/stt-clipboard.log
```

### Debug Logs

Edit `config/config.yaml`:

```yaml
logging:
  level: DEBUG
```

Then restart:

```bash
systemctl --user restart stt-clipboard
```

## Service File

The service file is located at:

```
~/.config/systemd/user/stt-clipboard.service
```

Contents:

```ini
[Unit]
Description=STT Clipboard - Offline Speech-to-Text
After=graphical-session.target

[Service]
Type=simple
WorkingDirectory=/path/to/stt-clipboard
ExecStart=/path/to/uv run python -m src.main --daemon
Restart=on-failure
RestartSec=5

[Install]
WantedBy=default.target
```

## Troubleshooting

### Service won't start

```bash
# Check logs
journalctl --user -u stt-clipboard -n 50

# Common issues:
# 1. Dependencies not installed
./scripts/install_deps.sh

# 2. Permission issues
chmod +x scripts/*.sh

# 3. Wrong working directory
# Check ExecStart path in service file
```

### Socket not found

```bash
# Check if service is running
systemctl --user status stt-clipboard

# Check socket file
ls -la /tmp/stt-clipboard.sock
```

### Hotkey doesn't trigger

```bash
# Test trigger manually
./scripts/trigger.sh

# Check socket permissions
ls -la /tmp/stt-clipboard.sock
# Should show: srw------- (0600)
```
