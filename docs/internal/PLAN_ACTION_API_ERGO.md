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

### P0 - Ergonomie immediate — **fait**

- Ajouter `R3XAFile.load(path)` et `R3XAFile.loads(text)`.
- Ajouter `R3XAFile.dump(indent=4)`.
- Faire evoluer `R3XAFile.save(..., validate=True)` pour aligner son comportement avec `save_item(...)`.
- Etendre `Registry` avec:
  - `load(...)`
  - `load_validated(...)`
  - `list(...)`
  - `iter_items(...)`

### P1 - Clarification de la couche guidee — **fait**

- Conserver une vraie couche guidee coherente.
- Les helpers guides doivent imposer les champs `required` du schema.
- La couverture doit devenir systematique sur les types importants, ou etre explicitement bornee si on s'arrete avant.

### P2 - Abstraction `RegistryItem` — **fait**

- Introduire une vraie classe `RegistryItem`.
- Y rattacher les operations utiles:
  - `validate()`
  - `merge(...)`
  - `save(...)` ou `save_to(...)`
- Garder les fonctions libres existantes pour compatibilite.

### P3 - Generation depuis le schema — **partiellement fait**

- Generer les helpers guides depuis le schema plutot que les maintenir manuellement.
- Generer egalement des enums/constantes de `kind` pour la decouverte et l'autocompletion.
- Etat actuel:
  - les helpers guides sont bien derives du schema;
  - un stub `r3xa_api/core.pyi` est genere pour exposer ces helpers aux IDE;
  - les enums/constantes de `kind` ne sont pas encore en place.

### P4 - Nommage utilisateur — **non fait**

- Garder `unit()` pour compatibilite et coherence avec le schema (`kind="unit"`).
- Ajouter un alias utilisateur plus explicite:
  - `value()`, ou
  - `quantity()`

### P5 - Chantier schema separe — **fait pour `uncertainty`**

- Traiter explicitement `uncertainty` dans le schema.
- Ne pas melanger ce sujet avec le refactoring ergonomique Python.

## Etat actuel

- `R3XAFile.load(...)`, `loads(...)`, `dump(...)` et `save(..., validate=True)` sont en place.
- `Registry` expose `load(...)`, `load_validated(...)`, `list(...)`, `iter_items(...)` et `merge(...)`.
- `RegistryItem` existe et porte `validate()`, `merge(...)`, `save(...)`, `save_to(...)`.
- La couche guidee est maintenant systematique sur les `kind` du schema et verifiee par tests de contrat.
- Le schema source vit dans `R3XA_SPEC`; `R3XA_API` embarque une copie runtime synchronisee.
- `uncertainty` a ete ajoute a `data_sources/generic` dans la source de verite du schema.
- Un stub type `r3xa_api/core.pyi` + `py.typed` expose les helpers guides aux IDE.
- Restent ouverts:
  - enums/constantes de `kind`;
  - alias utilisateur pour `unit()` (`value()` / `quantity()`);
  - eventuelle sortie de `exec()` pour la v2.0.

## Ordre d'execution

1. P3 restant - enums/constantes de `kind`.
2. P4 - alias de nommage utilisateur pour `unit()`.
3. Stabilisation v2.0 - decision sur le remplacement ou non de `exec()` pour les helpers guides.

## Principe directeur

On garde deux niveaux lisibles:

- Niveau bas: API generique stable (`new_item`, `add_item`, `add_setting`, `add_data_source`, `add_data_set`).
- Niveau haut: API guidee coherente, stricte et decouvrable.

L'objectif n'est pas de masquer le schema, mais de rendre son usage naturel.
