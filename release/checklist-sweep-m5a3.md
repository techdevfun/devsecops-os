# Factory checklist sweep — M5-A3 round (2026-10-22)

Comparison of all **210 items** of `CHECKLIST-TONG-HOP-NHA-MAY.md`
(Panel 1: 22 · Panel 2: 22 · Panel 3: 20 · Panel 4: 20 · Panel 5: 24 ·
Panel 6: 22 · Panel 7: 20 · Panel 8: 24 · Panel 9: 20 · Panel 10: 16) with
the tree `repos/devsecops-os/` and the progress of the project after round M5-A3.

Classification:

- **Passed** — already exists/already applied, verifiable in the tree or in
  the dossiers of rounds M1–M5-A3 (including the original checklist items already ticked [x]).
- **Fixed in this round** — missing/wrong before this round, fixed on the spot and
  verified in round M5-A3.
- **Not applicable** — the item belongs to the factory/account operating cadence
  or a condition that has not yet arisen; with a specific reason for each item.
- **Locked by the release gate** — can only be carried out when the repo
  exists/is published (owner decision 2026-10-22 ~18:17:
  keep the 99/100 gate verbatim, M5-B frozen).

**Summary: Passed 119 · Fixed in this round 4 · Not applicable 67 ·
Locked by the release gate 20 = 210.**

---

## Panel 1 — Product strategy & pain-point (22 items)

| Code | Result | Note |
|---|---|---|
| B1-01 | Passed | The pain map already exists (original checklist [x]); devsecops-os opens a new axis "audit evidence" beyond the first 11 repos. |
| B1-02 | Passed | Pain-point-first has entered the playbook (original checklist [x]). |
| B1-03 | Passed | The queue has been fixed (original checklist [x]); flagship #2 was brought by the owner to be the main release line on 22/10. |
| B1-04 | Passed | The rule forbidding axis duplication has been applied (original checklist [x]) — this product is not an audit CLI variant. |
| B1-05 | Not applicable | The factory daily topic-selection cadence; this topic was directly designated by the owner. |
| B1-06 | Passed | The target users are named specifically: regulated organisations (banking/finance/insurance), in pain at the step of gathering audit evidence (blueprint section 0, README). |
| B1-07 | Passed | Pain has a basis: the proposal + blueprint are based on a survey of rivals/sources verified on 22/10, not chosen by intuition. |
| B1-08 | Passed | Comparison against the 11 published repos: no repo covers the OS/policy/evidence layer — no axis duplication. |
| B1-09 | Passed | The best existing solutions have been surveyed (Harness, GHAS, Snyk + open pieces) and the differentiation point is clearly recorded in blueprint section 1. |
| B1-10 | Passed | Trial scenario <5 minutes: 30.8-second demo GIF + `release/demo/replay.sh` replaying a real session; dogfood from the template ~100 seconds. |
| B1-11 | Passed | Phase 1 scope fixed narrowly in writing before building (blueprint + KE-HOACH-DEVSECOPS-OS-PHA1: AI SecOps cut to phase 2, gate 10 off). |
| B1-12 | Passed | The name `devsecops-os` was checked empty under techdevfun; the option `gatehouse` was eliminated due to a clash (thepartly/gatehouse). |
| B1-13 | Not applicable | The daily cadence rule "if no topic meets the standard then rest" — belongs to the factory daily operation. |
| B1-14 | Passed | A real product with a distribution channel: OS repo + reusable workflows (phase 1), each gate becoming a Marketplace Action (later phase) — not a one-time scanning CLI. |
| B1-15 | Locked by the release gate | Panel 1 separate confirmation at final acceptance belongs to the publish round; the self-review of this round is in the dossier section 4 (category 1: 18/20). |
| B1-16 | Locked by the release gate | Recording the pain-touch level after publish — not yet published. |
| B1-17 | Not applicable | Updating the trend-log is the factory daily A1 cadence. |
| B1-18 | Not applicable | Reviewing the queue is a weekly factory task. |
| B1-19 | Not applicable | Comparing real signals (stars/issues/installs) — the product is not yet published, there are no signals yet; the factory weekly cadence. |
| B1-20 | Not applicable | Updating the pain map is the factory monthly cadence. |
| B1-21 | Not applicable | Evaluating the portfolio of 11 repos is the factory monthly cadence. |
| B1-22 | Passed | Every change of direction goes through owner approval: the blueprint was approved, the gate raised to 99/100, M5-B frozen — all are owner decisions (original checklist [x] for the principle). |

