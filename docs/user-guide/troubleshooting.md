# Troubleshooting

## Common Issues

### Service Won't Start

```bash
# Check status and logs
systemctl --user status stt-clipboard
journalctl --user -u stt-clipboard -n 50
```

**Common causes:**

1. **Dependencies not installed**: Run `./scripts/install_deps.sh`
2. **uv not found**: Script will auto-install it
3. **Permission issues**: Run `chmod +x scripts/*.sh`

### Hotkey Doesn't Work

```bash
# Test trigger manually
./scripts/trigger.sh
```

**"Socket not found" error:**

```bash
# Start the service
systemctl --user start stt-clipboard
```

**"Failed to send trigger" error:**

```bash
# Check logs
journalctl --user -u stt-clipboard -f
```

### No Microphone Input

```bash
# List available devices
uv run python -c "import sounddevice as sd; print(sd.query_devices())"

# Test recording
uv run python -m src.audio_capture
```

**If no devices found:**

- Check microphone connection
- Verify microphone permissions
- On Linux, check PulseAudio/PipeWire settings

### Transcription Is Slow

1. **Check CPU usage:**
   ```bash
   htop
   ```

2. **Close resource-intensive apps**

3. **Try a smaller model:**
   ```yaml
   # config/config.yaml
   transcription:
     model_size: tiny  # Instead of base
   ```

### Poor Transcription Accuracy

1. **Improve audio quality:**
    - Use in quiet environment
    - Position microphone closer
    - Speak clearly

2. **Try a larger model:**
   ```yaml
   transcription:
     model_size: base  # or small
   ```

3. **Adjust VAD threshold:**
   ```yaml
   vad:
     threshold: 0.6  # Increase to filter noise
   ```

### Clipboard Not Working

```bash
# Check session type
echo $XDG_SESSION_TYPE
```

**For Wayland:**

```bash
# Test wl-clipboard
echo "test" | wl-copy && wl-paste
```

**For X11:**

```bash
# Test xclip
echo "test" | xclip -selection clipboard
xclip -selection clipboard -o
```

### Auto-Paste Not Working

**Linux (X11):**

```bash
# Test xdotool
xdotool key ctrl+v
```

**Linux (Wayland):**

```bash
# Check ydotool daemon
systemctl status ydotool

# Start if not running
sudo systemctl start ydotool
```

**macOS:**

1. Check Accessibility permissions:
   **System Settings → Privacy & Security → Accessibility**

2. Test osascript:
   ```bash
   osascript -e 'tell application "System Events" to keystroke "v" using command down'
   ```

## Debug Mode

Enable verbose logging:

```bash
uv run python -m src.main --daemon --log-level DEBUG
```

Or in config:

```yaml
logging:
  level: DEBUG
```

## Getting Help

1. Check the [GitHub Issues](https://github.com/christopherlouet/stt-clipboard/issues)
2. Search existing issues for similar problems
3. Open a new issue with:
    - Your OS and version
    - Error messages from logs
    - Steps to reproduce
