# Rapport de validation — `examples/essai-torsion.json`

Date: 2026-02-11

## Contexte

Le fichier testé est:

- `examples/essai-torsion.json`

Le validateur utilisé est celui de `R3XA_API`:

- `r3xa_api/validate.py`
- schéma chargé par défaut via `r3xa_api/resources/schema.json`

Vérification complémentaire:

- `examples/schema_JC.json` est identique au schéma actif (`r3xa_api/resources/schema.json`) au moment du test.

## Commande utilisée

```bash
cd /home/jeff/Code/R3XA/R3XA_API
python - <<'PY'
import json
from pathlib import Path
from r3xa_api.validate import validate
import jsonschema

p = Path("examples/essai-torsion.json")
obj = json.loads(p.read_text(encoding="utf-8"))
try:
    validate(obj)
    print("VALID")
except jsonschema.exceptions.ValidationError as e:
    print(str(e))
PY
```

## Résultat

Le fichier est **non valide** avec le schéma courant.

Deux erreurs principales sont remontées:

1. `data_sources/0` invalide
2. `data_sources/1` invalide

## Détail des erreurs bloquantes

### 1) `data_sources/0` (`kind: data_sources/generic`)

Objet concerné:

- `examples/essai-torsion.json:64`

Propriétés bloquantes:

- `capacity` à `examples/essai-torsion.json:79`
- `uncertainty` à `examples/essai-torsion.json:84`

Cause:

- Pour `data_sources/generic`, ces propriétés sont considérées comme `additionalProperties` non autorisées dans le schéma actuel.

Message clé:

> Additional properties are not allowed ('capacity', 'uncertainty' were unexpected) of data_sources/generic

### 2) `data_sources/1` (`kind: data_sources/generic`)

Objet concerné:

- `examples/essai-torsion.json:92`

Propriété bloquante:

- `uncertainty` à `examples/essai-torsion.json:107`

Cause:

- Pour `data_sources/generic`, `uncertainty` n’est pas autorisé dans le schéma actuel.

Message clé:

> Additional properties are not allowed ('uncertainty' was unexpected) of data_sources/generic

## Conclusion technique

Le JSON n’est pas compatible **en l’état** avec le schéma actif.

Le problème n’est pas sur la structure globale du fichier R3XA, mais sur le typage/attributs de deux `data_sources` déclarés en `generic` avec des champs (`capacity`, `uncertainty`) qui ne sont pas permis pour ce type.

## Pistes de correction

Option A (correctif minimal):

- Conserver `kind: data_sources/generic`
- Retirer les champs non autorisés (`capacity`, `uncertainty`) pour ces deux objets.

Option B (sémantique capteur plus riche):

- Reclasser ces sources vers un type de `data_sources/*` qui autorise explicitement ces métadonnées (si pertinent dans le schéma), puis compléter les champs requis de ce type.

Option C (évolution de schéma):

- Étendre le schéma pour autoriser `capacity` / `uncertainty` sur `data_sources/generic` si c’est une convention souhaitée à long terme.

## Mise à jour — 2026-04-04

Statut actuel :

- **VALID**

La cause de l’invalidité originale — refus de `capacity` et `uncertainty` sur `data_sources/generic` — a été résolue par l’évolution du schéma en version **1.3.3**.

Le choix retenu correspond à l’**option C** du rapport original :

- évolution du schéma pour autoriser `uncertainty` sur `data_sources/generic`

Le fichier est désormais couvert par un test automatisé :

- `tests/test_examples.py::test_essai_torsion_validates`

Validation confirmée contre le schéma `2024.7.1` embarqué dans :

- `r3xa_api/resources/schema.json`
