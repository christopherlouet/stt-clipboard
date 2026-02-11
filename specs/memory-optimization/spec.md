# Specification : Optimisation Memoire & Securisation STT Clipboard

**Branche**: `feature/memory-optimization`
**Date**: 2026-02-11
**Statut**: Valide

## Resume

STT Clipboard consomme ~412 MB au repos, principalement a cause du modele de transcription qui reste charge en permanence, meme sans activite. Ce plan ameliore la gestion memoire (economie de 200-800 MB en inactivite), renforce la securisation du canal de commande, et corrige les problemes de qualite de code identifies par l'audit complet.

## User Stories (prioritisees)

### US1 - Dechargement automatique du modele en inactivite (Priorite: P1) MVP

**En tant qu'** utilisateur de STT Clipboard en mode TUI ou daemon
**Je veux** que le modele de transcription soit libere automatiquement apres une periode d'inactivite
**Afin de** recuperer 200-800 MB de memoire quand je ne dicte pas

**Pourquoi P1**: C'est l'optimisation a plus fort impact. Sur une machine avec 4 GB de RAM, liberer 250 MB change radicalement l'experience.

**Test independant**: Lancer l'application, attendre le delai d'inactivite configure, verifier que la memoire a diminue. Relancer une dictee et verifier que le modele se recharge automatiquement.

**Criteres d'acceptation**:

1. **Etant donne** l'application en mode TUI avec le modele charge, **Quand** aucune transcription n'est lancee pendant le delai configure (defaut: 5 minutes), **Alors** le modele est decharge et la memoire diminue d'au moins 150 MB
2. **Etant donne** le modele decharge par inactivite, **Quand** l'utilisateur lance une nouvelle dictee, **Alors** le modele est recharge automatiquement et la transcription fonctionne normalement
3. **Etant donne** le mode TUI, **Quand** l'utilisateur ne modifie rien, **Alors** le dechargement automatique est active par defaut (5 minutes d'inactivite)
4. **Etant donne** le mode daemon, **Quand** l'utilisateur ne modifie rien, **Alors** le dechargement automatique est desactive par defaut (reactivite prioritaire)
5. **Etant donne** l'option activee dans la configuration, **Quand** le modele se recharge apres inactivite, **Alors** un indicateur visuel informe l'utilisateur du chargement en cours

---

### US2 - Validation stricte des commandes recues (Priorite: P1) MVP

**En tant qu'** utilisateur de STT Clipboard
**Je veux** que seules les commandes connues soient acceptees par le canal de commande
**Afin de** eviter tout comportement inattendu cause par des donnees invalides

**Pourquoi P1**: Vulnerabilite securitaire haute (VUL-001). Correction simple et rapide.

**Test independant**: Envoyer des commandes valides et invalides au canal, verifier que seules les valides sont traitees.

**Criteres d'acceptation**:

1. **Etant donne** le service en cours d'execution, **Quand** une commande valide est envoyee (TRIGGER_COPY, TRIGGER_PASTE, TRIGGER_PASTE_TERMINAL, TRIGGER), **Alors** elle est traitee normalement
2. **Etant donne** le service en cours d'execution, **Quand** une commande inconnue est envoyee, **Alors** elle est rejetee avec un message d'erreur et un log d'avertissement
3. **Etant donne** le service en cours d'execution, **Quand** des donnees non-textuelles sont envoyees, **Alors** elles sont rejetees proprement sans crash
4. **Etant donne** le service en cours d'execution, **Quand** plus de 5 commandes sont recues en 10 secondes, **Alors** les commandes supplementaires sont rejetees temporairement (protection anti-flood, valeurs fixes non configurables)

---

### US3 - Protection des donnees dans les logs (Priorite: P1) MVP

**En tant qu'** utilisateur soucieux de sa vie privee
**Je veux** que le contenu de mes dictees ne soit pas enregistre en clair dans les logs
**Afin de** preserver la confidentialite de mes transcriptions

