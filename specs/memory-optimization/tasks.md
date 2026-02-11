# Taches : Optimisation Memoire & Securisation

## Vue d'ensemble

```
Phase 1 (Fondation)  ──▶  Phase 2 (US1: Model Unload)  ──▶  Phase 5 (US4+5: TUI Log + History)
                      │                                  │
                      ├──▶  Phase 3 (US2: Validation)    ├──▶  Phase 6 (US6: MemoryPanel)
                      │                                  │
                      └──▶  Phase 4 (US3: Log Masking)   └──▶  Phase 7 (US7: Mypy Strict)
                                                         │
                                                         └──▶  Phase 8 (US8: Fix TUI Tests)
```

**Legende**: `[P]` = parallelisable | `[US1]` = tracabilite User Story

---

## Phase 1 : Fondation (bloquant pour toutes les phases suivantes)

### T001 - [US1,4,5] Ajouter MemoryConfig dans config.py
- **Fichier**: `src/config.py`
- **Action**: Creer `MemoryConfig` dataclass avec:
  - `auto_unload_model: bool` (defaut: True)
  - `idle_timeout_seconds: int` (defaut: 300)
  - `max_tui_log_lines: int` (defaut: 1000)
  - `max_history_text_length: int` (defaut: 1000)
- Integrer dans `Config`, `from_yaml()`, `validate()`, `to_dict()`
- **TDD**: Ecrire tests dans `tests/test_config.py` AVANT le code

### T002 - [P] [US6] Ajouter psutil comme dependance
- **Fichier**: `pyproject.toml`
- **Action**: Ajouter `"psutil>=5.9.0"` dans `[project] dependencies`

### T003 - [P] [US7] Dedupliquer les dev dependencies
- **Fichier**: `pyproject.toml`
- **Action**: Supprimer le bloc `[dependency-groups] dev` (lignes 76-92), garder uniquement `[project.optional-dependencies] dev` (lignes 39-55)

### T004 - [P] [US1] Ajouter section memory dans config.yaml
- **Fichier**: `config/config.yaml`
- **Action**: Ajouter section `memory:` avec les 4 valeurs par defaut

---

## Phase 2 : US1 - Dechargement automatique du modele (P1 MVP)

> Depend de: Phase 1 (T001)

### T005 - [US1] Tests pour unload_model ameliore
- **Fichier**: `tests/test_memory_management.py` (nouveau)
- **Action**: Tests TDD pour:
  - `unload_model()` appelle `gc.collect()`
  - `is_loaded` property retourne le bon etat
  - `transcribe()` recharge si modele decharge
  - Dechargement annule si transcription en cours

### T006 - [US1] Ameliorer unload_model() dans transcription.py
- **Fichier**: `src/transcription.py`
- **Action**:
  - Ajouter `import gc` et `del self.model` avant `gc.collect()`
  - Ajouter property `is_loaded -> bool`
  - Ajouter lock pour empecher dechargement pendant transcription
- Depend de: T005

### T007 - [US1] Tests pour idle timer dans STTService
- **Fichier**: `tests/test_memory_management.py`
- **Action**: Tests TDD pour:
  - Timer demarre apres transcription reussie
  - Timer se reset a chaque nouvelle transcription
  - Timer declenche `unload_model()` apres le delai
  - Timer desactive quand `auto_unload_model=False`
  - Comportement defaut: active en TUI, desactive en daemon

### T008 - [US1] Ajouter idle timer dans main.py
- **Fichier**: `src/main.py`
- **Action**:
  - Ajouter `_idle_timer: asyncio.TimerHandle | None` dans `STTService`
  - Ajouter `_reset_idle_timer()` appele apres chaque transcription
  - Ajouter `_on_idle_timeout()` qui appelle `transcriber.unload_model()`
  - Respecter `config.memory.auto_unload_model` et `idle_timeout_seconds`
- Depend de: T006, T007

### T009 - [US1] Tests pour integration idle timer dans TUI
- **Fichier**: `tests/test_memory_management.py`
- **Action**: Tests TDD pour:
  - Indicateur visuel "Chargement du modele..." affiche dans TUI
  - Timer s'integre avec le cycle de vie du TUI

### T010 - [US1] Integration idle timer dans tui.py
- **Fichier**: `src/tui.py`
- **Action**:
  - Afficher indicateur visuel lors du rechargement du modele
  - Logger etat du modele (charge/decharge) dans le journal
- Depend de: T008, T009

---

## Phase 3 : US2 - Validation des commandes (P1 MVP)

> [P] Parallelisable avec Phase 2. Depend de: Phase 1 (T001)

