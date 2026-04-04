.PHONY: docs generate-spec generate-models generate-stubs notebook-dic notebook-dic-export clean-artifacts source-archive

PYTHON ?= python3

generate-spec:
	$(PYTHON) tools/generate_spec.py \
		r3xa_api/resources/schema.json \
		docs/specification.md

docs: generate-spec
	./docs/build.sh

generate-models:
	./.venv/bin/datamodel-codegen \
		--input r3xa_api/resources/schema.json \
		--input-file-type jsonschema \
		--output r3xa_api/models.py \
		--use-standard-collections \
		--target-python-version 3.10 \
		--field-constraints \
		--output-model-type pydantic_v2.BaseModel \
		--class-name R3XADocument \
		--disable-timestamp \
		--no-use-union-operator
	./.venv/bin/python scripts/postprocess_models.py

generate-stubs:
	$(PYTHON) scripts/generate_core_stub.py

notebook-dic:
	./.venv/bin/marimo edit examples/notebooks/dic_base_marimo.py

notebook-dic-export:
	./.venv/bin/marimo export html examples/notebooks/dic_base_marimo.py -o docs/figures/dic_base_marimo/index.html --force

clean-artifacts:
	rm -rf docs/_build web/node_modules build dist .pytest_cache .mypy_cache .ruff_cache htmlcov .coverage
	find . -type d -name "__pycache__" -prune -exec rm -rf {} +
	find . -type f -name "*.py[co]" -delete
	find . -maxdepth 2 -type d -name "*.egg-info" -prune -exec rm -rf {} +

source-archive:
	mkdir -p archives
	git archive --format=zip --output archives/R3XA_API-source.zip HEAD
