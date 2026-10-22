# base_image — base image của Dockerfile phải: (1) ghim theo digest
# hoặc tag có patch-level CÒN được duy trì; (2) không thuộc danh sách
# dòng image đã hết hỗ trợ (EOL) khai báo trong dữ liệu pack; (3) không
# dùng tag "latest". Đây là lớp policy bổ trợ cho gate 5 (container
# scanning bằng Trivy/Grype): scanner báo CVE trong image, policy này
# chặn các mẫu rủi ro cấu trúc (image đóng băng/EOL) ngay cả trước khi
# quét.
#
# Input:
#   { "dockerfiles": [ {"path": "Dockerfile",
#        "images": [ {"image": "python", "tag": "3.10.4-slim-bullseye",
#                     "digest": null} ] } ],
#     "eol_images": [ {"image": "python", "tag_prefix": "3.10",
#                      "eol": "2026-04-01", "note": "CPython 3.10 EOL"},
#                     {"image": "python", "tag_contains": "bullseye",
#                      "eol": "2024-08-01", "note": "Debian bullseye het LTS thuong"} ] }
package devsecops.base_image

deny contains msg if {
	d := input.dockerfiles[_]
	img := d.images[_]
	img.tag == "latest"
	msg := sprintf("%s: base image %s dung tag 'latest' — phai ghim tag cu the/digest", [d.path, img.image])
}

deny contains msg if {
	d := input.dockerfiles[_]
	img := d.images[_]
	e := input.eol_images[_]
	e.image == img.image
	tag_matches_eol(img.tag, e)
	msg := sprintf("%s: base image %s:%s thuoc dong da het ho tro (%s, EOL %s) — nang cap len dong con duoc duy tri (mo phong PLANTED flaw #4)", [d.path, img.image, img.tag, e.note, e.eol])
}

tag_matches_eol(tag, e) if {
	e.tag_prefix != null
	startswith(tag, e.tag_prefix)
}

tag_matches_eol(tag, e) if {
	e.tag_contains != null
	contains(tag, e.tag_contains)
}
