# Plan d'action (hors schéma)

Ce plan couvre les améliorations proposées qui **ne nécessitent pas** de modifier le schéma JSON.

## P0 — Hygiène dépôt / archive (immédiat)

- Nettoyer définitivement les artefacts générés :
  - `docs/_build/`
  - `web/node_modules/`
  - `build/`, `dist/`, `*.egg-info/`
  - `__pycache__/`, `*.pyc`
- Verrouiller `.gitignore` pour éviter les réintroductions.
- Ajouter une cible de nettoyage (`make clean-artifacts`) et une commande d’archive source propre.

**Critère de validation :**
- Clone propre + tests OK + archive légère sans fichiers générés.

## P1 — Stabilisation graphes (priorité haute)

- Conserver Graphviz (`dot`) comme moteur principal de layout.
- Utiliser le fallback uniquement si `dot` est absent.
- Ajouter des tests de non-régression sur les cas `dic_pipeline` et `qi_hu` :
  - présence/compte de nœuds et d’arêtes
  - génération des fichiers attendus (`.svg`, `.html`, `.png`).

**Critère de validation :**
- Sorties stables entre exécutions, sans régression visuelle majeure sur les cas de référence.

## P2 — Simplification API typée (priorité haute)

- Permettre à `R3XAFile` d’accepter directement des objets Pydantic.
- Conserver compatibilité totale avec l’API dict actuelle.
- Garder le fonctionnement sans extra `[typed]`.

**Critère de validation :**
- Un même flux de création fonctionne en mode dict et en mode typé.

## P3 — Réduction du boilerplate `core.py` (priorité moyenne)

- Réduire les helpers redondants en les générant depuis le schéma (ou un mapping dérivé).
- Conserver manuellement seulement les helpers les plus utilisés / lisibles.

**Critère de validation :**
- Moins de duplication, API publique inchangée ou clairement versionnée.

## P4 — Documentation technique ciblée (priorité moyenne)

- Documenter explicitement :
  - moteur graphe principal vs fallback
  - dépendances optionnelles
  - workflow développeur (génération modèles, nettoyage, tests, archive).

**Critère de validation :**
- Un nouveau contributeur peut reproduire l’environnement et le pipeline sans ambiguïté.

## Ordre d'exécution recommandé

1. P0  
2. P1  
3. P2  
4. P3  
5. P4

