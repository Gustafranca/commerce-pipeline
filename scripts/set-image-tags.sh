#!/usr/bin/env bash
# Usage: scripts/set-image-tags.sh <git-sha-or-tag>
# Rewrites image tags in k8s/overlays/staging/kustomization.yaml (and optionally prod).
set -euo pipefail
TAG="${1:?usage: $0 <tag-or-sha>}"

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
STAGING="$ROOT/k8s/overlays/staging/kustomization.yaml"

if [[ ! -f "$STAGING" ]]; then
  echo "missing $STAGING" >&2
  exit 1
fi

tmp="$(mktemp)"
awk -v tag="$TAG" '
  /newTag:/ { sub(/newTag: .*/, "newTag: " tag) }
  { print }
' "$STAGING" > "$tmp"
mv "$tmp" "$STAGING"

echo "Updated $STAGING to newTag: $TAG"
