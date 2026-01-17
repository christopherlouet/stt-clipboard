# Découpage en tâches : Améliorations STT Clipboard v2

## Légende

| Marqueur | Signification |
|----------|---------------|
| `[P]` | Parallélisable (pas de dépendance) |
| `[S1]` | Sprint 1 |
| `[S2]` | Sprint 2 |
| `[S3]` | Sprint 3 |
| `[S4]` | Sprint 4 |
| `[S5]` | Sprint 5 |
| `[S6]` | Sprint 6 |
| `→` | Dépend de la tâche précédente |
| `TDD` | Approche Test-Driven Development |

---

## Sprint 1 : Fondation (Tests, Sécurité, Documentation)

### Branche : `feature/improve-test-coverage`

```
T001 ──▶ T002 ──▶ T003 ──▶ T004
```

- [ ] **T001** [P] [S1] `tests/test_transcription.py`
  - Ajouter tests pour bloc `if __name__ == "__main__"`
  - Couvrir `transcribe_with_timestamps` edge cases
  - Agent: `/dev-test`

- [ ] **T002** [P] [S1] `tests/test_audio_capture.py`
  - Tests pour `_audio_callback` avec status erreur
  - Tests timeout et edge cases `record_until_silence`
  - Agent: `/dev-test`

- [ ] **T003** [P] [S1] `tests/test_hotkey.py`
  - Tests serveur avec connexions simultanées
  - Tests client avec différents trigger types
  - Agent: `/dev-test`

- [ ] **T004** [S1] Vérification couverture globale
  - Exécuter `uv run pytest --cov=src --cov-report=html`
  - Objectif: >= 90% couverture
  - Documenter zones non couvertes justifiées
  - Agent: `/qa-coverage`

### Branche : `feature/property-based-testing`

```
T005 ──▶ T006 ──▶ T007
              └──▶ T008
```

- [ ] **T005** [P] [S1] `pyproject.toml`
  - Ajouter `hypothesis>=6.0` aux dev dependencies
  - Configurer hypothesis dans pytest settings
  - Agent: `/ops-deps`

- [ ] **T006** [S1] `tests/conftest.py` (dépend T005)
  - Créer fixtures hypothesis pour audio data
  - Créer strategies pour textes multilingues
  - Agent: `/dev-test`

- [ ] **T007** [P] [S1] `tests/property_tests/test_punctuation.py` (dépend T006)
  - Propriété: capitalisation préservée après processing
  - Propriété: pas de double espaces
  - Propriété: ponctuation finale préservée
  - Agent: `/dev-tdd`

- [ ] **T008** [P] [S1] `tests/property_tests/test_audio.py` (dépend T006)
  - Propriété: normalisation dans [-1, 1]
  - Propriété: conversion int16→float32 réversible
  - Agent: `/dev-tdd`

### Branche : `feature/security-improvements`

```
T009 ──┬──▶ T012
T010 ──┤
T011 ──┘
```

- [ ] **T009** [P] [S1] `src/hotkey.py`
  - Documenter le choix 0600 pour permissions socket
  - Expliquer les risques de permissions plus permissives
  - Agent: `/doc-explain`

- [ ] **T010** [P] [S1] `.github/workflows/security.yml`
  - Workflow hebdomadaire audit dépendances
  - Utiliser safety et pip-audit
  - Alerter si vulnérabilités trouvées
  - Agent: `/ops-ci`

- [ ] **T011** [P] [S1] `pyproject.toml`
  - Ajouter `pip-audit>=2.0` aux dev deps
  - Ajouter `safety>=3.0` si pas déjà présent
  - Agent: `/ops-deps`

- [ ] **T012** [S1] `Makefile` (dépend T010, T011)
  - Cible `make security-audit`
  - Exécute pip-audit et safety
  - Agent: `/ops-ci`

### Branche : `feature/documentation-improvements`

```
T013 ──┬──▶ T017
T014 ──┤
T015 ──┤
T016 ──┘
```

