---
name: phase6-qa
description: >
  Phase 6: QA, Testing & Security Audit.
  Activate when writing tests, running security scans,
  performing UAT, or validating quality.
triggers:
  - "phase 6"
  - "QA"
  - "testing"
  - "security audit"
  - "UAT"
  - "test coverage"
  - "performance test"
  - "accessibility audit"
---

# PHASE 6 — QA, TESTING & SECURITY AUDIT

## SPRINT DISCIPLINE
Work in MICRO-SPRINTS (one test layer per cycle):
1. Unit Tests → Integration Tests → E2E Tests → Security Audit → Performance → Accessibility → UAT → Sign-off
2. `/compact` after each layer. `/clear` after phase completion.
3. Update contextlog.md + buglog.md continuously — every bug found gets a buglog entry immediately.

## INPUTS & VERIFICATION
Read before starting:
- PRD.md — acceptance criteria (Given/When/Then), edge cases (§8), non-functional requirements
- Tech_Blueprint.md — architecture, API contracts, data model, security model
- Sprint_Plan.md — DoD checklist, what was built in Phase 5
- Design_Package — UI states (loading, error, empty) to verify rendering

Any PRD acceptance criteria not testable → flag to PM. Never skip a criterion — mark it as BLOCKED instead.

## SEQUENCE
```
Phase 5 output (code + staging)
  → QA Lead: unit test coverage audit → Integration test audit → E2E test audit
  → Security Auditor: OWASP checklist → dependency scan → threat verification
  → Performance Engineer: Lighthouse → load test → API p95
  → Accessibility Auditor: automated a11y scan → manual keyboard test → screen reader
  → QA Lead: UAT execution → bug triage → fix loop
  → PM + PO: sign-off gate
```
Bugs found → buglog.md immediately → assigned to dev → fix → retest → buglog updated. No bug left in limbo.

---

## TEST STRATEGY

### 1. Unit Tests
**Framework:** Vitest (or Jest — per Tech_Blueprint choice)
**Coverage target:** ≥ 80% line coverage on all new code. 100% on business-critical logic (rule engines, calculations, auth).
**What to test:**
- Every pure function (rule engines, calculations, formatters, validators)
- Edge cases: null/undefined input, boundary values (e.g., exactly 20% YoY increase), empty arrays
- Error paths: thrown exceptions, rejected promises, invalid input handling
- All status transitions (e.g., AUTOMATIC_REDUCTION, PROTEST_RECOMMENDED, NO_ACTION, CONTACT_WESTROM)

**Pattern:** Arrange-Act-Assert. One behavior per test. Descriptive names: `it('returns AUTOMATIC_REDUCTION when YoY increase exceeds 20%')`.
**Mocking:** Mock external APIs and services. Never mock internal modules.

**Run:** `npm run test` or `npx vitest run`. CI blocks merge if coverage drops below threshold.

### 2. Integration Tests
**What to test:**
- API request → service layer → data layer → response (full stack slice)
- AI extraction pipeline: file input → base64 → Gemini API mock → parsed result → rule engine → recommendation
- State transitions in React components: upload → loading → result → error recovery
- API error handling: network failure, invalid API key, malformed response, rate limit (429)

**Tools:** Vitest + React Testing Library for component integration. MSW (Mock Service Worker) for API mocking.
**Scope:** Every API endpoint, every async flow, every form submission.

### 3. End-to-End Tests
**Framework:** Playwright (preferred) or Cypress
**Environment:** Staging (not production, not local)
**Critical paths ONLY:**
1. New user arrives → sees landing page → navigates to Tax Hub → uploads document → sees recommendation
2. New user arrives → navigates to Insurance Hub → uploads declaration page → sees recommendation
3. Invalid file uploaded → sees helpful error → retries with valid file → succeeds
4. API key not configured → prompted to set key → sets key → analysis works
5. Navigation: home ↔ tax hub ↔ insurance hub → back navigation works

**Each E2E test must verify:**
- Correct page title / heading visible
- No JavaScript console errors
- Loading state appears during processing
- Success state shows actual recommendation content
- Error state shows actionable message (not generic "something went wrong")

**Run:** `npx playwright test`. Screenshots on failure. CI blocks merge if any E2E fails.

---

## SECURITY AUDIT CHECKLIST (OWASP Top 10 — 2025)

Run this audit against EVERY feature before sign-off.