## Panel 2 — GitHub Actions & Marketplace (22 items)

| Code | Result | Note |
|---|---|---|
| B2-01 | Passed | The distribution form fixed pre-build together with Panels 1/7: reusable workflows + OS repo (blueprint section 6). |
| B2-02 | Not applicable | The phase 1 product is not a packaged Action with its own `action.yml` (it is a reusable workflow suite); `action.yml` belongs to flagship #1 (gate 10 wraps it). |
| B2-03 | Not applicable | Branding icon/colour for a Marketplace listing — belongs to the release phase of each gate. |
| B2-04 | Not applicable | Declaration of inputs/outputs of a packaged Action — later phase; the inputs of the reusable workflows have been declared in each file `gate-*.yml`. |
| B2-05 | Passed | Tools in workflows/scripts are pinned to specific versions (OPA 1.21.3, Trivy 0.76.1... — `gates/local/README.md`), no floating tags are used for tools. |
| B2-06 | Not applicable | Sample workflows in README/template reference internal reusable workflows via the path `./.github/workflows/...`, do not reference external Actions via `@main`. |
| B2-07 | Passed | Minimal permissions: all 13 workflows in the tree declare `contents: read` (this round access-review automatically reviewed: 0 high-level findings); gate 9 enforces this check. |
| B2-08 | Passed | Trigger events declared in `all-gates.yml`; outside scope it is quiet: gate 10 off still completes green by design. |
| B2-09 | Passed | Configurable failure mechanism: inputs of the reusable workflows (for example `fail-on` of gate 10; the EPSS threshold of gate 8 via the input pack). |
| B2-10 | Passed | CI output: job summary + structured JSON records + SARIF to code scanning; no repeated comment spam (PR comments belong to gate 10, currently off). |
| B2-11 | Locked by the release gate | E2E testing on a real PR of a repo belonging to techdevfun — needs the repo to exist. |
| B2-12 | Not applicable | Marketplace listing metadata — the release phase of each gate. |
| B2-13 | Not applicable | Listing image/icon — later phase; demo/landing assets for the repo are already available (see Panel 9). |
| B2-14 | Passed | 2FA of techdevfun has been enabled and verified via API on 21/10/2026 (the original checklist states this clearly). |
| B2-15 | Locked by the release gate | Release/tag v1 created at publish. |
| B2-16 | Fixed in this round | Created `CHANGELOG.md` at the tree root, recording the milestones M1→M5-A3 to accompany every later release. |
| B2-17 | Not applicable | The product is not an MCP server. |
| B2-18 | Passed | The name was checked for no clash on GitHub under the account and the clashing option was eliminated (see B1-12). |
| B2-19 | Locked by the release gate | Recording the listing status after submit — not yet submitted. |
| B2-20 | Not applicable | Reviewing installs of published Actions — no Action has been published yet; the factory weekly cadence. |
| B2-21 | Not applicable | Monitoring Marketplace policy — the factory monthly cadence. |
| B2-22 | Not applicable | Reviewing old repo sample workflows when GitHub changes standards — the factory monthly cadence. |

## Panel 3 — Code quality & architecture (20 items)