**Pourquoi P1**: Le texte dicte peut contenir des informations sensibles (mots de passe, donnees personnelles). Logger en clair est un risque de confidentialite (VUL-004).

**Test independant**: Effectuer une transcription, verifier dans les logs qu'aucun texte complet n'apparait au niveau INFO.

**Criteres d'acceptation**:

1. **Etant donne** une transcription reussie, **Quand** les logs sont au niveau INFO ou superieur, **Alors** seule la longueur du texte et la langue detectee sont affichees (pas le contenu)
2. **Etant donne** le niveau de log regle a DEBUG, **Quand** une transcription est effectuee, **Alors** le contenu complet est visible (utile pour le developpement)
3. **Etant donne** les logs existants, **Quand** on inspecte les fichiers de log, **Alors** aucune transcription complete n'est presente au-dessus du niveau DEBUG

---

### US4 - Limitation de la croissance du journal TUI (Priorite: P2)

**En tant qu'** utilisateur en session continue prolongee
**Je veux** que le journal de transcriptions dans l'interface ne consomme pas de memoire indefiniment
**Afin de** pouvoir laisser l'application ouverte toute la journee sans degradation

**Pourquoi P2**: Impact memoire reel mais progressif (~500 octets par entree). Problematique seulement en sessions tres longues (>1000 dictees).

**Test independant**: Simuler un grand nombre de transcriptions dans le TUI, verifier que la memoire reste stable apres le seuil configure.

**Criteres d'acceptation**:

1. **Etant donne** le journal TUI avec plus de 1000 entrees (defaut), **Quand** une nouvelle transcription arrive, **Alors** le journal est nettoye avec un message indicatif
2. **Etant donne** la limite de lignes configurable, **Quand** l'utilisateur modifie la limite, **Alors** le nouveau seuil est respecte
3. **Etant donne** un nettoyage du journal, **Quand** l'utilisateur consulte l'historique complet, **Alors** il peut retrouver ses anciennes transcriptions via l'historique persistant (fichier)

---

### US5 - Troncature des textes longs dans l'historique (Priorite: P2)

**En tant qu'** utilisateur qui dicte occasionnellement de longs textes
**Je veux** que l'historique ne stocke pas des textes demesurement longs
**Afin de** eviter une consommation memoire excessive sur les cas extremes

**Pourquoi P2**: Cas rare mais non borne. Une dictee de 10 000 caracteres x 100 entrees = 2 MB inutile.

**Test independant**: Ajouter un texte tres long a l'historique, verifier qu'il est tronque a la limite configuree.

**Criteres d'acceptation**:

