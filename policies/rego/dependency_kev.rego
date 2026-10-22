# dependency_kev — dependency dính CVE thuộc CISA KEV (đang bị khai thác
# thật) hoặc EPSS >= ngưỡng thì CHẶN; CVE còn lại chỉ cảnh báo (chống
# alert fatigue — quyết định chặn thuộc gate 8, dữ liệu quét thuộc gate 3).
#
# Input:
#   { "dependencies": [ {"name": "starlette", "version": "1.0.0",
#                        "ecosystem": "pip"} ],
#     "vulnerabilities": [ {"id": "CVE-2026-48710", "package": "starlette",
#                            "affected": ">=0.8.3,<1.0.1", "fixed": "1.0.1",
#                            "in_kev": true, "epss": 0.42} ],
#     "config": {"epss_threshold": 0.5} }
package devsecops.dependency_kev

default epss_threshold := 0.5

epss_threshold := input.config.epss_threshold if {
	input.config.epss_threshold != null
}

deny contains msg if {
	d := input.dependencies[_]
	v := input.vulnerabilities[_]
	v.package == d.name
	version_in_range(d.version, v.affected)
	v.in_kev == true
	msg := sprintf("dependency %s==%s dinh %s (CISA KEV, dang bi khai thac) — nang cap toi >= %s (SSDF RV.1/RV.2, PCI DSS Req 11 tham chieu)", [d.name, d.version, v.id, v.fixed])
}

deny contains msg if {
	d := input.dependencies[_]
	v := input.vulnerabilities[_]
	v.package == d.name
	version_in_range(d.version, v.affected)
	v.epss >= epss_threshold
	msg := sprintf("dependency %s==%s dinh %s voi EPSS %v >= nguong %v — chan theo gate 8", [d.name, d.version, v.id, v.epss, epss_threshold])
}

# --- so sánh phiên bản dạng semver rút gọn (số, tách theo ".") ---

ver_parts(v) := [n | some p in split(v, "."); n := to_number(p)]

cmp_ver(a, b) := -1 if {
	pa := ver_parts(a)
	pb := ver_parts(b)
	pa < pb
}

cmp_ver(a, b) := 0 if {
	ver_parts(a) == ver_parts(b)
}

cmp_ver(a, b) := 1 if {
	pa := ver_parts(a)
	pb := ver_parts(b)
	pa > pb
}

satisfies(version, constraint) if {
	startswith(constraint, ">=")
	cmp_ver(version, trim_prefix(constraint, ">=")) >= 0
}

satisfies(version, constraint) if {
	startswith(constraint, "<")
	not startswith(constraint, "<=")
	cmp_ver(version, trim_prefix(constraint, "<")) < 0
}

satisfies(version, constraint) if {
	startswith(constraint, "<=")
	cmp_ver(version, trim_prefix(constraint, "<=")) <= 0
}

satisfies(version, constraint) if {
	startswith(constraint, ">")
	not startswith(constraint, ">=")
	cmp_ver(version, trim_prefix(constraint, ">")) > 0
}

version_in_range(version, range_expr) if {
	every part in split(range_expr, ",") {
		satisfies(version, trim_space(part))
	}
}
