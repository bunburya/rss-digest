#!/bin/bash

# Run through a sequence of OPML files and generate digests for each. Perform some basic checks to ensure that no fatal
# errors are encountered and that some output is generated (not much output validation is done).

BASE_DIR="../test_data/run/opml_list_test"
CONFIG_DIR="$BASE_DIR/config"
TEMPLATES_DIR="../../templates"
HELPERS_DIR="../../helpers"
DATA_DIR="$BASE_DIR/data"
OUTPUT_DIR="$BASE_DIR/output"
CONFIG_INI="../../config/config.ini"
OUTPUT_INI="../../config/output.ini"

if [ -d "$CONFIG_DIR" ]; then rm -r "$CONFIG_DIR"; fi
if [ -d "$DATA_DIR" ]; then rm -r "$DATA_DIR"; fi
if [ -d "$OUTPUT_DIR" ]; then rm -r "$DATA_DIR"; fi

mkdir -p "$CONFIG_DIR"
cp -r "$TEMPLATES_DIR" "$CONFIG_DIR/"
cp -r "$HELPERS_DIR" "$CONFIG_DIR/"
mkdir -p "$DATA_DIR"
mkdir -p "$OUTPUT_DIR"

cp "$CONFIG_INI" "$CONFIG_DIR/"
cp "$OUTPUT_INI" "$CONFIG_DIR/"


error_codes=0
bad_output=0

while [ -n "$1" ]; do
  echo "Testing $1."
  base="$(basename "$1")"
  profile_name="${base/\.opml/_profile}"
  output_file="$OUTPUT_DIR/${base/\.opml/_plaintext}"
  python ../../rss-digest -c "$CONFIG_DIR" -d "$DATA_DIR" profile add "$profile_name"
  cp "$1" "$CONFIG_DIR/profiles/$profile_name/feeds.opml"
  python ../../rss-digest -c "$CONFIG_DIR" -d "$DATA_DIR" run "$profile_name" > "$output_file"
  status_code=$?
  if [ ! $status_code -eq 0 ]; then
    echo "Status code was $status_code."
    (( error_codes++ ))
  fi
  if [ ! -f "$output_file" ] || [ "$(wc -l < "$output_file")" -le 1 ]; then
    echo "Bad output."
    (( bad_output++ ))
  fi
  shift
done

echo "Fatal errors encountered: $error_codes."
echo "Bad output encountered: $bad_output."
echo "(Not all bad output necessarily detected.)"
