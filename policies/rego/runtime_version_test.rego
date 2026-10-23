package devsecops.runtime_version

# Mirror of the PHP entry in policies/data/runtime_floors.json
# (kept small and explicit so the tests stay readable; the fixture
# pair fixtures/runtime_version.{pass,fail}.json carries the full
# data-file copy).
floors_data := {"runtimes": {"php": {
	"image_names": ["php"],
	"advisory": "PHP2Shell",
	"references": ["CVE-2026-109618", "CVE-2026-109619"],
	"branches": {
		"8.2": {"min_version": "8.2.35"},
		"8.3": {"min_version": "8.3.36"},
		"8.4": {"min_version": "8.4.27"},
		"8.5": {"min_version": "8.5.12"},
	},
}}}

input_with(tag) := {
	"dockerfiles": [{"path": "Dockerfile", "images": [{"image": "php", "tag": tag, "digest": null}]}],
	"runtime_floors": floors_data,
}

test_below_floor_denied if {
	ds := deny with input as input_with("8.3.0")
	count(ds) == 1
	contains(ds[_], "8.3.36")
	contains(ds[_], "CVE-2026-109618")
	contains(ds[_], "CVE-2026-109619")
}

test_below_floor_other_branch_denied if {
	ds := deny with input as input_with("8.2.34")
	count(ds) == 1
	contains(ds[_], "8.2.35")
}

test_at_floor_passes if {
	count(deny) == 0 with input as input_with("8.4.27")
}

test_above_floor_passes if {
	count(deny) == 0 with input as input_with("8.3.40")
}

test_eol_branch_denied if {
	ds := deny with input as input_with("8.1.27")
	count(ds) == 1
	contains(ds[_], "no fixed upstream release")
}

test_very_old_branch_denied if {
	ds := deny with input as input_with("7.4.33")
	count(ds) == 1
	contains(ds[_], "no fixed upstream release")
}

test_latest_tag_denied if {
	ds := deny with input as input_with("latest")
	count(ds) == 1
	contains(ds[_], "unpinned/unparseable")
}

test_partial_version_tag_denied if {
	ds := deny with input as input_with("8.3")
	count(ds) == 1
	contains(ds[_], "unpinned/unparseable")
}

test_suffixed_tag_below_floor_denied if {
	ds := deny with input as input_with("8.3.0-fpm-alpine")
	count(ds) == 1
	contains(ds[_], "8.3.36")
}

test_newer_branch_than_table_passes if {
	count(deny) == 0 with input as input_with("8.6.0")
}

test_uncovered_runtime_not_applicable if {
	count(deny) == 0 with input as {
		"dockerfiles": [{"path": "Dockerfile", "images": [{"image": "python", "tag": "3.10.4", "digest": null}]}],
		"runtime_floors": floors_data,
	}
}

test_no_dockerfiles_passes if {
	count(deny) == 0 with input as {"dockerfiles": [], "runtime_floors": floors_data}
}

test_missing_floor_data_passes if {
	count(deny) == 0 with input as {
		"dockerfiles": [{"path": "Dockerfile", "images": [{"image": "php", "tag": "8.3.0", "digest": null}]}],
	}
}
