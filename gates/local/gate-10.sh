#!/usr/bin/env bash
# Gate 10 — AI PR Review Gate (the factory's flagship #1).
# OFF BY DEFAULT in phase 1 (blueprint section 5.3): only enabled once flagship #1 passes
# its own publish gate (re-measured on the real repo to standard + a new
# publish order from the owner). Phase-1 acceptance runs with this gate off —
# when off, this script only records the state and exits 0, producing NO
# pr-review-report evidence (per the M2 pack map: that evidence type
# only exists when the gate is on).
# Enable with: ENABLE_AI_PR_REVIEW=true (locally) / the workflow's enable_ai_pr_review
# input. Even when enabled in phase 1, flagship #1 is not published yet, so the gate
# only runs at placeholder-declaration level with a clear warning — it does not block.
source "$(dirname "$0")/lib.sh"
gate_begin 10 ai-pr-review

if [ "${ENABLE_AI_PR_REVIEW:-false}" != "true" ]; then
  echo "[gate 10] OFF (phase 1 default) — flagship #1 is not published yet;" \
       "the PR-layer slot is kept empty per the check-run/SARIF interface."
  printf '%s\n' \
    "gate 10 (AI PR Review Gate): disabled by default in phase 1." \
    "Flagship #1 is not published yet; phase-1 acceptance runs with" \
    "this gate OFF (blueprint section 5.3)." \
    > "$GATE_OUT/disabled-note.txt"
  exit 0
fi

echo "[gate 10] WARNING: enabled manually but flagship #1 is NOT" \
     "published yet — no artefact to run; the gate skips at declaration level" \
     "(report-only placeholder), it does not block."
printf '%s\n' \
  "gate 10 enabled manually, but flagship #1 (ai-pr-review-gate) is" \
  "not published yet — no runnable artefact. Placeholder pass," \
  "report-only, NOT a review result." \
  > "$GATE_OUT/enabled-placeholder-note.txt"
exit 0