### A01 — Broken Access Control
□ Every endpoint checks authentication (is user logged in?)
□ Every endpoint checks authorization (does THIS user own THIS resource?)
□ No direct object references (IDs in URL must be validated against session)
□ CORS restricted to known origins — no wildcards (`*`) in production

### A02 — Cryptographic Failures
□ HTTPS enforced everywhere — no HTTP fallback, HSTS header set
□ API keys not stored in plaintext in client code or git history
□ Sensitive data not logged (no PII, no keys in logs)
□ No deprecated algorithms (MD5, SHA-1) used

### A03 — Injection
□ All user inputs parameterized (SQL: prepared statements; command: no exec with user input)
□ HTML output from AI sanitized with DOMPurify (verify in code review)
□ No eval(), innerHTML with unsanitized strings, or template literals with user data

### A04 — Insecure Design
□ File uploads: type validated by MIME magic bytes (not just extension)
□ File uploads: size limited (≤ 5 MB enforced server-side)
□ Document processing timeout enforced (≤ 30s — no hanging requests)
□ Rate limiting on all AI analysis endpoints (client-side cooldown + server-side IP limit)

### A05 — Security Misconfiguration
□ No stack traces or internal paths in error responses
□ No debug mode or verbose logging in production
□ No hardcoded credentials in code or config files
□ Content Security Policy (CSP) header set and tested
□ X-Frame-Options, X-Content-Type-Options, Referrer-Policy headers set

### A06 — Vulnerable and Outdated Components
□ `npm audit` — zero HIGH or CRITICAL vulnerabilities
□ All production dependencies at latest stable minor/patch
□ No unlicensed packages (check LICENSE field)
□ Dependency lock file committed and up to date

### A07 — Authentication Failures (if auth implemented)
□ Passwords: bcrypt with cost ≥ 12 or argon2id
□ Session tokens: cryptographically random, ≥ 128 bits, HttpOnly + Secure + SameSite=Strict
□ Token expiry: access token ≤ 1 hour, refresh token rotated on use
□ Account lockout after 5 failed attempts (or CAPTCHA)
□ Password reset: time-limited (≤ 15 min), single-use token

### A08 — Data Integrity Failures
□ Extracted JSON from AI validated against schema before use (never trust raw LLM output)
□ No deserialization of untrusted data
□ Subresource integrity (SRI) on any external CDN scripts

### A09 — Logging & Monitoring
□ All security events logged (auth failures, invalid uploads, rate limit hits)
□ Logs do not contain sensitive data (PII, tokens, file contents)
□ Alert defined for quota threshold (80%, 95%, 100% of API budget)

### A10 — SSRF (if server makes external requests)
□ URLs for external requests validated against allowlist
□ No user-controlled URLs fetched without validation

### Dependency Scan
Run: `npm audit --audit-level=high`
All HIGH + CRITICAL findings must be resolved before sign-off. MODERATE findings logged in buglog.md with accepted-risk note from PM.

---

## PERFORMANCE BENCHMARKS

### Frontend (Lighthouse — run on staging, incognito)
| Metric | Target | Fail Threshold |
|--------|--------|---------------|
| Performance score | ≥ 90 | < 75 |
| LCP (Largest Contentful Paint) | < 2.5s | > 4s |
| FID / INP (Interaction to Next Paint) | < 200ms | > 500ms |
| CLS (Cumulative Layout Shift) | < 0.1 | > 0.25 |
| FCP (First Contentful Paint) | < 1.8s | > 3s |
| Accessibility score | ≥ 90 | < 80 |

Run: `npx lighthouse [staging-url] --output html --output-path ./lighthouse-report.html`

### API / Backend
| Metric | Target | Fail Threshold |
|--------|--------|---------------|
| AI extraction response time (p95) | < 5s | > 10s |
| AI recommendation response time (p95) | < 5s | > 10s |
| Full analysis flow end-to-end (p95) | < 10s | > 20s |
| Error rate | < 1% | > 5% |

### Load Test
Tool: k6 or Artillery
Scenario: 50 concurrent users × 10 min × 2 requests/min
Verify: No memory leak, no error rate spike, response times stay within targets.

---

## ACCESSIBILITY AUDIT (WCAG 2.1 AA)

### Automated Scan
Tool: axe DevTools (browser extension) or `@axe-core/playwright` in E2E suite.
Run on every screen. Zero CRITICAL or SERIOUS violations before sign-off.

