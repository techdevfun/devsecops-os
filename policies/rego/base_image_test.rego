package devsecops.base_image

eol_data := [
	{"image": "python", "tag_prefix": "3.10", "eol": "2026-04-01", "note": "CPython 3.10 sap EOL"},
	{"image": "python", "tag_contains": "bullseye", "eol": "2024-08-01", "note": "Debian bullseye out of regular support"},
]

test_clean_image_passes if {
	count(deny) == 0 with input as {
		"dockerfiles": [{"path": "Dockerfile", "images": [{"image": "python", "tag": "3.13-slim", "digest": null}]}],
		"eol_images": eol_data,
	}
}

test_planted_image_denied if {
	count(deny) == 2 with input as {
		"dockerfiles": [{"path": "Dockerfile", "images": [{"image": "python", "tag": "3.10.4-slim-bullseye", "digest": null}]}],
		"eol_images": eol_data,
	}
}

test_latest_tag_denied if {
	count(deny) == 1 with input as {
		"dockerfiles": [{"path": "Dockerfile", "images": [{"image": "node", "tag": "latest", "digest": null}]}],
		"eol_images": eol_data,
	}
}
