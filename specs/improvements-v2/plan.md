# Plan d'implémentation : Améliorations STT Clipboard v2

## Résumé

Ce plan couvre 16 améliorations regroupées en 6 sprints thématiques, allant des optimisations de performance à l'ajout de nouvelles fonctionnalités majeures comme le mode dictée continue et l'interface TUI.

## Contexte Technique

| Aspect | Choix |
|--------|-------|
| Langage | Python 3.10+ |
| Framework | asyncio, loguru |
| Tests | pytest, pytest-asyncio, hypothesis |
| Linting | ruff, mypy, black |
| CI/CD | GitHub Actions |
| Versioning | Conventional Commits, GitFlow |

## Organisation des Sprints

```
Sprint 1: Fondation         Sprint 2: Performance       Sprint 3: Robustesse
(Tests & Docs)              (Optimisations)             (Fiabilité)
     │                           │                           │
     ▼                           ▼                           ▼
┌─────────────┐           ┌─────────────┐           ┌─────────────┐
│ 5.1, 5.3    │           │ 1.1, 1.2    │           │ 2.1, 2.3    │
│ 6.1, 6.2    │           │ 1.3         │           │ 4.1         │
│ 7.1, 7.2    │           └─────────────┘           └─────────────┘
└─────────────┘
     │                           │                           │
     └───────────────────────────┴───────────────────────────┘
                                 │
                                 ▼
                    Sprint 4: Fonctionnalités I
                    (Langues & Historique)
                    ┌─────────────┐
                    │ 3.1, 3.3    │
                    └─────────────┘
                                 │
                                 ▼
                    Sprint 5: Fonctionnalités II
                    (Dictée continue)
                    ┌─────────────┐
                    │ 3.2         │
                    └─────────────┘
                                 │
                                 ▼
                    Sprint 6: UX Avancée
                    (Interface TUI)
                    ┌─────────────┐
                    │ 4.3         │
                    └─────────────┘
```

## Fichiers Impactés

### À créer

| Fichier | Responsabilité | Sprint |
|---------|----------------|--------|
| `src/cache.py` | Cache LRU pour VAD | 2 |
| `src/warmup.py` | Pre-warming des modèles | 2 |
| `src/history.py` | Historique transcriptions | 4 |
| `src/languages.py` | Support multi-langues | 4 |
| `src/tui.py` | Interface TUI avec rich | 6 |
| `src/continuous.py` | Mode dictée continue | 5 |
| `tests/test_cache.py` | Tests cache | 2 |
| `tests/test_warmup.py` | Tests warmup | 2 |
| `tests/test_history.py` | Tests historique | 4 |
| `tests/test_languages.py` | Tests langues | 4 |
| `tests/test_continuous.py` | Tests dictée continue | 5 |
| `tests/test_tui.py` | Tests TUI | 6 |
| `tests/property_tests/` | Tests property-based | 1 |
| `docs/examples/` | Exemples d'utilisation | 1 |
| `.github/workflows/security.yml` | Audit dépendances | 1 |

### À modifier

| Fichier | Modification | Sprint |
|---------|--------------|--------|
| `src/audio_capture.py` | Intégration cache, notifications | 2, 3 |
| `src/transcription.py` | Streaming, warmup, langues | 2, 4 |
| `src/clipboard.py` | Retry avec backoff | 3 |
| `src/config.py` | Validation tools, nouvelles options | 3, 4 |
| `src/main.py` | Warmup, historique, mode continu | 2, 4, 5 |
| `src/punctuation.py` | Règles multi-langues | 4 |
| `src/hotkey.py` | Commandes historique | 4 |
| `src/notifications.py` | Notification "pas de parole" | 3 |
| `pyproject.toml` | Dépendances (hypothesis, rich) | 1, 6 |
| `tests/conftest.py` | Fixtures hypothesis | 1 |

---

## Sprint 1 : Fondation (Tests, Sécurité, Documentation)