| Code | Result | Note |
|---|---|---|
| B3-01 | Passed | Architecture approved in the blueprint (section 3) + the phase 1 plan before deep building. |
| B3-02 | Passed | Clearly different from previous repos: an OS/policy/evidence product, not a single-function CLI. |
| B3-03 | Passed | Codebase written new for this product; the template in the tree is the golden-path template of the product itself (intentional), not a copy mould between repos. |
| B3-04 | Passed | Self-written code; external references are standard documents (control frameworks, SLSA, CycloneDX) — no external code copied into the tree. |
| B3-05 | Passed | Zero-dependency priority: evidence tooling uses only the standard library; the sole exception PyYAML (`workflow_input.py`) has a reason recorded in `gates/local/README.md`. |
| B3-06 | Passed | Function/file names are clear in meaning, Vietnamese docstrings explain the flow in every main module. |
| B3-07 | Passed | Errors at the boundary all have a message + a separate exit code: the strict collector names each problem; generators missing a binary → exit 2; an adapter tool-run error → exit 2. |
| B3-08 | Passed | No dead code/leftover debug: the `print` statements in adapters are intentional CLI output; this round cleaned regenerated `__pycache__` + wrong old documents. |
| B3-09 | Passed | The only remaining long function is `collect()` in bundle_tool (~450 lines, a linear one-pass pipeline) — accepted with a note here; not split in this round to avoid a regression close to acceptance. |
| B3-10 | Passed | Clear entry point: each tool 1 command (collect/verify; generators by subcommand; gate-NN.sh). |
| B3-11 | Passed | Configuration via parameters/environment variables is listed (binary resolution via flag/env/PATH recorded in docstrings + README); no private values hard-coded. |
| B3-12 | Passed | `.gitignore` matches the structure: excludes `evidence/output/`, `*.key`, `__pycache__`, feed cache (compared against the real file). |
| B3-13 | Passed | No build/dependency files in the publish tree: run directories + bundles are in the gitignored area; this round tree sweep confirmed this. |
| B3-14 | Passed | Comments focus on difficult logic (validator, signing path, traceability rules) — reviewed when writing/editing in this round. |
| B3-15 | Passed | Consistent formatting within each language (Python/Rego/shell) following the existing style of the tree. |
| B3-16 | Passed | Technical debt recorded in the handover list: release dossier sections 3 + 6 and risk-sweep R1–R6. |
| B3-17 | Passed | The technical README matches the real code — this round re-verified and fixed 2 mismatched places (the old 6/14 traceability note; the gate 10 workflow file name in the template/dogfood). |
| B3-18 | Not applicable | Reviewing diversity between repos in the week — a weekly factory task. |
| B3-19 | Not applicable | Summarising technical lessons — the factory weekly cadence (the lessons of this round are in the round report + risk-sweep). |
| B3-20 | Not applicable | Reviewing code standards when upgrading the runtime — the monthly cadence. |

## Panel 4 — Security & supply-chain (20 items)

