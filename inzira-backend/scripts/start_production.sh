#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

echo "=== Inzira production start ==="

export INZIRA_DATA_DIR="${INZIRA_DATA_DIR:-/tmp/inzira}"
export HOME="${HOME:-/home/user}"
export USER="${USER:-user}"
export TORCHINDUCTOR_CACHE_DIR="${TORCHINDUCTOR_CACHE_DIR:-/tmp/torch-cache}"
export TORCH_COMPILE_DISABLE=1
mkdir -p "$INZIRA_DATA_DIR" "$TORCHINDUCTOR_CACHE_DIR" "$HOME"

# Asset zip /tmp may keep an older registry — always prefer the image bundle.
if [ -f "registry.db" ]; then
  cp -f registry.db "$INZIRA_DATA_DIR/registry.db"
  echo "[assets] Applied image registry.db -> $INZIRA_DATA_DIR/registry.db ($(wc -c < registry.db) bytes)"
else
  echo "[assets] WARNING: /app/registry.db missing from image — check .dockerignore"
fi

# Download assets first (needs Hub access for HF dataset)
python scripts/download_deploy_assets.py || exit 1

# Re-apply AFTER asset extract (zip can overwrite DATA_DIR/registry.db with the old 132-row DB).
if [ -f "registry.db" ]; then
  cp -f registry.db "$INZIRA_DATA_DIR/registry.db"
  echo "[assets] Re-applied image registry.db after assets step"
fi

# Defense in depth: never ship fake demo analytics into the live impact counters.
python -c "
import os, sqlite3
from pathlib import Path
reg=Path(os.environ['INZIRA_DATA_DIR'])/'registry.db'
con=sqlite3.connect(str(reg))
tables={r[0] for r in con.execute(\"SELECT name FROM sqlite_master WHERE type='table'\")}
if 'search_events' in tables:
    n=con.execute('SELECT COUNT(*) FROM search_events').fetchone()[0]
    # Cap accidental demo dumps (>10k in an empty prod is never real yet).
    if n >= 10000:
        con.execute('DELETE FROM search_events')
        con.commit()
        print(f'[assets] Cleared suspicious demo search_events ({n} rows)')
con.close()
" || true

python -c "
import os, sqlite3
from pathlib import Path
d=os.environ['INZIRA_DATA_DIR']
p=Path(d)/'models/bert_classifier/config.json'
assert p.is_file(), f'missing {p}'
reg=Path(d)/'registry.db'
assert reg.is_file(), f'missing {reg}'
n=sqlite3.connect(str(reg)).execute('SELECT COUNT(*) FROM opportunities').fetchone()[0]
print('[assets] verified', p, 'registry_opportunities=', n)
min_n=int(os.getenv('INZIRA_MIN_REGISTRY_OPPS','200'))
assert n >= min_n, f'registry too small ({n} < {min_n}) — seeded registry.db did not take effect'
" || exit 1

# Offline mode after bundle is local — blocks accidental Hub calls during inference
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1

if [ -n "${DATABASE_URL:-}" ]; then
  echo "Running database migrations..."
  python -m alembic -c alembic.ini upgrade head
fi

PORT="${PORT:-8000}"
echo "Starting uvicorn on 0.0.0.0:${PORT}"
exec python -m uvicorn main:app --host 0.0.0.0 --port "$PORT"