### Manual Keyboard Navigation Test
Walk through all critical paths using ONLY keyboard (no mouse):
□ Tab order is logical (top-left → bottom-right, no jumps)
□ All interactive elements reachable by Tab / Shift+Tab
□ Buttons activated by Enter or Space
□ Modals: focus trapped inside, closed by Escape, focus returns to trigger on close
□ File upload: accessible via keyboard (not mouse-only)
□ No keyboard trap (can always Tab away from any element)

### Screen Reader Test
Tool: NVDA (Windows, free) or VoiceOver (Mac, built-in)
Browser: Chrome + NVDA or Safari + VoiceOver
□ Page title announces correctly on navigation
□ Headings create logical document outline (H1 → H2 → H3, no skips)
□ Images with meaning have descriptive alt text
□ Upload zone announces "file upload" role and instructions
□ Loading state announced to screen reader (`aria-live="polite"`)
□ Error messages announced immediately (`aria-live="assertive"`)
□ Recommendation result announced when it appears

---

## BUG SEVERITY CLASSIFICATION

| Severity | Definition | SLA | Example |
|----------|-----------|-----|---------|
| **P0 — Critical** | Blocks core function or causes data loss/security breach | Fix before any sign-off | Wrong rule engine result, API key exposed |
| **P1 — High** | Major feature broken for most users | Fix before Phase 7 | Upload fails on valid PDF, recommendation not shown |
| **P2 — Medium** | Feature works but UX is degraded | Fix in next sprint | Loading spinner doesn't show, typo in recommendation |
| **P3 — Low** | Cosmetic or minor edge case | Backlog | Padding misalignment on narrow screen |

All P0 and P1 bugs: dev fix → QA retest → buglog updated → sign-off withheld until resolved.
P2 and P3: logged in buglog.md → PM decides include/defer.

---

## UAT PROTOCOL (User Acceptance Testing)

**Participants:** 3–5 real users matching primary persona (Texas rental property owners, non-technical)
**Environment:** Staging with production-like data
**Facilitator:** QA Lead (observe, don't help — note where users get stuck)

### UAT Scenarios
1. "Upload your most recent property tax notice and find out what to do."
2. "Upload your insurance declaration page and check if your policy is right for a rental."
3. "Find the contact information for your county's appraisal district."
4. "Read the 20% rule and explain it back to me."

### UAT Success Criteria
□ ≥ 80% of participants complete primary task without facilitator intervention
□ Zero P0 or P1 bugs discovered in UAT session
□ Average task completion time ≤ 5 minutes
□ User satisfaction: ≥ 4/5 on "I understood what action to take after using this tool"

### Sign-off Process
PO + PM review UAT findings. For each finding:
- Blocks launch? → fix required before Phase 7
- Acceptable risk? → PM documents rationale → logged in contextlog.md
- Out of scope? → logged in backlog for Phase 9 iteration

---

## DELIVERABLES CHECKLIST

```
□ test/unit/        — unit tests, ≥80% coverage report
□ test/integration/ — integration tests, all API flows
□ test/e2e/         — Playwright E2E, all critical paths
□ security-audit.md — OWASP checklist completed, findings + resolutions
□ lighthouse-report.html — Lighthouse report on staging
□ a11y-audit.md     — Automated + manual accessibility findings
□ uat-report.md     — UAT participants, scenarios, findings, sign-off
□ buglog.md         — All bugs found, severity, status (resolved/deferred)
```

## ALL ROLES — RULES
- Never mark a test as "passed" when it isn't. Never skip a test to meet a deadline.
- Every bug found: buglog.md entry immediately (not at the end of the day).
- Security findings: PM informed within 1 hour of discovery. P0 security = stop all work.
- Don't fix bugs without a root-cause analysis. Symptoms → causes → fix.
- Re-test every fix. Don't assume it worked.

## PHASE 6 COMPLETE WHEN
□ Unit coverage ≥ 80% on all new code □ Integration tests pass for all API flows
□ E2E tests pass for all critical paths □ Zero P0/P1 bugs open
□ OWASP checklist 100% complete □ `npm audit` zero HIGH/CRITICAL
□ Lighthouse Performance ≥ 90 □ Zero CRITICAL/SERIOUS a11y violations
□ UAT completed with ≥ 80% task success □ PO + PM sign-off obtained
□ buglog.md current □ contextlog.md updated → `/compact` → `/clear`
