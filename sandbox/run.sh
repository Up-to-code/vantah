#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
container="${1:-alpine-glass-demo}"
port="${2:-6081}"
docker build -t alpine-glass-shell:local -f sandbox/Dockerfile .
docker run -d --name "$container" --cap-drop ALL --security-opt no-new-privileges \
  --memory 1g --cpus 1 -p "127.0.0.1:$port:6080" alpine-glass-shell:local
printf 'Open http://127.0.0.1:%s/vnc.html?autoconnect=true&resize=remote\n' "$port"
