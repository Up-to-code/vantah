#!/bin/sh
# Build the current KWin desktop from source in an isolated Docker container.
set -eu
for tool in git docker; do
  command -v "$tool" >/dev/null 2>&1 || { printf 'Install %s first.\n' "$tool" >&2; exit 1; }
done
docker info >/dev/null 2>&1 || { printf 'Start Docker first.\n' >&2; exit 1; }
container=${VANTAH_CONTAINER:-vantah-current}
port=${VANTAH_PORT:-6081}
case "$container" in ''|*[!A-Za-z0-9_.-]*) echo 'Invalid container name' >&2; exit 1;; esac
case "$port" in ''|*[!0-9]*) echo 'Invalid port' >&2; exit 1;; esac
[ "$port" -ge 1 ] && [ "$port" -le 65535 ] || { echo 'Port must be 1–65535' >&2; exit 1; }
if docker container inspect "$container" >/dev/null 2>&1; then
  label=$(docker inspect --format '{{index .Config.Labels "org.qentrah.vantah"}}' "$container")
  [ "$label" = current ] || { echo 'Name already belongs to another container; set VANTAH_CONTAINER.' >&2; exit 1; }
  docker start "$container" >/dev/null
  docker port "$container" 6080/tcp
  printf 'Open the listed localhost port with /vnc.html?autoconnect=true&resize=scale\n'
  exit 0
fi
source_dir=$(mktemp -d)
trap 'rm -rf "$source_dir"' EXIT
trap 'exit 1' HUP INT TERM
git clone --depth 1 https://github.com/Up-to-code/vantah.git "$source_dir"
sh "$source_dir/sandbox/run.sh" "$container" "$port"
