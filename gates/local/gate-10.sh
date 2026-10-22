#!/usr/bin/env bash
# Gate 10 — AI PR Review Gate (flagship #1 của nhà máy).
# MẶC ĐỊNH TẮT ở pha 1 (blueprint mục 5.3): chỉ bật khi flagship #1 qua
# cổng publish riêng của nó (đo lại trên repo thật đạt chuẩn + lệnh
# publish mới của chủ sở hữu). Nghiệm thu pha 1 chạy khi gate này tắt —
# script này khi tắt chỉ ghi nhận trạng thái và thoát 0, KHÔNG sinh
# evidence pr-review-report (theo bản đồ pack M2: loại bằng chứng đó
# chỉ tồn tại khi gate bật).
# Bật bằng: ENABLE_AI_PR_REVIEW=true (cục bộ) / input enable_ai_pr_review
# của workflow. Kể cả khi bật ở pha 1, flagship #1 chưa publish nên gate
# chỉ chạy ở mức khai báo placeholder và cảnh báo rõ — không chặn.
source "$(dirname "$0")/lib.sh"
gate_begin 10 ai-pr-review

if [ "${ENABLE_AI_PR_REVIEW:-false}" != "true" ]; then
  echo "[gate 10] TẮT (mặc định pha 1) — flagship #1 chưa publish;" \
       "vị trí cắm ở tầng PR giữ trống theo giao diện check-run/SARIF."
  printf '%s\n' \
    "gate 10 (AI PR Review Gate): disabled by default in phase 1." \
    "Flagship #1 is not published yet; phase-1 acceptance runs with" \
    "this gate OFF (blueprint section 5.3)." \
    > "$GATE_OUT/disabled-note.txt"
  exit 0
fi

echo "[gate 10] CẢNH BÁO: được bật thủ công nhưng flagship #1 CHƯA" \
     "publish — không có artefact để chạy; gate bỏ qua ở mức khai báo" \
     "(report-only placeholder), không chặn."
printf '%s\n' \
  "gate 10 enabled manually, but flagship #1 (ai-pr-review-gate) is" \
  "not published yet — no runnable artefact. Placeholder pass," \
  "report-only, NOT a review result." \
  > "$GATE_OUT/enabled-placeholder-note.txt"
exit 0
