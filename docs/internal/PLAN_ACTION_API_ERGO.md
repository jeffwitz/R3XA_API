# Plan d'action ergonomie API

Ce document formalise les retours d'usage sur `R3XA_API` et fixe un ordre d'execution pragmatique.

## Constats

- L'API coeur est fonctionnelle, mais reste trop basse niveau pour un nouvel utilisateur.
- `R3XAFile.save(...)` existe sans methode symetrique `load(...)`.
- La couche guidee (`add_camera_source`, `add_image_set_list`, etc.) est utile, mais partielle et donc ambiguë.
- La partie `Registry` manque d'operations de decouverte (`list`, `iter`) et de primitives centrees "item".
- `merge_item(...)` existe comme fonction libre, alors que l'utilisateur s'attend plutot a une operation attachee a l'objet ou au registre.
- Le sujet `uncertainty` releve du schema et doit etre traite separement.

## Retour de JC integre

- Si on garde des helpers guides (`add_camera_source`, `add_image_set_list`, etc.), ils doivent:
  - imposer les attributs `required` du schema;
  - exister de maniere coherente pour les autres `settings`, `data_sources` et `data_sets`.
- `load` doit exister en miroir de `save`.
- `Registry` doit permettre de lister/parcourir les items.
- Les operations de type `merge` seraient plus naturelles si elles etaient rattachees a un objet `item` ou au `Registry`.
- Le helper `unit()` pourrait avoir un alias plus parlant (`value()` ou `quantity()`), sans casser l'existant.

## Strategie retenue

### P0 - Ergonomie immediate

- Ajouter `R3XAFile.load(path)` et `R3XAFile.loads(text)`.
- Ajouter `R3XAFile.dump(indent=4)`.
- Faire evoluer `R3XAFile.save(..., validate=True)` pour aligner son comportement avec `save_item(...)`.
- Etendre `Registry` avec:
  - `load(...)`
  - `load_validated(...)`
  - `list(...)`
  - `iter_items(...)`

### P1 - Clarification de la couche guidee

- Conserver une vraie couche guidee coherente.
- Les helpers guides doivent imposer les champs `required` du schema.
- La couverture doit devenir systematique sur les types importants, ou etre explicitement bornee si on s'arrete avant.

### P2 - Abstraction `RegistryItem`

- Introduire une vraie classe `RegistryItem`.
- Y rattacher les operations utiles:
  - `validate()`
  - `merge(...)`
  - `save(...)` ou `save_to(...)`
- Garder les fonctions libres existantes pour compatibilite.

### P3 - Generation depuis le schema

- Generer les helpers guides depuis le schema plutot que les maintenir manuellement.
- Generer egalement des enums/constantes de `kind` pour la decouverte et l'autocompletion.

### P4 - Nommage utilisateur

- Garder `unit()` pour compatibilite et coherence avec le schema (`kind="unit"`).
- Ajouter un alias utilisateur plus explicite:
  - `value()`, ou
  - `quantity()`

### P5 - Chantier schema separe

- Traiter explicitement `uncertainty` dans le schema.
- Ne pas melanger ce sujet avec le refactoring ergonomique Python.

## Ordre d'execution

1. P0 - Chargement/sauvegarde symetriques + decouverte du registre.
2. P1 - Helpers guides stricts et coherents.
3. P2 - `RegistryItem`.
4. P3 - Generation d'API depuis le schema.
5. P4 - Alias de nommage.
6. P5 - Corrections schema hors API.

## Principe directeur

On garde deux niveaux lisibles:

- Niveau bas: API generique stable (`new_item`, `add_item`, `add_setting`, `add_data_source`, `add_data_set`).
- Niveau haut: API guidee coherente, stricte et decouvrable.

L'objectif n'est pas de masquer le schema, mais de rendre son usage naturel.
