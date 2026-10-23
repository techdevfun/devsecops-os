# RELEASE DOSSIER — devsecops-os phase 1 (M5-A, local part)

**Product:** devsecops-os (flagship #2 of the repo factory, Assistant A).
**Dossier date:** 2026-10-22. **Prepared by:** worker M5-A.
**Scope of this dossier:** all LOCAL work of milestone M5. No
release action has been taken yet: no GitHub repo created/pushed, no deploy,
no change to DNS/the live techdev.fun site — exactly the hard limit of the milestone.

**Release gate applied** (owner via the Coordinator, 2026-10-22):
release only when reaching **99/100 under RUBRIC-NGHIEM-THU-100 from the council**
plus all 6 acceptance criteria of the blueprint and a pre-release
risk sweep. Below 99 → keep improving, do not release in any
case.

**OWNER DECISION (2026-10-22 ~18:17, via the Coordinator) —
current release status:** keep the 99/100 gate **exactly as written** —
do **not** create a temporary private repo for measurement, **no** measurement
exception of any kind; accept a ceiling score below 99 until another valid
verification method exists. Consequence: devsecops-os remains **NOT
RELEASED** and the whole of **M5-B IS FROZEN** (no repo creation in any
form, no Actions measurement, no live landing, no dev.to
article). The M5-B work lines in this dossier are now only records
of conditions that cannot be verified, **not open options**.

**M5-A2 update (2026-10-22, worker M5-A2):** the two local technical
deductions of category 3 were handled within local scope — Cosign signing for
the evidence bundle (temporary per-run local key level) and a dedicated unit test suite
for bundle_tool — and exactly the affected lines were re-scored
(sections 1, 3, 5). All score lines belonging to M5-B/UNVERIFIED remain unchanged.

**M5-A3 update (2026-10-22, worker M5-A3, under the owner order
"work continuously until the doable part is done before stopping"):** the local
exhaustion round — closing the 4 missing evidence rows of the phase 1 map plus
ci-log (traceability 6/14 → **13/14 complete**, proven by a new bundle
with verify PASS); sweeping all 210 factory checklist items (119 passed, 4 fixed
in this round, 67 not applicable with reasons, 20 locked by release —
`release/checklist-sweep-m5a3.md`); increasing Python unit tests 8 → 36;
drafting the dev.to article in advance (not yet published). Re-scored: category 6 from 0
→ 2 (complete draft verified), **total 69.5/100 — this is the
LOCAL CEILING**: all of the remaining 30.5 points are locked on the release/
real-user side (breakdown in section 5). All frozen lines remain unchanged.

## CONCLUSION OF THE DOSSIER

**Total council score: 69.5/100 — HAS NOT REACHED GATE 99. DO NOT RELEASE.**
(66/100 at M5-A; +1.5 at M5-A2 from the two local technical deductions of
category 3 that were completed and truly verified; +2 at M5-A3 from the complete
dev.to article draft of category 6 — see sections 3 and 5. **69.5 is the
local ceiling**: after the M5-A3 round there is no longer any deduction that can be removed
on the spot; the remaining 30.5 points all need a real repo/CI, a publish
action, or real users.)

Most of the unearned points lie in categories that *by nature* can only be verified
on a real release (GitHub Actions, distribution, dev.to article) — they
are recorded as UNVERIFIED and are **not** awarded points under the rules of
the milestone. Under the owner decision (2026-10-22 ~18:17, recorded at the head of this
dossier), these categories must **not** be unlocked by a temporary repo or any
measurement exception: a ceiling score below 99 is accepted until there is
another valid verification method, and M5-B remains frozen. Details
of each deduction are in sections 4–5. This is the expected result of an honest
dossier, not a technical failure: all of the locally verifiable part
has passed (sections 1–2).

---

## 1. Work done at M5-A (tasks 1–6) and evidence

| # | Category | Result | Evidence in the tree |
|---|---|---|---|
| 1 | Unlock terraform plan/validate | Refactored inline SG rules → separate `aws_vpc_security_group_*_rule` resources, consistent across 2 variants; still exactly the differing 4 files of planted, the nature of the 4 errors unchanged. `terraform validate` **PASS for both variants** (before: FAIL due to a cycle); `terraform fmt -check` PASS. Re-ran the full verification: matrix unchanged (clean passes everything; planted DENY at exactly gates 1/4/5/8, network_exposure DENY ×2). Policy harness still 34/34. **terraform plan still cannot be generated locally** — the real reason: plan needs to call the AWS API for the data source `aws_availability_zones`; a plan attempt with fake credentials hung exactly at this data source (recorded in gate-04.sh + record). The gate continues to use conftest HCL2 parsing + validate. | `examples/payments-sample/{clean,planted}/infra/main.tf`, `evidence/output/local-*/gate-04-iac/validate.json` (passed=true), `gates/verification/results.md` (re-rendered) |
| 2 | Clean up workflow | Completely removed the job `collect-gate-outputs` (merging artefacts with `merge-multiple` causing record overwrites) from `all-gates.yml`; the job `evidence-bundle` is the sole collection path. All 12 workflow YAML files are valid; gate 9 re-ran: PASS for both variants. | `.github/workflows/all-gates.yml` |
| 3 | Golden path + dogfood | Complete template at `templates/api-service/` (service skeleton + standard Dockerfile/IaC/K8s + CI 10 gates + `devsecops-os.yml` + CODEOWNERS + branch-protection-as-code + step-by-step guide). Dogfood: built `examples/checkout-sample/` **from the template itself**, ran the full local pipeline (real backend smoke + 10 gates + bundle + verify): **every step exit 0 on the very first run, total 100 seconds** (budget 30 minutes). The real CI part: UNVERIFIED. | `templates/`, `examples/checkout-sample/`, `release/dogfood-checkout-sample.md`, `release/dogfood-run.log` |
| 4 | Demo | 30-second GIF built from the output of a REAL run session (`script` recording, 91 real run seconds: gates on 2 variants + bundle verify + a 1-byte edit attempt → FAIL on exactly the right file). Accompanied by a text transcript + reproduction script. The GIF is a text re-enactment of the real output lines (waiting time compressed, content unchanged — stated clearly in the transcript). | `release/demo/demo-terminal.gif`, `demo-transcript.txt`, `replay.sh`, `demo-raw.typescript` |
| 5 | Landing content | Landing page content for techdev.fun drafted in advance (hero "who hurts/what it does", how it works, evidence labelled local, known limitations) — **not yet deployed**. The repo README already has the demo + "who hurts, what the system does" at the top of the page and a truthful M5-A status banner. | `release/landing-techdev-fun.md`, `README.md` |
| 6 | Risk sweep | Gitleaks over the whole tree + review of 5 risk layers. Fixed on the spot: deleted 3 temporary cosign.key + 3 `__pycache__`, added SECURITY.md, fixed 4 wrong/outdated documentation points (README, payments-sample README, golden-paths.md, a hard-coded sentence in render_results_md.py). 5 items remain, R1–R5, the highest being R4 (not yet measured on Actions). | `release/risk-sweep-m5a.md` |
| 7 | (M5-A2) Bundle signing + bundle_tool unit tests | `collect --sign`: Cosign signing on `bundle.sha256` with a temporary key generated outside the tree, destroyed immediately after signing (the private key does not enter the bundle, does not remain in the tree); the signature declaration + public key fingerprint are in manifest/bundle.json; `verify` in one command additionally checks the signature and FAILs loudly when it is missing/wrong/unverifiable. Truly verified on the run data `local-clean`: signed bundle → verify PASS for both hash + signature; a 1-byte edit → FAIL naming exactly the right file; replacing the signature with the signature of the planted bundle → FAIL "invalid signature"; editing a record together with consistently recomputing the hash (automated test) → FAIL at the signature layer; a bundle declaring a signature but the machine has no cosign → FAIL. Unit tests: **8 tests, all green** (`python3 -m unittest discover -s evidence/tests`, 15.3 seconds) covering collect/verify/strict schema + allow-incomplete/gate 10 disabled/1-byte edit/3 signature cases. Limitations recorded in `evidence/README.md`: temporary local key, no tlog, no OIDC identity binding — keyless on CI belongs to M5-B (currently frozen). | `evidence/bundle_tool.py` (v1.1.0), `evidence/verify_bundle.py`, `evidence/tests/test_bundle_tool.py`, `evidence/README.md` |
| 8 | (M5-A3) Closing decision/periodic evidence + local exhaustion | **Evidence generator suite** `evidence/generators.py` (stdlib-only): `change-record` generated from the real gate results of a run (the decision by the policy `change_record` truly run with OPA — DENY exactly because the local run has no PR approval), `drift-report` from comparing the IaC configuration with the declared baseline (correctly detected +2 open rules on planted, 0 items on clean), `access-review-report` reviewing 13 workflows in the tree (0 high-level findings), `config-baseline-report` evaluating 3 IaC policies on the current configuration (planted: network_exposure DENY). The collector (`bundle_tool.py` v1.2.0) additionally scans the directory `supplementary-records/` and **self-issues the record `ci-log`** (packing the run log into a deterministic zip with SHA-256; verify cross-checks record hash ↔ artefact — a tampering test was caught). Proof: bundle `local-clean-m5a3` closed in strict mode + verify **PASS** (66 hash files, 27 records matching schema), traceability **13/14 complete** (row-05 remains because gate 10 is off by design). Accompanying: sweep of 210 checklist items (4 items fixed on the spot: CHANGELOG.md, CONTRIBUTING.md, ISSUE_TEMPLATE, secret-leak procedure in SECURITY.md; fixed a wrongly named gate-10 workflow reference in the template + dogfood; deleted 2 leftover cosign keys in run directories); **28 new unit tests** (15 for the generator suite + collector extensions, 13 for gate adapters — including a real Syft+Cosign chain); dev.to article draft `release/devto-article-draft.md` (not yet published). | `evidence/generators.py`, `evidence/baselines/`, `evidence/bundles/local-clean-m5a3-*`, `evidence/tests/test_generators.py`, `gates/local/tests/test_adapters.py`, `release/checklist-sweep-m5a3.md`, `release/devto-article-draft.md`, `CHANGELOG.md`, `CONTRIBUTING.md` |

## 2. Comparison against the 6 acceptance criteria of the blueprint

| # | Criterion | Conclusion at M5-A |
|---|---|---|
| 1 | Master workflow ≤ 15 minutes, median of 3 runs on GitHub Actions | **UNVERIFIED** — no repo/Actions yet. Local estimate: the gate suite running sequentially ~141 seconds/variant (verification machine, warm cache); on Actions the gates run in parallel by job. The official number only exists at M5-B. |
| 2 | Clean passes 100%; planted blocked at exactly the right gates; 0 false blocks / 0 misses | **PASSED (local)** — fully re-verified at M5-A after the refactor: exactly the absolute matrix in `gates/verification/results.md`. |
| 3 | Every phase 1 mapping row has a policy + enforcement + self-generated evidence | **PASSED (13/14 rows complete)** — at M4/M5-A: 6/14 complete, 4 partial, 4 missing. At M5-A3: the evidence generator suite + the collector ci-log closed rows 02, 03, 08, 09, 12, 13, 14 (proving bundle `local-clean-m5a3`, verify PASS). The only row still partial is row-05 (`pr-review-report`) — generated only when gate 10 is on, and gate 10 OFF is a design condition of phase 1, so this state is correct acceptance rather than a shortcoming. |
| 4 | Evidence bundle has manifest SHA-256, one-command verification | **PASSED (local)** — verify PASS for both variants + the dogfood copy; a 1-byte edit → FAIL on exactly the right file (re-verified right in the M5-A demo session). From M5-A2: a bundle closed with `--sign` also has a Cosign signature on `bundle.sha256` and the same verify command additionally checks the signature (3 verification cases in section 1 row 7). |
| 5 | Golden path ≤ 30 minutes, CI green on the very first run | **PASSED for the local part** (100 seconds, green on the first run — dogfood record); **UNVERIFIED for the GitHub Actions part** (awaiting M5-B). |
| 6 | Documentation for each policy + README has demo/"who hurts" at the top of the page | **PASSED** — `policies/README.md` + documentation for each policy; the README top has the demo GIF + the section "Who hurts, what this system does" + truthful status. |

## 3. Council score table (RUBRIC-NGHIEM-THU-100)

The original scale of the rubric remains unchanged. Panel 5 (Review council & trial
users) is the main scoring panel for every category; cross-confirming panels record separate
opinions. The part depending on a real environment (GitHub Actions/release) is recorded as
UNVERIFIED and is not awarded points.

| Category | Maximum | Score | Scoring / confirming panel | Basis & deductions |
|---|---|---|---|---|
| 1. Pain fit & differentiation | 20 | **18** | Panel 5 scores; Panel 1 (strategy) confirms | Clear pain with specifically named people in pain in README/landing; differentiation from Harness/GHAS/Snyk has source analysis from the blueprint. −2: no verification from any real user/real organisation yet; differentiation has not been measured against rivals by hand. |
| 2. Real runs & e2e | 20 | **12** | Panel 5 | Locally at the maximum achievable: absolute gate matrix on 2 variants + dogfood green on the first run + two-way bundle verify. −8: the original criterion requires real runs *in the target environment* — the master workflow on GitHub Actions (median of 3 runs) and the golden path on real CI are both UNVERIFIED (this entire part awaits M5-B). |
| 3. Code quality & testing | 15 | **14.5** | Panel 5; Panel 3 (technical) confirms | Toolchain pinned by version + SHA-256; OPA tests 48/48; harness 34/34; Kyverno passed; internal tooling stdlib-only; template truly dogfooded. At M5-A2: a dedicated unit test suite for bundle_tool now exists (**8 tests, all green** — added back +1); the bundle is now Cosign-signed and verified in 3 real cases, but only at the temporary local key level (no tlog, no OIDC identity binding) so only +0.5 added — still −0.5 for the full attestation part (keyless/OIDC + Rekor on CI, belonging to M5-B, currently frozen). |
| 4. Demo + README top of page | 15 | **13** | Panel 5; Panel 9 (presentation) confirms | ~30-second GIF from a real run session + transcript + reproduction script; README top has enough demo + "who hurts" + truthful status. −1: the GIF is a text re-enactment of real output (labelled as such) instead of a direct screen recording; −1: the demo image can only be displayed after the repo is published (relative link within the repo). |
| 5. Distribution readiness | 15 | **5** | Panel 5; Panel 2 (growth) + Panel 7 (release operations) confirm | Already has: LICENSE, SECURITY.md, landing content drafted in advance, release dossier, clean repo tree after the risk sweep. −10: the repo does not yet exist on GitHub (exactly the M5-A limit), no topics/release/live landing page yet, no distribution channel operating — this category by nature belongs to M5-B. |
| 6. Dev.to article | 10 | **2** | Panel 5; Panel 6 (content) confirms | At M5-A: 0 (no article yet). At M5-A3: **a complete technical article draft has been drafted and verified** at `release/devto-article-draft.md` — structure problem → approach → demo → repo, a rival comparison table with sources + a section "where rivals beat us", only verified claims, the content axis is the dogfood record + the planted matrix (exactly the proposal of Panel 6 at M5-A) — added +2 for the publish-ready content part. Remaining −8: the article is **not yet published** (no id/link yet, no two-way canonical binding with the repo) — belonging to frozen M5-B. |
| 7. Safety & compliance | 5 | **5** | Panel 5; Panel 8 (safety) cross-confirms — veto right not used | Gitleaks sweep: the source code contains only deliberately planted fake secrets that have been documented; temporary keys deleted; full MIT LICENSE; no copyright-infringing content; no fake interactions. See `risk-sweep-m5a.md`. |
| **TOTAL** | **100** | **69.5** | | (66 at M5-A; 67.5 after M5-A2 re-scoring; 69.5 after M5-A3 — only category 6 changed in this round) |

### Opinions of each panel (summary)

- **Panel 1 — Strategy & positioning:** confirms category 1; the positioning
  "governance layer + evidence on top of the scanners" is a real differentiation,
  not overlapping the claims of large rivals.
- **Panel 2 — Growth & distribution:** category 5 cannot be higher while
  not yet present on GitHub; the drafted landing is good input for M5-B.
- **Panel 3 — Technical & architecture:** confirms category 3; notes
  the SG refactor correctly following the separate-resource standard and the adapter/harness having been
  extended accordingly without changing verification expectations. (M5-A2: confirms the addition of
  Cosign signing for the bundle + 8 unit tests of bundle_tool — the category 3 score
  increased 13 → 14.5 according to exactly the verified part, the keyless/OIDC part
  not yet scored.) (M5-A3: confirms the evidence generator suite + 28 new unit tests
  are all truly verified — the category 3 score is **unchanged** because its remaining
  deduction is only the attestation of signature identity (OIDC/Rekor), not
  test coverage.)
- **Panel 4 — Product & experience:** README top meets the requirement
  "understand in 30 seconds"; the local trial-run path is clear.
- **Panel 5 — Review council & trial users:** keeps the principle of
  no points for UNVERIFIED; the total 69.5 (after M5-A3) correctly reflects
  the distance to release, not the quality of the verified part.
- **Panel 6 — Content & dev.to:** at M5-A: 0 points for category 6; proposed
  that the article use the dogfood record itself + the planted matrix as its content
  axis. (M5-A3: the draft following exactly that axis has been completed and self-
  verified against the Panel 6 checklist — scored 2/10 for the ready content part;
  the remaining 8 points are tied to the publishing action.)
- **Panel 7 — Operations & handover:** dossier + records + reproduction scripts
  are sufficient to hand over M5-B; note R5 (gate 6 temporary key) for the later phase.
- **Panel 8 — Safety & legal:** no veto; all 5 hard conditions
  passed (section 4). Reminder: when creating the repo at M5-B, commit exactly the swept tree.
- **Panel 9 — Presentation & documentation:** confirms category 4; the GIF is clear, Vietnamese
  displays correctly, honest labelling about how the demo was built.
- **Panel 10 — Independent verification:** independently compared the numbers in this
  dossier with `gates/verification/results.md`, `validate.json`,
  `release/dogfood-timings.tsv` and the demo session log — matching.

## 4. Five hard conditions (rubric — violating any = FAIL regardless of score)

| Condition | Result |
|---|---|
| Code runs / e2e passes | ✅ Passed locally (the entire pipeline truly runs; the Actions part is UNVERIFIED rather than FAIL) |
| Contains no secrets | ✅ Passed (only deliberately planted fake secrets, documented as verification fixtures) |
| No copyright infringement | ✅ Passed (original code; external tools are only invoked, not embedded) |
| Has LICENSE | ✅ Passed (MIT) |
| No fake interactions | ✅ Passed (not yet released; no fake star/issue/comment exists) |

## 5. Deductions and the path to 99

Total deducted: **30.5 points** (34 at M5-A; reduced by 1.5 at M5-A2; reduced
by a further 2 at M5-A3). Exact breakdown:

| Deduction block | Points | What must be done to regain them | Milestone |
|---|---|---|---|
| Category 2 — e2e in the target environment not yet verified | −8 | Run the master workflow on GitHub Actions ≥3 times, take a median ≤15 minutes; run the golden path on real CI green on the first run; record the numbers in the dossier and re-score | M5-B — **FROZEN** (owner decision 22/10/2026) |
| Category 5 — distribution does not yet exist | −10 | Publish the repo with exactly the approved tree (topics, description, release), put the landing on techdev.fun from the drafted file, check real display | M5-B — **FROZEN** |
| Category 6 — dev.to article not yet published | −8 | PARTIALLY HANDLED AT M5-A3: a complete draft has been drafted + verified (+2). The remainder: publish the article after the repo is public, bind the two-way link repo ↔ article, record the id/link in the dossier | M5-B — **FROZEN** |
| Category 1 — no real-user verification yet | −2 | Have feedback/trial-use evidence from at least one real team, or manually compare against rivals on the same workload and publish the measurement results | After release |
| Category 3 — full attestation part of the bundle signature | −0.5 | HANDLED AT M5-A2: bundle_tool unit tests (+1) and Cosign signing at the local key level (+0.5). The remainder: keyless/OIDC signature + Rekor on CI so that the signature identity is bound to the workflow | M5-B — **FROZEN** |
| Category 4 — text re-enactment demo; demo link awaiting the repo | −2 | After the repo is public: check the GIF truly displays on the repo page; consider an additional direct capture recording if the council requires it | M5-B — **FROZEN** |

**Frank assessment:** the M5-B blocks above are currently **frozen under the
owner decision** (no repo creation in any form for
measurement) — they are recorded purely so that the dossier is honest about the
unverified conditions, not an open path. Even in the hypothetical
case that M5-B were reopened and done in full, the projected score would reach ~97–99 — the
99 gate requires the council to re-score on real evidence and almost no
deductions remain, including the small deductions in categories 1/3/4. This dossier
does not round numbers and does not promise re-scoring results in advance.

**LOCAL CEILING = 69.5/100 (fixed at M5-A3).** After the exhaustion
round M5-A3, all 6 remaining deduction blocks lie outside local reach, block
by block: −8 (category 2) needs real GitHub Actions — non-existent
while there is no repo; −10 (category 5) is the very action of publishing the repo/
landing — frozen; −8 (category 6) is the action of publishing the article —
going together with publish; −2 (category 1) needs real users/organisations to trial-
use it — cannot be self-created without becoming fake interaction (forbidden by a hard
condition); −0.5 (category 3) needs the OIDC/Rekor identity of real CI;
−2 (category 4) includes a display link on a public repo and the
requirement for direct capture to be accepted by the council on the public copy.
There is no longer any deduction within local reach still open.

## 6. Decision status (fixed — no open recommendation remaining)

1. **Do not release in the current state** (69.5/100 < 99) — exactly
   the gate rule as set.
2. **The owner has decided (2026-10-22 ~18:17, via the Coordinator):**
   keep the 99/100 gate exactly as written; **do not create a temporary private repo to
   measure, no measurement exception**; accept a ceiling score below 99
   until there is another valid verification method. M5-B **frozen**:
   do not create a repo (public or private), do not measure GitHub Actions,
   do not put the landing live, do not write/publish a dev.to article.
   This dossier does not re-propose measurement paths via a temporary repo as an
   option — the decision is fixed.
3. The two local technical deductions stated in the M5-A version of this section
   (bundle signing, bundle_tool unit tests) **were completed at M5-A2**
   (section 1 row 7); the **M5-A3** round exhausted the remaining local part
   (section 1 row 8): decision/periodic evidence, test coverage,
   comprehensive checklist sweep, dev.to draft. **The local ceiling is fixed at
   69.5/100** — the part still open consists only of the UNVERIFIED items belonging to frozen M5-B
   and category 1 (real-user verification — after release).

---

## 7. M5-B LIVE — SUPPLEMENTARY ACCEPTANCE ON REAL GITHUB (night of 2026-10-22)

The owner **unlocked measurement** (2026-10-22 ~23:02) and ordered repo creation
right in the night (~23:17, the owner personally overrode the repo-creation time window
08:00–22:00 for this time). All measurements below are real evidence
on GitHub, re-verified via API:

- Repo `techdevfun/devsecops-os` (id 1430021492) created **PRIVATE**;
  a tree of 235 files pushed via the Git Data API, every blob matching SHA with the local
  copy. Release candidate commit: `1b4d1f87`.
- **Overall workflow on Actions (3 consecutive times, clean workload):**
  run 39818433394 = 54 seconds, run 39818602558 = 66 seconds,
  run 39818765418 = 58 seconds — all 3 `success`, 11/11 jobs green.
  **Median 58 seconds** (criterion ≤ 15 minutes → PASSED, by far).
- **Planted variant on CI:** run 39818945487 `failure` exactly by
  design — failed at exactly gate-01, gate-04, gate-05, gate-08; the remaining 7 jobs
  success. The gate matrix matches 100% with local acceptance.
- **Golden path on real CI:** a separate scratch repo
  `techdevfun/devsecops-os-goldenpath-ci` (id 1430031722, private)
  built from the template; run 39819226621 `success` **on the very first run**,
  11/11 jobs green; total build + push + CI **5 minutes 42 seconds**
  (criterion ≤ 30 minutes → PASSED).
- **Keyless signing (OIDC) for the evidence bundle on CI:** the candidate commit
  connected Cosign sign-blob + verify-blob into the evidence-bundle job
  (cosign v3.1.4 pinned by sha256; only added the permission `id-token: write` for
  that job). Confirmation run 39820512697 `success` 69 seconds; the signing step +
  self-verification **success**. The keyless deduction part of category 3 at
  M5-A2 has now been removed.
- The repo now has: a description, 12 topics, release `v1.0.0-phase1`
  (prerelease, id 420992051) pointing exactly at the candidate commit.
- Technical incidents in the night (handled, not affecting the product):
  the Git Data API returned 409 on an empty repo → initialised with the Contents API
  then continued pushing; POSTing the tree of 235 items was timed out by GitHub with 422 → built the tree
  incrementally by directory (exactly the suggestion in the GitHub error message).

### Council score table after M5-B (scored on real evidence)

| # | Category | Maximum | Score | Basis |
|---|----------|-------:|-----:|--------|
| 1 | Real problem & differentiation | 20 | **18** | Unchanged: no real external-user verification yet — by nature only after release. |
| 2 | Real runs & e2e | 20 | **20** | Real CI on exactly the candidate commit: 3 runs success, median 58 seconds; planted blocked at exactly 4 gates on CI; golden path green on the first run 5 minutes 42 seconds; all local tests green (OPA 48/48, harness 34/34, evidence 23 tests, adapters 13 tests). |
| 3 | Code quality & testing | 15 | **15** | Keyless OIDC/Rekor signing for the CI bundle connected and verified at run 39820512697 — removed the last deduction part of M5-A2. |
| 4 | Demo & README | 15 | **14** | Re-scored 2026-10-23 (§8): the GIF replaced by a RAW RECORDING of a real terminal — a `script` session running `replay.sh`, built frame-by-frame from the raw recording with VT emulation, real speed 1.0×, no retyping/editing of output — removed the deduction "text re-enactment". Remaining −1: display verification on a public repo — completed by the release action itself. |
| 5 | Distribution readiness | 15 | **11** | Repo + description + topics + candidate release already exist; −4: the landing is not yet live and the repo is not yet public — both are release actions. |
| 6 | Dev.to article | 10 | **2** | A complete draft verified (M5-A3); −8 the article is not yet published — publishing the article is a release action (the canonical must point to a public repo). |
| 7 | Safety & compliance | 5 | **5** | All 5 hard conditions pass all 5 (see below). |
| | **TOTAL** | **100** | **85** | |

**5 hard conditions: PASSED ALL 5** — code runs + e2e CI pass on the candidate
commit; no real secret in the pushed tree (gitleaks sweep at freeze time: only 2 noted fake fixtures); no copyright infringement (third-
party tools downloaded at runtime, not repackaged); has LICENSE (MIT);
no fake interactions.

### M5-B conclusion under the exact wording of the gate (GD8)

**84/100 < 99 → DO NOT RELEASE in this round.** The repo remains PRIVATE.
Breakdown of the remaining 16 deductions: **15 points locked by the release
action itself** (category 1: −2 user verification after release;
category 4: −1 public display; category 5: −4 landing + making
public; category 6: −8 publishing the dev.to article) and 1 point in demo form (the GIF
text re-enactment, honestly noted — the council choice remains unchanged). In other words: **every criterion measurable before release
has reached the maximum or near-maximum** (categories 2 and 3 reached the absolute score
on real CI evidence); a score of 99 under the exact wording can only be
scored AFTER the release actions have been carried out — the current gate
requires the score first, the actions after, so this round stops at GD8 and awaits
the owner decision: (a) accept release at the current evidence level
then re-score after release, or (b) keep the gate verbatim
and keep the repo private.

## 8. RE-SCORING UNDER THE FEASIBLE GATE — owner decision 2026-10-23 00:33

**Owner decision (2026-10-23 00:33, replacing the condition
"≥99 before flipping to public" in §6–§7 and all earlier documents):** apply the **FEASIBLE
RELEASE GATE** to both flagships, drawing the lesson from the LinkedIn voice gate
(an absolute scale cannot operate → high median + floor for each
panel + recorded override). New scoring method: **QUALITY score** = the total of
categories 1+2+3+4+7 (maximum 75) normalised /100; **DISTRIBUTION score** =
categories 5+6 (maximum 25) tracked separately and completed BY the
release action. Conditions to flip to public: quality ≥ 95/100 AND floor for each
panel (HM1 ≥ 18/20, HM2 ≥ 18/20, HM3 ≥ 13.5/15, HM4 ≥ 13.5/15,
HM7 = 5/5) AND 5 hard conditions pass AND 0 high risks unhandled.
99/100 from now on is the **polishing target AFTER release**, not a
release condition. The GD8 conclusion in §7 (stopping because 84 < 99 under the old gate) is
replaced by this section.

### Work done in the re-scoring round (2026-10-23)

The only locally fixable remaining deduction was in category 4: the demo GIF was a
text re-enactment from real output (−1). It was redone with a **raw recording
of a real terminal**, exactly the technique that had just brought flagship #1
(ai-pr-review-gate 0.4.3) to 15/15 in the corresponding category:

- A real terminal session running `bash release/demo/replay.sh` (gates 1/4/8
  on both variants clean/planted + packing & verifying the evidence
  bundle + the 1-byte edit case → verify FAIL on exactly the right file), recorded in full
  with `script` (util-linux) on 2026-10-23 00:57 Vietnam time
  (17:57:13–17:57:46 UTC, session exit code 0). The results in the session match
  the script: clean passes all 3 gates; planted is DENY at exactly gate 1 (secret),
  gate 4 (network_exposure), gate 8 (CVE-2026-48710); bundle verify
  PASS (58 files matching hash, 21 records matching schema); the 1-byte edited copy
  (`ci-log.record.json`) → verify FAIL on exactly that file only.
- The GIF built frame-by-frame from the raw recording itself
  (`release/demo/demo-raw.typescript` + accompanying `demo-raw.timing`) with
  a minimal VT emulator — no retyping of commands, no editing of any output
  line, no inserted presentation text in the frames; keeping the original line wrap
  and real terminal colours; replay at real speed 1.0× (recording
  33.3 seconds → GIF 34.5 seconds, 24 frames, 774 KB). The transcript and notes
  in the README were corrected to match the new nature.
- **Conservative re-scoring, only category 4: 13 → 14/15** (+1 — the deduction
  "text re-enactment" has been fully removed). The remaining deduction of category 4
  (−1, display verification on a public repo) belongs to the class completed
  by the release action, not awarded in advance.

### Score table under the feasible gate

| Category | Score | Floor | Meets floor |
|----------|-----:|----:|:-------:|
| 1. Real problem & differentiation | 18/20 | ≥ 18 | ✓ |
| 2. Real runs & e2e | 20/20 | ≥ 18 | ✓ |
| 3. Code quality & testing | 15/15 | ≥ 13.5 | ✓ |
| 4. Demo & README | 14/15 | ≥ 13.5 | ✓ |
| 7. Safety & compliance | 5/5 | = 5 | ✓ |
| **QUALITY (HM 1+2+3+4+7)** | **72/75 = 96.0/100** | **≥ 95** | **✓** |
| 5. Distribution readiness | 11/15 | — (tracked separately) | |
| 6. Dev.to article | 2/10 | — (tracked separately) | |
| **DISTRIBUTION (HM 5+6)** | **13/25** | completed by release | |

- **5 hard conditions: PASSED ALL 5** (unchanged from §7 — the changes in this round
  are only demo/dossier files, not touching the code or the release tree).
- **High risks unhandled: 0** (pre-release risk sweep at M5-B;
  this round creates no new risk).
- Total under the old 100 rubric (reference): **85/100**.

### Conclusion under the feasible gate

**PASSED THE FEASIBLE GATE — eligible for release:** quality 96.0/100
≥ 95, every floor passed, 5 hard conditions passed, 0 high risks unhandled. The remaining release steps follow exactly the discipline sequence: send
this score table to the Coordinator FIRST → flip to public → publish the dev.to article →
techdev.fun landing → dispatch backup → directly verify each
destination. (This re-scoring round only pushes the demo/dossier files to the private repo;
it does not flip to public itself.)

## 9. RELEASE — re-scoring after release (2026-10-23)

The §8 score table was sent to the Coordinator BEFORE flipping to public (exactly the
discipline sequence). The release round executed GD7–GD8 of RUNBOOK-M5B and directly
verified each destination — results:

- **Flip to public:** `techdevfun/devsecops-os` has been switched to public; the API confirms
  `private=false`, `visibility=public`. The public repo page displays
  exactly commit `54cdb099` (the copy scored in §8), the README renders in full,
  MIT LICENSE. No sensitive content or serious display error
  was detected (the secrets in the `planted/` variant are deliberately planted fake secrets,
  documented in `PLANTED.md`).
- **HM4 — 14 → 15/15:** the last deduction of category 4 (−1, display
  verification on a public repo) HAS BEEN REMOVED: the Demo section appears in
  the rendered README on the public page, the GIF file
  `release/demo/demo-terminal.gif` is publicly accessible (HTTP 200).
- **HM5 — 11 → 15/15:** the part still missing in §8 (−4: landing + making public)
  HAS BEEN COMPLETED BY RELEASE: the repo is public with exactly the approved tree
  (topics, description, prerelease `v1.0.0-phase1`); the techdev.fun landing has
  put up the devsecops-os card with a repo link + a dev.to article link on all 4 pages
  (`/`, `/vi/`, `/tools/`, `/vi/tools/`) — directly verified after
  deploy: HTTP 200 and the card seen on each page.
- **HM6 — 2 → 10/10:** the dev.to article HAS BEEN PUBLISHED and verified by an actual
  public URL (not relying only on the helper output): id `4899032`,
  https://dev.to/techdevfun/your-scanners-pass-your-audit-evidence-doesnt-exist-we-built-the-missing-layer-1pco
  — `canonical_url` points to the public GitHub repo; the content keeps the
  rival comparison section with "Where the rivals beat us" and has updated the real
  measurements: Actions median **58 seconds** (3 runs 54/66/58 seconds), golden
  path **5 minutes 42 seconds** green on the first run, CI bundle **keyless
  Cosign/OIDC signing verified in the job**. The demo GIF displays in the article.
- **Backup:** dispatched `backup-orchestrator` after the repo went public —
  run `39829531353` concluded **completed / success** (the repo has entered the mirror scope
  of the backup system, which only mirrors public repos).

### Score table after release

| Category | Score |
|----------|-----:|
| 1. Real problem & differentiation | 18/20 |
| 2. Real runs & e2e | 20/20 |
| 3. Code quality & testing | 15/15 |
| 4. Demo & README | **15/15** |
| 7. Safety & compliance | 5/5 |
| **QUALITY (HM 1+2+3+4+7)** | **73/75 = 97.3/100** |
| 5. Distribution readiness | **15/15** |
| 6. Dev.to article | **10/10** |
| **DISTRIBUTION (HM 5+6)** | **25/25 — completed by release** |
| **TOTAL (old 100 rubric, reference)** | **98/100** |

**The only remaining deduction: HM1 −2** — no real-user verification
yet. This point remains honestly unchanged: it can only be removed when there is a real external team
trial-using it with evidence; absolutely no fake interactions are to be self-created.
This is also the only distance to the polishing target 99/100 after release.
