#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-or-later
# Build the installable archive of the app: <Name>-<version>.tar.gz with the files its install.sh needs, ready for
#   tar -xzf <Name>-<version>.tar.gz && cd <app>-<version> && ./install.sh
#
#   packaging/build-tarball.sh                      from this checkout, into dist/
#   packaging/build-tarball.sh --source DIR         build another checkout (e.g. a release tag in a worktree)
#   packaging/build-tarball.sh --out DIR            where to write the archive (default: dist/)
#
# The file list is the one of install.sh (FILES, and COMMON_FILES in common/), plus the documentation. The
# archive is reproducible: same sources, same bytes (sorted entries, fixed owner, mtime of the last commit).
set -euo pipefail

NAME="Lectern"
ROOT="$(cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")/.." && pwd)"
SOURCE="$ROOT"
OUT="$ROOT/dist"
while (( $# )); do
    case "$1" in
        --source) SOURCE="$(cd "$2" && pwd)"; shift 2 ;;
        --out) OUT="$2"; shift 2 ;;
        -h|--help) sed -n '2,8p' "$0"; exit 0 ;;
        *) echo "Unknown argument: $1 (see --help)" >&2; exit 1 ;;
    esac
done
mkdir -p "$OUT"
OUT="$(cd "$OUT" && pwd)"

eval "$(grep '^APP_ID=' "$SOURCE/install.sh")"
eval "$(grep '^SCRIPT=' "$SOURCE/install.sh")"
eval "$(sed -n '/^FILES=(/,/)/p' "$SOURCE/install.sh")"
eval "$(sed -n '/^COMMON_FILES=(/,/)$/p' "$SOURCE/install.sh")"
version="$(sed -n 's/^APP_VERSION = "\([^"]*\)".*/\1/p' "$SOURCE/$SCRIPT")"
[[ -n "$version" ]] || { echo "No APP_VERSION in $SOURCE/$SCRIPT" >&2; exit 1; }

# the same paths as in the repository: the app at the top, the kit in common/
paths=("${FILES[@]}" README.md LICENSE CHANGELOG.md docs/troubleshooting.md)
for f in "${COMMON_FILES[@]}"; do
    paths+=("common/$f")
done
for f in "${paths[@]}"; do
    [[ -f "$SOURCE/$f" ]] || { echo "Missing file: $SOURCE/$f" >&2; exit 1; }
done

# Modes from git (755 for the executables, 644 for the rest), not from the disk, where ACLs or a umask could
# change them; without git, the executable bit of the file decides
plain=() executable=()
for f in "${paths[@]}"; do
    mode="$(git -C "$SOURCE" ls-files -s -- "$f" 2>/dev/null | cut -d' ' -f1)"
    if [[ "$mode" == 100755 || ( -z "$mode" && -x "$SOURCE/$f" ) ]]; then
        executable+=("$f")
    else
        plain+=("$f")
    fi
done

top="$APP_ID-$version"
mtime="$(git -C "$SOURCE" log -1 --format=%ct 2>/dev/null || date +%s)"
file_name="${NAME// /-}-$version.tar.gz"
tar_file="$OUT/${file_name%.gz}"
common=(--sort=name --owner=0 --group=0 --numeric-owner --mtime="@$mtime" --transform="s|^|$top/|" -C "$SOURCE")
tar "${common[@]}" --mode=644 -cf "$tar_file" "${plain[@]}"
tar "${common[@]}" --mode=755 -rf "$tar_file" "${executable[@]}"
gzip -n -9 -f "$tar_file"   # replaces the .tar with the .tar.gz
echo "✓ $OUT/$file_name ($(du -h "$OUT/$file_name" | cut -f1))"
