# TrabajoAI — Product Requirements Document (PRD)

**Version:** 1.0 · **Date:** 2026-11-08 · **Status:** Working specification / implementation in progress  
**Owner:** Product owner (single-user MVP)  
**Code:** [dvrbuilder94/trabajoai](https://github.com/dvrbuilder94/trabajoai)  
**Backend:** Supabase AIJOBS (project `lpbqzagdforlafvavgkx`)  
**Design constraint:** No Lovable; prioritize low recurring cost, explicit control, and portable code.

> This PRD is the source of truth for the product. "Built" means code or schema was written; it does not mean end-to-end operation has been verified. Treat this as a living document. Never confuse mock postings with real openings.

## 1. Problem and outcome

Searching across companies, countries and job families consumes time; many listings are expired, duplicated, geo-restricted, or a poor fit. Creating a tailored CV for every opening adds friction. The product should find credible opportunities daily, explain fit, prepare tailored documents and support application review. The user makes the final decision before every submission.

**North-star outcome:** Number of *relevant, verified, actionable* job opportunities advanced to approved application per week; secondary metrics: interviews and offers, not raw job count.

### Non-goals for initial release
- Mass automated applications, CAPTCHA circumvention, scraping that violates site rules, automatic messaging.
- Fabricating employment history, quantitative achievements, salary, visa sponsorship or remote-country eligibility.
- Monetization, multiple users, a native mobile app, paid CV-generation services, or LinkedIn bot automation.

## 2. Primary user and constraints

One Chile-based bilingual Spanish/English B2 professional in financial services, corporate strategy, venture development, fintech, payments, capital markets, business/product strategy, and adjacent AI roles.

**Search tracks (not mutually exclusive):**
1. Chile: high-compensation strategy, leadership, business development and product roles.
2. Remote: employer explicitly accepts a worker based in **Chile** (not merely "Remote", "US remote" or "LATAM" without verification).
3. Relocation: US (especially Miami), Europe, UAE/Dubai, Singapore; confirm sponsorship or feasible hiring route; EU work eligibility may apply in Europe, subject to applicable jurisdiction.
4. Broad discovery: transferable opportunities beyond familiar job titles; Spanish fluency as differentiator.

**Compensation:** For international in-person opportunities, target at least USD 100k gross/year when disclosed; Chilean or remote compensation assessed in relevant local market context. Never infer undisclosed salary. Do not filter out unspecified pay merely because absent.

**Budget:** Design for free tiers plus controlled and optional AI API spend. A target is not a guarantee; enforce configurable caps and measure costs.

## 3. User journey

1. Open app from mobile or desktop; sign in for personal features.
2. See **new since last visit**, **high fit**, **requires verification**, **saved**, **approved**, and **submitted** counts.
3. Filter by function, location, remote-from-Chile eligibility, salary, language advantage, job age and company.
4. Open detail page: authoritative company apply URL, posted/last-checked timestamps, factual responsibilities, fit evidence, missing requirements, salary source, visa/geo evidence, confidence and verification status.
5. Save, reject or approve an opportunity for CV preparation.
6. Generate a tailored **draft** CV from verified master profile; view difference from original, edit, export as PDF/DOCX.
7. Prepare short application answers/cover letter if needed.
8. User reviews the **exact** final files, company, destination URL, fields and privacy notice; explicitly confirms submission.
9. For supported sites, authorized submission completes and returns confirmation; otherwise hand-off to official apply page with a prepared package. "Approved" is never "submitted".
10. Track application lifecycle, interview reminders, decisions, and user corrections to future matching.

## 4. Requirements and acceptance criteria

| ID | Priority | Requirement | Testable acceptance |
|---|---|---|---|
| FR-01 | P0 | Daily multi-source collection | Scheduled run records source, fetched timestamp, successes/failures; one source failure does not erase previous data |
| FR-02 | P0 | Deduplicate and freshness | Stable job ID, canonical URL and company; detect updates, first_seen and last_seen, closed status; no duplicate display |
| FR-03 | P0 | Real/verified distinction | Every card labels **verified active**, **not independently verified**, **closed**, or **demo**; no fictitious job in production results |
| FR-04 | P0 | Search and filters | Keyword, fit, market, function, remote-eligibility status and freshness filters work on mobile and desktop |
| FR-05 | P0 | Geo and work eligibility | Remote-from-Chile and sponsorship each have values confirmed / unknown / excluded, with source excerpts; unknown never counted as confirmed |
| FR-06 | P0 | Matching and explanation | Deterministic baseline score 0–100, separate eligibility blockers and explainable positives/gaps; no "probability of selection" claim without calibration |
| FR-07 | P0 | Secure account and data | Supabase Auth session, RLS tests for own CV, decisions and generated documents; anon cannot access private profile |
| FR-08 | P0 | Durable decisions | Save/reject/approve synchronizes to Supabase by user; persists across browsers and devices |
| FR-09 | P1 | Master CV and source of truth | User can review verified CV facts and edit profile; source uploaded to private storage, not public repo |
| FR-10 | P1 | CV tailored to job | Spanish/English versions preserve factual experience; side-by-side diff, download PDF/DOCX and version history |
| FR-11 | P1 | Application review queue | User sees company, position, destination, answers and attachments before *each* send; explicit confirmation required |
| FR-12 | P2 | Supported submission routes | Integrations or browser workflows only when authorized and supported; save confirmation ID/time or clearly mark manual handoff |
| FR-13 | P2 | Follow-up tracking | Applied, interview, rejected, offer, withdrawn; timestamps and notes; no automatic outreach |
| FR-14 | P1 | Cost controls | Per-day API usage counts and configurable spend limit; degrade gracefully to heuristic matching |
| FR-15 | P0 | Operator visibility | Source-run dashboard shows last success, errors, stale results and integration health |

### Quality bar
- Empty state explicitly tells the user why there are zero jobs.
- Keyboard navigation, accessible labels, usable on 375px mobile width.
- No secrets in GitHub, client-side bundles or build artifacts. Public publishable Supabase key is permitted **only with proper RLS**.
- Job descriptions are untrusted input: never follow instructions embedded in listing content.
- No POST/application action without a fresh, direct user confirmation.
- On failed external submission, mark unknown/pending verification; **never** silently label as applied.
- Tests cover RLS, link validation, deduplication, UI workflows and CV fact preservation.

## 5. Data model (target)

- `job_sources`: provider, org slug, enabled, last_run, error history.
- `collection_runs`: start/end, successes, failures, counts, cost.
- `job_listings`: canonical ID/url, title, company, description, source, first/last seen, status, location, salary and evidence, geo eligibility and evidence.
- `candidate_profiles`: user_id, verified skills, source-of-truth master CV and version.
- `job_decisions`: (user_id, job_id), review state, notes, timestamps.
- `cv_variants`: user, job, document version, language, change summary, approved export.
- `applications`: user, job, status, application route, submitted_at, confirmation, audit log.
- `application_approvals`: user, job, payload digest, time, exact destination, decision.
- Private Storage bucket for master CV and generated documents with owner-scoped access.

**Security:** public.job_listings can be readable without login; all candidate data and decisions require owner-scoped RLS. Any temporary internal imports require restricted schema/grants and explicit security review. Confirm no service-role keys leak to the browser. Authentication must be complete before exposing any CV viewer.

## 6. Technical architecture

- **Frontend:** current static HTML/JS and CSS (no framework required to achieve initial visual MVP); evolve to React only when UI complexity justifies it.
- **Hosting:** GitHub Pages for public app shell / mock preview; optionally switch to Cloudflare Pages for production. Static deployment is **not** private auth by itself.
- **Persistence:** Supabase PostgreSQL + Auth + RLS; Storage private documents.
- **Collectors:** Python on GitHub Actions; Greenhouse/Lever public postings APIs first, expand with Ashby and official career sites where permitted. Backoff, timeouts, source health and retries.
- **Ingestion:** server-side validated upsert to Supabase via a secure channel, not a browser-exposed service role. Do not commit private tokens.
- **AI enrichment:** optional OpenAI API server-side for normalized role taxonomy, verified evidence and CV drafting; explicit cost caps; deterministic fallback.
- **Exports:** server-side or local DOCX/PDF renderer; preserve editable master CV.
- **Application layer:** separate approval and submission service with an immutable approval record.

### Explicit architecture decisions
- No Lovable.
- One-user MVP before multitenancy.
- Human approval required per application; no auto-send.
- Never represent guessed visa/salary/remote eligibility as verified.
- GitHub repository may be public; all candidate data remains private in Supabase.
- Use documented APIs where available; respect robots.txt, provider rules and rate limits.

## 7. Operational metrics

Measure: unique open roles/new roles per run; percent with working official links; percent with confirmed Chile-remote or relocation compatibility; high-fit opportunities/week; save-to-approved rate; approved-to-submitted rate; interviews/applications; false positives; collector success rate; AI spend per run. Set targets only after observing baseline.

## 8. Milestones / release gates

### M0: Visible and working (current priority)
- [x] Basic responsive dashboard committed to GitHub.
- [x] Explicit demo mode with fictional jobs.
- [x] GitHub Pages workflow committed.
- [x] Collector code and scheduled GitHub Actions workflow committed.
- [x] Initial Supabase schema committed and applied.
- [x] Existing CV text imported into internal Supabase staging table.
- [ ] Confirm live GitHub Pages deployment succeeds and app loads on mobile.
- [ ] Confirm scheduled collector runs successfully and produces fresh postings from source APIs (unverified as of latest check).
- [x] Seed three real-source job *candidates* in Supabase, explicitly marked as not independently verified for application availability or Chile eligibility.
- [x] Commit GitHub Actions → Supabase sync script with server-side credentials and fallback to public JSON.
- [ ] Configure GitHub Actions secrets and verify end-to-end DB sync; verify links and location requirements.
- [ ] Display real jobs with evidence, refresh timestamp and **no demo leakage**.
- [ ] Run basic security verification of private CV staging area and RLS.

### M1: Useful personal dashboard
- [ ] Supabase Auth (account provisioning and sign-in).
- [ ] Decisions in Supabase; persist on multiple devices.
- [ ] Source health, job statuses, deduplication, verification flags.
- [ ] Matching methodology and configurable preferences.
- [ ] Show last successful refresh and errors.

### M2: Personalized CV factory
- [ ] Transfer CV from private staging to verified owner account.
- [ ] Master CV editing and audit trail.
- [ ] Generate CV variants for selected roles; user validates factual correctness.
- [ ] Export PDF/DOCX and approve final attachment.

### M3: Assisted applying
- [ ] Submission queue with exact review of company, URL, answers and documents.
- [ ] Manual handoff for unsupported destinations.
- [ ] Supported integrations only, with explicit per-application user approval and confirmation logging.
- [ ] Interview funnel and follow-up tracking.

## 9. Current implementation inventory (as of 2026-11-08)

**GitHub:** `index.html`, `scripts/collect.py`, `data/sources.json`, `data/jobs.json`, workflows `collect.yml` and `pages.yml`, `supabase/schema.sql`. UI approvals are stored locally in browser and **do not submit anything**. Source list is small and collection has not been verified end to end. GitHub Pages publication has not yet been independently verified.

**Supabase:** AIJOBS project was connected; four initial `public` tables exist with RLS, plus restricted `internal.cv_imports` with one 3,099-character CV import. There were zero Auth users at last check. Three real-source job candidates were manually seeded on 2026-11-08; all remain unverified for Chile eligibility and application status. The internal staging table's RLS state requires a separate review; restricted-schema grants should not be mistaken for a completed security audit.

## 10. Risks and open decisions

| Risk / question | Handling |
|---|---|
| External ATS posting URL has expired | Re-check before recommendation; record date and failure |
| Remote label doesn't permit Chile | Separate "remote" from "Chile eligible" and require direct evidence |
| Data sources fail or throttle | Preserve old data with stale markers; surface failures |
| CV tailoring hallucinates achievements | Only rewrite source-backed facts; user diff and explicit approval |
| Public frontend accesses personal profile | No CV display before Auth/RLS checks |
| Form submission lacks stable API | Use manual prefilled workflow; no CAPTCHA bypass |
| Supabase staging import has no linked account | Authenticate and transfer only after ownership is proven |
| Pages activation / external deployment blocked | Provide local preview; never assert live URL without testing |
| Cost unpredictability | Budget caps, cheap models, batch processing and deterministic fallback |

## 11. Definition of done for first real release

A user can open a verified live URL, sign in, see at least one independently checked legitimate job or a truthful no-results state, inspect source/evidence, persist a decision, and retrieve it from another browser session. No CV content is public; no application is submitted. Automated tests and manual smoke checks demonstrate this flow.

---

**Change control:** Any new feature must map to a requirement ID or be added here before implementation. Update the checkbox, evidence link, owner and verification date when a milestone is completed.
