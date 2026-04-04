# Engineering Contract — user and developer requirements

This page is **explanation documentation**.
Use it to understand the engineering choices, stability rules, and maintenance constraints behind the public API.

This document explains **how to use R3XA_API correctly** and **why some engineering decisions were made**.

It targets two audiences:

- **User perspective**: you want to create, load, validate, and save R3XA files without worrying about the internal implementation.
- **Developer perspective**: you want to evolve the schema, the Python API, the documentation, or the surrounding tooling without breaking existing workflows.

The goal is not only to describe the current code. The goal is to make the **contract** explicit between:

- the R3XA schema,
- the Python library,
- the documentation,
- and the users.


## 1. Project goals

R3XA_API must serve four roles at the same time:

1. **Allow creation of valid R3XA files**.
2. **Allow loading and editing of existing files**.
3. **Allow reuse of registry items** (cameras, specimens, software, dataset templates).
4. **Remain aligned with the official R3XA schema**, which is the source of truth for the data model.

In practice, this imposes a balance:

- a simple API for users,
- an architecture strict enough for developers to evolve the project safely,
- and documentation that clearly explains **what is stable**, **what is recommended**, and **what is only compatibility support**.


## 2. User perspective — what matters in practice

### 2.1. There is a recommended public API surface

For normal users, the API to remember is intentionally limited.

The recommended entry points are:

- `R3XAFile`
- `Registry`
- `RegistryItem`
- `new_item(...)`
- `unit(...)`
- `data_set_file(...)`
- `validate(...)`
- the guided helpers `add_<kind>_setting(...)`, `add_<kind>_source(...)`, `add_<kind>_data_set(...)`

The rule is simple:

- **if it is documented in `docs/api.md`, it is supported API**;
- **if it is not documented there, it should not be considered a primary entry point**.

### 2.2. The recommended full-file workflow is `load -> edit -> validate/save`

For a complete R3XA file, the intended workflow is:

```python
from r3xa_api import R3XAFile

r3xa = R3XAFile.load("experiment.json")
r3xa.set_header(title="Updated title")
r3xa.save("experiment_updated.json")
```

This is not a cosmetic choice. It answers a usability problem:

- `save(...)` already existed;
- a symmetric `load(...)` was therefore expected;
- a user should not have to write `json.load(...)` and then `R3XAFile.from_dict(...)` for such a common task.

### 2.3. The registry is used in two different ways

There are two valid registry workflows:

1. **I only want a validated dictionary**  
   → use `Registry.load(...)` or `Registry.load_validated(...)`

2. **I want to manipulate an item as an object, then merge, validate, or save it**  
   → use `Registry.get_item(...)`

Example:

```python
from r3xa_api import Registry

registry = Registry("registry")

camera_dict = registry.load("data_sources/camera/avt_dolphin_f145b")
camera_item = registry.get_item("data_sources/camera/avt_dolphin_f145b")
camera_item = camera_item.merge(description="Camera used in experiment 01")
camera_item.save("camera_exp01.json")
```

This distinction exists to avoid reducing everything to bare `dict` values while keeping a simple access path when a dictionary is enough.

### 2.4. Why `RegistryItem` was introduced

Without `RegistryItem`, operations such as `merge`, `validate`, or `save` had to be called through free functions detached from the item itself.

Older style:

```python
merged = merge_item(item, id="new_id")
save_item("path.json", merged)
```

Current style:

```python
item = registry.get_item("data_sources/camera/avt_dolphin_f145b")
item = item.merge(id="new_id")
item.save("path.json")
```

The second style is simpler for users because the important operations are attached to the object they are manipulating.

### 2.5. Guided helpers exist to speed up file creation

R3XA_API provides helpers such as:

- `add_camera_source(...)`
- `add_specimen_setting(...)`
- `add_generic_data_set(...)`

They exist to avoid two common mistakes:

- forgetting the `kind`,
- writing incomplete fields relative to the schema.

The current contract is:

- there is a guided helper for each `kind` supported by the runtime schema;
- required fields are derived from the schema;
- helper names follow a stable rule in `1.x`.

### 2.6. Compatibility helpers still exist, but they are no longer the recommended path

Some functions still exist for compatibility:

- `load_item(...)`
- `save_item(...)`
- `load_item_path(...)`
- `save_item_path(...)`
- `validate_item(...)`
- `merge_item(...)`
- `Registry.get(...)`
- `Registry.get_validated(...)`

They remain usable during the `1.x` series, but they are no longer the preferred entry points for new code.

The practical rule is:

- **new code** → use `load(...)`, `load_validated(...)`, `get_item(...)`, `RegistryItem`
- **older code** → remains supported without immediate breakage

### 2.7. Validation is not optional in the project philosophy

R3XA_API is built around a JSON schema. Validation guarantees:

- presence of required fields,
- type consistency,
- interoperability of metadata,
- reuse of files by other teams.

This matters for the community: a file that is “almost correct” is not sufficient if the goal is reproducibility.

### 2.8. Typing and IDE autocompletion are optional, but useful

The core API remains **dict-based**. This is intentional:

- it is lightweight,
- robust,
- easy to serialize to JSON,
- and compatible with many environments.

But the project also provides:

- generated typed Pydantic models (`r3xa_api/models.py`),
- and a stub file `r3xa_api/core.pyi` that makes guided helpers visible to IDEs.

For users, the key point is:

- **it is not mandatory**;
- **it significantly improves comfort in VS Code / PyCharm / mypy / pyright**.


## 3. Developer perspective — what must be respected

### 3.1. The source of truth is not this repository

The R3XA schema is not edited “first” inside `R3XA_API`.

