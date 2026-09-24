# Edit a Registry item in the browser

Open the [public Registry editor](https://photomechanics.gitlab.io/R3XA_API/registry/)
to create or validate a reusable item. This is a browser-local workspace, not
a publishing interface for the canonical
[R3XA_REGISTRY](https://gitlab.com/photomechanics/R3XA_REGISTRY) repository.

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

1. Open `/registry/` on the public site.
2. Either click **Load JSON** to import an item without filling in missing
   values, or create a new illustrative item from an **Example profile**.
3. Choose the item kind from the schema catalogue if necessary.
4. Edit fields in the generated form or in the Expert JSON view.
5. Click **Validate item** to check the item against its own kind schema.
6. Click **Add to local registry** to reuse a valid item in this browser.
7. Click **Save JSON** to export it.

The `id` field includes **Generate new ID**. It creates a unique identifier with
the conventional section prefix (`stg-`, `src-`, or `set-`) and checks the
templates already stored in this browser. Saving a local item is also refused
when its identifier or title would duplicate another local item. Updating the
same item with the same identifier and title remains allowed.

Creating an example fills scalar, unit, file and nested-object fields with
domain-specific illustrative values (for example, a camera exposure is shown as
`0.01 s`, a focal length as `25 mm`, and a load-cell capacity as `10 kN`).
Importing an existing item does not fill its missing fields automatically.
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

New IDs use kind-specific prefixes such as `src-camera-...`. Legacy IDs and
references should be reviewed when importing older items.

## Share a reusable item

The reusable Registry is maintained in the separate `R3XA_REGISTRY` repository,
which is the canonical source for shareable items. The `registry/` directory in
this repository contains a small bundled example and test catalogue for the SDK
and WebUI; it is not an independent Registry publication. The API CI validates
the canonical Registry against the schema and SDK used by the current branch.

Use **Save JSON** to export the item, then contribute it separately to
`R3XA_REGISTRY` if it should be shared. For full-document editing and
graph export, see [Using the WebUI](web.md). For the static build and
deployment, see [Static WebUI build and deployment](static_web.md).
