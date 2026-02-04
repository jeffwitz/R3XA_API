# Cahier des charges détaillé — Web Editor/Validator pour R3XA (intégré à `R3XA_API`)

## 0) Contexte et objectif

### Contexte

* Dépôt existant : `R3XA_API` (package Python `r3xa_api` + schéma JSON + validate + registry + examples + tests).
* Le dépôt sert de **point de convergence** : API + schéma + registry + (nouveau) web UI.
* Objectif : fournir une **UI web** pour éditer / valider / comprendre des fichiers R3XA, y compris en **batch**, tout en restant compatible avec une évolution vers un usage **site externe** (potentiellement async/websocket).

### Objectif produit (v0)

* Outil utilisable en visio / démo : “on charge un R3XA, on comprend, on édite, on valide, on exporte”.
* Outil utilisable en interne : batch validation, visualisation du schéma, erreurs lisibles.

### Principes non négociables

* ✅ **Le package `r3xa_api` reste la source de vérité** pour :

  * validation (JSON Schema),
  * formatage des erreurs,
  * chargement schéma,
  * (plus tard) normalisation.
* ✅ Le web doit **consommer** ces fonctions (pas les répliquer).
* ✅ La UI doit offrir un **fallback JSON brut** (éditeur texte) même si on a un formulaire guidé.
* ✅ Conception TDD : contrats stables (`ValidationReport`, `SchemaSummary`).

---

## 1) Positionnement dans l’arborescence (avant de coder)

### Recommandation de structure : monorepo multi-composants

On garde le repo `R3XA_API`, on ajoute une UI dans un dossier `web/` **sans transformer le package Python** en monolithe.

#### Arborescence cible

```
R3XA_API/
├─ pyproject.toml                 # package r3xa-api (inchangé)
├─ r3xa_api/
│  ├─ __init__.py
│  ├─ core.py
│  ├─ validate.py
│  ├─ registry.py
│  ├─ resources/
│  │  └─ schema.json
│  └─ webcore/                    # NOUVEAU : logique “web” testable (pure python)
│     ├─ __init__.py
│     ├─ reports.py               # ValidationReport (format stable)
│     ├─ schema_summary.py         # SchemaSummary (format stable)
│     ├─ batch.py                  # batch validate helpers
│     └─ normalize.py              # (optionnel, stub v0)
├─ web/                           # NOUVEAU : application web (outil)
│  ├─ app/                        # backend FastAPI (ASGI)
│  │  ├─ main.py                  # create_app(), routes, mounting static/templates
│  │  ├─ api.py                   # routes /api/*
│  │  ├─ pages.py                 # routes pages HTML
│  │  └─ settings.py              # config (paths, env)
│  ├─ templates/                  # Jinja2 templates
│  ├─ static/                     # CSS/JS (HTMX, editor, etc.)
│  └─ README.md                   # doc usage web
├─ tests/
│  ├─ api/                        # tests r3xa_api (existants + nouveaux)
│  ├─ webcore/                    # tests unitaires reports/summary/batch
│  └─ web/                        # tests API FastAPI + (option) Playwright e2e
├─ examples/
│  ├─ python/
│  └─ artifacts/
├─ Makefile (ou justfile)         # commandes: test, run-web, format, lint
└─ docs/ (si existant)
```

### Pourquoi cette structure ?

* `r3xa_api/webcore/` = logique réutilisable, testable, sans HTTP (TDD facile).
* `web/` = outil UI (peut rester non-packagé au début, ou packagé plus tard).
* `tests/webcore` verrouille les **contrats** dont dépend l’UI.
* Possibilité future : extraire `web/` dans un autre repo sans réécrire le cœur.

### Ce qu’il faut éviter

* ❌ Mettre de la logique de validation/formatage d’erreurs dans `web/app/*` (duplication).
* ❌ Dépendre d’un framework front lourd (React/Vue build) dès v0 (risque d’explosion de scope).
* ❌ Coupler la release PyPI API avec le web : le web est “outil repo” au départ.

---

## 2) Dépendances et packaging

### Backend web

* Framework : **FastAPI** (ASGI)
* Serveur dev : `uvicorn`
* Templates : Jinja2
* Upload : FastAPI `UploadFile`
* Static : served by FastAPI

### Dépendances dans `pyproject.toml`

* Ajouter des extras (recommandé) :

```toml
[project.optional-dependencies]
web = [
  "fastapi>=0.110",
  "uvicorn>=0.27",
  "jinja2>=3.1",
  "python-multipart>=0.0.9"
]
dev = ["pytest>=8", "ruff>=0.6"]
```

Le web est installé via :

* `pip install -e .[web,dev]`

---

## 3) Contrats stables (TDD-first)

### 3.1 ValidationReport (format de sortie stable)

**But** : l’UI ne lit jamais des exceptions brutes `jsonschema`, elle lit un report stable.

