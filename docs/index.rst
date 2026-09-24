R3XA API documentation
======================

R3XA describes experimental and computational photomechanics data in a JSON
document. This repository provides the Python SDK, a MATLAB binding, and a
browser editor for creating, validating, and visualising those documents.

**Start in the browser:** `Open the public R3XA WebUI
<https://photomechanics.gitlab.io/R3XA_API/>`_. The GitLab Pages version runs
entirely in the browser: editing, validation, Registry items, and graphs do not
send your document to an application server. See :doc:`web` for the workflow.

**Start in Python:** follow :doc:`getting_started`, then the progressive
:doc:`notebooks`. If you already know the API and need to accomplish a
particular task, use :doc:`examples`.

The three repositories have distinct responsibilities:

* `R3XA_SPEC <https://gitlab.com/photomechanics/R3XA_SPEC>`_ defines the
  normative JSON Schema.
* `R3XA_API <https://gitlab.com/photomechanics/R3XA_API>`_ derives the SDK,
  validators, WebUI catalogues, and documentation from that schema.
* `R3XA_REGISTRY <https://gitlab.com/photomechanics/R3XA_REGISTRY>`_ maintains
  shareable, validated items. Browser-local Registry items remain private to
  that browser unless you export them.

This documentation follows the Diátaxis distinction: **tutorials** teach a
workflow, **how-to guides** solve a specific task, **explanations** describe
the design, and **reference** pages list exact contracts. Maintained source
examples live only in `examples/tutorials/` and `examples/cases/`. Generated
JSON and graph outputs are kept separately in `artifacts/examples/`.

.. toctree::
   :maxdepth: 2
   :caption: Start here

   getting_started.md

.. toctree::
   :maxdepth: 2
   :caption: Learn

   notebooks.md
   qi_case.md

.. toctree::
   :maxdepth: 2
   :caption: Do a task

   web.md
   registry_web.md
   examples.md

.. toctree::
   :maxdepth: 2
   :caption: Understand

   overview.md
   typed_models.md

.. toctree::
   :maxdepth: 2
   :caption: Reference

   api.md
   specification.md
   validation.md
   matlab.md

.. toctree::
   :maxdepth: 2
   :caption: Maintain and deploy

   static_web.md
   dev_workflow.md
   graphviz_wasm_development.md
   engineering_contract.md