The source of truth is the **`R3XA_SPEC`** repository:

- `schema-full.json` = editorial source
- `schema.json` = generated runtime schema

Only then does `R3XA_API` embed a frozen runtime copy in:

- `r3xa_api/resources/schema.json`

This separation is fundamental:

- `R3XA_SPEC` owns the standard;
- `R3XA_API` owns a versioned Python implementation of that standard.

### 3.2. Why the API does not depend on the spec repository at runtime

It would be tempting to say: “just read the schema directly from `R3XA_SPEC`”.

That would be the wrong design for several reasons:

- `pip install .` must remain self-contained;
- Binder, the docs, the tests, and the web UI must work without a neighboring repository;
- a given `R3XA_API` release must support **one precise schema version**, not a moving target.

The correct workflow is therefore:

1. edit `R3XA_SPEC`
2. regenerate the runtime schema
3. sync that runtime schema into `R3XA_API`
4. regenerate everything that depends on it

### 3.3. When the schema changes, several derived artifacts must change too

A schema update does not affect only `schema.json`.

It must be propagated to:

- `r3xa_api/resources/schema.json`
- `docs/specification.md`
- `r3xa_api/models.py` (typed models)
- `r3xa_api/core.pyi` (IDE stub for guided helpers)
- runtime guided helpers
- examples
- tests

In other words: the schema is the source of truth, but there are several **derived products** that must remain synchronized.

### 3.4. Why the `.pyi` file exists

Guided helpers on `R3XAFile` exist at runtime, but they are created dynamically from the schema.

Without a stub:

- IDEs have trouble seeing these methods,
- autocompletion is incomplete,
- static analysis does not know which signatures to expose.

The file `r3xa_api/core.pyi` solves this:

- it changes **nothing** at runtime;
- it exists only for static tooling;
- it exposes the signatures that IDEs should see.

The file `r3xa_api/py.typed` additionally declares that the package officially ships typing information.

### 3.5. Why guided helpers are not yet implemented as static Python methods

Today, guided helpers are still generated dynamically.

This is not a bug.

It is a reasonable `1.x` compromise:

- the schema drives the helpers,
- behavior is tested,
- the `.pyi` stub already provides good IDE ergonomics.

The limitation is mostly on the maintenance side:

- debugging is less pleasant,
- the architecture is less “normal” for Python developers,
- implementation-level static analysis remains limited.

This is a **known technical debt**, not an urgent defect.

### 3.6. Why the top-level API surface was reduced

The `r3xa_api` module should no longer be treated as a catch-all namespace.

The goal is that a user immediately understands what is stable and recommended.

We therefore separate:

- **recommended public surface**
- **compatibility helpers**
- **internal or specialized helpers**

This serves two purposes:

1. reduce noise for new users;
2. prevent internal details from becoming “public by accident”.

### 3.7. Stability policy for the `1.x` series

The project follows a pragmatic policy:

- what is documented in `docs/api.md` is part of the public contract;
- compatibility helpers remain available during `1.x`;
- they must not disappear abruptly before `2.0`;
- `main` and release tags (`v1.x.y`, etc.) carry stable releases;
- `develop` carries preparation work for the next version.

In short:

- `main` = stable
- `develop` = ongoing work

### 3.8. What developers must do before a release

Before publishing:

1. verify that the runtime schema is the intended one;
2. regenerate models if needed:
   - `make generate-models`
3. regenerate IDE stubs if needed:
   - `make generate-stubs`
4. regenerate the specification page:
   - `make generate-spec`
5. run the tests:
   - `./.venv/bin/pytest -q`
6. rebuild the docs:
   - `./docs/build.sh`

This is not bureaucracy. It is the mechanism that prevents silent drift between:

- schema,
- code,
- docs,
- examples,
- tooling.


## 4. Common misunderstandings

### “Why keep a dict-based API if Pydantic exists?”

Because Pydantic and the dict-based API do not serve the same purpose.

- the dict API is the simple, robust runtime foundation;
- Pydantic provides editing comfort and typing;
- the two layers can coexist without replacing each other.

### “Why is the helper called `unit()` if the object contains more than a unit?”

The name is not perfect semantically.

But:

- it is already deeply established in the API,
- it matches `kind="unit"` in the schema,
- renaming it abruptly would cost more than it would bring.

The correct `1.x` strategy is therefore stability, not renaming for its own sake.

### “Why keep some helpers if they are no longer recommended?”

Because a serious API does not break existing users abruptly.

Keeping compatibility aliases during the `1.x` series makes it possible to improve the library without punishing historical usage patterns.


## 5. Structural decisions to keep in mind

### For users

- use the documented workflows first;
- use stable tags (`v1.x.y`, for example the latest stable release tag) if you want a frozen behavior;
- treat `develop` as a preparation branch, not as a release.

### For developers

- do not edit the editorial schema first in `R3XA_API`;
- do not make a function “public” just because it is importable;
- do not mix compatibility, recommended API, and internal logic;
- do not allow schema, docs, models, stubs, and examples to drift apart.


## 6. Operational summary

### User perspective

If you are starting with the library, remember this:

- `R3XAFile` for full files
- `Registry` / `RegistryItem` for registry items
- `validate()` for checking correctness
- `load()` / `save()` for reading and writing
- `add_<kind>_...` helpers to move faster

### Developer perspective

If you are evolving the project, remember this:

- `R3XA_SPEC` is the schema source of truth
- `R3XA_API` embeds a versioned runtime snapshot
- models, documentation spec pages, and stubs are schema-derived artifacts
- the public API is a contract, not a side effect of the code base
