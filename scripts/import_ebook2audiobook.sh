#!/usr/bin/env bash
set -e

# Simple helper to copy selected parts of a cloned `ebook2audiobook` repo into
# the project. By default this script will not duplicate the full upstream
# repository but can copy the `lib` folder into the integration area if desired.

ROOT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
THIRD="$ROOT_DIR/third_party/ebook2audiobook"
DEST="$ROOT_DIR/src/podcastforge/integrations/ebook2audiobook/third_party_lib"

echo "Import helper: checking for cloned repo at: $THIRD"
if [ ! -d "$THIRD" ]; then
  echo "Repository not found in third_party; aborting. Run setup.sh to clone first." >&2
  exit 1
fi

if [ -d "$DEST" ]; then
  echo "Destination already exists: $DEST";
  echo "If you want to refresh, remove it first and re-run this script.";
  exit 0
fi

echo "Copying selected files from $THIRD/lib to $DEST ..."
mkdir -p "$DEST"
cp -r "$THIRD/lib"/* "$DEST/"

echo "Copy complete. Note: prefer using the runtime wrapper at src/podcastforge/integrations/ebook2audiobook/__init__.py which imports the cloned lib directly from third_party.")

echo "Done."
