# drift_control — kết quả kiểm tra drift (cấu hình thực tế lệch khỏi
# IaC khai báo) theo lịch: drift trên tài nguyên trọng yếu (network,
# IAM, storage) chưa được xác nhận/xử lý trong hạn cấu hình thì CHẶN
# kỳ báo cáo. Policy quyết định trên báo cáo drift mà job IaC scan/drift
# (gate 4 mở rộng) sinh ra — phục vụ SOC 2 CC7.1–CC7.2 (ánh xạ tham
# chiếu).
#
# Input:
#   { "report_date": "2026-10-22",
#     "drift_items": [ {"resource": "aws_security_group.app",
#                       "category": "network", "detected_on": "2026-10-20",
#                       "acknowledged": false, "ticket": null} ],
#     "config": {"sla_days": 7,
#                "critical_categories": ["network","iam","storage"]} }
package devsecops.drift_control

deny contains msg if {
	d := input.drift_items[_]
	d.category in input.config.critical_categories
	not d.acknowledged
	age_days(d) > input.config.sla_days
	msg := sprintf("drift tren %s (%s) phat hien %s, chua xu ly sau %d ngay (SLA %d) — SOC 2 CC7.2", [d.resource, d.category, d.detected_on, age_days(d), input.config.sla_days])
}

deny contains msg if {
	d := input.drift_items[_]
	d.category in input.config.critical_categories
	d.acknowledged == true
	object.get(d, "ticket", null) == null
	msg := sprintf("drift tren %s da acknowledge nhung chua co ticket xu ly", [d.resource])
}

age_days(d) := (time.parse_rfc3339_ns(sprintf("%sT00:00:00Z", [input.report_date])) - time.parse_rfc3339_ns(sprintf("%sT00:00:00Z", [d.detected_on]))) / 86400000000000