- [ ] **T013** [P] [S1] `src/audio_capture.py`
  - Docstring détaillée `_detect_speech()`
  - Docstring détaillée `_audio_callback()`
  - Expliquer le flow de données
  - Agent: `/doc-explain`

- [ ] **T014** [P] [S1] `src/transcription.py`
  - Docstrings méthodes internes
  - Documenter format audio attendu
  - Agent: `/doc-explain`

- [ ] **T015** [P] [S1] `docs/examples/custom_trigger.py`
  - Exemple script Python trigger personnalisé
  - Avec gestion d'erreurs
  - Agent: `/doc-generate`

- [ ] **T016** [P] [S1] `docs/examples/batch_transcription.py`
  - Exemple transcription de fichiers WAV en batch
  - Avec progress bar
  - Agent: `/doc-generate`

- [ ] **T017** [S1] `docs/examples/integration_obs.md`
  - Guide intégration avec OBS Studio
  - Utilisation pour live streaming
  - Agent: `/doc-generate`

---

## Sprint 2 : Performance (Optimisations)

### Branche : `feature/vad-cache`

```
T018 ──▶ T019 ──▶ T020 ──▶ T021
```

- [ ] **T018** [S2] `src/cache.py` TDD
  - Créer d'abord `tests/test_cache.py` avec tests
  - Implémenter `AudioChunkCache` avec LRU
  - Méthode `get_or_compute(chunk, compute_fn)`
  - Statistiques hit/miss rate
  - Agent: `/dev-tdd`

- [ ] **T019** [S2] `tests/test_cache.py` (avec T018)
  - Tests LRU eviction
  - Tests thread-safety
  - Tests performance
  - Agent: `/dev-tdd`

- [ ] **T020** [S2] `src/audio_capture.py` (dépend T018)
  - Intégrer cache dans `_detect_speech`
  - Hash du chunk audio comme clé
  - Agent: `/dev-refactor`

- [ ] **T021** [S2] `src/config.py` (dépend T020)
  - Ajouter `VADConfig.cache_enabled: bool = False`
  - Ajouter `VADConfig.cache_size: int = 100`
  - Agent: `/dev-refactor`

### Branche : `feature/model-warmup`

```
T022 ──▶ T023 ──▶ T024 ──▶ T025
```

- [ ] **T022** [S2] `src/warmup.py` TDD
  - Créer d'abord tests
  - Fonction `warmup_transcriber(transcriber)`
  - Génère audio silencieux, transcrit
  - Mesure temps de warmup
  - Agent: `/dev-tdd`

- [ ] **T023** [S2] `tests/test_warmup.py` (avec T022)
  - Test warmup réussit sans erreur
  - Test warmup améliore temps 1ère transcription
  - Agent: `/dev-tdd`

- [ ] **T024** [S2] `src/main.py` (dépend T022)
  - Appeler warmup dans `STTService.initialize()`
  - Logger temps de warmup
  - Agent: `/dev-refactor`

- [ ] **T025** [S2] `src/config.py` (dépend T024)
  - Ajouter `TranscriptionConfig.warmup_enabled: bool = True`
  - Agent: `/dev-refactor`

### Branche : `feature/streaming-transcription`

```
T026 ──▶ T027 ──▶ T028 ──▶ T029
```

- [ ] **T026** [S2] `src/transcription.py` TDD
  - Rechercher API streaming faster-whisper
  - Implémenter `transcribe_stream()` si supporté
  - Sinon: chunked transcription avec overlap
  - Agent: `/dev-tdd`

- [ ] **T027** [S2] `tests/test_transcription.py` (dépend T026)
  - Tests streaming avec différentes durées
  - Tests qualité vs mode classique
  - Agent: `/dev-test`

- [ ] **T028** [S2] `src/main.py` (dépend T026)
  - Option streaming dans `process_request`
  - Fallback mode classique si échec
  - Agent: `/dev-refactor`

