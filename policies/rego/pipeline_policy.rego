# pipeline_policy — hợp nhất ba kiểm soát trên chính pipeline CI:
#  (1) Vệ sinh pipeline (gate 9): workflow phải khai báo `permissions`
#      tường minh ở mức tối thiểu, KHÔNG dùng write-all; action bên thứ
#      ba phải ghim full commit SHA (bài học R9 flagship #1).
#  (2) Cấu hình build an toàn (SSDF PW.9): mọi workflow chạy gate phải
#      có đủ các gate bắt buộc của pack đang bật.
#  (3) Định danh workload (SOC 2 CC6.1 / PCI Req 8 tham chiếu): job chạm
#      vào cloud phải dùng OIDC (id-token: write + audience khai báo),
#      cấm secret cloud dài hạn dạng tên biến tĩnh trong workflow.
#
# Input (JSON chuẩn hoá từ workflow YAML):
#   { "workflows": [ { "file": ".github/workflows/ci.yml",
#       "permissions": {"contents": "read"},
#       "uses": ["actions/checkout@<40-hex-sha>"],
#       "gates_enabled": ["secret","sast","sca","iac"],
#       "jobs": [ {"name": "deploy", "oidc": true,
#                  "static_cloud_secrets": []} ] } ],
#     "config": {"required_gates": ["secret","sast","sca","iac","kev"]} }
package devsecops.pipeline_policy

deny contains msg if {
	w := input.workflows[_]
	w.permissions == "write-all"
	msg := sprintf("workflow %s dung permissions write-all — phai khai bao quyen toi thieu tung job (SSDF PW.9, SOC 2 CC6.1)", [w.file])
}

deny contains msg if {
	w := input.workflows[_]
	w.permissions == null
	msg := sprintf("workflow %s khong khai bao permissions — mac dinh nen tang co the thua quyen; khai bao quyen toi thieu (gate 9)", [w.file])
}

deny contains msg if {
	w := input.workflows[_]
	u := w.uses[_]
	not pinned_to_sha(u)
	msg := sprintf("workflow %s dung action %q chua ghim full commit SHA — rui ro supply chain (gate 9)", [w.file, u])
}

deny contains msg if {
	w := input.workflows[_]
	g := input.config.required_gates[_]
	not g in w.gates_enabled
	msg := sprintf("workflow %s thieu gate bat buoc %q cua pack dang bat (ISO A.8.25-A.8.28, SSDF PW.9)", [w.file, g])
}

deny contains msg if {
	w := input.workflows[_]
	j := w.jobs[_]
	s := j.static_cloud_secrets[_]
	msg := sprintf("workflow %s job %s dung secret cloud tinh %q — phai chuyen sang OIDC federation (PCI Req 8/SOC 2 CC6.1 tham chieu, identity-first)", [w.file, j.name, s])
}

deny contains msg if {
	w := input.workflows[_]
	j := w.jobs[_]
	j.cloud_access == true
	j.oidc != true
	msg := sprintf("workflow %s job %s truy cap cloud nhung khong dung OIDC — cam credential dai han trong CI", [w.file, j.name])
}

# "actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683" → true
pinned_to_sha(u) if {
	parts := split(u, "@")
	count(parts) == 2
	regex.match(`^[0-9a-f]{40}$`, parts[1])
}

# Action nội bộ của chính tổ chức khai báo trong config được miễn ghim SHA.
pinned_to_sha(u) if {
	some prefix in input.config.internal_action_prefixes
	startswith(u, prefix)
}
