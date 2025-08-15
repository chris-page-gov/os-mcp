#!/usr/bin/env bash
set -euo pipefail
# Simple guard against committing raw ${env:...} or ${{ ... }} placeholders in shell scripts
# that would trip `set -u` (for ${env:...}) or are unintended GitHub Actions style tokens.
# Allowable patterns for env placeholders:
#   1. Escaped form: \${env:VAR}
#   2. Assigned to a placeholder var: PLACEHOLDER='${env:VAR}'
# Raw GitHub Actions interpolation patterns (`${{`) are always flagged; escape as \${{ if literal.
# Any disallowed occurrence triggers a non‑zero exit with a message.

fail=0
# Collect shell scripts tracked by git (so we don't scan venvs, etc.)
while IFS= read -r file; do
  while IFS= read -r line; do
    # Check for VS Code env pattern
    if [[ "$line" == *'${env:'* ]]; then
      # Allowed if escaped
      if [[ "$line" =~ \\\$\{env: ]]; then
        :
      # Allowed if placeholder assignment
      elif [[ "$line" =~ PLACEHOLDER=.*\$\{env: ]]; then
        :
      else
  echo "[check_env_placeholders] Disallowed unescaped \${env: pattern in $file:" >&2
        printf '  %s\n' "$line" >&2
        fail=1
      fi
    fi

    # Check for raw GitHub Actions style pattern
    if [[ "$line" == *'${{'* ]]; then
      if [[ "$line" =~ \\\$\{\{ ]]; then
        :
      else
  echo "[check_env_placeholders] Disallowed raw GitHub Actions style interpolation in $file:" >&2
        printf '  %s\n' "$line" >&2
        fail=1
      fi
    fi
  done < "$file"
done < <(git ls-files '*.sh')

if [[ $fail -ne 0 ]]; then
  echo "[check_env_placeholders] One or more issues found. Fix or escape \${env:...} and \${{ ... }} usages." >&2
  exit 1
fi

echo "[check_env_placeholders] OK (no unsafe \${env:...} or \${{ ... }} patterns)."
