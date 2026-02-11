# Plan d'implementation : Optimisation Memoire & Securisation

## Resume

Implementer le dechargement automatique du modele Whisper en inactivite (economie 200-800 MB), securiser le canal de commande Unix socket (validation + rate limiting), masquer les transcriptions dans les logs, et renforcer la qualite du code (mypy strict, TUI tests).

## Contexte Technique

| Aspect | Choix |
|--------|-------|
| Langage | Python 3.10+ |
| Framework TUI | Textual >= 3.0.0 |
| STT Engine | faster-whisper 1.1.0 (CTranslate2) |
| Tests | pytest 8.3.4 + pytest-asyncio |
| Linting | ruff, black, mypy 1.13.0 |
| Nouvelle dep | psutil (monitoring memoire RSS) |

## Architecture

```
                    ┌──────────────────────┐
                    │   config.py          │
                    │  + MemoryConfig      │
                    └──────────┬───────────┘
                               │
          ┌────────────────────┼────────────────────┐
          │                    │                    │
          ▼                    ▼                    ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│ transcription.py │  │   hotkey.py     │  │   main.py       │
│ + gc.collect()   │  │ + validation    │  │ + log masking   │
│ (decharge modele)│  │ + RateLimiter   │  │ + idle timer    │
└────────┬────────┘  └─────────────────┘  └────────┬────────┘
         │                                          │
         ▼                                          ▼
┌─────────────────┐                       ┌─────────────────┐
│    tui.py       │◄──────────────────────│  history.py     │
│ + idle timer    │                       │ + truncation    │
│ + MemoryPanel   │                       └─────────────────┘
│ + max_lines log │
└────────┬────────┘
         │
         ▼
┌─────────────────────────┐
│ tui_widgets/             │
│ + memory_panel.py (new) │
└─────────────────────────┘
```

## Fichiers Impactes

### A creer

| Fichier | Responsabilite | US |
|---------|----------------|----|
| `src/tui_widgets/memory_panel.py` | Widget Textual affichant la memoire RSS via psutil | US6 |
| `tests/test_memory_management.py` | Tests dechargement modele, gc.collect, idle timer | US1 |
| `tests/test_rate_limiter.py` | Tests rate limiter (5 req/10s) | US2 |

### A modifier

| Fichier | Modification | US |
|---------|-------------|----|
| `src/config.py` | Ajouter `MemoryConfig` dataclass (auto_unload, idle_timeout, max_tui_log_lines, max_history_text_length) | US1,4,5 |
| `src/transcription.py` | Ajouter `gc.collect()` + `ctranslate2` cleanup dans `unload_model()`, ajouter `is_loaded` property | US1 |
| `src/hotkey.py` | Ajouter whitelist `VALID_TRIGGERS`, validation stricte, `RateLimiter` class | US2 |
| `src/main.py` | Remplacer 4 `logger.info(text)` par version masquee (longueur + langue), ajouter gestion idle timer | US1,3 |
| `src/tui.py` | Idle timer integration, MemoryPanel dans compose(), max_lines sur TranscriptionLog | US1,4,6 |
| `src/history.py` | Troncature texte dans `add()` si > max_text_length | US5 |
| `src/tui_widgets/__init__.py` | Exporter `MemoryPanel` | US6 |
| `config/config.yaml` | Ajouter section `memory:` | US1,4,5 |
| `pyproject.toml` | Ajouter psutil, dedup dev deps, activer mypy strict | US6,7 |
| `tests/test_hotkey.py` | Ajouter tests validation + rate limiting | US2 |
| `tests/test_history.py` | Ajouter tests troncature | US5 |
| `tests/test_config.py` | Ajouter tests MemoryConfig | US1 |
| `tests/test_main.py` | Ajouter tests log masking | US3 |
| `tests/test_tui.py` | Corriger erreurs de collection (18 erreurs) | US8 |
| `tests/test_tui_settings.py` | Corriger erreurs de collection | US8 |
| `tests/test_tui_widgets.py` | Corriger erreurs de collection | US8 |
| `src/*.py` (multiples) | Corriger erreurs mypy strict | US7 |