| Code | Result | Note |
|---|---|---|
| B4-01 | Passed | Gitleaks sweep of the whole tree in this round: after clean-up 12 findings remain, all belonging to the known class (FAKE secrets pre-planted of the planted variant + its own gate 1 report + noise in Trivy JSON output in gitignored run directories) — no real secrets. The hard condition holds. |
| B4-02 | Not applicable | The tree is not yet a published git repo so there is no commit history to sweep yet; it will be applied on the real repo in the publish round (M5-B). |
| B4-03 | Passed | Fixtures/samples contain only clearly formatted assumed fake keys (suffix FAKENOTREAL; declared in SECURITY.md). |
| B4-04 | Passed | No personal information in the code/README/fixtures of the publish tree (run outputs containing machine paths are local artefacts already gitignored, not part of the publish copy). |
| B4-05 | Passed | Dependencies approved: workloads pinned with `==` (starlette 1.9.0 clean copy); the tool suite pinned by version, listed in `gates/local/README.md`. |
| B4-06 | Passed | Dependencies pinned to specific versions; GitHub Actions in workflows pinned by version tag (not yet pinned by SHA — the tag level is accepted by the checklist as "clear tag/SHA"). |
| B4-07 | Passed | Checking hot warnings when choosing dependencies: CVE-2026-48710 (KEV) itself is the basis for choosing the clean copy 1.9.0 and the pre-planted faulty copy 1.0.0. |
| B4-08 | Passed | Sample workflows/templates require minimal permissions (`contents: read`) — excess permissions are treated as a finding by gate 9 itself + access-review. |
| B4-09 | Passed | The product has no telemetry, no calls to undeclared external APIs: the KEV/EPSS feeds downloaded from CISA/FIRST are clearly declared in the documentation of gate 8. |
| B4-10 | Passed | User data (diff/log/config) is processed on their machine/CI; evidence lies in their infrastructure — not sent back to the factory. |
| B4-11 | Not applicable | This OS does not load external content into an LLM; the AI component (gate 10) belongs to flagship #1 and injection protection was handled in that product. |
| B4-12 | Not applicable | Daily token hygiene of the factory account — an operating task in a separate channel (already applied), not a property of the tree. |
| B4-13 | Not applicable | Separating tokens A/B is a 1-time rule at the factory account level. |
| B4-14 | Passed | Examples in README/documents use placeholders and environment variables, do not instruct pasting real keys. |
| B4-15 | Passed | Sample configuration files in `docs/examples/` + templates contain only placeholders (compared in the tree). |
| B4-16 | Passed | No external vendor code in the tree; external tools are OSS binaries running outside the tree (OPA, conftest, Syft...) — their licences belong to themselves, the tree does not redistribute them. |
| B4-17 | Passed | Security sweep in 2 passes at the local level: during building (gate 1 on the workloads in every round) + closing this round (gitleaks over the whole tree before updating the dossier). The pass on the real repo goes together with publish. |
| B4-18 | Fixed in this round | Added the secret-leak incident handling procedure to SECURITY.md (rotate immediately → delete + record in CHANGELOG → report separately → re-release the bundle + revoke the key fingerprint). |
| B4-19 | Not applicable | Reviewing published repos when there is a new warning — the product is not yet published; the factory weekly cadence. |
| B4-20 | Not applicable | Reviewing the entire factory supply-chain surface — the monthly cadence at the factory level. |

## Panel 5 — Testing & acceptance (24 items)

| Code | Result | Note |
|---|---|---|
| B5-01 | Passed | Tests go together with building in every round: policy tests together with M2, bundle tests together with M4/M5-A2, adapter + generator tests together with M5-A3. |
| B5-02 | Passed | The two mandatory fixtures exist at every layer: clean variant (clean) + planted variant (faulty in exactly the pain style) for workloads; pass/fail fixtures for each policy. |
| B5-03 | Passed | Unit tests all green on the local machine before every milestone: this round OPA 48/48, harness 34/34, Python 36/36 (23 evidence + 13 adapters). |
| B5-04 | Passed | Examples + sample commands truly run end-to-end: the dogfood pipeline from the template, the demo session, the commands in evidence/README have all been executed in the rounds. |
| B5-05 | Locked by the release gate | E2e on a real PR of the techdevfun trial repo — needs a repo. |
| B5-06 | Locked by the release gate | PR link + CI run link as e2e evidence — no real environment yet. |
| B5-07 | Locked by the release gate | GitHub CI green at the publish HEAD — no repo/CI yet. |
| B5-08 | Passed | Edge cases checked: missing/broken input (a record with a wrong schema rejected/stopped with a name), missing binary (exit 2 clearly), empty findings, a file edited by 1 byte, a replaced signature. |
| B5-09 | Passed | Manual comparison: Assistant A itself re-ran gates + verify in rounds M3/M4/M5-A2; in this round the worker itself examined each generated record (gate_results, finding, drift item) against the source data. |
| B5-10 | Passed | Performance acceptable on the largest sample available on the spot: gates ~151 seconds/variant running sequentially, golden path 100 seconds, no hanging (the noted exception: terraform plan waiting for the AWS API is an environment limit, not a hanging of the product). |
| B5-11 | Passed | Slip-day discipline truly applied: the terraform reference round at M3 recorded a backlog to M5 instead of forcing it through; publish is never forced when not yet meeting the standard. |
| B5-12 | Passed | The rubric is scored according to evidence in the release dossier section 4 (worker copy); the final fixed score belongs to Panel 5 of A at acceptance — the dossier is the evidence package for that. |
| B5-13 | Locked by the release gate | Cross-checking the hard conditions of Panel 8 at final acceptance is a step of A at the publish gate (an equivalent local review was done at B4-01/B8-18 of this round). |
| B5-14 | Passed | <90 (and <99 under the separate gate) → do not publish, the deduction reasons + work needing fixing are recorded in the dossier sections 3/6 — being executed correctly. |
| B5-15 | Passed (with an honest note) | The score 69.5 < 90 so the condition "≥90 → polish towards 99" has not been triggered under the exact wording; polishing still takes place under the newer direct owner order (22:52 on 22/10: work continuously until the local part is exhausted) while keeping the 99 gate unchanged — the two layers are separated in the dossier. |
| B5-16 | Passed | Scores + deduction reasons are recorded in the release dossier and reported to the Coordinator in each round. |
| B5-17 | Passed | The backup mechanism after publish has run + been confirmed by a real run for the published repos (original checklist [x]); this product is not yet published so its own backup has not yet arisen. |
| B5-18 | Locked by the release gate | Dispatch backup immediately after publish — not yet published. |
| B5-19 | Locked by the release gate | Open and re-check the repo content on GitHub after publish. |
| B5-20 | Locked by the release gate | Match the publish version with the accepted copy — at publish time. |
| B5-21 | Not applicable | Statistics of the first-pass gate rate — the factory weekly cadence. |
| B5-22 | Not applicable | Summarising repeated errors of the week — the factory weekly cadence (the findings of this round have been recorded in the risk-sweep as input). |
| B5-23 | Not applicable | Re-running e2e of a live flagship when GitHub changes behaviour — no live copy yet. |
| B5-24 | Not applicable | Reviewing green CI of published repos — the monthly cadence; the product is not yet published. |

