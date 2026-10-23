# Landing-page content for devsecops-os on techdev.fun — PREPARED DRAFT (M5-A)

> Status: **prepared at M5-A; the repository has since been released
> publicly (M5-B) and this content deployed to techdev.fun**. This
> file is the content source for the project's page. Every number
> below comes from verification evidence in this repo; figures that
> were local-only at drafting time are labelled as such, and the
> GitHub Actions measurements taken at release are stated where
> they apply — do not strip these labels when publishing.

---

## [Hero]

# devsecops-os

**An open-source DevSecOps + AI SecOps operating layer for regulated
organisations.** Policy-as-code pre-mapped to ISO 27001:2022, NIST
CSF/SSDF, PCI DSS 4.0 and APRA CPS 234/230 — running in your own CI,
with audit evidence generated automatically from every pipeline run.
No intermediary server, no data leaves your organisation's
infrastructure.

[Demo GIF — release/demo/demo-terminal.gif: the gate suite running
for real on the two-variant sample workload + evidence bundle
verification]

**Who hurts:** CISOs and platform teams in banking/finance/insurance
— where every team assembles its security pipeline differently,
compliance policy lives in Word documents, and at audit time the
whole organisation gathers evidence by hand. devsecops-os builds
exactly that missing part: a golden path so a new service is born
meeting the controls, policy as code living in the organisation's
own repositories, and evidence as an automatic by-product of
operations — the pipeline does not only block faults, it proves
that it did.

## [How it works]

1. **10 CI gates** on every pull request: secret scanning, SAST,
   SCA, IaC, container, SBOM + attestation, licensing,
   vulnerability prioritisation by CISA KEV/EPSS, pipeline hygiene,
   and an optional AI review gate (off by default).
2. **Policy at the centre**: 14 policies (OPA/Rego + Kyverno) mapped
   to the control frameworks — *reference* mappings to support
   audit preparation, not a compliance certification.
3. **Evidence bundle**: every run is packaged with a SHA-256
   manifest and its integrity verified with **one command** —
   including detecting a 1-byte edit.
4. **Golden path**: a service template (API + IaC + manifests + CI)
   so teams onboard in minutes instead of assembling everything over
   weeks.

## [Evidence, not promises]

- The two-variant sample workload runs for real: the clean variant
  passes all 10 gates; the variant with exactly 4 planted faults
  (fake secret, dependency carrying a CVE in CISA KEV, security
  group open to 0.0.0.0/0, base image frozen since 2022) is blocked
  at **exactly the 4 corresponding gates** — no false blocks,
  nothing slips through.
- Policy harness: 34/34 checks pass. Evidence bundle: verification
  passes on both variants; a 1-byte edit → verification FAILS and
  names exactly the edited file.
- The golden path has been dogfooded: a second service built from
  the template, the full local pipeline green on the first run in
  ~100 seconds.

*(The measurements above are local measurements on the project's
verification machine. The workflow timings on real GitHub Actions,
measured at release: master workflow median 58 seconds over 3 runs;
golden path green on its first CI run, 5 minutes 42 seconds for
build + CI — see the README status banner.)*

## [Known limits — stated plainly]

- This is **phase 1**: GitHub Actions is the implemented CI
  platform; GitLab/Jenkins/on-prem are designed integration points,
  not yet implemented.
- Decision/periodic evidence (change records, drift reports,
  access reviews, configuration baselines) **now has automatic
  generators** running on the run's/tree's data (round M5-A3,
  traceability 13/14 rows) — but their full audit value still needs
  a real organisation's operating data (real PR approvals, real
  drift history), which only exists after real adoption.
- The `change-record` record in local runs is currently **DENIED**
  by its policy because there is no real PR approval — that is its
  nature: truthful evidence of a change that has not been approved,
  not a bug.
- Evidence bundles have SHA-256 integrity and can be Cosign-signed
  at bundle level — bundles from CI runs are signed keyless with
  Cosign via OIDC and verify themselves in the job; local bundles
  still use a per-run temporary local key.
- This system **does not replace** Harness, GitHub Advanced Security
  or Snyk in scanning depth or enterprise support — it is the
  cross-cutting governance + evidence layer that sits on top of
  those tools.

## [Get started]

GitHub repository: https://github.com/techdevfun/devsecops-os — the
technical write-up is published on dev.to (linked from the
repository). Source code under the MIT licence.
