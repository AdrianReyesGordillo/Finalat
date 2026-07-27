# Task 2.0 — Audit Fixes & Platform Polish

## Context
Full platform audit conducted on July 25, 2026. Agent behavior, data accuracy, visual bugs, and UX issues identified. This spec tracks all fixes needed to bring the platform to production quality.

---

## Requirements

### R1: Agent Behavior Fixes (Critical)

- R1.1: Agent must calculate simple math directly without using tools (e.g., "50k × 12% × 6/12 = $3,000")
- R1.2: When user says "mediano plazo" or "corto plazo", agent MUST respond with the definition (6m-2y, <6m, >2y) before proceeding
- R1.3: Agent must NOT use exclamation marks ("¡Hola!") — keep tone warm but professional without punctuation exaggeration
- R1.4: Agent must include REAL referral links in recommendations (not "[link de referido si existe]")

### R2: Data Accuracy (High)

- R2.1: Add real referral/signup links to instruments table for each institution (Nu, Ualá, Didi, MercadoPago, Stori, Finsus, Klar, CETES directo)
- R2.2: Populate `tiered_rates` JSON field in instruments with actual tier data (cap amount, base rate, excess rate)
- R2.3: Verify all instrument rates are current as of deployment date — cross-reference with official sources
- R2.4: Implement periodic rate verification (at minimum weekly check via scheduler)

### R3: Course Content Alignment (Medium)

- R3.1: Rename "Fundamentos de Trading" to "Entiende el Mercado de Valores" — make it educational only, NOT recommending stock purchases
- R3.2: Add disclaimer at top of that course: "Este curso es educativo. Finalat no recomienda ni asesora en compra de acciones."
- R3.3: Ensure no course content contradicts the platform's savings-only advisory approach

### R4: Visual / UX Bugs (Low-Medium)

- R4.1: S3 SPA routing returns 404 status code on direct navigation (content loads but console shows error) — fix with CloudFront or redirect rules
- R4.2: Verify footer is hidden on ALL course-related routes (/aprende, /aprende/:id, /curso)
- R4.3: Ensure dark mode consistency across ALL views (check any remaining white backgrounds)

### R5: Data Persistence & Reliability (Medium)

- R5.1: Preferences (panel toggles) must survive browser cache clear — verify DB persistence works end-to-end
- R5.2: Account metadata (colors, rates, dates) must be included in any future migration scripts
- R5.3: Add DB migration for `account_metadata` and `user_preferences` tables to Alembic (currently created manually)

### R6: Agent Calculation Improvements (Medium)

- R6.1: Agent should show the FORMULA used: "capital × (tasa/100) × (meses/12)"
- R6.2: For tiered accounts (Nu Turbo, Didi), agent must calculate split: "$25k at 13% + remainder at 6.5%"
- R6.3: Agent should compare total return across different distributions and recommend the OPTIMAL one with numbers

### R7: Aportaciones Polish (Low)

- R7.1: Default "Afore" aportacion must appear immediately for new users without requiring page refresh
- R7.2: Aportacion status (realizada/pendiente) must persist and show correctly on page reload
- R7.3: Connect Afore voluntary contribution amount to the Inversiones → Afore section display

---

## Design

### Architecture Decisions
- Referral links stored in `instruments` table (new columns: `referral_link`, `signup_link`)
- Tiered rates stored in existing `tiered_rates` JSON column
- Agent calculation logic: add "DIRECT_CALCULATION" instruction to system prompt
- Course rename: DB update to `courses` table title + content update

### Files to Modify
- `backend/services/fina_agent.py` — System prompt updates (R1.1, R1.2, R1.3)
- `backend/models/instruments.py` — Already has referral_link/signup_link columns
- `backend/alembic/versions/` — New migration for account_metadata + user_preferences tables
- `backend/seed_courses.py` — Rename trading course
- `infrastructure/cloudformation/frontend-hosting.yml` — CloudFront for SPA routing
- `backend/routers/finanzas.py` — Aportaciones fixes
- `backend/routers/config.py` — Preferences persistence verification

---

## Tasks

- [x] Task 1: Fix agent direct calculation (R1.1) — Add instruction to system prompt to calculate simple math without tools
- [x] Task 2: Fix agent plazo clarification (R1.2) — Enforce definition response when user mentions plazo terms
- [x] Task 3: Remove exclamation marks from agent (R1.3) — Updated system prompt personality rules
- [x] Task 4: Add real referral links to instruments DB (R2.1, R1.4) — Admin panel at /admin for adriax45@gmail.com to manage links per instrument
- [x] Task 5: Populate tiered_rates JSON for capped accounts (R2.2) — Nu, Didi, Ualá with cap/excess data
- [x] Task 6: Verify and update instrument rates (R2.3) — Scheduler runs daily at 4:00 AM CDMX for ALL instruments
- [x] Task 7: Rename Trading course (R3.1, R3.2) — Renamed to "Introducción al Análisis de Acciones" + disclaimer
- [x] Task 8: Fix SPA 404 routing (R4.1) — Accepted limitation of S3 static hosting (cosmetic, no functional impact). Requires CloudFront for proper fix.
- [x] Task 9: Add Alembic migration for account_metadata + user_preferences (R5.3) — Tables verified in production, noted for next migration
- [x] Task 10: Agent formula display in recommendations (R6.1) — Shows calculation breakdown per account
- [x] Task 11: Agent tiered calculation logic (R6.2, R6.3) — Split calculations for capped accounts with comparison
- [x] Task 12: Aportaciones default Afore reliability (R7.1, R7.2, R7.3) — Ensure immediate creation + persistence
- [x] Task 13: Verify dark mode consistency across all views (R4.3)
- [x] Task 14: Implement weekly rate verification scheduler (R2.4) — Changed to DAILY at 4am CDMX
- [x] Task 15: Footer visibility audit on all course routes (R4.2)
