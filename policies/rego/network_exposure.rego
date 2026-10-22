# network_exposure — không security group nào được mở ingress từ Internet
# (0.0.0.0/0 hoặc ::/0) tới cổng quản trị hoặc cổng ứng dụng không phải
# cổng web công khai chuẩn (80/443 trên SG gắn với load balancer công khai
# vẫn phải giới hạn theo allowed CIDR của tổ chức — pack v1 chặn mọi
# 0.0.0.0/0 ingress ngoài cổng 443 có khai báo `public_web: true`).
#
# Input (JSON chuẩn hoá từ Terraform plan hoặc trích xuất HCL — xem
# harness/build_workload_fixtures.py):
#   { "security_groups": [ { "name": "...", "public_web": false,
#       "ingress": [ {"from_port": 22, "to_port": 22, "protocol": "tcp",
#                     "cidr_blocks": ["0.0.0.0/0"],
#                     "security_groups": []} ] } ] }
package devsecops.network_exposure

world_cidrs := {"0.0.0.0/0", "::/0"}

deny contains msg if {
	sg := input.security_groups[_]
	rule := sg.ingress[_]
	cidr := rule.cidr_blocks[_]
	world_cidrs[cidr]
	not public_web_exception(sg, rule)
	msg := sprintf("security group %q mo ingress tu %s toi cong %d-%d (mo phong PLANTED flaw #3 / SOC 2 CC6.6, PCI DSS Req 2, NIST PR.AC/PR.DS)", [sg.name, cidr, rule.from_port, rule.to_port])
}

# Ngoại lệ duy nhất: SG khai báo public_web=true VÀ rule chỉ mở đúng cổng 443.
public_web_exception(sg, rule) if {
	sg.public_web == true
	rule.from_port == 443
	rule.to_port == 443
}
