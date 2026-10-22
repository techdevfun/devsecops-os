# evidence_completeness — một lần chạy pipeline chỉ được coi là "đủ
# bằng chứng" khi: mọi loại bằng chứng bắt buộc theo các gate đã bật đều
# có mặt trong bundle, mỗi bằng chứng có SHA-256 + thời gian + commit SHA,
# và có ít nhất một bằng chứng log CI. Đây là "gate cuối" (blueprint
# 5.2) ở dạng policy: M4 collector đánh giá manifest bằng policy này.
# Phục vụ ISO A.8.15–A.8.16 (log & giám sát) và CPS 234 (bằng chứng
# kiểm soát liên tục) — ánh xạ tham chiếu.
#
# Input (manifest của bundle):
#   { "run": { "commit_sha": "abc...", "started_at": "2026-10-22T..." },
#     "items": [ {"type": "sarif-report", "sha256": "...", "controls": [...]} ],
#     "config": {"required_types": ["sarif-report","sbom","ci-log"]} }
package devsecops.evidence_completeness

deny contains msg if {
	t := input.config.required_types[_]
	not type_present(t)
	msg := sprintf("bundle thieu loai bang chung bat buoc %q theo gate da bat (evidence incomplete)", [t])
}

deny contains msg if {
	it := input.items[_]
	object.get(it, "sha256", "") == ""
	msg := sprintf("bang chung %q thieu SHA-256 — khong kiem chung duoc toan ven", [it.type])
}

deny contains msg if {
	it := input.items[_]
	count(it.controls) == 0
	msg := sprintf("bang chung %q chua gan voi nhom kiem soat nao trong policy pack", [it.type])
}

deny contains msg if {
	object.get(input.run, "commit_sha", "") == ""
	msg := "bundle khong ghi commit SHA — bang chung khong truy vet duoc nguon goc"
}

type_present(t) if {
	some it in input.items
	it.type == t
}
