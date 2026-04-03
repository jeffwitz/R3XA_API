R3XA_API Documentation
======================

Environment assumption
----------------------
Documentation commands assume a local virtual environment exists at ``.venv`` (project root).

Create it once from the project root:

.. code-block:: bash

   python3 -m venv .venv
   source .venv/bin/activate
   python -m pip install --upgrade pip

On Windows, activate it with:

.. code-block:: bat

   .venv\Scripts\activate

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
- Original repository: ``https://gitlab.com/photomecanics/r3xa``

Installation profiles
---------------------
Choose one profile from the project root, inside ``.venv``:

- **Install everything** — all optional Python features in one command:

  .. code-block:: bash

     pip install -e ".[dev,typed,web,notebook,graph_nx]"

  .. warning::

     This installs all Python extras, but it does **not** install the Graphviz executable ``dot``.
     If you want SVG graph generation in the web UI or notebook, install Graphviz at system level too:

     - Linux: ``sudo apt-get install graphviz``
     - macOS: ``brew install graphviz``
     - Windows: install from ``https://graphviz.org/download/`` and make sure ``dot`` is in ``PATH``

- **Core SDK** — create and validate JSON files:

  .. code-block:: bash

     pip install -e .

- **Typed SDK** — add IDE autocompletion with generated Pydantic models:

  .. code-block:: bash

     pip install -e ".[typed]"

- **Web UI** — run the FastAPI editor and validator:

  .. code-block:: bash

     pip install -e ".[web]"
     ./.venv/bin/uvicorn web.app.main:app --reload --port 8002

- **Notebook** — run the Marimo notebook example:

  .. code-block:: bash

     pip install -e ".[notebook]"
     ./.venv/bin/marimo edit examples/notebooks/dic_base_marimo.py

- **Static graph fallback** — enable the optional NetworkX/Matplotlib renderer:

  .. code-block:: bash

     pip install -e ".[graph_nx]"

- **Contributor setup** — install the full local stack:

  .. code-block:: bash

     pip install -e ".[dev,typed,web,notebook,graph_nx]"

.. warning::

   SVG graph generation depends on the Graphviz executable ``dot``.
   The Python package ``graphviz`` alone is **not sufficient**.
   See :doc:`web` and :doc:`notebooks` for details.

Web UI
------
The optional web interface is documented here: :doc:`web`.

Quick links
-----------
- :doc:`overview`
- :doc:`examples`
- :doc:`notebooks`
- :doc:`matlab`
- :doc:`validation`
- :doc:`web`
- :doc:`DEPLOY_RAILWAY`
- :doc:`dev_workflow`

Common workflows
----------------
If you do not want to read the whole documentation, start from one of these three workflows:

- **Create a new R3XA file** — use ``R3XAFile`` with the guided helpers documented in :doc:`api`.
- **Load, edit, and save an existing file** — see :doc:`api` and ``examples/python/load_edit_save.py``.
- **Reuse or create registry items** — use ``Registry`` and ``RegistryItem``, documented in :doc:`api` and demonstrated in ``examples/python/create_registry_camera.py`` and ``examples/python/registry_discovery.py``.

.. toctree::
   :maxdepth: 2
   :caption: Contents

   overview.md
   api.md
   specification.md
   typed_models.md
   matlab.md
   examples.md
   notebooks.md
   qi_case.md
   validation.md
   web.md
   registry_web.md
   DEPLOY_RAILWAY.md
   dev_workflow.md
