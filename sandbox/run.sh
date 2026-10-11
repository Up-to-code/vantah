#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
container="${1:-vantah-demo}"
port="${2:-6081}"
docker build -t vantah:local -f sandbox/Dockerfile .
docker run -d --name "$container" --label org.qentrah.vantah=v0.1.1 --cap-drop ALL --security-opt no-new-privileges \
  --memory 1g --cpus 1 -p "127.0.0.1:$port:6080" vantah:local
printf 'Open http://127.0.0.1:%s/vnc.html?autoconnect=true&resize=remote\n' "$port"