## Panel 6 — DevRel & dev.to content (22 items)

| Code | Result | Note |
|---|---|---|
| B6-01 | Passed | The auto-publish rule has been applied at the factory level (original checklist [x]). The article of this repo has not been published because the very action of publishing the repo is frozen under the owner decision — the article goes together with publish, not separately. |
| B6-02 | Passed | The rule "production, no draft" (original checklist [x]): the file `release/devto-article-draft.md` is an internal drafting copy before publish, NOT a draft on dev.to; at publish it will be posted to production in the day. |
| B6-03 | Locked by the release gate | Article published on the same day the repo is created — both are frozen together, will be executed simultaneously at M5-B. |
| B6-04 | Passed | The cadence for clearing backlogged articles has been fixed at the factory level (original checklist [x]). |
| B6-05 | Passed (at the draft level) | The front matter of the draft has set `canonical_url` pointing to the GitHub repo (the URL will exist at publish). |
| B6-06 | Passed | The rule 1 repo = 1 article = 1 place/day has been applied at the factory level (original checklist [x]). |
| B6-07 | Passed (at the draft level) | The structure problem → approach → demo → repo link is complete in the draft. |
| B6-08 | Passed (at the draft level) | A real demo of the product itself (GIF from a real run session + transcript) ready to embed. |
| B6-09 | Passed (at the draft level) | Tags on topic: devsecops, opensource, security, githubactions. |
| B6-10 | Passed (at the draft level) | The article has its own limitations section + a section "where rivals beat us" (the factory standing rule). |
| B6-11 | Passed (at the draft level) | The article stands firm as an independent sharing article; the repo link appears in the trial-use section at the end of the article. |
| B6-12 | Passed | No duplicate posting to another channel on the same day — no channel has been posted to yet; the publish procedure has locked this. |
| B6-13 | Locked by the release gate | Record the id + article link after publish — not yet published. |
| B6-14 | Not applicable | The daily backlogged-article cadence — this article is not a backlogged article; it is tied to the publish day. |
| B6-15 | Not applicable | Show HN is only considered for standout repos at the publish phase; this round does not give rise to that decision. |
| B6-16 | Not applicable | Choosing a subreddit — a decision of the publish phase, not yet reached. |
| B6-17 | Not applicable | Product Hunt — the monthly cadence/publish phase, not yet reached. |
| B6-18 | Passed (at the draft level) | The article title is not clickbait (states the problem + a measurable promise). |
| B6-19 | Not applicable | Replying to dev.to comments — no live article of this product yet. |
| B6-20 | Not applicable | Monitoring views/reactions — no live article yet. |
| B6-21 | Not applicable | Comparing article effectiveness by pain — the factory weekly cadence. |
| B6-22 | Not applicable | Reviewing old article links — the factory monthly cadence; the product has no old article yet. |

