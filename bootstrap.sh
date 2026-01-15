#!/bin/bash
set -e

REPO_URL="${REPO_URL:-https://github.com/USER/REPO.git}"
INSTALL_DIR="/tmp/kiosk-install"

if [ "$EUID" -ne 0 ]; then
    echo "Bu script root olarak calistirilmali!"
    echo "Kullanim: curl -sSL URL | sudo bash"
    exit 1
fi

echo "Kiosk MVP indiriliyor..."

apt-get update -qq
apt-get install -y -qq git

rm -rf "$INSTALL_DIR"
git clone --depth 1 "$REPO_URL" "$INSTALL_DIR"

cd "$INSTALL_DIR"
chmod +x install.sh
./install.sh

rm -rf "$INSTALL_DIR"

echo "Kurulum tamamlandi!"