- [ ] **T029** [S2] `src/config.py` (dépend T028)
  - Ajouter `TranscriptionConfig.streaming_enabled: bool = False`
  - Agent: `/dev-refactor`

---

## Sprint 3 : Robustesse (Fiabilité)

### Branche : `feature/clipboard-retry-backoff`

```
T030 ──▶ T031 ──▶ T032
```

- [ ] **T030** [S3] `src/clipboard.py` TDD
  - Implémenter backoff exponentiel dans `copy_with_retry`
  - Base 0.1s, max 2s, jitter aléatoire
  - Agent: `/dev-tdd`

- [ ] **T031** [S3] `tests/test_clipboard.py` (avec T030)
  - Tests backoff avec mocks
  - Vérifier délais exponentiels
  - Agent: `/dev-test`

- [ ] **T032** [S3] `src/config.py` (dépend T030)
  - Ajouter `ClipboardConfig.max_retries: int = 3`
  - Ajouter `ClipboardConfig.backoff_base: float = 0.1`
  - Agent: `/dev-refactor`

### Branche : `feature/no-speech-notification`

```
T033 ──▶ T034 ──▶ T035 ──▶ T036
```

- [ ] **T033** [S3] `src/notifications.py` TDD
  - Créer tests d'abord
  - Fonction `notify_no_speech_detected()`
  - Message: "Aucune parole détectée"
  - Agent: `/dev-tdd`

- [ ] **T034** [S3] `tests/test_notifications.py` (avec T033)
  - Test notification envoyée
  - Test fallback si notify-send absent
  - Agent: `/dev-test`

- [ ] **T035** [S3] `src/audio_capture.py` (dépend T033)
  - Appeler notification après timeout 5s sans parole
  - Ne pas bloquer le recording
  - Agent: `/dev-refactor`

- [ ] **T036** [S3] `src/main.py` (dépend T035)
  - Gérer retour None de record proprement
  - Logger l'événement
  - Agent: `/dev-refactor`

### Branche : `feature/startup-validation`

```
T037 ──▶ T038 ──▶ T039
T040 ──┘
T041 ──┘
```

- [ ] **T037** [S3] `src/config.py` TDD
  - Méthode `validate_system_tools()`
  - Vérifie wl-copy/xclip/pbcopy présent
  - Vérifie xdotool/ydotool/osascript si paste enabled
  - Agent: `/dev-tdd`

- [ ] **T038** [S3] `tests/test_config.py` (avec T037)
  - Tests validation avec mocks shutil.which
  - Tests erreurs claires si tool manquant
  - Agent: `/dev-test`

- [ ] **T039** [S3] `src/main.py` (dépend T037)
  - Appeler `config.validate_system_tools()` au démarrage
  - Exit propre avec message si tool manquant
  - Agent: `/dev-refactor`

- [ ] **T040** [P] [S3] `src/clipboard.py`
  - Helper `check_clipboard_tool() -> str | None`
  - Retourne nom du tool disponible ou None
  - Agent: `/dev-refactor`

- [ ] **T041** [P] [S3] `src/autopaste.py`
  - Helper `check_paste_tool() -> str | None`
  - Agent: `/dev-refactor`

---

## Sprint 4 : Fonctionnalités I (Langues & Historique)

### Branche : `feature/multi-language-support`

```
T042 ──▶ T043 ──▶ T044 ──▶ T045 ──▶ T046 ──▶ T047
```

- [ ] **T042** [S4] `src/languages.py` TDD
  - Enum `SupportedLanguage`: FR, EN, DE, ES, IT
  - Dataclass `LanguageRules` avec règles ponctuation
  - Registre des règles par langue
  - Agent: `/dev-tdd`

- [ ] **T043** [S4] `tests/test_languages.py` (avec T042)
  - Tests enum values
  - Tests règles par langue
  - Agent: `/dev-test`

- [ ] **T044** [S4] `src/punctuation.py` (dépend T042)
  - Intégrer `LanguageRules` dans processing
  - Règles DE: pas d'espace avant ponctuation
  - Règles ES: ¿ ¡ en début de phrase
  - Règles IT: similaire à FR pour certains cas
  - Agent: `/dev-refactor`