### T011 - [P] [US2] Tests pour validation des commandes
- **Fichier**: `tests/test_hotkey.py` (existant, ajout de tests)
- **Action**: Tests TDD pour:
  - Commandes valides acceptees (TRIGGER_COPY, TRIGGER_PASTE, TRIGGER_PASTE_TERMINAL, TRIGGER)
  - Commandes inconnues rejetees avec log warning
  - Donnees non-UTF8 rejetees sans crash
  - Messages vides rejetes
  - Messages trop longs (>100 bytes) rejetes

### T012 - [US2] Ajouter validation stricte dans hotkey.py
- **Fichier**: `src/hotkey.py`
- **Action**:
  - Definir `VALID_COMMANDS: frozenset` avec les 4 commandes valides
  - Valider la commande avant traitement dans `_handle_client()`
  - Ajouter `try/except UnicodeDecodeError` pour donnees non-textuelles
  - Logger un warning pour chaque commande rejetee
- Depend de: T011

### T013 - [P] [US2] Tests pour rate limiter
- **Fichier**: `tests/test_rate_limiter.py` (nouveau)
- **Action**: Tests TDD pour:
  - 5 requetes autorisees dans 10 secondes
  - 6eme requete rejetee
  - Requetes autorisees apres expiration de la fenetre
  - Thread-safety du rate limiter

### T014 - [US2] Ajouter RateLimiter dans hotkey.py
- **Fichier**: `src/hotkey.py`
- **Action**:
  - Creer classe `RateLimiter` avec deque de timestamps
  - Constantes `MAX_REQUESTS=5`, `WINDOW_SECONDS=10.0`
  - Integrer dans `_handle_client()` avant validation
  - Logger un warning quand rate limit atteint
- Depend de: T013

---

## Phase 4 : US3 - Protection des donnees dans les logs (P1 MVP)

> [P] Parallelisable avec Phases 2 et 3. Depend de: Phase 1

### T015 - [P] [US3] Tests pour log masking
- **Fichier**: `tests/test_main.py` (existant, ajout de tests)
- **Action**: Tests TDD pour:
  - Niveau INFO: seule la longueur et la langue apparaissent
  - Niveau DEBUG: texte complet visible
  - Verifier les 4 points de log concernes

### T016 - [US3] Masquer les transcriptions dans les logs
- **Fichier**: `src/main.py`
- **Action**: Modifier les 4 occurrences:
  - Ligne 152: `logger.info(f"Transcription: '{text}'")` → `logger.info(f"Transcription: {len(text)} chars")` + `logger.debug(f"Content: '{text}'")`
  - Ligne 159: `logger.info(f"After punctuation: '{text}'")` → idem
  - Ligne 289: `logger.info(f"Transcribed: {text}")` → idem
  - Ligne 349: `logger.info(f"Transcribed: {text}")` → idem
- Depend de: T015

---

## Phase 5 : US4 + US5 - Limitation journal TUI + Troncature historique (P2)

> Depend de: Phase 1 (T001)

### T017 - [P] [US4] Tests pour TranscriptionLog max_lines
- **Fichier**: `tests/test_tui.py` (existant, ajout de tests)
- **Action**: Tests TDD pour:
  - Journal nettoye quand > max_tui_log_lines
  - Message indicatif affiche lors du nettoyage
  - Nouvelles transcriptions continuent apres nettoyage

### T018 - [US4] Ajouter max_lines a TranscriptionLog
- **Fichier**: `src/tui.py`
- **Action**:
  - Ajouter compteur `_line_count` dans `TranscriptionLog`
  - Dans `add_transcription()`: si `_line_count > max_tui_log_lines`, appeler `clear()` et afficher message
  - Lire la limite depuis `config.memory.max_tui_log_lines`
- Depend de: T017

### T019 - [P] [US5] Tests pour troncature historique
- **Fichier**: `tests/test_history.py` (existant, ajout de tests)
- **Action**: Tests TDD pour:
  - Texte > 1000 chars tronque avec "[...]"
  - Texte <= 1000 chars conserve tel quel
  - Texte exactement 1000 chars conserve tel quel
  - Presse-papier recoit le texte complet (non tronque)

### T020 - [US5] Ajouter troncature dans history.py
- **Fichier**: `src/history.py`
- **Action**:
  - Dans `add()`: si `len(text) > max_text_length`, tronquer a `text[:max_text_length] + " [...]"`
  - `max_text_length` lu depuis config ou parametre
- Depend de: T019

---

## Phase 6 : US6 - Indicateur memoire TUI (P2)

> Depend de: Phase 1 (T002 pour psutil)

### T021 - [P] [US6] Tests pour MemoryPanel
- **Fichier**: `tests/test_tui_widgets.py` (existant, ajout de tests)
- **Action**: Tests TDD pour:
  - Widget affiche memoire en MB
  - Rafraichissement toutes les 5 secondes
  - Affiche "N/A" si psutil echoue
  - Precision 0.1 MB

