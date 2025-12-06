#!/bin/bash
# Pre-deployment cache busting update
# Run this before deploying to ensure all static file versions are updated

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "🚀 Pre-deployment checks..."
echo ""

# Run cache busting update
echo "📦 Updating cache busting versions..."
cd "$PROJECT_ROOT"
python3 scripts/update_cache_bust.py

echo ""
echo "✅ Pre-deployment checks complete!"
