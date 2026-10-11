#!/bin/sh
# vAntah v0.1.1: download, verify, and start the isolated Docker desktop.
set -eu
version=v0.1.1
repo=Up-to-code/vantah
container=${VANTAH_CONTAINER:-vantah-demo}
port=${VANTAH_PORT:-6081}
install_dir=${VANTAH_INSTALL_DIR:-${XDG_DATA_HOME:-$HOME/.local/share}/vantah/releases/$version}
for dependency in docker curl tar; do
  command -v "$dependency" >/dev/null 2>&1 || { printf 'vAntah requires %s. Install it and retry.\n' "$dependency" >&2; exit 1; }
done
docker info >/dev/null 2>&1 || { printf 'Start your Docker engine and retry.\n' >&2; exit 1; }
case "$port" in ''|*[!0-9]*) printf 'VANTAH_PORT must be a TCP port number.\n' >&2; exit 1;; esac
[ "$port" -ge 1 ] && [ "$port" -le 65535 ] || { printf 'VANTAH_PORT must be 1–65535.\n' >&2; exit 1; }
case "$container" in ''|*[!A-Za-z0-9_.-]*) printf 'Invalid VANTAH_CONTAINER name.\n' >&2; exit 1;; esac
if docker container inspect "$container" >/dev/null 2>&1; then
  label=$(docker inspect --format '{{index .Config.Labels "org.qentrah.vantah"}}' "$container")
  [ "$label" = "$version" ] || { printf 'Container %s already exists. Set VANTAH_CONTAINER to a new name.\n' "$container" >&2; exit 1; }
  docker start "$container" >/dev/null
  mapping=$(docker port "$container" 6080/tcp)
  port=${mapping#127.0.0.1:}
  printf 'vAntah is running. Open http://127.0.0.1:%s/vnc.html?autoconnect=true&resize=remote\n' "$port"
  exit 0
fi
temp_dir=$(mktemp -d)
trap 'rm -rf "$temp_dir"' EXIT
trap 'exit 1' HUP INT TERM
archive=vantah-$version.tar.gz
base=https://github.com/$repo/releases/download/$version
curl -fL --retry 3 "$base/$archive" -o "$temp_dir/$archive"
curl -fL --retry 3 "$base/SHA256SUMS" -o "$temp_dir/SHA256SUMS"
expected=$(awk -v name="$archive" '$2 == name { print $1 }' "$temp_dir/SHA256SUMS")
if command -v sha256sum >/dev/null 2>&1; then
  actual=$(sha256sum "$temp_dir/$archive" | awk '{print $1}')
elif command -v shasum >/dev/null 2>&1; then
  actual=$(shasum -a 256 "$temp_dir/$archive" | awk '{print $1}')
else
  printf 'Install sha256sum or shasum to verify the download.\n' >&2; exit 1
fi
[ -n "$expected" ] && [ "$actual" = "$expected" ] || { printf 'Download checksum mismatch.\n' >&2; exit 1; }
mkdir -p "$install_dir"
tar -xzf "$temp_dir/$archive" -C "$install_dir" --strip-components=1
sh "$install_dir/sandbox/run.sh" "$container" "$port"
