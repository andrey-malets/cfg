#!/usr/bin/env bash

CUR=$(dirname "$0")
BASE="$CUR/.."
CFGDIR=$BASE/cfg
export CFG=$CFGDIR/conf.yaml

output=$(tempfile)
config=$(tempfile)

cp "$CUR/nagios_prefix.cfg" "$config"
echo "cfg_file=$output" >> "$config"

chmod o+r "$output" "$config"

python "$BASE/main.py" nagios "$CFGDIR/nagios.template" > "$output"
/usr/bin/env nagios3 -v "$config"
rv=$?

rm "$output" "$config"
exit "$rv"
