#!/usr/bin/env bash
set -euo pipefail
PLAYCORE_BUNDLE_DIR="$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
if ! command -v python3 >/dev/null 2>&1; then
    echo 'No se encuentra python3. Este paquete necesita Python 3.11 o posterior.' >&2
    exit 1
fi
exec python3 -I "$PLAYCORE_BUNDLE_DIR/instalar.py" "$@"