1. **Etant donne** une transcription depassant la limite configuree (defaut: 1000 caracteres), **Quand** elle est ajoutee a l'historique, **Alors** elle est tronquee avec un marqueur "[...]"
2. **Etant donne** la copie dans le presse-papier, **Quand** un texte long est transcrit, **Alors** le texte complet est copie (la troncature ne concerne que l'historique)

---

### US6 - Indicateur de memoire dans le TUI (Priorite: P2)

**En tant qu'** utilisateur de STT Clipboard en mode TUI
**Je veux** voir la consommation memoire actuelle dans l'interface
**Afin de** verifier l'impact du dechargement et surveiller les ressources

**Pourquoi P2**: Donne de la visibilite sur l'optimisation US1. Utile pour le debug et le monitoring.

**Test independant**: Lancer le TUI, verifier qu'un indicateur memoire s'affiche et se met a jour.

**Criteres d'acceptation**:

1. **Etant donne** le TUI en cours d'execution, **Quand** l'utilisateur regarde l'interface, **Alors** un indicateur affiche la memoire utilisee en MB (mise a jour toutes les 5 secondes)
2. **Etant donne** le dechargement du modele (US1), **Quand** le modele est decharge, **Alors** l'indicateur reflète la baisse de memoire
3. **Etant donne** l'indicateur memoire, **Quand** psutil est installe, **Alors** il affiche la memoire RSS du processus

---

### US7 - Renforcement de la qualite du code (Priorite: P2)

**En tant que** developpeur du projet
**Je veux** que les regles de verification de types soient renforcees et les doublons corriges
**Afin de** detecter les erreurs plus tot et simplifier la maintenance

**Pourquoi P2**: Dette technique identifiee par l'audit. Les reglages permissifs masquent des bugs potentiels.

**Test independant**: Lancer la verification de types apres les changements, verifier que le projet compile sans erreur.

**Criteres d'acceptation**:

1. **Etant donne** la configuration de verification de types, **Quand** les reglages stricts sont actives (disallow_untyped_defs=true, warn_return_any=true), **Alors** le projet passe la verification sans erreur
2. **Etant donne** les dependances de developpement, **Quand** on inspecte la configuration, **Alors** il n'y a pas de doublons
3. **Etant donne** le code existant, **Quand** les regles strictes sont activees, **Alors** toutes les erreurs de type sont corrigees dans le meme sprint (pas de progression incrementale)

---

### US8 - Correction des tests TUI (Priorite: P3)

**En tant que** developpeur du projet
**Je veux** que les tests de l'interface utilisateur fonctionnent a nouveau
**Afin de** garantir la non-regression sur le composant TUI

**Pourquoi P3**: 18 erreurs de collection dans les tests TUI. Important pour la qualite long terme mais n'affecte pas les utilisateurs.

**Test independant**: Lancer la suite de tests complete et verifier que les tests TUI s'executent sans erreur de collection.

**Criteres d'acceptation**:

1. **Etant donne** la suite de tests du projet, **Quand** on execute les tests TUI, **Alors** il n'y a plus d'erreurs de collection
2. **Etant donne** les tests TUI corriges, **Quand** on lance la suite complete, **Alors** les 3 fichiers de tests TUI passent

## Exigences Fonctionnelles

- **EF-001**: Le systeme DOIT pouvoir decharger le modele de transcription apres une periode configurable d'inactivite
- **EF-002**: Le systeme DOIT recharger le modele automatiquement et de facon transparente lors de la prochaine dictee
- **EF-003**: Le systeme DOIT rejeter toute commande non reconnue sur le canal de commande
- **EF-004**: Le systeme DOIT limiter le debit des commandes recues (anti-flood, 5 req / 10s, valeurs fixes)
- **EF-005**: Le systeme NE DOIT PAS enregistrer le contenu des transcriptions dans les logs au-dessus du niveau DEBUG
- **EF-006**: Le systeme DOIT limiter le nombre de lignes affichees dans le journal TUI
- **EF-007**: Le systeme DOIT tronquer les textes trop longs dans l'historique persistant
- **EF-008**: Le dechargement DOIT etre active par defaut en mode TUI et desactive en mode daemon
- **EF-009**: Le systeme DOIT afficher un indicateur de memoire dans le TUI (via psutil, dependance obligatoire)
- **EF-010**: Le systeme DOIT passer la verification de types stricte (mypy strict) sans erreur

## Cas Limites (Edge Cases)

- Que se passe-t-il quand l'utilisateur lance une dictee exactement au moment du dechargement ?
  -> Le dechargement est annule et la dictee continue normalement
- Que se passe-t-il si le modele ne peut pas se recharger (disque plein, fichier corrompu) ?
  -> Message d'erreur clair a l'utilisateur, le service reste fonctionnel mais ne peut pas transcrire
- Que se passe-t-il en mode oneshot avec le dechargement active ?
  -> Le modele est decharge immediatement apres la transcription (pas de timer)
- Que se passe-t-il si le canal de commande recoit des centaines de requetes simultanees ?
  -> Le rate limiter rejette les requetes excessives (5/10s fixe), les requetes valides continuent d'etre traitees
- Que se passe-t-il si le texte fait exactement la taille limite de troncature ?
  -> Il est conserve tel quel (la troncature s'applique uniquement au-dessus de la limite)
- Que se passe-t-il si psutil ne peut pas lire la memoire (permissions) ?
  -> Le widget affiche "N/A" sans crash

## Entites Cles

| Entite | Description | Attributs cles |
|--------|-------------|----------------|
| Configuration memoire | Parametres de gestion de la memoire | dechargement auto, delai inactivite, limite log TUI, limite texte historique |
| Modele de transcription | Modele Whisper charge en memoire | etat (charge/decharge), taille, temps de chargement |
| Journal TUI | Affichage des transcriptions recentes | nombre de lignes, limite max |
| Historique | Stockage persistant des transcriptions | nombre d'entrees, longueur max texte |
| Indicateur memoire | Widget TUI affichant la RAM | memoire RSS, frequence mise a jour (5s) |

## Criteres de Succes (mesurables)

- **CS-001**: La memoire au repos diminue d'au moins 150 MB apres le dechargement du modele (mesure via RSS)
- **CS-002**: Le temps de rechargement du modele est inferieur a 5 secondes
- **CS-003**: Aucune commande invalide n'est traitee (taux de rejet = 100% pour les commandes inconnues)
- **CS-004**: Le contenu des transcriptions n'apparait plus dans les logs au niveau INFO
- **CS-005**: La memoire du journal TUI reste stable apres 1000+ transcriptions
- **CS-006**: Aucune regression fonctionnelle (tous les tests existants passent)
- **CS-007**: Le comportement par defaut est : active en TUI, desactive en daemon
- **CS-008**: L'indicateur memoire affiche la valeur RSS avec une precision de 0.1 MB
- **CS-009**: mypy passe sans erreur avec disallow_untyped_defs=true et warn_return_any=true

## Hors Scope (explicitement exclus)

- Migration du VAD vers ONNX (gain de 30-50 MB mais complexite elevee pour un gain faible)
- Optimisation du runtime PyTorch (depasse le scope du projet)
- Authentification par token sur le canal de commande (VUL-002 - sera traite separement)
- Refactoring de process_request() (dette technique identifiee mais hors scope)
- Remplacement des exceptions larges (dette technique, sprint separe)
- Integration de pip-audit dans le CI (ops, sprint separe)
- Rate limiting configurable (valeurs fixes suffisantes pour v1)

## Hypotheses et Dependances

### Hypotheses
- Le dechargement du modele via `gc.collect()` libere effectivement la memoire RSS (pas seulement la memoire virtuelle)
- Le rechargement du modele est acceptable en termes de latence (< 5s) pour l'experience utilisateur TUI
- Le rate limiting fixe a 5 requetes / 10 secondes est suffisant pour un usage normal
- L'activation stricte de mypy generera des erreurs corrigeables dans un effort raisonnable

### Dependances
- faster-whisper doit supporter le dechargement/rechargement propre du modele
- Le framework Textual doit supporter le nettoyage du contenu du RichLog
- psutil doit etre ajoute comme dependance obligatoire (pour le widget MemoryPanel)

## Clarifications

### Session 2026-02-11
- Q: Le dechargement automatique doit-il avoir un comportement different par mode ? -> R: **Active par defaut en TUI (5 min), desactive en daemon** (reactivite prioritaire en daemon)
- Q: Le rate limiting doit-il etre configurable ? -> R: **Valeurs fixes** (5 req / 10s). Pas de config supplementaire, ajustable dans une future version.
- Q: Faut-il un widget MemoryPanel dans le TUI ? -> R: **Oui, inclus dans ce sprint**. psutil en dependance obligatoire.
- Q: psutil obligatoire ou optionnel ? -> R: **Obligatoire** (~5 MB, dependance legere et standard).
- Q: Strategie mypy stricte ? -> R: **Tout d'un coup**. Activer toutes les regles strictes et corriger toutes les erreurs dans ce sprint.