### T022 - [US6] Creer MemoryPanel widget
- **Fichier**: `src/tui_widgets/memory_panel.py` (nouveau)
- **Action**:
  - Classe `MemoryPanel(Static)` avec `set_interval(5)`
  - Utiliser `psutil.Process().memory_info().rss`
  - Formater en `f"{rss_mb:.1f} MB"`
  - try/except avec fallback "N/A"
- Depend de: T021

### T023 - [US6] Integrer MemoryPanel dans tui.py
- **Fichier**: `src/tui.py`, `src/tui_widgets/__init__.py`
- **Action**:
  - Ajouter `MemoryPanel` dans `compose()` du TUI
  - Exporter dans `__init__.py`
- Depend de: T022

---

## Phase 7 : US7 - Renforcement mypy strict (P2)

> [P] Parallelisable. Depend de: Phases 1-6 (idealement apres le code fonctionnel)

### T024 - [US7] Activer mypy strict dans pyproject.toml
- **Fichier**: `pyproject.toml`
- **Action**:
  - `disallow_untyped_defs = true`
  - `warn_return_any = true`
  - `allow_untyped_calls = false`
  - `no_implicit_optional = true`
  - Supprimer le bloc `[[tool.mypy.overrides]]` permissif

### T025 - [US7] Corriger toutes les erreurs mypy
- **Fichiers**: `src/*.py` (multiples)
- **Action**:
  - Lancer `uv run mypy src/` et corriger toutes les erreurs
  - Ajouter type hints manquants
  - Corriger les retours `Any` implicites
  - S'assurer que le code passe sans erreur
- Depend de: T024

---

## Phase 8 : US8 - Correction des tests TUI (P3)

> [P] Parallelisable avec Phase 7

### T026 - [US8] Diagnostiquer les erreurs de collection TUI
- **Fichiers**: `tests/test_tui.py`, `tests/test_tui_settings.py`, `tests/test_tui_widgets.py`
- **Action**:
  - Lancer `uv run pytest tests/test_tui.py --co` pour identifier les erreurs
  - Corriger les imports, fixtures, ou incompatibilites Textual

### T027 - [US8] Verifier que tous les tests passent
- **Action**:
  - Lancer `uv run pytest` complet
  - Verifier aucune regression (CS-006)
  - Verifier couverture >= 80% sur nouveau code
- Depend de: T026

---

## Resume des dependances

```
T001 ──┬──▶ T005 ──▶ T006 ──▶ T007 ──▶ T008 ──▶ T009 ──▶ T010
       │
T002 ──┼──▶ T021 ──▶ T022 ──▶ T023
       │
T003   │
       │
T004   ├──▶ T011 ──▶ T012
       │    T013 ──▶ T014
       │
       ├──▶ T015 ──▶ T016
       │
       ├──▶ T017 ──▶ T018
       │    T019 ──▶ T020
       │
       └──▶ T024 ──▶ T025

T026 ──▶ T027
```

## Estimation de complexite

| Phase | Complexite | Fichiers | Lignes estimees |
|-------|------------|----------|-----------------|
| Phase 1 (Fondation) | Simple | 3 | ~80 |
| Phase 2 (US1 Model Unload) | Complexe | 4 | ~250 |
| Phase 3 (US2 Validation) | Moyenne | 2 | ~150 |
| Phase 4 (US3 Log Masking) | Simple | 1 | ~30 |
| Phase 5 (US4+5 TUI/History) | Moyenne | 2 | ~80 |
| Phase 6 (US6 MemoryPanel) | Moyenne | 3 | ~100 |
| Phase 7 (US7 Mypy) | Complexe | 10+ | ~200 |
| Phase 8 (US8 TUI Tests) | Moyenne | 3 | ~100 |
| **Total** | **Complexe** | **15+** | **~990** |

## Checklist de validation

### Completude
- [x] Tous les fichiers identifies avec chemins exacts
- [x] Toutes les taches listees avec IDs (T001-T027)
- [x] User stories tracees ([US1]-[US8])
- [x] Tests planifies (TDD: tests AVANT code)
- [x] Risques documentes

### Faisabilite
- [x] `unload_model()` existe deja, extension naturelle
- [x] `transcribe()` recharge deja le modele si None
- [x] Textual supporte `Static` widget et `set_interval`
- [x] psutil est une dependance legere et standard

### Qualite
- [x] Respecte les conventions Python du projet
- [x] TDD obligatoire (tests avant code)
- [x] Pas d'over-engineering (rate limiter simple, pas configurable)
- [x] Chaque US testable independamment