## Points de conception cles

### Idle Timer (US1)

Le timer d'inactivite est gere par `STTService` dans `main.py`. Le modele `WhisperTranscriber` possede deja `unload_model()` et `transcribe()` recharge automatiquement le modele si `self.model is None` (ligne 76-78 de transcription.py).

```python
# Pseudo-code du timer
class STTService:
    def _reset_idle_timer(self):
        if self._idle_task:
            self._idle_task.cancel()
        if self.config.memory.auto_unload_model:
            self._idle_task = asyncio.get_event_loop().call_later(
                self.config.memory.idle_timeout_seconds,
                self._on_idle_timeout
            )

    def _on_idle_timeout(self):
        self.transcriber.unload_model()  # gc.collect() inclus
```

**Comportement par defaut**: active en TUI (5 min), desactive en daemon.

### RateLimiter (US2)

Classe simple basee sur une fenetre glissante de timestamps :

```python
class RateLimiter:
    MAX_REQUESTS = 5
    WINDOW_SECONDS = 10.0

    def __init__(self):
        self._timestamps: deque[float] = deque()

    def is_allowed(self) -> bool:
        now = time.monotonic()
        # Purger les timestamps hors fenetre
        while self._timestamps and now - self._timestamps[0] > self.WINDOW_SECONDS:
            self._timestamps.popleft()
        if len(self._timestamps) >= self.MAX_REQUESTS:
            return False
        self._timestamps.append(now)
        return True
```

### Log Masking (US3)

Remplacer les 4 occurrences de log INFO contenant le texte par :

```python
# Avant
logger.info(f"Transcription: '{text}'")
# Apres
logger.info(f"Transcription: {len(text)} chars, lang={language}")
logger.debug(f"Transcription content: '{text}'")
```

### MemoryPanel (US6)

Widget Textual avec `set_interval(5)` pour rafraichir l'affichage RSS :

```python
class MemoryPanel(Static):
    def on_mount(self):
        self.set_interval(5, self._refresh_memory)

    def _refresh_memory(self):
        try:
            process = psutil.Process()
            rss_mb = process.memory_info().rss / (1024 * 1024)
            self.update(f"RAM: {rss_mb:.1f} MB")
        except Exception:
            self.update("RAM: N/A")
```

## Risques et Mitigations

| Risque | Impact | Mitigation |
|--------|--------|------------|
| `gc.collect()` ne libere pas la memoire RSS | CS-001 echoue | Tester avec `del self.model` explicite + `torch.cuda.empty_cache()` en fallback |
| Race condition dictee vs dechargement | Crash ou perte de dictee | Lock mutex, annulation du timer si transcription en cours |
| mypy strict genere trop d'erreurs | Blocage du sprint | Commencer par lister les erreurs (`mypy --strict src/`), corriger par fichier |
| Textual RichLog.clear() n'existe pas | US4 bloquee | Verifier API Textual, alternative: remplacer le widget |
| psutil non disponible sur certains OS | Widget MemoryPanel crash | try/except avec fallback "N/A" |
| Tests TUI collection errors complexes | US8 bloquee | Diagnostiquer d'abord avec `pytest tests/test_tui.py --co` |

## Criteres de Validation

- [ ] CS-001: Memoire RSS diminue >= 150 MB apres dechargement
- [ ] CS-002: Rechargement modele < 5 secondes
- [ ] CS-003: 100% des commandes invalides rejetees
- [ ] CS-004: Aucun texte transcrit dans les logs INFO
- [ ] CS-005: Journal TUI stable apres 1000+ entrees
- [ ] CS-006: Tous les tests existants passent (pas de regression)
- [ ] CS-007: Defaut = active TUI / desactive daemon
- [ ] CS-008: Indicateur memoire affiche RSS a 0.1 MB pres
- [ ] CS-009: `uv run mypy src/` passe sans erreur en mode strict
- [ ] Couverture >= 80% sur le nouveau code
