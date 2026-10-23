# runtime_version — every runtime a workload DECLARES must be at or
# above the security floor recorded for its branch in the pack data
# file (policies/data/runtime_floors.json, carried in the input as
# "runtime_floors" by the gate 11 adapter).
#
# Why this policy exists: some critical vulnerabilities live in the
# runtime interpreter itself and are invisible to the pack's other
# signals — CVE matching against image packages misses runtimes that
# are compiled from source into the image (e.g. the official PHP
# image), and CISA KEV membership lags disclosure (PHP2Shell,
# CVE-2026-109618 / CVE-2026-109619, was in neither the KEV catalog
# nor Trivy's image matches when measured on 2026-10-23). A declared
# version floor needs neither signal: the Dockerfile FROM line is the
# runtime that actually runs, and the floor is data, not code.
#
# Scope note: the version source is the Dockerfile FROM declaration.
# A composer.json "platform" requirement is a constraint expression,
# not the running runtime, so it is deliberately NOT used as the
# version source.
#
# Input:
#   { "dockerfiles": [ {"path": "Dockerfile",
#        "images": [ {"image": "php", "tag": "8.3.0",
#                     "digest": null} ] } ],
#     "runtime_floors": { "runtimes": {
#        "php": { "image_names": ["php"], "advisory": "PHP2Shell",
#                 "references": ["CVE-2026-109618", "CVE-2026-109619"],
#                 "branches": { "8.3": {"min_version": "8.3.36"} } } } } }
#
# Verdicts:
#   - declared version below its branch floor        -> DENY
#   - branch older than every branch in the data file -> DENY
#     (end-of-life line, no fixed upstream release)
#   - tag not an exact x.y.z version ("latest", "8.3") -> DENY
#     (unpinned/unparseable — a floating tag cannot be verified
#     against a floor)
#   - runtime not covered by the data file, or no
#     floor data at all                                  -> no deny
#     (not applicable; the gate passes)
package devsecops.runtime_version

default floors := {}

floors := input.runtime_floors if {
	input.runtime_floors != null
}

# --- runtime lookup ---------------------------------------------------------

runtime_name(img) := name if {
	some name
	img.image == floors.runtimes[name].image_names[_]
}

in_scope(img) if {
	runtime_name(img)
}

rtdef(img) := floors.runtimes[runtime_name(img)]

# --- version parsing --------------------------------------------------------
# Exact x.y.z only. A suffix after the numeric core ("8.3.0-fpm-alpine",
# "8.4.27+deb") is ignored; anything else ("latest", "8.3", "8") does
# not parse, which the caller treats as unpinned/unparseable.

parse_version(tag) := parts if {
	core := split(split(tag, "-")[0], "+")[0]
	raw := split(core, ".")
	count(raw) == 3
	every p in raw {
		re_match("^[0-9]+$", p)
	}
	parts := [n | some p in raw; n := to_number(p)]
}

cmp_parts(a, b) := -1 if {
	a < b
}

cmp_parts(a, b) := 0 if {
	a == b
}

cmp_parts(a, b) := 1 if {
	a > b
}

branch_key(parts) := sprintf("%d.%d", [parts[0], parts[1]])

branch_parts(key) := [n | some p in split(key, "."); n := to_number(p)]

lowest_branch_key(def) := key if {
	keys := [k | some k in object.keys(def.branches)]
	key := [k | some k in keys; branch_parts(k) == min([branch_parts(x) | some x in keys])][0]
}

# --- deny rules ---------------------------------------------------------------

# (1) in-scope runtime whose tag is not an exact x.y.z version.
deny contains msg if {
	d := input.dockerfiles[_]
	img := d.images[_]
	in_scope(img)
	not parse_version(img.tag)
	msg := sprintf("%s: runtime %s (image %s) uses tag '%s' — unpinned/unparseable runtime version; pin an exact x.y.z tag so the version floor can be verified", [d.path, runtime_name(img), img.image, img.tag])
}

# (2) declared version below the floor of its branch.
deny contains msg if {
	d := input.dockerfiles[_]
	img := d.images[_]
	in_scope(img)
	parts := parse_version(img.tag)
	def := rtdef(img)
	br := def.branches[branch_key(parts)]
	cmp_parts(parts, parse_version(br.min_version)) < 0
	msg := sprintf("%s: runtime %s %s is below the security floor %s for branch %s — affected by %s (%s) — upgrade the runtime to >= %s", [d.path, runtime_name(img), img.tag, br.min_version, branch_key(parts), concat(", ", def.references), def.advisory, br.min_version])
}

# (3) branch older than the lowest branch in the data file: an
# end-of-life line with no fixed upstream release.
deny contains msg if {
	d := input.dockerfiles[_]
	img := d.images[_]
	in_scope(img)
	parts := parse_version(img.tag)
	def := rtdef(img)
	not def.branches[branch_key(parts)]
	lowest := lowest_branch_key(def)
	cmp_parts([parts[0], parts[1]], branch_parts(lowest)) < 0
	msg := sprintf("%s: runtime %s %s is on branch %s, which has no fixed upstream release for %s (%s) — upgrade to a supported branch (>= %s)", [d.path, runtime_name(img), img.tag, branch_key(parts), concat(", ", def.references), def.advisory, lowest])
}
