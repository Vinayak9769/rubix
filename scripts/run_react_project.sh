#!/usr/bin/env zsh
# scripts/run_react_project.sh

set -eo pipefail
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
export PATH="/home/vin/.nvm/versions/node/v23.3.0/bin:$PATH"

#if [ -z "$1" ]; then
#  echo "Error: GitHub URL required" >&2
#  exit 1
#fi

GITHUB_URL="https://github.com/Vinayak9769/mprsem3.git"
TEMP_DIR=$(mktemp -d)
PROJECT_DIR="$TEMP_DIR/react-project"
cleanup() {
  echo "Cleaning up..."
  pkill -f "npm run dev"
  rm -rf "$TEMP_DIR"
}
trap cleanup EXIT
echo "🚀 Cloning repository..."
git clone "$GITHUB_URL" "$PROJECT_DIR"
echo "🔍 Verifying structure..."
if [ ! -f "$PROJECT_DIR/package.json" ]; then
  echo "❌ Error: No package.json found" >&2
  exit 1
fi
echo "📦 Installing dependencies..."
(cd "$PROJECT_DIR" && npm install --silent)
echo "⚡ Starting development server..."
(cd "$PROJECT_DIR" && npm run dev) | while IFS= read -r line; do
  echo "   $line"
done
wait
