# Workflow Git et Agents - Améliorations STT Clipboard v2

## Structure GitFlow

```
main ───────────────────────────────────────────────────────────────▶
  │
  │  Tag v1.2.0 (état actuel)
  │
  └──▶ develop ─────────────────────────────────────────────────────▶
         │
         │  Sprint 1: Fondation
         ├──▶ feature/improve-test-coverage
         ├──▶ feature/property-based-testing
         ├──▶ feature/security-improvements
         ├──▶ feature/documentation-improvements
         │
         │  Sprint 2: Performance
         ├──▶ feature/vad-cache
         ├──▶ feature/model-warmup
         ├──▶ feature/streaming-transcription
         │
         │  Sprint 3: Robustesse
         ├──▶ feature/clipboard-retry-backoff
         ├──▶ feature/no-speech-notification
         ├──▶ feature/startup-validation
         │
         │  Sprint 4: Langues & Historique
         ├──▶ feature/multi-language-support
         ├──▶ feature/transcription-history
         │
         │  Sprint 5: Dictée continue
         ├──▶ feature/continuous-dictation
         │
         │  Sprint 6: TUI
         ├──▶ feature/tui-interface
         │
         │  Release
         └──▶ release/v2.0.0 ──▶ main (Tag v2.0.0)
```

---

## Initialisation GitFlow

```bash
# Si pas déjà fait, initialiser GitFlow
git flow init -d

# Créer la branche develop si elle n'existe pas
git checkout -b develop main
git push -u origin develop
```

---

## Workflow par feature

### Démarrer une feature

```bash
# Méthode GitFlow
git flow feature start improve-test-coverage

# Ou manuellement
git checkout develop
git pull origin develop
git checkout -b feature/improve-test-coverage
```

### Travailler sur une feature

```bash
# Commits atomiques avec Conventional Commits
git add <files>
git commit -m "test(coverage): add tests for transcription __main__ block"

# Ou utiliser l'agent
# /work-commit
```

### Pattern TDD recommandé

Pour chaque tâche marquée `TDD` :

1. **Red** : Écrire le test qui échoue
   ```bash
   # Créer le fichier test
   # /dev-tdd "créer test pour AudioChunkCache"
   uv run pytest tests/test_cache.py -v  # Doit échouer
   ```

2. **Green** : Implémenter le minimum pour passer
   ```bash
   # Implémenter la fonctionnalité
   uv run pytest tests/test_cache.py -v  # Doit passer
   ```

3. **Refactor** : Améliorer le code
   ```bash
   uv run black src/cache.py
   uv run ruff check --fix src/cache.py
   uv run mypy src/cache.py
   ```

4. **Commit**
   ```bash
   # /work-commit
   git add .
   git commit -m "feat(cache): implement LRU cache for VAD chunks"
   ```

### Terminer une feature

```bash
# Vérifier que tout passe
uv run pytest
uv run mypy src/
uv run ruff check .

# Créer la PR
# /work-pr

# Ou manuellement
git push -u origin feature/improve-test-coverage

# Après review et merge, supprimer la branche
git flow feature finish improve-test-coverage
# Ou manuellement
git checkout develop
git merge feature/improve-test-coverage
git branch -d feature/improve-test-coverage
```

---

## Agents par phase

### Sprint 1 : Fondation

| Tâche | Agent principal | Agents secondaires |
|-------|-----------------|-------------------|
| T001-T004 (Tests coverage) | `/dev-test` | `/qa-coverage` |
| T005-T008 (Property tests) | `/dev-tdd` | `/dev-test` |
| T009-T012 (Sécurité) | `/qa-security` | `/ops-ci` |
| T013-T017 (Documentation) | `/doc-generate` | `/doc-explain` |

```bash
# Exemple workflow Sprint 1
git flow feature start improve-test-coverage

# Pour chaque fichier de test
# /dev-test "améliorer couverture test_transcription.py"

# Vérifier couverture
# /qa-coverage

# Commit
# /work-commit

# PR
# /work-pr
```

### Sprint 2 : Performance

| Tâche | Agent principal | Agents secondaires |
|-------|-----------------|-------------------|
| T018-T021 (Cache VAD) | `/dev-tdd` | `/qa-perf` |
| T022-T025 (Warmup) | `/dev-tdd` | `/dev-refactor` |
| T026-T029 (Streaming) | `/dev-tdd` | `/dev-refactor` |

