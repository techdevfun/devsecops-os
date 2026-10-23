# base_image — a Dockerfile base image must: (1) be pinned by digest
# or by a patch-level tag that is STILL maintained; (2) not belong to
# an end-of-life (EOL) image line declared in the pack data; (3) not
# use the "latest" tag. This policy complements gate 5 (container
# scanning with Trivy/Grype): scanners report CVEs in the image, while
# this policy blocks structural risk patterns (frozen/EOL images)
# even before scanning.
#
# Input:
#   { "dockerfiles": [ {"path": "Dockerfile",
#        "images": [ {"image": "python", "tag": "3.10.4-slim-bullseye",
#                     "digest": null} ] } ],
#     "eol_images": [ {"image": "python", "tag_prefix": "3.10",
#                      "eol": "2026-04-01", "note": "CPython 3.10 EOL"},
#                     {"image": "python", "tag_contains": "bullseye",
#                      "eol": "2024-08-01", "note": "Debian bullseye out of regular LTS"} ] }
package devsecops.base_image

deny contains msg if {
	d := input.dockerfiles[_]
	img := d.images[_]
	img.tag == "latest"
	msg := sprintf("%s: base image %s uses the 'latest' tag — pin a specific tag/digest", [d.path, img.image])
}

deny contains msg if {
	d := input.dockerfiles[_]
	img := d.images[_]
	e := input.eol_images[_]
	e.image == img.image
	tag_matches_eol(img.tag, e)
	msg := sprintf("%s: base image %s:%s belongs to an end-of-life line (%s, EOL %s) — upgrade to a line that is still maintained (simulates PLANTED flaw #4)", [d.path, img.image, img.tag, e.note, e.eol])
}

tag_matches_eol(tag, e) if {
	e.tag_prefix != null
	startswith(tag, e.tag_prefix)
}

tag_matches_eol(tag, e) if {
	e.tag_contains != null
	contains(tag, e.tag_contains)
}