- [ ] **T045** [S4] `tests/test_punctuation.py` (dépend T044)
  - Tests ponctuation allemande
  - Tests ponctuation espagnole (¿¡)
  - Tests ponctuation italienne
  - Agent: `/dev-test`

- [ ] **T046** [S4] `src/config.py` (dépend T044)
  - Valider langue dans liste supportée
  - Message erreur clair si langue non supportée
  - Agent: `/dev-refactor`

- [ ] **T047** [S4] `docs/LANGUAGES.md`
  - Documentation langues supportées
  - Exemples par langue
  - Guide contribution nouvelle langue
  - Agent: `/doc-generate`

### Branche : `feature/transcription-history`

```
T048 ──▶ T049 ──▶ T050 ──▶ T051 ──▶ T052 ──▶ T053
```

- [ ] **T048** [S4] `src/history.py` TDD
  - Classe `TranscriptionHistory`
  - Méthodes: `add()`, `get_previous()`, `get_next()`, `get_all()`
  - Limite configurable (default 50)
  - Thread-safe avec Lock
  - Agent: `/dev-tdd`

- [ ] **T049** [S4] `tests/test_history.py` (avec T048)
  - Tests ajout et navigation
  - Tests limite max
  - Tests thread-safety
  - Agent: `/dev-test`

- [ ] **T050** [S4] `src/main.py` (dépend T048)
  - Ajouter `self.history = TranscriptionHistory()`
  - Appeler `history.add()` après transcription réussie
  - Agent: `/dev-refactor`

- [ ] **T051** [S4] `src/config.py` (dépend T050)
  - Ajouter dataclass `HistoryConfig`
  - Options: `enabled`, `max_items`, `persist_to_file`
  - Agent: `/dev-refactor`

- [ ] **T052** [S4] `src/hotkey.py` (dépend T050)
  - Nouveau TriggerType: `HISTORY_PREV`, `HISTORY_NEXT`
  - Handler pour copier entrée historique
  - Agent: `/dev-refactor`

- [ ] **T053** [S4] `scripts/trigger_history.sh`
  - Script pour récupérer entrée précédente
  - Script pour récupérer entrée suivante
  - Agent: `/doc-generate`

---

## Sprint 5 : Fonctionnalités II (Dictée continue)

### Branche : `feature/continuous-dictation`

```
T054 ──▶ T055 ──▶ T056 ──▶ T057 ──▶ T058 ──▶ T059 ──▶ T060 ──▶ T061
```

- [ ] **T054** [S5] `src/continuous.py` TDD
  - Classe `ContinuousDictation`
  - Gestion état: IDLE, RECORDING, PAUSED
  - Accumulation des transcriptions
  - Callback sur nouveau segment
  - Agent: `/dev-tdd`

- [ ] **T055** [S5] `tests/test_continuous.py` (avec T054)
  - Tests transitions d'état
  - Tests accumulation
  - Tests callbacks
  - Agent: `/dev-test`

- [ ] **T056** [S5] `src/audio_capture.py` (dépend T054)
  - Mode `record_continuous()` sans arrêt sur silence
  - Détection pause longue pour segmentation
  - Agent: `/dev-refactor`

- [ ] **T057** [S5] `src/main.py` (dépend T054, T056)
  - Méthode `run_continuous_mode()`
  - Gestion start/stop via triggers
  - Agent: `/dev-refactor`

- [ ] **T058** [S5] `src/config.py` (dépend T057)
  - Dataclass `ContinuousConfig`
  - Options: `enabled`, `segment_duration`, `pause_threshold`
  - Agent: `/dev-refactor`

- [ ] **T059** [S5] `src/hotkey.py` (dépend T057)
  - TriggerType: `START_CONTINUOUS`, `STOP_CONTINUOUS`, `PAUSE_CONTINUOUS`
  - Agent: `/dev-refactor`

