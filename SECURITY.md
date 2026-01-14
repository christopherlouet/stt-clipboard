# Security Policy

## Security Features

STT Clipboard takes security seriously. This document describes the security measures in place.

### Built-in Security Measures

1. **Offline-First Architecture**
   - All processing happens locally
   - No network connectivity required
   - No data sent to external servers
   - No telemetry or analytics

2. **Privacy Protection**
   - Audio is processed in-memory only
   - No audio files are saved to disk
   - Logs contain only metadata (duration, performance metrics)
   - No personally identifiable information (PII) is logged

3. **Automated Security Scanning**
   - **Bandit**: Scans Python code for common security issues
   - **Safety**: Checks dependencies for known vulnerabilities (CVEs)
   - **detect-secrets**: Prevents secrets from being committed
   - **Gitleaks**: Scans git history for leaked credentials
   - All scans run automatically via pre-commit hooks

4. **Dependency Management**
   - Pinned dependencies with version locks
   - Regular dependency updates
   - Automated vulnerability scanning
   - Use of uv for fast, secure dependency resolution

5. **Code Quality**
   - Type checking with MyPy
   - Linting with Ruff (includes security rules)
   - Code formatting with Black
   - Automated testing with pytest

## Security Best Practices for Users

### Installation

1. **Verify the source**
   ```bash
   # Clone from official repository only
   git clone https://github.com/christopherlouet/stt-clipboard.git
   ```

2. **Review the code**
   - All code is open source and can be inspected
   - Check the LICENSE file (GPL-3.0)
   - Review CHANGELOG for recent changes

3. **Use system package manager**
   - Install system dependencies via apt (Ubuntu/Debian)
   - Avoid downloading pre-built binaries from untrusted sources

### Running the Service

1. **User-level service**
   - Service runs as your user, not root
   - Uses systemd user session
   - No elevated privileges required

2. **Socket permissions**
   - Unix socket has restrictive permissions (0600)
   - Only accessible by the user who created it
   - Socket path: `/tmp/stt-clipboard.sock`

3. **Resource limits**
   - Service has memory limits (2GB max)
   - CPU quota to prevent resource exhaustion

### Data Privacy

1. **Audio handling**
   - Audio is captured and processed in RAM
   - No audio files written to disk
   - Audio buffer is cleared after processing

2. **Transcription results**
   - Text is copied to clipboard only
   - No transcription history is saved
   - Clipboard can be cleared manually

3. **Logs**
   - Logs in `logs/stt-clipboard.log`
   - Contains only performance metrics
   - No sensitive data logged
   - Logs rotate automatically (10MB limit)

## Reporting Security Vulnerabilities

If you discover a security vulnerability, please report it responsibly:

1. **Do NOT** open a public GitHub issue
2. Email: [your-email@example.com] (replace with your email)
3. Include:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

We will respond within 48 hours and work on a fix promptly.

## Security Scanning Schedule

### Automated (Pre-commit)
- **Code vulnerabilities**: Every commit (Bandit)
- **Secret detection**: Every commit (detect-secrets, Gitleaks)
- **Dependency check**: Every commit (Safety)

### Scan Results

Current scan results:
- ✅ **Bandit**: No issues identified (7 documented exceptions)
- ⚠️ **Safety**: 3 PyTorch vulnerabilities (low risk - see [Dependency Vulnerabilities](docs/DEPENDENCY_VULNERABILITIES.md))
- ✅ **detect-secrets**: No secrets found
- ✅ **Gitleaks**: No leaks detected

For detailed security scan results and justifications, see:
- [Security Scan Results](docs/SECURITY_SCAN_RESULTS.md)
- [Dependency Vulnerabilities](docs/DEPENDENCY_VULNERABILITIES.md)

### Manual (Recommended)
- **Full security audit**: Monthly
  ```bash
  make security
  ```

- **Dependency updates**: Weekly
  ```bash
  make update
  uv run safety check
  ```

## Known Security Considerations

1. **Clipboard Access**
   - Application has access to system clipboard
   - Uses `wl-clipboard` (Wayland) for clipboard operations
   - Clipboard data can be accessed by other applications

2. **Microphone Access**
   - Application requires microphone access
   - Uses `sounddevice` library
   - Audio is processed locally, not transmitted

3. **Model Files**
   - Whisper models downloaded from Hugging Face
   - Stored in `./models/` directory
   - Verify checksums if concerned about model integrity

4. **Unix Socket**
   - Trigger uses Unix socket for IPC
   - Limited to user's session
   - Socket file deleted on service stop

## Security Updates

- Check for updates regularly: `git pull`
- Review CHANGELOG.md for security-related updates
- Subscribe to repository releases for notifications

## Compliance

- **GDPR**: No personal data collected or transmitted
- **License**: GPL-3.0 (open source, auditable)
- **Dependencies**: All dependencies are open source

## Additional Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Python Security Best Practices](https://python.readthedocs.io/en/latest/library/security_warnings.html)
- [Bandit Documentation](https://bandit.readthedocs.io/)
- [detect-secrets Documentation](https://github.com/Yelp/detect-secrets)