**Objectif** : Consolider la base avant d'ajouter des fonctionnalités

### Phase 1.1 : Amélioration couverture tests (5.1)

**Branche** : `feature/improve-test-coverage`

| Tâche | Fichier | Description |
|-------|---------|-------------|
| T001 | `tests/test_transcription.py` | Couvrir les sections `__main__` |
| T002 | `tests/test_audio_capture.py` | Tests callbacks d'erreur |
| T003 | `tests/test_hotkey.py` | Tests serveur/client |
| T004 | Tous | Atteindre 90% couverture globale |

### Phase 1.2 : Property-based testing (5.3)

**Branche** : `feature/property-based-testing`

| Tâche | Fichier | Description |
|-------|---------|-------------|
| T005 | `pyproject.toml` | Ajouter hypothesis |
| T006 | `tests/conftest.py` | Fixtures hypothesis |
| T007 | `tests/property_tests/test_punctuation.py` | Tests propriétés ponctuation |
| T008 | `tests/property_tests/test_audio.py` | Tests normalisation audio |

### Phase 1.3 : Sécurité (6.1, 6.2)

**Branche** : `feature/security-improvements`

| Tâche | Fichier | Description |
|-------|---------|-------------|
| T009 | `src/hotkey.py` | Documenter permissions socket 0600 |
| T010 | `.github/workflows/security.yml` | Workflow audit deps (safety, pip-audit) |
| T011 | `pyproject.toml` | Ajouter pip-audit aux dev deps |
| T012 | `Makefile` | Cible `make security-audit` |

### Phase 1.4 : Documentation (7.1, 7.2)

**Branche** : `feature/documentation-improvements`

| Tâche | Fichier | Description |
|-------|---------|-------------|
| T013 | `src/audio_capture.py` | Docstrings `_detect_speech`, `_audio_callback` |
| T014 | `src/transcription.py` | Docstrings méthodes internes |
| T015 | `docs/examples/custom_trigger.py` | Exemple script trigger personnalisé |
| T016 | `docs/examples/batch_transcription.py` | Exemple transcription batch |
| T017 | `docs/examples/integration_obs.md` | Intégration avec OBS Studio |

---

## Sprint 2 : Performance (Optimisations)

**Objectif** : Réduire la latence et améliorer les performances

### Phase 2.1 : Cache LRU pour VAD (1.1)

**Branche** : `feature/vad-cache`

| Tâche | Fichier | Description |
|-------|---------|-------------|
| T018 | `src/cache.py` | Classe `AudioChunkCache` avec LRU |
| T019 | `tests/test_cache.py` | Tests unitaires cache |
| T020 | `src/audio_capture.py` | Intégrer cache dans `_detect_speech` |
| T021 | `src/config.py` | Option `vad.cache_enabled` |

### Phase 2.2 : Pre-warming modèle (1.3)

**Branche** : `feature/model-warmup`

| Tâche | Fichier | Description |
|-------|---------|-------------|
| T022 | `src/warmup.py` | Fonction `warmup_transcriber()` |
| T023 | `tests/test_warmup.py` | Tests warmup |
| T024 | `src/main.py` | Appeler warmup dans `initialize()` |
| T025 | `src/config.py` | Option `transcription.warmup_enabled` |

### Phase 2.3 : Streaming transcription (1.2)

**Branche** : `feature/streaming-transcription`

| Tâche | Fichier | Description |
|-------|---------|-------------|
| T026 | `src/transcription.py` | Méthode `transcribe_stream()` |
| T027 | `tests/test_transcription.py` | Tests streaming |
| T028 | `src/main.py` | Option streaming dans `process_request` |
| T029 | `src/config.py` | Option `transcription.streaming_enabled` |

---

## Sprint 3 : Robustesse (Fiabilité)

**Objectif** : Améliorer la gestion des erreurs et le feedback utilisateur

### Phase 3.1 : Retry avec backoff (2.1)

**Branche** : `feature/clipboard-retry-backoff`