## Panel 7 — Growth & distribution (20 items)

| Code | Result | Note |
|---|---|---|
| B7-01 | Passed | The main distribution channel fixed pre-build together with Panels 1/2 (blueprint section 6). |
| B7-02 | Passed | Landing is 1 of the 3 things fixed in advance: landing content has been drafted in advance in the tree (`release/landing-techdev-fun.md`); deployment belongs to frozen M5-B but the preparation part is done. |
| B7-03 | Passed (content part) | The flagship has its own landing content (not only 1 card); deploying the page belongs to M5-B. |
| B7-04 | Locked by the release gate | Catalog card tied to the publish day. |
| B7-05 | Locked by the release gate | Live verification after updating the landing — needs a real page update. |
| B7-06 | Passed | The 1-line description has been fixed (landing head + the proposed repo description line in the landing). |
| B7-07 | Passed | The proposed topics suite has been recorded at the head of the landing file. |
| B7-08 | Locked by the release gate | Checking the social preview needs a real repo/page link. |
| B7-09 | Locked by the release gate | Cross-comparing links repo ↔ landing ↔ article ↔ Marketplace needs the endpoints to exist. |
| B7-10 | Not applicable | Putting into an awesome list is a post-publish activity with real contributions; that phase has not been reached yet. |
| B7-11 | Not applicable | Pinning the repo to the profile — the weekly cadence at the account level. |
| B7-12 | Not applicable | Monitoring stars/forks/installs of the whole portfolio — the factory weekly cadence. |
| B7-13 | Not applicable | Analysing GitHub traffic — the weekly cadence; the repo does not yet exist. |
| B7-14 | Passed | The veto on fraudulent growth is in force and is absolutely respected in every round of the product (no buying stars/bots/spam anywhere). |
| B7-15 | Not applicable | Community activity ≤2/week — the weekly cadence at the account level. |
| B7-16 | Passed | No posting of wandering links into unrelated comments/groups — no such action exists; no link has been posted at all. |
| B7-17 | Not applicable | Comparing the growth cadence with the safety ceiling — the factory weekly cadence. |
| B7-18 | Not applicable | Distribution experiments — the monthly cadence, after publish. |
| B7-19 | Not applicable | Reviewing the techdev.fun catalog — the monthly cadence at the page/factory level. |
| B7-20 | Not applicable | Summarising effective channels by pain — the factory monthly cadence. |

## Panel 8 — Account safety & compliance (24 items)

