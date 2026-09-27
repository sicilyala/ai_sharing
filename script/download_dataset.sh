#!/usr/bin/env bash
set -euo pipefail

# Usage: cd $(git rev-parse --show-toplevel) && script/download_dataset.sh [--data_path data]
# Output: data/Metro_Interstate_Traffic_Volume.csv (downloaded only when absent)

DATA_PATH="data"
while (($# > 0)); do
  case "$1" in
    --data_path)
      if (($# < 2)) || [[ -z "$2" || "$2" == --* ]]; then
        echo "Missing value for --data_path" >&2
        exit 2
      fi
      DATA_PATH="$2"
      shift 2
      ;;
    *)
      echo "Unsupported argument: $1" >&2
      echo "Supported argument: --data_path VALUE" >&2
      exit 2
      ;;
  esac
done

WORKSPACE_ROOT="$(git rev-parse --show-toplevel)"
if [[ "$DATA_PATH" = /* ]]; then
  DATA_DIR="$DATA_PATH"
else
  DATA_DIR="$WORKSPACE_ROOT/$DATA_PATH"
fi
TARGET_PATH="$DATA_DIR/Metro_Interstate_Traffic_Volume.csv"
if [[ -e "$TARGET_PATH" ]]; then
  echo "Dataset already exists; leaving it unchanged: $TARGET_PATH" >&2
  exit 1
fi

mkdir -p "$DATA_DIR"
ARCHIVE_PATH="$(mktemp /tmp/uci-metro.XXXXXX)"
TEMP_DATA_PATH="$(mktemp "$DATA_DIR/.Metro_Interstate_Traffic_Volume.XXXXXX")"
cleanup() {
  rm -f "$ARCHIVE_PATH" "$TEMP_DATA_PATH"
}
trap cleanup EXIT

curl --fail --location --max-time 60 \
  'https://archive.ics.uci.edu/static/public/492/metro+interstate+traffic+volume.zip' \
  --output "$ARCHIVE_PATH"
unzip -p "$ARCHIVE_PATH" Metro_Interstate_Traffic_Volume.csv.gz | gzip -dc > "$TEMP_DATA_PATH"
mv "$TEMP_DATA_PATH" "$TARGET_PATH"
echo "Downloaded UCI dataset to $TARGET_PATH"
