#!/usr/bin/env bash
# Download LiveKit server and SeaweedFS for Linux/macOS.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OS="$(uname -s | tr '[:upper:]' '[:lower:]')"
ARCH="$(uname -m)"
case "$ARCH" in
  x86_64|amd64) ARCH=amd64 ;;
  arm64|aarch64) ARCH=arm64 ;;
  *) echo "Unsupported arch: $ARCH"; exit 1 ;;
esac
if [[ "$OS" == "darwin" ]]; then GOOS=darwin
elif [[ "$OS" == "linux" ]]; then GOOS=linux
else echo "Unsupported OS: $OS"; exit 1
fi

mkdir -p "$ROOT/bin" "$ROOT/data/seaweed/volume" "$ROOT/data/seaweed/master"

LK_VER="1.13.11"
LK_BIN="$ROOT/bin/livekit-server"
if [[ ! -x "$LK_BIN" ]]; then
  echo "Downloading LiveKit server $LK_VER ($GOOS/$ARCH) ..."
  TMP="$(mktemp -d)"
  curl -fsSL "https://github.com/livekit/livekit/releases/download/v${LK_VER}/livekit_${LK_VER}_${GOOS}_${ARCH}.tar.gz" -o "$TMP/lk.tgz"
  tar -xzf "$TMP/lk.tgz" -C "$TMP"
  cp "$TMP/livekit-server" "$LK_BIN"
  chmod +x "$LK_BIN"
  rm -rf "$TMP"
fi
"$LK_BIN" --version || true

WEED="$ROOT/bin/weed"
if [[ ! -x "$WEED" ]]; then
  echo "Downloading SeaweedFS ($GOOS/$ARCH) ..."
  TMP="$(mktemp -d)"
  curl -fsSL "https://github.com/seaweedfs/seaweedfs/releases/download/3.97/${GOOS}_${ARCH}.tar.gz" -o "$TMP/sw.tgz"
  tar -xzf "$TMP/sw.tgz" -C "$TMP"
  FOUND="$(find "$TMP" -name weed -type f | head -n 1)"
  cp "$FOUND" "$WEED"
  chmod +x "$WEED"
  rm -rf "$TMP"
fi
"$WEED" version || true
echo "Done. LiveKit + weed are in $ROOT/bin"
