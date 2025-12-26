#!/usr/bin/env bash
set -e

# Resolve project root (parent of scripts/)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

DATA_DIR="${PROJECT_ROOT}/data"
URL="https://www.research-collection.ethz.ch/bitstreams/7b2419c1-62b5-4714-b7f8-485e5fe3e5fe/download"
ARCHIVE="euroc_mav_dataset.zip"

mkdir -p "${DATA_DIR}"
cd "${DATA_DIR}"

echo "[INFO] Downloading EuRoC MAV dataset..."
wget -O "${ARCHIVE}" "${URL}"

echo "[INFO] Extracting..."
unzip -q "${ARCHIVE}"

echo "[INFO] Done. Dataset is in ${DATA_DIR}"