```bash
# Exemple workflow TDD
git flow feature start vad-cache

# 1. Créer les tests d'abord
# /dev-tdd "créer tests pour AudioChunkCache avec LRU"

# 2. Implémenter
# /dev-tdd "implémenter AudioChunkCache"

# 3. Benchmark performance
# /qa-perf "mesurer impact cache VAD"

# 4. Commit et PR
# /work-commit
# /work-pr
```

### Sprint 3 : Robustesse

| Tâche | Agent principal | Agents secondaires |
|-------|-----------------|-------------------|
| T030-T032 (Retry backoff) | `/dev-tdd` | `/dev-error-handling` |
| T033-T036 (Notifications) | `/dev-tdd` | `/dev-test` |
| T037-T041 (Validation) | `/dev-tdd` | `/dev-error-handling` |

### Sprint 4 : Langues & Historique

| Tâche | Agent principal | Agents secondaires |
|-------|-----------------|-------------------|
| T042-T047 (Langues) | `/dev-tdd` | `/doc-generate` |
| T048-T053 (Historique) | `/dev-tdd` | `/dev-component` |

### Sprint 5 : Dictée continue

| Tâche | Agent principal | Agents secondaires |
|-------|-----------------|-------------------|
| T054-T061 | `/dev-tdd` | `/dev-component`, `/doc-generate` |

### Sprint 6 : TUI

| Tâche | Agent principal | Agents secondaires |
|-------|-----------------|-------------------|
| T062-T070 | `/dev-component` | `/dev-tdd`, `/doc-generate` |

---

## Release

### Préparer la release

```bash
# Créer branche release
git flow release start v2.0.0

# Mettre à jour version dans pyproject.toml
# /work-commit "chore(release): bump version to 2.0.0"

# Générer changelog
# /doc-changelog "v2.0.0"

# Tests finaux
uv run pytest
uv run mypy src/
uv run pre-commit run --all-files

# Commit changelog
# /work-commit "docs(changelog): update for v2.0.0"
```

### Terminer la release

```bash
# Fusionner dans main et develop
git flow release finish v2.0.0

# Push avec tags
git push origin main develop --tags

# Créer GitHub release
# /ops-release "v2.0.0"
```

---

## Commandes utiles

### Suivi des tâches

```bash
# Voir tâches en cours
grep -E "^\- \[ \]" specs/improvements-v2/tasks.md | head -20

# Marquer une tâche comme terminée (remplacer [ ] par [x])
sed -i 's/\- \[ \] \*\*T001\*\*/- [x] **T001**/' specs/improvements-v2/tasks.md

# Compter progression
echo "Terminées: $(grep -c '^\- \[x\]' specs/improvements-v2/tasks.md)"
echo "Restantes: $(grep -c '^\- \[ \]' specs/improvements-v2/tasks.md)"
```

### Vérifications avant PR

```bash
# Script de vérification
#!/bin/bash
echo "🧪 Running tests..."
uv run pytest --cov=src --cov-report=term-missing

echo "📝 Type checking..."
uv run mypy src/

echo "🔍 Linting..."
uv run ruff check .

echo "🎨 Formatting check..."
uv run black --check .

echo "🔒 Security scan..."
uv run bandit -c pyproject.toml -r src/

echo "✅ All checks passed!"
```

### Hotfix urgent

```bash
# Si bug critique en production
git flow hotfix start fix-critical-bug

# Fix et test
# /dev-debug "corriger bug X"
# /dev-test "ajouter test de non-régression"

# Commit
# /work-commit "fix: resolve critical bug in clipboard"

# Terminer (merge dans main ET develop)
git flow hotfix finish fix-critical-bug
```

---

## Checklist par Sprint

### Avant de commencer un sprint

- [ ] Branche develop à jour (`git pull origin develop`)
- [ ] Toutes les features du sprint précédent mergées
- [ ] Pas de bugs bloquants ouverts
- [ ] Dépendances vérifiées (`uv sync`)

### Avant chaque PR

- [ ] Tests passent (`uv run pytest`)
- [ ] Couverture >= 85% (`uv run pytest --cov=src`)
- [ ] Types vérifiés (`uv run mypy src/`)
- [ ] Lint propre (`uv run ruff check .`)
- [ ] Format correct (`uv run black --check .`)
- [ ] Commit messages suivent Conventional Commits
- [ ] Documentation mise à jour si nécessaire

### Avant la release

- [ ] Tous les sprints terminés
- [ ] Tests d'intégration passent
- [ ] CHANGELOG.md mis à jour
- [ ] Version bumped dans pyproject.toml
- [ ] README.md à jour
- [ ] Documentation complète
- [ ] Security audit passé
