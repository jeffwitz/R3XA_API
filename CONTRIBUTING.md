# Contributing

Thanks for your interest in improving R3XA_API!

## Development setup
```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install -e ".[dev,docs]"
```

## Run tests
```bash
python -m pytest
```

## Build docs
```bash
python scripts/dev.py build-docs
```

## Style
- Keep changes minimal and focused.
- Update docs/examples when you add features.

## License
By contributing, you agree that your changes are licensed under **GPL-2.0-or-later**.
