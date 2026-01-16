# Security

STT Clipboard is designed with privacy and security as core principles.

## Privacy-First Design

### 100% Offline Processing

- **No network calls** after initial model download
- All transcription happens locally on your machine
- No data is sent to external servers
- No telemetry or analytics

### In-Memory Processing

- Audio is **never saved to disk**
- Processed entirely in RAM
- Cleared after transcription
- No temporary files created

### No Content Logging

- Audio content is **never logged**
- Transcribed text is **never logged**
- Only operational logs (errors, status)

## Security Measures

### Unix Socket Security

The trigger socket uses strict permissions:

```bash
# Socket permissions
ls -la /tmp/stt-clipboard.sock
# Output: srw------- (0600) - owner only
```

- Only the owner can read/write
- Prevents unauthorized triggering
- Created fresh on each service start

### Subprocess Security

All external commands use safe patterns:

```python
# Safe: argument list
subprocess.run(["wl-copy", text], ...)

# NEVER: shell=True (vulnerable to injection)
subprocess.run(f"wl-copy {text}", shell=True)  # DON'T DO THIS
```

### Input Validation

- All configuration values are validated
- Type checking with dataclasses
- Bounds checking on numeric values

## Best Practices

### Configuration

```yaml
# config/config.yaml

# Safe defaults
logging:
  level: INFO  # Not DEBUG in production
  # Never log transcribed content
```

### Environment

```bash
# Never store secrets in config files
# Use environment variables if needed
export STT_API_KEY=xxx  # If you add API features
```

### File Permissions

```bash
# Secure the config directory
chmod 700 config/
chmod 600 config/config.yaml

# Secure logs
chmod 700 logs/
```

## Security Scanning

### Automated Scans

```bash
# Run security checks
make security

# Or individually:
uv run bandit -c pyproject.toml -r src/
uv run detect-secrets scan --baseline .secrets.baseline
```

### Dependency Audit

```bash
# Check for vulnerable dependencies
uv run pip-audit
```

### Pre-commit Hooks

Security checks run automatically:

- Bandit (code security)
- detect-secrets (credential scanning)

## Threat Model

### Trusted

- Local user running the service
- Local audio input
- Local keyboard events

### Untrusted

- Network input (none by design)
- External APIs (none by design)
- Other users on the system

### Mitigations

| Threat | Mitigation |
|--------|------------|
| Unauthorized trigger | 0600 socket permissions |
| Data exfiltration | No network access |
| Audio recording | User-initiated only |
| Log leakage | No content logging |

## Reporting Vulnerabilities

If you discover a security vulnerability:

1. **Do NOT** open a public issue
2. Email the maintainer directly
3. Include:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact

## Security Checklist

### For Users

- [ ] Keep the system updated
- [ ] Secure config file permissions
- [ ] Review log files periodically
- [ ] Use strong system password

### For Developers

- [ ] Run `make security` before commits
- [ ] Never use `shell=True` in subprocess
- [ ] Never log sensitive data
- [ ] Validate all inputs
- [ ] Use type hints for safety
- [ ] Review dependencies for vulnerabilities

## Compliance

### GDPR Considerations

STT Clipboard is designed for privacy:

- No data collection
- No external processing
- User controls all data
- Easy to delete (just remove the app)

### Data Retention

- Audio: Never stored
- Transcriptions: Only in clipboard (user-controlled)
- Logs: Operational only, rotated automatically

## Known Limitations

### Clipboard Security

- Clipboard content is accessible to other applications
- Consider clearing clipboard after use
- Some clipboard managers may store history

### Microphone Access

- Requires microphone permission
- Recording only when triggered
- No background listening

### Display Server Access

- Requires access to display server for:
  - Clipboard operations
  - Auto-paste functionality
- Minimal permissions requested
