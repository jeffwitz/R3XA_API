# Registry Web Editor

This page documents the dedicated web page for registry work in `R3XA_API`.

## Why a dedicated page

The standard editor (`/edit`) targets full R3XA documents.  
Registry work usually targets **single reusable items** (for example one camera or one specimen).

The `/registry` page focuses on that use case:

- load a local JSON item,
- edit it in-place,
- validate it against the item schema definition,
- save it back locally.

## Route

- `GET /registry`

## Validation API

- `POST /api/registry/validate`
  - payload accepts:
    - `{ "item": { ... } }`
    - or `{ "item": { ... }, "kind": "data_sources/camera" }` to force schema target
  - response:
    - `{ "valid": true, "errors": [] }`
    - or `{ "valid": false, "errors": ["..."] }`

## Local workflow

1. Open `/registry`.
2. Click **Load JSON** to import an existing registry item.
3. Optionally set **Kind override** when a strict target is needed.
4. Click **Validate item**.
5. Click **Save JSON** to export the updated item.

Draft state is stored in browser local storage under a dedicated key (`r3xaRegistryDraft`).

## Relation to existing web docs

The general web architecture and deployment details are still documented in:

- `docs/web.md`
- `docs/DEPLOY_RAILWAY.md`
- The standalone offline export is available from `/schema` (button: `Export standalone HTML`).

Use this page as an extension of the main web UI documentation.