```json
{
  "valid": false,
  "errors": [
    {
      "path": "data_sources/0/model",
      "message": "is a required property",
      "validator": "required",
      "schema_path": "#/$defs/data_source_camera/required"
    }
  ]
}
```

Règles :

* `path` : chemin “slash” stable (utiliser `error.path`).
* `schema_path` : idem, stable.
* Toujours un tableau `errors` (vide si valid).

Implémentation : `r3xa_api/webcore/reports.py`

### 3.2 SchemaSummary (résumé stable du schéma)

**But** : afficher et générer des formulaires sans exposer tout le JSON Schema brut.

Format minimal :

```json
{
  "schema_version": "1.0.0",
  "sections": {
    "header": {...},
    "settings": {...},
    "data_sources": {...},
    "data_sets": {...}
  }
}
```

Chaque section doit contenir :

* champs
* type
* required
* enum (si existant)
* description (si existant)
* structure children (objet/array)

Implémentation : `r3xa_api/webcore/schema_summary.py`

---

## 4) Fonctionnalités v0 (obligatoires)

### F1 — Édition (formulaire basé sur schéma + JSON brut)

UI propose 2 modes synchronisés :

* **Mode Form** : édition guidée par sections (schema summary)
* **Mode JSON** : éditeur texte (CodeMirror/Monaco léger, ou textarea v0)

Règles :

* le JSON brut est “source affichée” et peut être copié/collé.
* le formulaire modifie l’objet JSON (JS) et met à jour le JSON brut.
* si JSON brut invalide (parse error), on le signale sans casser.

### F2 — Validation (unitaire)

Bouton “Validate” :

* POST `/api/validate` avec JSON
* retour ValidationReport
* affichage : liste cliquable → scroll vers champ (si possible), sinon highlight path.

### F3 — Batch validation

Page “Batch” :

* upload multi fichiers `.json`
* POST `/api/batch/validate` (multipart)
* réponse : tableau `{filename, valid, error_count, errors_preview}`

Option v0 :

* télécharger un `report.json`
  Option v0+ :
* zip des fichiers valides / invalides séparés

### F4 — Schéma viewer

Page “Schema” :

* affiche SchemaSummary en arborescence
* recherche (filter) par mot-clé (nom champ / description)
* indique required/optional

---

## 5) API web (routes à implémenter)

### `GET /api/schema`

* renvoie `schema.json` brut (pour debug)

### `GET /api/schema/summary`

* renvoie SchemaSummary

### `POST /api/validate`

Input : JSON instance (body)
Output : ValidationReport

### `POST /api/batch/validate`

Input : multipart files[] (json)
Output :

```json
{
  "results": [
    {"filename":"a.json","valid":true,"error_count":0},
    {"filename":"b.json","valid":false,"error_count":2,"errors":[...first2]}
  ]
}
```

---

## 6) UI (Option 1 : templates + HTMX)

### Pages

* `/` : accueil + liens
* `/edit` : éditeur (form + json)
* `/batch` : batch validation
* `/schema` : schema viewer

### Front minimal (v0)

* HTMX pour soumissions/updates
* JS léger pour :

  * synchroniser formulaire ↔ JSON
  * gérer l’éditeur JSON (textarea v0 acceptable)
  * afficher erreurs proprement

---

## 7) Tests (TDD)

### 7.1 Unit tests (webcore)

* `test_validation_report_structure()`
* `test_validation_report_path_format()`
* `test_schema_summary_sections_present()`
* `test_schema_summary_required_fields()`
* `test_batch_validate_mixed_files()`

### 7.2 API tests (FastAPI)

* `test_post_validate_valid()`
* `test_post_validate_invalid()`
* `test_get_schema_summary()`
* `test_batch_validate_endpoint()`

### 7.3 UI tests (option v0+)

* Playwright :

  * upload + validate
  * edit field + validate OK
  * batch validation table appears

---

## 8) Roadmap d’implémentation (ordre recommandé)

1. Ajouter `webcore/reports.py` + tests (contrat ValidationReport)
2. Ajouter `schema_summary.py` + tests
3. Ajouter FastAPI app + endpoints API + tests
4. Ajouter pages templates + interaction basique (textarea JSON)
5. Ajouter formulaire guidé (schema-assisted) section par section
6. Batch UI + export report

---

## 9) Préparation “site externe” (sans l’implémenter)

* FastAPI (ASGI) choisi pour compat websocket
* Prévoir `POST /api/jobs/batch_validate` + polling (v1)
* Websocket réservé à :

  * progress live
  * autosave
  * collaboration (hors scope)

---

## 10) Livrables

* Code dans `web/` + `r3xa_api/webcore/`
* Tests `pytest` passants
* README `web/README.md` :

  * installation
  * `pip install -e .[web,dev]`
  * `uvicorn web.app.main:app --reload`
  * exemples
