# Releasing `ticktick-cli`

This project uses the standard minimal Python packaging flow with a small `Makefile`:

1. bump version in `pyproject.toml`
2. run release checks
3. commit and tag
4. publish to TestPyPI/PyPI
5. verify installed package

No custom release script is required.

## Prerequisites

- Python 3.11+
- Access to this repository with push rights
- PyPI token (`pypi-...`) for `ticktick-cli`

Install dev + release tooling:

```bash
python3 -m pip install -e ".[dev,release]"
```

Set Twine credentials:

```bash
export TWINE_USERNAME=__token__
export TWINE_PASSWORD=pypi-REDACTED
```

## 1) Bump version

Edit `[project].version` in `pyproject.toml` to the release version (for example `0.2.1`).

## 2) Validate and build

From a clean `main` branch:

```bash
make release-check
```

This runs:

- `make test`
- `make build`
- `make dist-check`

## 3) Commit and tag

```bash
git add pyproject.toml
git commit -m "release: vX.Y.Z"
git tag -a vX.Y.Z -m "Release vX.Y.Z"
git push origin main --tags
```

Use the exact version from `pyproject.toml`.

## 4) Publish (manual step)

Optional smoke test on TestPyPI first:

```bash
make publish-testpypi
```

Publish to PyPI:

```bash
make publish-pypi
```

## 5) Post-release verification

Install from PyPI in a clean virtual env:

```bash
python3 -m pip install --upgrade ticktick-cli
ticktick --version
```
