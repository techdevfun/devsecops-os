# secret_findings — chính sách quyết định trên KẾT QUẢ quét secret.
#
# Lý do chọn cơ chế này (không phải policy trên code trực tiếp): phát hiện
# secret là việc của scanner chuyên dụng (gitleaks — gate 1). Policy này là
# lớp quyết định: bất kỳ finding secret nào chưa hết hạn allowlist đều
# CHẶN. Đầu vào là JSON chuẩn hoá từ kết quả quét (gitleaks JSON hoặc bộ
# trích xuất tương đương trong harness), nên thay scanner không đổi policy.
#
# Input:
#   { "findings": [ { "file": "backend/config.py", "line": 18,
#                     "rule": "generic-api-key", "match_preview": "sk_live_...",
#                     "allowlisted_until": null } ],
#     "scan_date": "2026-10-22" }
package devsecops.secret_findings

deny contains msg if {
	f := input.findings[_]
	not allowlist_active(f)
	msg := sprintf("secret chua allowlist tai %s:%d (rule %s) — phai go bo va xoay vong credential (ISO A.8.28, PCI DSS Req 6/8 tham chieu)", [f.file, f.line, f.rule])
}

allowlist_active(f) if {
	f.allowlisted_until != null
	f.allowlisted_until >= input.scan_date
}
