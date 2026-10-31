#!/usr/bin/env bash
# Python 3.15 has no upstream PyYAML wheel. Build its hash-pinned pure-Python distribution explicitly,
# without credentials, in a disposable environment whose backend wheels are also hash-pinned.
set -euo pipefail
work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT
source_url=https://files.pythonhosted.org/packages/05/8e/961c0007c59b8dd7729d542c61a4d537767a59645b82a0b521206e1e25c2/pyyaml-6.0.3.tar.gz
source_sha=d76623373421df22fb4cf8817020cbb7ef15c725b9d5e45f17e189bfc384190f
curl --fail --silent --show-error --location --proto '=https' --proto-redir '=https' \
  "$source_url" --output "$work/pyyaml-6.0.3.tar.gz"
printf '%s  %s\n' "$source_sha" "$work/pyyaml-6.0.3.tar.gz" | shasum -a 256 --check --status
uv venv --python "${UV_PYTHON:-3.15}" "$work/backend"
uv pip install --python "$work/backend/bin/python" --no-build --require-hashes \
  --requirements "$(dirname "$0")/pyyaml-build-requirements.txt"
unset PYYAML_FORCE_CYTHON
PYYAML_FORCE_LIBYAML=0 uv build --wheel --no-build-isolation --python "$work/backend/bin/python" \
  --out-dir "$work/dist" "$work/pyyaml-6.0.3.tar.gz"
uv pip install --python .venv/bin/python --no-build --no-deps "$work"/dist/*.whl