| Tâche | Fichier | Description |
|-------|---------|-------------|
| T030 | `src/clipboard.py` | Implémenter backoff exponentiel |
| T031 | `tests/test_clipboard.py` | Tests backoff |
| T032 | `src/config.py` | Options `clipboard.max_retries`, `clipboard.backoff_base` |

### Phase 3.2 : Notification "pas de parole" (2.3)

**Branche** : `feature/no-speech-notification`

| Tâche | Fichier | Description |
|-------|---------|-------------|
| T033 | `src/notifications.py` | Fonction `notify_no_speech_detected()` |
| T034 | `tests/test_notifications.py` | Tests nouvelle notification |
| T035 | `src/audio_capture.py` | Appeler notification sur timeout |
| T036 | `src/main.py` | Gérer le cas "pas de parole" |

### Phase 3.3 : Validation tools au démarrage (4.1)

**Branche** : `feature/startup-validation`

| Tâche | Fichier | Description |
|-------|---------|-------------|
| T037 | `src/config.py` | Méthode `validate_system_tools()` |
| T038 | `tests/test_config.py` | Tests validation tools |
| T039 | `src/main.py` | Appeler validation au démarrage |
| T040 | `src/clipboard.py` | Helper `check_clipboard_tool()` |
| T041 | `src/autopaste.py` | Helper `check_paste_tool()` |

---

## Sprint 4 : Fonctionnalités I (Langues & Historique)

**Objectif** : Ajouter le support multi-langues et l'historique

### Phase 4.1 : Support langues supplémentaires (3.1)

**Branche** : `feature/multi-language-support`

| Tâche | Fichier | Description |
|-------|---------|-------------|
| T042 | `src/languages.py` | Enum `SupportedLanguage`, règles par langue |
| T043 | `tests/test_languages.py` | Tests langues |
| T044 | `src/punctuation.py` | Règles DE, ES, IT |
| T045 | `tests/test_punctuation.py` | Tests ponctuation nouvelles langues |
| T046 | `src/config.py` | Validation nouvelles langues |
| T047 | `docs/LANGUAGES.md` | Documentation langues supportées |

### Phase 4.2 : Historique transcriptions (3.3)

**Branche** : `feature/transcription-history`

| Tâche | Fichier | Description |
|-------|---------|-------------|
| T048 | `src/history.py` | Classe `TranscriptionHistory` |
| T049 | `tests/test_history.py` | Tests historique |
| T050 | `src/main.py` | Intégrer historique dans STTService |
| T051 | `src/config.py` | Options `history.enabled`, `history.max_items` |
| T052 | `src/hotkey.py` | Commande `HISTORY_PREV`, `HISTORY_NEXT` |
| T053 | `scripts/trigger_history.sh` | Script récupérer historique |

---

## Sprint 5 : Fonctionnalités II (Dictée continue)

**Objectif** : Implémenter le mode dictée continue

### Phase 5.1 : Mode dictée continue (3.2)

**Branche** : `feature/continuous-dictation`

| Tâche | Fichier | Description |
|-------|---------|-------------|
| T054 | `src/continuous.py` | Classe `ContinuousDictation` |
| T055 | `tests/test_continuous.py` | Tests dictée continue |
| T056 | `src/audio_capture.py` | Mode enregistrement continu |
| T057 | `src/main.py` | Intégrer mode continu |
| T058 | `src/config.py` | Options `continuous.enabled`, `continuous.segment_duration` |
| T059 | `src/hotkey.py` | Commandes `START_CONTINUOUS`, `STOP_CONTINUOUS` |
| T060 | `scripts/trigger_continuous.sh` | Scripts start/stop continu |
| T061 | `docs/CONTINUOUS_MODE.md` | Documentation mode continu |

---

## Sprint 6 : UX Avancée (Interface TUI)

**Objectif** : Créer une interface terminal interactive

### Phase 6.1 : Interface TUI (4.3)