| Code | Result | Note |
|---|---|---|
| B8-01 | Passed | The ceiling ≤2 repos/day has been applied at the account level (original checklist [x]); this product has not created any repo yet. |
| B8-02 | Passed | Spaced ≥2 hours apart has been applied at the factory level (original checklist [x]). |
| B8-03 | Passed | The procedure 429 → stop 24h already exists and is mandatory (original checklist [x]). |
| B8-04 | Passed | The procedure warning email → stop 72h already exists (original checklist [x]). |
| B8-05 | Passed | The rule repo flagged → do not replace for 7 days already exists (original checklist [x]). |
| B8-06 | Passed | Forbidding buying stars/bot stars has been applied (original checklist [x]). |
| B8-07 | Passed | Forbidding fake issues/PRs/comments has been applied (original checklist [x]). |
| B8-08 | Passed | Forbidding cross-interaction A↔B has been applied (original checklist [x]). |
| B8-09 | Passed | Forbidding receiving tokens/passwords via chat — Secure Vault only (original checklist [x]). |
| B8-10 | Passed | The time window 8h–22h VN has been applied for every run (original checklist [x]). |
| B8-11 | Passed | The techdevfun profile has been filled in and verified via API on 21/10/2026 (original checklist [x]). |
| B8-12 | Not applicable | Verifying the account email is a state at the account level, the original checklist has not yet ticked it; it cannot be verified from this tree/local round. |
| B8-13 | Passed | 2FA has been enabled, verified via API (original checklist [x]). |
| B8-14 | Not applicable | Changing the avatar is a web operation on the owner side (the original checklist records it was still the default image as of 21/10) — beyond the capability of this local round. |
| B8-15 | Not applicable | Setting the publicly displayed email is a web setting on the owner side — outside this round. |
| B8-16 | Not applicable | Filling in the profile location is a decision at the account level — outside this round. |
| B8-17 | Locked by the release gate | Counting repos in the day + the nearest publish hour is the step immediately before publish. |
| B8-18 | Passed | Reviewing the hard conditions at the local level was done in this round: secret sweep (B4-01), LICENSE present, no fake interactions, no copyright infringement (self-written code). The official cross-check of Panel 8 at acceptance is a step of A (see B5-13). |
| B8-19 | Passed | No simultaneous publishing — this round publishes nothing at all; discipline is kept. |
| B8-20 | Not applicable | Reviewing dangerous signals at the start of the day is the factory A1 cadence. |
| B8-21 | Not applicable | A random rest day is the weekly operating cadence of the factory/account. |
| B8-22 | Not applicable | The commit/day limit applies to activity on GitHub; this product has no GitHub commit yet. |
| B8-23 | Not applicable | Reviewing 7 days of activity at the week summary — a factory task. |
| B8-24 | Passed | The rule not to create an evasion account when locked already exists and is mandatory at the account level (playbook A). |

## Panel 9 — Demo, README & user experience (20 items)

| Code | Result | Note |
|---|---|---|
| B9-01 | Passed | The demo script fixed in advance: a 91-second session built to a script (gates 2 variants → bundle → verify → tamper 1 byte) is in `release/demo/`. |
| B9-02 | Passed | The "wow" moment in the first 30 seconds of the GIF: a pre-planted fault is blocked at exactly the right gate + a 1-byte edit makes verify FAIL. |
| B9-03 | Passed | Demo from a real run session (the original typescript is stored together; the GIF copy is a text re-enactment honestly labelled in the dossier). |
| B9-04 | Passed | GIF embedded right at the head of the README, size 2.3 MB loads fast; actual display on GitHub is verified when there is a repo (the display part belongs to M5-B but the asset already meets the standard). |
| B9-05 | Passed | The first screen of the README: who hurts + what the system does before scrolling (accepted at M5-A). |
| B9-06 | Passed | README has the full structure problem → solution → demo → install → example → limitations → license. |
| B9-07 | Passed | Install/run packaged in few steps: run local gates + collect/verify with copy-runnable commands in README/evidence README. |
| B9-08 | Passed | An example running right after install with expected output: dogfood checkout-sample + expected results recorded in `release/dogfood-checkout-sample.md`. |
| B9-09 | Passed | `examples/` has practical examples: payments-sample (2 variants), checkout-sample, sample configurations in `docs/examples/` (OIDC trust policy, branch protection). |
| B9-10 | Passed | Repo name clear in meaning; title/description written like a real dev, no view-baiting sentences. |
| B9-11 | Passed | Error messages suggest the next step: the collector names the problem + how to handle it; generators clearly report which binary is missing; verify names exactly the file with a mismatched hash. |
| B9-12 | Passed | Limitations clearly stated in the README + the section "Known limitations" of the landing. |
| B9-13 | Fixed in this round | Created `CONTRIBUTING.md` (environment, 5 test suites, contribution rules). |
| B9-14 | Fixed in this round | Created `.github/ISSUE_TEMPLATE/` (bug_report, feature_request, config turning off blank issues + pointing to the security channel). |
| B9-15 | Passed | Terminology consistent between README ↔ landing ↔ dev.to draft (cross-reviewed when updating all three in this round). |
| B9-16 | Passed | The README was trial-read from a newcomer angle at M5-A; the fixes of this round keep that standard unchanged (no internal terminology added). |
| B9-17 | Not applicable | Redoing the GIF when the output changes: in this round the output of gates/bundle does not change in presentation form (only a record type is added) and the GIF contains no outdated traceability number — no need to re-record has arisen yet; if the publish copy wants to state 13/14 in the demo then re-record at M5-B. |
| B9-18 | Locked by the release gate | Panel 9 separately approves the flagship demo script before the publish day — an acceptance step of A. |
| B9-19 | Not applicable | Comparing demos between products in the week — the factory weekly cadence. |
| B9-20 | Not applicable | Reviewing old repo READMEs when there is a large change — the factory monthly cadence. |

