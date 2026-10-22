# change_record — hồ sơ thay đổi cho một release/merge vào nhánh bảo vệ
# phải đủ: (1) có phê duyệt PR của người khác tác giả; (2) mọi gate bắt
# buộc đã chạy và đạt (hoặc có ngoại lệ được duyệt còn hạn); (3) có liên
# kết bằng chứng. Thiếu bất kỳ mục nào → release chưa đủ điều kiện.
# Đây là policy quyết định trên dữ liệu hồ sơ thay đổi mà gate/evidence
# collector (M3/M4) sinh ra — phục vụ ISO A.8.32, PCI DSS Req 6.5,
# SOC 2 CC8.1 (ánh xạ tham chiếu).
#
# Input:
#   { "change": { "id": "PR-123", "target_branch": "release",
#                 "author": "dev1", "approvals": ["lead1"],
#                 "gate_results": {"secret": "pass", "sast": "pass"},
#                 "evidence_links": ["evidence://run/456"],
#                 "exceptions": [] },
#     "config": {"required_gates": ["secret","sast","sca"],
#                "protected_branches": ["main","release"]} }
package devsecops.change_record

deny contains msg if {
	c := input.change
	c.target_branch in input.config.protected_branches
	count(c.approvals) == 0
	msg := sprintf("thay doi %s vao nhanh bao ve %s chua co phe duyet PR (A.8.32 / PCI 6.5 / SOC 2 CC8.1)", [c.id, c.target_branch])
}

deny contains msg if {
	c := input.change
	c.author in c.approvals
	msg := sprintf("thay doi %s tu phe duyet boi chinh tac gia %s — cam self-approval", [c.id, c.author])
}

deny contains msg if {
	c := input.change
	g := input.config.required_gates[_]
	c.gate_results[g] != "pass"
	not exception_active(c, g)
	msg := sprintf("thay doi %s: gate bat buoc %q chua dat (trang thai: %v)", [c.id, g, object.get(c.gate_results, g, "missing")])
}

deny contains msg if {
	c := input.change
	c.target_branch in input.config.protected_branches
	count(c.evidence_links) == 0
	msg := sprintf("thay doi %s chua co lien ket bang chung — evidence collector phai gom truoc khi release", [c.id])
}

exception_active(c, gate) if {
	e := c.exceptions[_]
	e.gate == gate
	e.expires >= input.today
}
