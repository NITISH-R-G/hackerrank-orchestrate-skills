#!/usr/bin/env sh
# Install the Orchestrate skills into an agent's skills folder.
#
#   scripts/install-skills.sh                 # Claude Code: ~/.claude/skills
#   scripts/install-skills.sh --dest DIR      # any other harness's skills folder
#
# Copies every skills/<name>/ folder. Existing folders with the same name are
# replaced. Nothing outside those folders is touched.
set -eu

here="$(cd "$(dirname "$0")/.." && pwd)"
dest="${HOME}/.claude/skills"

while [ $# -gt 0 ]; do
  case "$1" in
    --dest) dest="$2"; shift 2 ;;
    -h|--help) sed -n '2,8p' "$0"; exit 0 ;;
    *) echo "unknown argument: $1" >&2; exit 2 ;;
  esac
done

mkdir -p "$dest"
for src in "$here"/skills/*/; do
  name="$(basename "$src")"
  rm -rf "${dest:?}/${name:?}"
  cp -r "$src" "$dest/$name"
  echo "installed $name -> $dest/$name"
done
echo "done. ${dest} now has $(ls -d "$dest"/orchestrate* | wc -l) orchestrate skills."
