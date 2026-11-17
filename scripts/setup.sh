#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/.."

# Keep configuration local to each checkout and preserve existing files.
for app in server client; do
  if [[ -e "$app/.env" || -L "$app/.env" ]]; then
    continue
  fi

  if [[ -n "${ENV_SOURCE:-}" && -f "$ENV_SOURCE/$app/.env" ]]; then
    (umask 077; cp -n "$ENV_SOURCE/$app/.env" "$app/.env")
    echo "Created $app/.env from the configured checkout."
  else
    echo "Missing $app/.env. Set ENV_SOURCE to an absolute path to a configured checkout," >&2
    echo "or copy $app/.env.example to $app/.env and fill in your local credentials." >&2
    exit 1
  fi
done

npm --prefix client ci --legacy-peer-deps
(cd server && uv sync --locked)

echo "Setup complete. Start the client with: cd client && npm start"
echo "Start the server separately with: cd server && uv run application.py"
