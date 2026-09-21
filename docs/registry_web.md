# Registry Web Editor

This page documents the dedicated web page for registry work in `R3XA_API`.

## Why a dedicated page

The standard editor (`/edit`) targets full R3XA documents.  
Registry work usually targets **single reusable items** (for example one camera or one specimen).

The `/registry` page focuses on that use case:

- load a local JSON item,
- choose its schema `kind`,
- edit it through a schema-generated form or the Expert JSON view,
- validate it against the item schema definition,
- save it back locally,
- keep it as a browser-local template for reuse in the document editor.

## Route

- `GET /registry`

## Validation

The server-backed page uses `POST /api/registry/validate`. The static WebUI uses
the same schema catalogue and generated JavaScript validator locally, without
uploading the item.

The validation report distinguishes JSON syntax errors from schema errors and
shows the affected JSON path when available.

## Local workflow

1. Open `/registry`.
2. Click **Load JSON** to import an existing registry item.
3. Choose the item kind from the schema catalogue if necessary.
4. Choose an **Example profile** to populate the fields with realistic values from a Guided workflow.
5. Edit common fields in the generated form, or use the highlighted Expert JSON view.
6. Click **Validate item** to run the lint and schema validation.
7. Click **Add to local registry** to make a valid item available as a template in this browser.
8. Click **Save JSON** to export the updated item.

The `id` field includes **Generate new ID**. It creates a unique identifier with
the conventional section prefix (`stg-`, `src-`, or `set-`) and checks the
templates already stored in this browser. Saving a local item is also refused
when its identifier or title would duplicate another local item. Updating the
same item with the same identifier and title remains allowed.

The generated example fills scalar, unit, file and nested-object fields with
domain-specific illustrative values (for example, a camera exposure is shown as
`0.01 s`, a focal length as `25 mm`, and a load-cell capacity as `10 kN`). Older
browser drafts containing generic placeholders are upgraded when the page opens.
Relationship lists remain empty unless the selected profile provides real
relationships, because inventing identifiers for other objects would make the
example misleading.

The form and JSON views share one document. Fields not exposed by the form are
preserved when another form field is edited, so expert extensions are not
silently discarded.

Draft state is stored in browser local storage under a dedicated key (`r3xaRegistryDraft`).
Local registry templates are stored under `r3xaLocalRegistryItems`. They remain on
the current browser and are not published to `R3XA_REGISTRY`. The static runtime
does not send them to a server; the server-backed runtime may send the current
item to its validation endpoint when **Validate item** is clicked. Adding a
template to an R3XA document creates a new local copy with a new identifier, so
the registry item itself is never modified.

When local storage contains an older identifier such as `ds_cam_legacy`, the
Registry editor migrates it to the canonical kind-specific form such as
`src-camera-...` and updates local references where necessary.

## Relation to existing web docs

The reusable Registry is maintained in the separate `R3XA_REGISTRY` repository,
which is the canonical source for shareable items. The `registry/` directory in
this repository contains a small bundled example and test catalogue for the SDK
and WebUI; it is not an independent Registry publication. The API CI validates
the canonical Registry against the schema and SDK used by the current branch.

The general web architecture and deployment details are still documented in:

- `docs/web.md`
- `docs/DEPLOY_RAILWAY.md`
- The standalone offline export is available from `/schema` (button: `Export standalone HTML`).

Use this page as an extension of the main web UI documentation.
