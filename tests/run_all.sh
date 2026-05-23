#!/usr/bin/env bash
# Run every bundle smoke test. Exit code is the count of failing tests.
#
# Usage:
#   bash tests/run_all.sh
#
# The harness is intentionally minimal — no pytest, no fixtures framework,
# just plain python3 + shell. This keeps the test surface obvious to
# anyone auditing the tree months from now.

set -u

here="$(cd "$(dirname "$0")" && pwd)"
cd "$here/.."

pass=0
fail=0
total=0
failed_names=()

# Find smoke tests at any depth under tests/ — previously only one level of
# nesting was searched, which silently dropped any test placed deeper.
while IFS= read -r t; do
    [ -f "$t" ] || continue
    total=$((total + 1))
    name="$(basename "$t")"
    echo "=== running $name ==="
    if python3 "$t"; then
        pass=$((pass + 1))
    else
        fail=$((fail + 1))
        failed_names+=("$name")
        echo "FAIL: $name"
    fi
    echo
done < <(find tests -type f -name 'smoke_*.py' | sort)

echo "---"
echo "$pass/$total PASS"
if [ "$fail" -ne 0 ]; then
    echo "failing: ${failed_names[*]}"
fi
exit "$fail"
