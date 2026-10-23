# network_exposure — no security group may open ingress from the
# Internet (0.0.0.0/0 or ::/0) to an admin port or to an application
# port that is not a standard public web port (80/443 on an SG
# attached to a public load balancer must still be limited to the
# organisation's allowed CIDRs — pack v1 blocks every 0.0.0.0/0
# ingress except port 443 declared with `public_web: true`).
#
# Input (normalised JSON from a Terraform plan or HCL extraction —
# see harness/build_workload_fixtures.py):
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
	msg := sprintf("security group %q opens ingress from %s to ports %d-%d (simulates PLANTED flaw #3 / SOC 2 CC6.6, PCI DSS Req 2, NIST PR.AC/PR.DS)", [sg.name, cidr, rule.from_port, rule.to_port])
}

# Only exception: the SG declares public_web=true AND the rule opens exactly port 443.
public_web_exception(sg, rule) if {
	sg.public_web == true
	rule.from_port == 443
	rule.to_port == 443
}
