---
title: "Your scanners pass. Your audit evidence doesn't exist. We built the missing layer."
published: false
tags: devsecops, opensource, security, githubactions
canonical_url: https://github.com/techdevfun/devsecops-os
---

<!--
====================================================================
INTERNAL DRAFT — ABSOLUTELY DO NOT PUBLISH (M5-A3 round, 2026-10-22)
Product status: devsecops-os NOT released yet. The GitHub repo has
not been created — the project is holding the factory council's
99/100 release gate (current score: see
release/RELEASE-DOSSIER.md). This article may only be posted on
publish day if the gate opens.
All numbers in this article are LOCAL measurements on the project's
verification machine and are labeled as such right in the article.
No GitHub Actions timing numbers are stated — that part could not
be measured while there is no repo (UNVERIFIED, no guessing).
To do when publishing: attach the real repo link, embed the demo
GIF (release/demo/demo-terminal.gif), a 1000x420 cover image,
update canonical_url, record the article id + link in the release
dossier (B6-13).
====================================================================
-->

Every regulated team I know has the same quiet problem: the pipeline
is green, the scanners are happy — and when the auditor asks "show
me the evidence that this control ran, on this change, with this
result", somebody spends two weeks assembling screenshots.

**devsecops-os** is an open-source, vendor-neutral operating layer
that treats audit evidence as a build artifact, not an afterthought:
a reference architecture, a policy-as-code pack mapped to real
control frameworks, 10 CI security gates, and an evidence collector
that bundles every run into a single verifiable package. In our
local verification runs, a sample workload with 4 planted faults is
blocked at exactly the gates designed to catch them, a clean
codebase passes all 10, and the evidence bundle for a run covers
**13 of 14** phase-1 control-mapping rows with real, schema-checked
records.

## 1. The problem, precisely

Scanners answer "is there a vulnerability?". Audits ask different
questions:

1. Which control did this check implement — ISO 27001 A.8.32?
   PCI DSS 4.0 requirement 6.5? SOC 2 CC8.1?
2. Did it run on *this* commit, and what exactly did it decide?
3. Who approved this change, and where is that recorded?
4. Can a third party verify the whole packet hasn't been edited
   afterwards?

Commercial platforms answer some of this — inside their own cloud,
in their own format, on their own retention schedule. For a
regulated organization, that makes the vendor part of your audit
supply chain. devsecops-os takes the opposite position: every
policy, decision and evidence record lives as plain files **in
your repository and your infrastructure**, produced by tools you
can rerun yourself.

## 2. What's inside

- **Reference architecture** — documents and worked examples for
  putting the layer around an existing GitHub-based pipeline.
- **Policy pack v1** — 14 policies (12 Rego/OPA + 2 Kyverno) and 14
  evidence schemas covering all 14 rows of the phase-1 control map
  (ISO 27001:2022, NIST CSF 2.0/SSDF, PCI DSS 4.0, APRA CPS 234,
  SOC 2 — reference mappings to support audit preparation, **not**
  a compliance certification).
- **10 CI gates** as reusable GitHub Actions workflows that call
  the *same* shell scripts you can run locally — CI and laptop run
  identical code, so "works on my machine" is checkable, not a
  slogan. Gate 10 (an AI PR review gate) ships **off by default**;
  the pipeline completes with it off.
- **Evidence automation** — a collector that harvests one run's
  records, validates every record against its schema, writes a
  SHA-256 manifest, and verifies a whole bundle with **one command**.
  Bundles can be Cosign-signed; verification then fails closed if
  the signature layer doesn't check out — including the case where
  someone edits a record *and* recomputes all hashes consistently.
- **Decision-layer evidence generators** — the records scanners
  never produce: change records (built from the run's own gate
  results, judged by a real OPA policy), drift reports (your IaC
  vs. a declared baseline), access-review and config-baseline
  reports, and a CI-log record the collector itself issues with the
  run logs' hash.

I built this after years of running infrastructure in regulated
environments and watching evidence assembly eat the last two weeks
before every audit. The design rule throughout: **never claim what
wasn't run**. Every number below comes from a run you can repeat.

## 3. Proof, not promises: the planted-fault matrix

The sample workload (`examples/payments-sample`) ships in two
variants that differ in exactly 4 planted faults. Measured locally
with pinned tool versions:

| Planted fault | Expected result | Measured |
|---|---|---|
| Fake Stripe key in backend config | Gate 1 (secrets) blocks | ✅ blocked |
| `starlette==1.0.0` (CVE-2026-48710, in CISA KEV) | Gate 8 blocks on KEV membership | ✅ blocked, exactly that CVE |
| Security group open to `0.0.0.0/0` on app + SSH ports | Gate 4 IaC policy denies | ✅ denied ×2 rules |
| End-of-life base image `python:3.10.4-slim-bullseye` | Gate 5 denies | ✅ denied ×2 checks |

The clean variant passes all 10 gates. Gate 3 (SCA) independently
reports 9 CVEs in the planted dependency set, including the KEV
one — detection and blocking are separate, deliberate layers.

Two more runs worth reporting:

- **Dogfooding:** a second workload (`examples/checkout-sample`)
  was generated from the project's own golden-path template
  (`templates/api-service/`) and ran the full local pipeline —
  backend smoke test, all 10 gates, evidence bundle, verification —
  green on the first attempt, ~100 seconds end to end locally.
- **Evidence coverage:** the bundle from a generated-evidence run
  verifies clean (66 files hash-checked, 27 records schema-checked)
  and its traceability table shows 13/14 mapping rows fully covered.
  The one partial row needs records from gate 10, which is off by
  design in phase 1. And one honest detail: the generated change
  record is *denied* by its own policy, because a local run has no
  real PR approval. That's not a bug — that's what truthful
  evidence of an unapproved change looks like.

Test counts at the time of writing: 48/48 OPA policy tests, 34/34
pack-harness checks, 36 Python unit tests across the evidence
tooling and gate adapters.

## 4. How it compares — honestly

| | devsecops-os | Harness | GitHub Advanced Security | Snyk |
|---|---|---|---|---|
| Form | Open source (MIT), self-hosted files | Proprietary SaaS platform | GitHub-native add-on | SaaS platform |
| Focus | Governance + policy + evidence layer | Full DevSecOps/AppSec platform | Scanning in the GitHub workflow | Developer-first scanning |
| Evidence custody | Your repo/infra, plain files, hash- and signature-verifiable | Vendor platform | GitHub platform | Vendor platform |
| Control mapping | Ships mapped policy pack (phase-1 scope) | Policy + audit evidence features in-platform | Partial (via platform features) | Partial |

**Where the rivals beat us — plainly:**

- **Scanning depth.** Harness STO, GHAS and Snyk scan far deeper
  than anything here. devsecops-os orchestrates commodity open
  scanners (gitleaks, Semgrep, OSV, Trivy); it does not out-scan
  anyone, and isn't trying to.
- **Enterprise support and integrations.** The vendors have support
  teams, SLA contracts and hundreds of integrations. This is a
  small open-source project with best-effort responses.
- **Vendor certifications.** A regulated buyer can point to the
  vendor's own SOC 2/ISO posture. An open-source layer gives you
  verifiable artifacts instead — a different thing, and for some
  procurement processes, not a substitute.

The wedge is narrow and specific: if your problem is *evidence and
governance across tools you already run*, a proprietary platform is
an expensive place to store your own audit trail. If your problem
is scanning depth, buy a scanner — and this layer can sit on top
of it.

## 5. Current limits (stated, not buried)

- Phase 1 targets GitHub Actions. GitLab/Jenkins integration is
  designed, not implemented.
- Signing is local-key Cosign today; keyless OIDC + transparency
  log identity is the CI-phase step.
- Terraform evidence uses parse + validate; a real `plan` needs a
  real cloud account, so plan-level drift evidence is out of scope
  for the local runs.
- Evidence records are only as meaningful as the operations behind
  them: a change record generated from a local run truthfully shows
  "no approval" — real approval data arrives when a real team runs
  it on real pull requests.

## 6. Try it

The repository goes public the day it clears the project's release
bar; the demo below (a real terminal session: gates on both
workload variants, a bundle verification, and a one-byte tamper
that fails it) is the fastest way to see the shape of the thing.

<!-- when publishing: embed release/demo/demo-terminal.gif here -->

If you've ever assembled audit evidence by hand from five different
tools the week before an assessment — what did your process look
like, and which part of it hurt the most? I'd genuinely like to
compare notes in the comments.