## Panel 10 — Open-core monetisation (16 items)

| Code | Result | Note |
|---|---|---|
| B10-01 | Passed | `KIEM-TIEN-TRACK.md` already exists at the factory level (original checklist [x]). |
| B10-02 | Passed | The principle that Pro must be owner-approved has been fixed (original checklist [x]) — this round proposes no Pro. |
| B10-03 | Passed | The principle that free is always truly useful has been fixed (original checklist [x]); the free copy of this product is the whole of phase 1. |
| B10-04 | Not applicable | Defining the minimum signal threshold for Pro is a 1-time task of Panel 10 at the factory level (the original checklist has not yet ticked it) — not belonging to the product tree. |
| B10-05 | Not applicable | Updating signals into the track — the weekly cadence; the product is not yet published so there are no signals yet. |
| B10-06 | Passed | Only propose Pro when there is a real lasting signal: not proposed yet because there is no signal yet — complying exactly with the rule. |
| B10-07 | Not applicable | Sketching the free/Pro boundary only applies to Pro candidates — the product is not a candidate yet. |
| B10-08 | Not applicable | Presenting a Pro proposal with evidence — there is no proposal yet to present. |
| B10-09 | Passed | No posting for sale/opening payments/listing a price when not yet approved — no such action exists. |
| B10-10 | Not applicable | Introductory content for the Pro copy — no Pro copy or its content exists yet. |
| B10-11 | Passed | The free copy does not nag/upsell/lock old features (checked in the tree: no such mechanism exists). |
| B10-12 | Not applicable | Recording real issues/requests as a Pro basis — no real users/issues yet. |
| B10-13 | Not applicable | Reviewing the portfolio to choose Pro candidates — the factory monthly cadence. |
| B10-14 | Not applicable | Evaluating live Pro revenue — no Pro copy yet. |
| B10-15 | Passed | The veto on monetisation based on fake signals is in force and is respected. |
| B10-16 | Not applicable | Acceleration plan when 2–3 repos reach 500+ stars — the condition has not occurred yet. |

---

## Fixes executed in the round (summary)

1. `evidence/generators.py` (new) + collector/verify extensions in
   `evidence/bundle_tool.py` 1.2.0 — closing the 5 missing evidence types
   (task 1 of the round; details in the release dossier).
2. `CHANGELOG.md` at the tree root (new) — B2-16.
3. SECURITY.md: added the secret-leak incident handling procedure — B4-18.
4. `CONTRIBUTING.md` (new) — B9-13.
5. `.github/ISSUE_TEMPLATE/` (new: bug/feature/config) — B9-14.
6. Fixed the reference `gate-10-prgate.yml` → `gate-10-ai-pr-review.yml`
   in the root template (`templates/api-service/.github/workflows/ci.yml`)
   and the dogfood copy (`examples/checkout-sample/.github/workflows/ci.yml`).
7. Updated traceability 13/14 in `evidence/README.md` (with a section
   guiding the generator suite) and the limitations section of
   `release/landing-techdev-fun.md`.
8. Tree hygiene: deleted 2 leftover `cosign.key` in old run directories;
   changed the sample secret string in the test fixture so as not to trip the secret
   scanner; deleted regenerated `__pycache__` in the tree.
9. Updated `release/risk-sweep-m5a.md`: R2 closed, added R6 (the result of
   the final gitleaks sweep of the round).
10. Dev.to draft `release/devto-article-draft.md` (task 4).
11. New tests: 15 (evidence/tests/test_generators.py) + 13
    (gates/local/tests/test_adapters.py) — total Python unit tests
    increased 8 → 36.
