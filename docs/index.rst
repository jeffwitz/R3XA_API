R3XA_API Documentation
======================

Environment assumption
----------------------
Documentation commands assume a local virtual environment exists at ``.venv`` (project root).

Create it once from the project root:

.. code-block:: bash

   python -m venv .venv

Activate it:

.. code-block:: bash

   # Linux / macOS
   source .venv/bin/activate

   # Windows (PowerShell)
   .venv\Scripts\Activate.ps1

Then upgrade ``pip``:

.. code-block:: bash

   python -m pip install --upgrade pip

Once the environment is activated, the documented ``python ...`` commands are the
same across Linux, macOS, and Windows.

Bootstrap the full contributor environment with one command:

.. code-block:: bash

   python scripts/dev.py setup-dev

This installs the editable contributor stack (``dev``, ``docs``, ``web``,
``notebook``, ``graph_nx``) and regenerates the schema-derived
artifacts tracked in the repository.

.. raw:: html

   <iframe
     src="presentation_swiper.html"
     width="100%"
     height="520"
     style="border:1px solid #ddd; margin-bottom: 16px;"
     title="JC Passieux presentation (PM_IDICS_2024)"
   ></iframe>

R3XA: Toward a metadata standard for experimental (photo)mechanics datasets - Jean-Charles Passieux *et al.* PM-IDICS 2024

.. image:: figures/R3XA.png
   :width: 140
   :alt: R3XA logo

Credits and origin
------------------
- Initial implementation by **E. Roubin**, based on a shared specification led by **J‑C. Passieux**.
- Original upstream repository: ``https://gitlab.com/photomechanics/r3xa``
- Current public repository: ``https://gitlab.com/photomechanics/R3XA_API``

Installation profiles
---------------------
Choose one profile from the project root, inside ``.venv``:

- **Install everything** — all optional Python features in one command:

  .. code-block:: bash

     pip install -e ".[dev,docs,web,notebook,graph_nx]"

  The standard SDK dependency set includes the Python ``graphviz`` wrapper,
  the bundled Graphviz WebAssembly module, and ``wasmtime``. The system
  Graphviz executable (``dot``) is optional and is only needed by the native
  ``graphviz`` backend:

  .. warning::

     This installs all Python extras, but it does **not** install the optional Graphviz executable ``dot``.
     Install it only if you explicitly select the native ``graphviz`` backend:

     - Linux: ``sudo apt-get install graphviz``
     - macOS: ``r3xa-ensure-graphviz`` (Homebrew)
     - Windows: ``r3xa-ensure-graphviz`` (WinGet or Chocolatey)

  The standard installation includes the Python WebAssembly runtime. Select
  the ``graphviz-wasm`` backend when a system ``dot`` executable is not
  available; it uses the bundled Graphviz WASI module and does not invoke a
  system executable.

- **Core SDK** — create and validate JSON files:

  .. code-block:: bash

     pip install -e .

  Graph support is included in this default installation through the bundled
  WebAssembly backend. The system executable is optional; install it only for
  the native ``graphviz`` backend.

 - **Object-first SDK** — IDE autocompletion comes from generated Pydantic models:

  .. code-block:: bash

     pip install -e .

- **Web UI** — run the FastAPI editor and validator:

  .. code-block:: bash

     pip install -e ".[web]"
     python scripts/dev.py run-web --port 8002

- **Notebook** — run the Marimo notebook example:

  .. code-block:: bash

     pip install -e ".[notebook]"
     python scripts/dev.py notebook-dic

- **Static graph rendering** — enable the optional NetworkX/Matplotlib renderer outside the WebUI:

  .. code-block:: bash

     pip install -e ".[graph_nx]"

- **Contributor setup** — install the full local stack:

  .. code-block:: bash

     python scripts/dev.py setup-dev

  If you only want the dependencies without regeneration, the equivalent install is:

  .. code-block:: bash

     pip install -e ".[dev,docs,web,notebook,graph_nx]"

.. note::

   The default WebAssembly backend needs no system Graphviz installation.
   ``pip install r3xa-api`` cannot install system software, so if you select
   the native ``graphviz`` backend, install ``dot`` with
   ``r3xa-ensure-graphviz`` on Windows/macOS or your Linux package manager.
   See :doc:`web` and :doc:`notebooks` for details.

Web UI
------
The optional web interface is documented here: :doc:`web`.

Quick links
-----------
- **Tutorials**: :doc:`notebooks`, :doc:`qi_case`
- **How-to guides**: :doc:`examples`, :doc:`registry_web`, :doc:`DEPLOY_RAILWAY`
- **Explanation**: :doc:`overview`, :doc:`engineering_contract`
- **Reference**: :doc:`api`, :doc:`specification`, :doc:`validation`, :doc:`matlab`, :doc:`web`, :doc:`dev_workflow`

Common workflows
----------------
If you do not want to read the whole documentation, start from one of these three workflows:

- **Learn the library interactively** — start with :doc:`notebooks`.
- **Study a full worked case** — continue with :doc:`qi_case`.
- **Create a new R3XA file** — use ``R3XAFile`` with the guided helpers documented in :doc:`api`.
- **Load, edit, and save an existing file** — see :doc:`api` and ``examples/python/load_edit_save.py``.
- **Reuse or create registry items** — use ``Registry`` and ``RegistryItem``, documented in :doc:`api` and demonstrated in ``examples/python/create_registry_camera.py`` and ``examples/python/registry_discovery.py``.

.. toctree::
   :maxdepth: 2
   :caption: Tutorials

   notebooks.md
   qi_case.md

.. toctree::
   :maxdepth: 2
   :caption: How-to guides

   examples.md
   registry_web.md
   DEPLOY_RAILWAY.md

.. toctree::
   :maxdepth: 2
   :caption: Explanation

   overview.md
   engineering_contract.md

.. toctree::
   :maxdepth: 2
   :caption: Reference

   api.md
   specification.md
   typed_models.md
   matlab.md
   validation.md
   web.md
   static_web.md
   dev_workflow.md
