# license_policy — license của dependency (đọc từ SBOM) thuộc danh sách
# cấm của tổ chức thì CHẶN; license chưa xác định thì cảnh báo bắt buộc
# rà soát (không chặn ở pack v1).
#
# Input:
#   { "components": [ {"name": "...", "version": "...",
#                      "license": "MIT"} ],
#     "config": {"denied_licenses": ["GPL-3.0-only", "AGPL-3.0-only"]} }
package devsecops.license_policy

default denied := {"GPL-3.0-only", "GPL-3.0-or-later", "AGPL-3.0-only", "AGPL-3.0-or-later", "SSPL-1.0"}

denied := {l | some l in input.config.denied_licenses} if {
	input.config.denied_licenses != null
}

deny contains msg if {
	c := input.components[_]
	denied[c.license]
	msg := sprintf("component %s@%s dung license bi cam %s — thay the hoac xin phe duyet ngoai le (ISO A.5.19-A.5.22 tham chieu)", [c.name, c.version, c.license])
}

warn contains msg if {
	c := input.components[_]
	c.license == "NOASSERTION"
	msg := sprintf("component %s@%s chua xac dinh duoc license — can ra soat thu cong truoc release", [c.name, c.version])
}