**Branche** : `feature/tui-interface`

| Tâche | Fichier | Description |
|-------|---------|-------------|
| T062 | `pyproject.toml` | Ajouter rich, textual |
| T063 | `src/tui.py` | Interface TUI avec rich/textual |
| T064 | `tests/test_tui.py` | Tests TUI |
| T065 | `src/tui.py` | Panel statut temps réel |
| T066 | `src/tui.py` | Panel historique |
| T067 | `src/tui.py` | Panel configuration |
| T068 | `src/tui.py` | Raccourcis clavier |
| T069 | `src/main.py` | Mode `--tui` |
| T070 | `docs/TUI.md` | Documentation interface TUI |

---

## Risques et Mitigations

| Risque | Impact | Probabilité | Mitigation |
|--------|--------|-------------|------------|
| Streaming transcription incompatible faster-whisper | Haut | Moyenne | Vérifier API, fallback mode classique |
| Mode continu consomme trop de RAM | Moyen | Moyenne | Limiter buffer, segments courts |
| TUI complexe à maintenir | Moyen | Faible | Utiliser textual (framework mature) |
| Règles ponctuation incorrectes nouvelles langues | Moyen | Moyenne | Valider avec locuteurs natifs |
| Cache VAD peu efficace | Faible | Haute | Mesurer hit rate, désactiver si < 5% |

---

## Dépendances externes à ajouter

| Package | Version | Sprint | Usage |
|---------|---------|--------|-------|
| hypothesis | ^6.0 | 1 | Property-based testing |
| pip-audit | ^2.0 | 1 | Audit sécurité deps |
| rich | ^13.0 | 6 | Interface TUI |
| textual | ^0.50 | 6 | Framework TUI |

---

## Critères de Validation Globaux

### Par Sprint
- [ ] Tests passent (pytest)
- [ ] Couverture >= 85%
- [ ] Mypy sans erreur
- [ ] Ruff sans warning
- [ ] Documentation à jour
- [ ] CHANGELOG mis à jour

### Release finale
- [ ] Tous les sprints complétés
- [ ] Tests d'intégration E2E
- [ ] Documentation utilisateur complète
- [ ] Release notes rédigées
- [ ] Tag version (v2.0.0)

---

## Workflow Git recommandé

```
main ────────────────────────────────────────────────────────────▶
  │
  └──▶ develop ──────────────────────────────────────────────────▶
         │
         ├──▶ feature/improve-test-coverage ──▶ PR ──▶ develop
         │
         ├──▶ feature/property-based-testing ──▶ PR ──▶ develop
         │
         ├──▶ feature/security-improvements ──▶ PR ──▶ develop
         │
         └──▶ ... (autres features)

         │
         └──▶ release/v2.0.0 ──▶ PR ──▶ main (tag v2.0.0)
```

### Commandes GitFlow

```bash
# Initialiser GitFlow
git flow init

# Démarrer un feature
git flow feature start improve-test-coverage

# Terminer un feature
git flow feature finish improve-test-coverage

# Démarrer une release
git flow release start v2.0.0

# Terminer une release
git flow release finish v2.0.0
```

---

## Agents à utiliser par phase

| Phase | Agents recommandés |
|-------|-------------------|
| Tests (5.1, 5.3) | `/dev-tdd`, `/qa-coverage` |
| Sécurité (6.1, 6.2) | `/qa-security`, `/ops-ci` |
| Documentation (7.1, 7.2) | `/doc-generate`, `/doc-explain` |
| Performance (1.x) | `/qa-perf`, `/dev-refactor` |
| Robustesse (2.x, 4.1) | `/dev-error-handling`, `/dev-test` |
| Fonctionnalités (3.x) | `/dev-tdd`, `/dev-component` |
| TUI (4.3) | `/dev-component`, `/dev-tdd` |
| Commits | `/work-commit` |
| PRs | `/work-pr` |
| Release | `/ops-release`, `/doc-changelog` |