- [ ] **T060** [S5] `scripts/trigger_continuous.sh`
  - Scripts start/stop/pause
  - Agent: `/doc-generate`

- [ ] **T061** [S5] `docs/CONTINUOUS_MODE.md`
  - Documentation mode continu
  - Cas d'usage
  - Limites et recommandations
  - Agent: `/doc-generate`

---

## Sprint 6 : UX Avancée (Interface TUI)

### Branche : `feature/tui-interface`

```
T062 ──▶ T063 ──▶ T064 ──▶ T065 ──▶ T066 ──▶ T067 ──▶ T068 ──▶ T069 ──▶ T070
```

- [ ] **T062** [S6] `pyproject.toml`
  - Ajouter `rich>=13.0`
  - Ajouter `textual>=0.50`
  - Agent: `/ops-deps`

- [ ] **T063** [S6] `src/tui.py` TDD
  - Classe `STTApp(textual.App)`
  - Layout de base avec header/footer
  - Agent: `/dev-tdd`, `/dev-component`

- [ ] **T064** [S6] `tests/test_tui.py` (avec T063)
  - Tests de base avec textual testing
  - Agent: `/dev-test`

- [ ] **T065** [S6] `src/tui.py` (dépend T063)
  - Panel "Statut" temps réel
  - Indicateur enregistrement
  - Dernière transcription
  - Agent: `/dev-component`

- [ ] **T066** [S6] `src/tui.py` (dépend T065)
  - Panel "Historique" scrollable
  - Sélection pour re-copier
  - Agent: `/dev-component`

- [ ] **T067** [S6] `src/tui.py` (dépend T066)
  - Panel "Configuration" éditable
  - Toggles pour options courantes
  - Agent: `/dev-component`

- [ ] **T068** [S6] `src/tui.py` (dépend T067)
  - Raccourcis clavier (q=quit, r=record, etc.)
  - Barre d'aide en footer
  - Agent: `/dev-component`

- [ ] **T069** [S6] `src/main.py` (dépend T068)
  - Argument `--tui` pour lancer interface
  - Intégration avec service existant
  - Agent: `/dev-refactor`

- [ ] **T070** [S6] `docs/TUI.md`
  - Documentation interface TUI
  - Screenshots
  - Raccourcis clavier
  - Agent: `/doc-generate`

---

## Résumé des dépendances

```
Sprint 1 (Fondation)
├── feature/improve-test-coverage (T001-T004) [P]
├── feature/property-based-testing (T005-T008)
├── feature/security-improvements (T009-T012) [P]
└── feature/documentation-improvements (T013-T017) [P]
         │
         ▼
Sprint 2 (Performance) - dépend Sprint 1
├── feature/vad-cache (T018-T021)
├── feature/model-warmup (T022-T025)
└── feature/streaming-transcription (T026-T029)
         │
         ▼
Sprint 3 (Robustesse) - dépend Sprint 1
├── feature/clipboard-retry-backoff (T030-T032)
├── feature/no-speech-notification (T033-T036)
└── feature/startup-validation (T037-T041)
         │
         ▼
Sprint 4 (Langues & Historique) - dépend Sprint 2, 3
├── feature/multi-language-support (T042-T047)
└── feature/transcription-history (T048-T053)
         │
         ▼
Sprint 5 (Dictée continue) - dépend Sprint 4
└── feature/continuous-dictation (T054-T061)
         │
         ▼
Sprint 6 (TUI) - dépend Sprint 5
└── feature/tui-interface (T062-T070)
```

---

## Commandes de suivi

```bash
# Voir tâches en cours
grep -E "^\- \[ \]" specs/improvements-v2/tasks.md | head -20

# Compter tâches restantes
grep -c "^\- \[ \]" specs/improvements-v2/tasks.md

# Compter tâches terminées
grep -c "^\- \[x\]" specs/improvements-v2/tasks.md

# Voir tâches d'un sprint
grep "\[S1\]" specs/improvements-v2/tasks.md
```
