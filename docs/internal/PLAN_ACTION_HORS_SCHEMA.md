# Plan d'action (hors schéma)

Ce plan couvre les améliorations proposées qui **ne nécessitent pas** de modifier le schéma JSON.

## P0 — Hygiène dépôt / archive — **fait**

- Nettoyer définitivement les artefacts générés :
  - `docs/_build/`
  - `web/node_modules/`
  - `build/`, `dist/`, `*.egg-info/`
  - `__pycache__/`, `*.pyc`
- Verrouiller `.gitignore` pour éviter les réintroductions.
- Ajouter une commande de nettoyage (`python scripts/dev.py clean-artifacts`) et une commande d’archive source propre.

**Critère de validation :**
- Clone propre + tests OK + archive légère sans fichiers générés.

## P1 — Stabilisation graphes — **fait**

- Conserver Graphviz (`dot`) comme moteur principal de layout.
- Utiliser le fallback uniquement si `dot` est absent.
- Ajouter des tests de non-régression sur les cas `dic_pipeline` et `qi_hu` :
  - présence/compte de nœuds et d’arêtes
  - génération des fichiers attendus (`.svg`, `.html`, `.png`).

**Critère de validation :**
- Sorties stables entre exécutions, sans régression visuelle majeure sur les cas de référence.

## P2 — Simplification API typée — **fait**

- Permettre à `R3XAFile` d’accepter directement des objets Pydantic.
- Conserver compatibilité totale avec l’API dict actuelle.
- Garder le fonctionnement sans extra `[typed]`.

**Critère de validation :**
- Un même flux de création fonctionne en mode dict et en mode typé.

## P3 — Réduction du boilerplate `core.py` — **fait**

- Réduire les helpers redondants en les générant depuis le schéma (ou un mapping dérivé).
- Conserver manuellement seulement les helpers les plus utilisés / lisibles.

**Critère de validation :**
- Moins de duplication, API publique inchangée ou clairement versionnée.

## P4 — Documentation technique ciblée — **fait**

- Documenter explicitement :
  - moteur graphe principal vs fallback
  - dépendances optionnelles
  - workflow développeur (génération modèles, nettoyage, tests, archive).

**Critère de validation :**
- Un nouveau contributeur peut reproduire l’environnement et le pipeline sans ambiguïté.

## Etat actuel

- `python scripts/dev.py clean-artifacts` et `python scripts/dev.py source-archive` existent et sont documentes.
- Les graphes de reference (`dic_pipeline`, `qi_hu`) sont testes et regenerables.
- `R3XAFile` accepte directement les objets Pydantic.
- Les helpers guides sont derives du schema et exposes aux IDE via `core.pyi`.
- Le workflow developpeur (modele, stub, spec, tests, archive) est documente.

## Suite utile

- Ce plan est globalement termine.
- Les sujets restants relevent plutot:
  - de l'hygiene documentaire continue;
  - de la stabilisation de l'API publique;
  - ou du chantier v2.0 autour des helpers guides.
