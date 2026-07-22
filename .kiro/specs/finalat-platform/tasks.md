# Implementation Plan: Finalat Platform

## Overview

This implementation plan covers the full-stack Finalat financial advisory platform for Mexico. Tasks are ordered by dependency: foundational infrastructure and shared services first, then backend modules, frontend shell, feature pages, AI advisor integration, and finally CI/CD and deployment. Each task builds incrementally on previous work, ensuring no orphaned code.

## Tasks

- [x] 1. Project scaffolding and shared infrastructure
  - [x] 1.1 Initialize backend project structure (FastAPI + Python 3.13)
    - Create `backend/` directory with `main.py`, `config.py`, `requirements.txt`
    - Set up FastAPI app with CORS middleware, Pydantic BaseSettings for config
    - Add `backend/models/database.py` with SQLAlchemy 2.0 engine + async session (PostgreSQL + SQLite fallback)
    - Add `backend/schemas/common.py` with APIResponse envelope schema
    - Add `backend/utils/response.py` with standard response builder
    - _Requirements: 19.1, 20.2, 20.3_

  - [x] 1.2 Initialize frontend project structure (Vue 3 + Vite + TypeScript)
    - Create `frontend/` directory with Vite + Vue 3 + TypeScript template
    - Install dependencies: vue-router, pinia, tailwindcss, primevue 4, axios
    - Configure Tailwind CSS with dark mode (`class` strategy)
    - Set up PrimeVue 4 plugin and theme
    - Add `frontend/src/types/index.ts` with core TypeScript interfaces (APIResponse, financial models)
    - Configure environment variables (VITE_API_URL, VITE_FIREBASE_CONFIG)
    - _Requirements: 21.1, 21.8, 21.9_

  - [x] 1.3 Define database schema and migration scripts
    - Create SQLAlchemy models for all 15 tables: users, ahorro, creditos, gastos_ingresos, deudas, aportaciones, afore, gbm_portfolio, categories, instruments, courses, lessons, lesson_progress, conversation_sessions, update_tracker
    - Define UUID PKs, user_id VARCHAR FKs, TEXT columns for encrypted fields, JSONB for tiered_rates/conversation
    - Add indexes on user_id columns for all user-scoped tables
    - Add created_at/updated_at timestamps with auto-update triggers
    - Configure cascade deletes from users table
    - Add Alembic for migrations
    - _Requirements: 19.2, 19.3, 19.4, 19.5, 19.6, 19.7, 19.8_

  - [x] 1.4 Implement Encryption Service
    - Create `backend/services/encryption.py` with EncryptionService class
    - Implement `encrypt(plaintext) -> ciphertext` and `decrypt(ciphertext) -> plaintext` using Fernet (cryptography library)
    - Implement `encrypt_fields(data, fields)` and `decrypt_fields(data, fields)` for batch field encryption
    - Load FERNET_KEY from environment variable; fail app startup if missing/invalid
    - Raise EncryptionError on decryption failures without logging plaintext
    - Ensure single field operation completes within 50ms
    - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5, 11.6, 11.7, 11.8_

  - [ ]* 1.5 Write property tests for Encryption Service
    - **Property 1: Encryption Round-Trip** — For any plaintext string, encrypt then decrypt produces identical original
    - **Property 2: Encryption Non-Identity** — For any non-empty plaintext, ciphertext ≠ plaintext
    - **Property 3: Decryption Failure on Corrupted Input** — Invalid tokens raise EncryptionError
    - **Validates: Requirements 11.2, 11.3, 11.6**

  - [x] 1.6 Implement LRU Cache Service
    - Create `backend/services/cache.py` with LRUCache class
    - Implement in-memory LRU eviction with max 500 entries
    - Implement 5-minute TTL per entry with expiry on access
    - Scope all cache entries by user_id (key = `{user_id}:{module}:{resource_key}`)
    - Implement `invalidate(user_id, module)` to clear all module entries for a user
    - Implement `invalidate_user(user_id)` to clear all entries for a user
    - _Requirements: 16.1, 16.2, 16.3, 16.4, 16.5, 16.6, 16.7, 16.8_

  - [ ]* 1.7 Write property tests for LRU Cache
    - **Property 11: Cache Size Invariant** — Cache never exceeds 500 entries after any sequence of operations
    - **Property 12: Cache TTL Expiry** — Entries older than 5 minutes return None
    - **Property 13: Cache User Isolation** — Data cached under user A never returned for user B
    - **Property 14: Cache Invalidation on Write** — After invalidation, reads return cache miss
    - **Validates: Requirements 16.1, 16.2, 16.3, 16.6, 16.7**

- [x] 2. Authentication and middleware layer
  - [x] 2.1 Implement JWT verification middleware
    - Create `backend/middleware/auth.py` with Firebase JWT validation
    - Validate Bearer token against Google's public X.509 certificates (RS256)
    - Extract user_id (Firebase UID) from validated token and inject into request state
    - Return HTTP 401 for missing, expired, or invalid tokens
    - Skip auth for /api/auth/login and /api/auth/register endpoints
    - _Requirements: 1.6, 1.7, 1.8, 1.9, 20.6_

  - [x] 2.2 Implement rate limiting middleware
    - Create `backend/middleware/rate_limiter.py`
    - Implement per-user rate limiting: 100 requests per minute per user_id
    - Return HTTP 429 with appropriate error envelope when limit exceeded
    - Use in-memory sliding window counter
    - _Requirements: 20.7_

  - [x] 2.3 Configure security headers and CORS
    - Add security headers middleware: Content-Security-Policy, X-Content-Type-Options: nosniff, X-Frame-Options: DENY, Strict-Transport-Security (max-age=31536000)
    - Configure CORS to allow only the SPA domain (CloudFront URL from env var)
    - Add gzip compression middleware for JSON responses > 1KB
    - _Requirements: 24.5, 20.8, 25.7_

  - [x] 2.4 Implement shared validation utilities
    - Create `backend/utils/validators.py` with reusable validators
    - Monetary amount validator: 0.01–999,999,999.99
    - String length validators (100 chars for names, 500 for descriptions)
    - SQL injection and XSS pattern detection in inputs
    - Sanitization helpers for all user-provided text
    - _Requirements: 24.1, 24.2, 3.7, 4.7, 5.10, 6.7_

  - [ ]* 2.5 Write property test for monetary validation
    - **Property 16: Monetary Field Validation Bounds** — Amounts in [0.01, 999999999.99] accepted; outside rejected
    - **Validates: Requirements 3.1, 3.7, 4.7, 5.10, 6.7, 7.6, 8.6**

- [x] 3. Checkpoint - Core infrastructure verification
  - Ensure all tests pass, ask the user if questions arise.

- [x] 4. Backend CRUD modules — Financial data
  - [x] 4.1 Implement Savings (Ahorro) router and service
    - Create `backend/routers/ahorro.py` with GET/POST/PUT/DELETE endpoints
    - Create Pydantic schemas for ahorro request/response
    - Integrate Encryption Service for amount field (encrypt on write, decrypt on read)
    - Scope all queries to authenticated user_id
    - Return aggregate total savings in list response
    - Handle partial results on decryption failure (exclude failed entries, return error count)
    - Integrate with Cache (invalidate on writes, serve from cache on reads)
    - Integrate with Update Tracker (record last write timestamp)
    - Require confirmation-aware delete (backend ownership check)
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8, 3.9_

  - [x] 4.2 Implement Credit Cards (Creditos) router and service
    - Create `backend/routers/creditos.py` with GET/POST/PUT/DELETE endpoints
    - Create Pydantic schemas for creditos request/response
    - Encrypt balance, limit, and minimum_payment fields
    - Calculate utilization percentage (balance/limit × 100) in response; return "N/A" when limit is 0
    - Scope all queries to user_id; return 403 on cross-user access
    - Handle encryption failures with error response
    - Integrate with Cache and Update Tracker
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7, 4.8, 4.9_

  - [x] 4.3 Implement Expenses/Income (Gastos_Ingresos) router and service
    - Create `backend/routers/gastos_ingresos.py` with GET/POST/PUT/DELETE endpoints
    - Create Pydantic schemas with type (income/expense), amount, description, category_id, date
    - Encrypt amount and description fields
    - Scope all queries to user_id; return 403 on cross-user access
    - Seed default categories (Sueldo, Creditos, Prestamos, Otros) on user creation
    - Protect system categories (Sueldo, Creditos) from deletion/modification (HTTP 403)
    - Return totals grouped by category and time period for chart data
    - Integrate with Cache and Update Tracker
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7, 5.8, 5.9, 5.10, 5.11, 5.12_

  - [x] 4.4 Implement Categories router and service
    - Create `backend/routers/categories.py` with GET/POST/PUT/DELETE endpoints
    - Implement system category protection (is_system=true → reject DELETE/PUT with 403)
    - Auto-seed default categories for new users
    - Scope all queries to user_id
    - _Requirements: 5.6, 5.7, 5.8_

  - [ ]* 4.5 Write property test for Protected Category Immutability
    - **Property 20: Protected Category Immutability** — System categories (Sueldo, Creditos) reject modifications with 403
    - **Validates: Requirements 5.8**

  - [x] 4.6 Implement Debts (Deudas) router and service
    - Create `backend/routers/deudas.py` with GET/POST/PUT/DELETE endpoints
    - Create Pydantic schemas with creditor_name, total_amount, monthly_payment, interest_rate, start_date
    - Encrypt total_amount and monthly_payment fields
    - Calculate remaining balance, estimated payoff date, and total interest cost
    - Return aggregate total debt and aggregate monthly payment
    - Handle partial results on decryption failure
    - Scope all queries to user_id; return 403 on cross-user access
    - Integrate with Cache and Update Tracker
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7, 6.8, 6.9_

  - [x] 4.7 Implement Contributions (Aportaciones) router and service
    - Create `backend/routers/aportaciones.py` with GET/POST/PUT/DELETE endpoints
    - Create Pydantic schemas with amount, frequency (weekly/biweekly/monthly), target_name, start_date
    - Encrypt amount field
    - Calculate projected annual contribution (amount × frequency multiplier: weekly=52, biweekly=26, monthly=12)
    - Return aggregate annual total across all schedules
    - Validate frequency enum values
    - Handle partial results on decryption failure
    - Scope all queries to user_id; integrate with Cache and Update Tracker
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 7.7_

  - [x] 4.8 Implement Afore (Pension) router and service
    - Create `backend/routers/afore.py` with GET/POST/PUT/DELETE endpoints
    - Create Pydantic schemas with provider_name, balance, last_update_date
    - Encrypt balance field
    - Return total Afore balance across all providers
    - Track days since last update via Update Tracker
    - Scope all queries to user_id; integrate with Cache
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 8.6, 8.7_

  - [x] 4.9 Implement GBM Portfolio router and service
    - Create `backend/routers/gbm.py` with GET, POST (upload), DELETE endpoints
    - Implement Excel (.xlsx) file upload parsing using openpyxl
    - Validate file format and reject files > 5MB or non-.xlsx
    - Extract positions: ticker, shares, avg_cost, market_value
    - Encrypt avg_cost and market_value fields
    - Full replacement on re-upload (delete old, insert new)
    - Skip rows with missing required fields; return skip count in response
    - Calculate gain/loss percentage per position: ((market_value - shares×avg_cost) / (shares×avg_cost)) × 100
    - Return total portfolio value
    - Scope all queries to user_id; integrate with Cache and Update Tracker
    - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5, 10.6, 10.7, 10.8, 10.9_

  - [x] 4.10 Implement Net Worth (Patrimonio) endpoint
    - Create `backend/routers/patrimonio.py` with GET endpoint
    - Aggregate data from ahorro, afore, gbm (assets) and deudas, creditos (liabilities)
    - Calculate: patrimonio = (total_ahorro + total_afore + total_gbm) - (total_deudas + total_creditos)
    - Return breakdown showing each component's contribution
    - Handle partial data when modules return errors (calculate with available data, indicate missing modules)
    - Scope all component queries to user_id
    - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 9.6_

  - [ ]* 4.11 Write property test for Net Worth Calculation
    - **Property 15: Net Worth Calculation Correctness** — patrimonio = total_assets - total_liabilities
    - **Validates: Requirements 9.1**

  - [x] 4.12 Implement Update Tracker router and service
    - Create `backend/services/update_tracker.py` for recording module update timestamps
    - Create `backend/routers/update_tracker.py` with GET endpoint returning all module timestamps
    - Record timestamp on each successful write operation per module per user
    - Store timestamps in UTC
    - _Requirements: 17.1, 17.6, 17.7_

  - [ ]* 4.13 Write unit tests for CRUD modules
    - Test happy-path CRUD for each financial module (ahorro, creditos, gastos_ingresos, deudas, aportaciones, afore, gbm)
    - Test validation rejection for out-of-range amounts, missing fields
    - Test user scope isolation (cannot access other user's records)
    - Test partial results on encryption failure
    - Test system category protection
    - _Requirements: 3.1–3.9, 4.1–4.9, 5.1–5.12, 6.1–6.9, 7.1–7.7, 8.1–8.7, 10.1–10.9_

  - [ ]* 4.14 Write property test for User Scope Isolation
    - **Property 18: User Scope Isolation** — Queries for user A never return records belonging to user B
    - **Validates: Requirements 3.4, 4.4, 5.4, 6.4, 7.4, 8.4, 9.6**

- [x] 5. Checkpoint - Backend CRUD verification
  - Ensure all tests pass, ask the user if questions arise.

- [x] 6. Rate Scraper and Investment Optimizer
  - [x] 6.1 Implement Rate Scraper service
    - Create `backend/services/rate_scraper.py`
    - Implement scraping logic for: Nu México, Ualá, CETES (Banxico), Stori, Mercado Pago, Klar, Finsus, Didi
    - Store fetched rates with: name, annual_rate, min_investment, max_investment, term, risk_level, liquidity_tier, tiered_rates (JSONB), last_fetch_status, last_fetched_at
    - Support tiered rate structures (e.g., Nu: 15.5% for 0–50k, 14.5% for 50k–200k)
    - On fetch failure for a specific instrument, retain previous rate and set last_fetch_status="error"
    - Complete full scrape cycle within 60 seconds
    - _Requirements: 12.1, 12.2, 12.3, 12.4, 12.6_

  - [x] 6.2 Implement Instruments router
    - Create `backend/routers/instruments.py` with GET (list instruments) and POST /scrape (admin trigger)
    - GET returns only instruments with last_fetch_status="success" by default
    - Flag instruments not updated in 7+ days as "stale"
    - POST /scrape restricted to admin (or scheduled trigger)
    - _Requirements: 12.5, 12.6, 12.7_

  - [x] 6.3 Implement Investment Optimizer (Greedy Allocation Algorithm)
    - Create `backend/services/optimizer.py` with Optimizer class
    - Accept input: total_capital, risk_tolerance, liquidity_preference, max_instruments (1–10)
    - Filter instruments by risk tolerance and liquidity preference
    - Sort eligible instruments by annual rate descending
    - Greedy allocation: iterate instruments, allocate min(remaining, max_investment), respect min_investment thresholds
    - Apply tiered rates based on allocated amount
    - Return: allocations list, total expected annual return, unallocated capital
    - Return empty list with message when capital insufficient for any instrument
    - Complete computation within 200ms for up to 50 instruments
    - Stop allocation at max_instruments limit
    - _Requirements: 13.1, 13.2, 13.3, 13.4, 13.5, 13.6, 13.7, 13.8_

  - [ ]* 6.4 Write property tests for Optimizer
    - **Property 4: Capital Conservation** — sum(allocations) + unallocated = total_capital
    - **Property 5: Respects Instrument Constraints** — each allocation within [min, max] bounds
    - **Property 6: Respects Risk and Liquidity Filters** — no allocation violates user preferences
    - **Property 7: Respects Max Instruments Limit** — len(allocations) ≤ max_instruments
    - **Validates: Requirements 13.2, 13.3, 13.4, 13.5, 13.8**

  - [ ]* 6.5 Write property test for Tiered Rate Resolution
    - **Property 17: Tiered Rate Resolution** — For any amount and tiered instrument, the applied rate matches the tier containing that amount
    - **Validates: Requirements 12.3**

- [x] 7. Fina AI Advisor — State Machine and Bedrock integration
  - [x] 7.1 Implement State Machine service
    - Create `backend/services/state_machine.py` with StateMachine class
    - Implement deterministic states: WELCOME → COLLECT_CAPITAL → COLLECT_RISK → COLLECT_LIQUIDITY → COLLECT_MAX_INSTRUMENTS → GENERATE_RECOMMENDATION → PRESENT_RESULTS → FOLLOW_UP → TERMINATED
    - Implement input validators per state (positive number, risk enum, liquidity enum, 1–10 int)
    - On invalid input: remain in current state, return clarifying message
    - On valid input: store param, transition to next state
    - At GENERATE_RECOMMENDATION: invoke Optimizer with collected params, transition to PRESENT_RESULTS
    - At FOLLOW_UP: offer adjust/ask/end options; "adjust" loops back to COLLECT_CAPITAL
    - Enforce max 20 interactions per session; transition to TERMINATED after limit
    - Persist conversation state per user session (JSONB in conversation_sessions table)
    - _Requirements: 14.1, 14.2, 14.3, 14.4, 14.5, 14.6, 14.7, 14.8, 14.9_

  - [ ]* 7.2 Write property tests for State Machine
    - **Property 8: Deterministic Transitions** — Valid inputs follow defined state order without skipping
    - **Property 9: Invalid Input Preservation** — Invalid input keeps state unchanged
    - **Property 10: Interaction Limit** — After 20 interactions, state becomes TERMINATED
    - **Validates: Requirements 14.1, 14.3, 14.4, 14.9**

  - [x] 7.3 Implement Amazon Bedrock client
    - Create `backend/services/bedrock_client.py`
    - Implement prompt construction: current state context + user input + last 5 messages + instrument data
    - Send to Amazon Bedrock (Claude 3 Sonnet) with 10-second timeout
    - Constrain outputs to financial advisory content via system prompt instructions
    - Enforce max 4000 token prompt size; truncate history if needed
    - Log each API call: timestamp, state, token count, latency (no personal financial details)
    - Never send encrypted/plaintext monetary amounts to LLM; only aggregate params
    - _Requirements: 15.1, 15.2, 15.3, 15.4, 15.6, 15.7, 15.8_

  - [x] 7.4 Implement Bedrock fallback and advisor router
    - Create `backend/routers/advisor.py` with POST /message, GET /session, POST /reset
    - On Bedrock error/timeout: fall back to pre-defined template responses per state
    - Inform user of limited AI service
    - Store fallback messages in a JSON config file
    - Wire State Machine + Bedrock client + Optimizer together in advisor router
    - _Requirements: 15.5, 14.6, 14.7_

- [x] 8. Learning System (Financial Education)
  - [x] 8.1 Implement Courses and Lessons routers
    - Create `backend/routers/courses.py` with GET /courses, GET /courses/{id}/lessons
    - Create `backend/routers/lessons.py` with POST /lessons/{id}/complete, GET /lessons/progress
    - Store courses/lessons in database (not hardcoded in frontend)
    - Track per-user lesson completion and course progress percentage
    - Allow non-sequential access but display recommendation for prior lessons
    - Scope all progress queries to user_id
    - _Requirements: 18.1, 18.2, 18.3, 18.4, 18.5, 18.6, 18.7, 18.8_

- [x] 9. Checkpoint - Backend API complete
  - Ensure all tests pass, ask the user if questions arise.

- [x] 10. Frontend shell — Layout, navigation, auth
  - [x] 10.1 Implement Firebase Auth composable and auth store
    - Create `frontend/src/composables/useAuth.ts` with Firebase Auth SDK integration
    - Implement login (email/password), register, Google OAuth, logout, silent token refresh
    - Create `frontend/src/stores/auth.ts` (Pinia) for auth state (user, token, loading)
    - On logout: clear token, redirect to /login within 1 second
    - On token expiry: attempt silent refresh without interrupting workflow
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.10, 1.11_

  - [x] 10.2 Implement API composable with interceptors
    - Create `frontend/src/composables/useApi.ts` with Axios instance
    - Attach Firebase ID token as Bearer in Authorization header on all requests
    - Intercept 401 responses: attempt token refresh, retry request once
    - Display loading indicators during API calls
    - Display error messages via ErrorAlert on failures without crashing app
    - _Requirements: 1.6, 21.5, 21.7_

  - [x] 10.3 Implement layout components (TopNav, Sidebar, MainContent)
    - Create `frontend/src/components/layout/TopNav.vue` — fixed 64px height, logo left, nav center, avatar+dropdown right
    - Create `frontend/src/components/layout/Sidebar.vue` — 200–280px width, navigation links to all /finanzas sub-routes, active link styling, collapse to hamburger below 768px
    - Create `frontend/src/components/layout/MainContent.vue` — content area wrapper
    - Create `frontend/src/layouts/DashboardLayout.vue` composing TopNav + Sidebar + MainContent
    - Create `frontend/src/layouts/DefaultLayout.vue` for public pages
    - _Requirements: 2.1, 2.3, 2.4, 2.6_

  - [x] 10.4 Implement Vue Router with guards and lazy loading
    - Create `frontend/src/router/index.ts` with all routes
    - Define routes: /login, /register, /home, /finanzas (with children: ahorro, creditos, gastos-ingresos, deudas, aportaciones, afore, patrimonio, gbm), /asesor, /aprendizaje
    - Implement auth route guards: redirect unauthenticated users to /login within 500ms
    - Lazy-load all page components; keep shell (TopNav, Sidebar, Router) in initial bundle
    - Handle undefined sub-routes with 404 message and link to /finanzas
    - _Requirements: 2.2, 2.3, 2.7, 2.8, 21.4, 21.6_

  - [x] 10.5 Implement dark mode toggle and theme composable
    - Create `frontend/src/composables/useTheme.ts` with dark mode toggle via `html.dark` CSS class
    - Apply Tailwind dark mode classes across all components
    - Theme change within 100ms of toggle action
    - Persist theme preference in localStorage
    - _Requirements: 2.5_

  - [x] 10.6 Implement reusable UI components
    - Create `frontend/src/components/ui/LoadingSpinner.vue`
    - Create `frontend/src/components/ui/ErrorAlert.vue` for error messages
    - Create `frontend/src/components/ui/ConfirmDialog.vue` for delete confirmations
    - Create `frontend/src/components/ui/DataTable.vue` with pagination (50 items/page, next/previous)
    - Create `frontend/src/components/ui/CurrencyInput.vue` with es-MX monetary formatting
    - All components accessible via keyboard (Tab, Enter, Escape)
    - Use semantic HTML and ARIA attributes
    - _Requirements: 25.6, 26.4, 26.5, 26.6, 21.7_

  - [x] 10.7 Implement Login and Register pages
    - Create `frontend/src/pages/LoginPage.vue` with email/password form and Google OAuth button
    - Create `frontend/src/pages/RegisterPage.vue` with email/password registration form
    - Validate email format and password length (≥8 chars) on frontend
    - Display error messages for duplicate email, invalid credentials (generic, not revealing which field failed)
    - Integrate with useAuth composable
    - Keyboard accessible forms with labels and ARIA
    - _Requirements: 1.1, 1.2, 1.3, 1.5, 26.4, 26.6_

- [x] 11. Checkpoint - Frontend shell verification
  - Ensure all tests pass, ask the user if questions arise.

- [x] 12. Frontend financial module pages
  - [x] 12.1 Implement Savings (Ahorro) page
    - Create `frontend/src/pages/finanzas/AhorroPage.vue`
    - CRUD interface with DataTable (paginated), CurrencyInput for amounts
    - Display aggregate total savings formatted to 2 decimals (es-MX locale)
    - Confirmation dialog before delete
    - Loading/error states
    - _Requirements: 3.1, 3.5, 3.8, 26.1, 26.2_

  - [x] 12.2 Implement Credit Cards (Creditos) page
    - Create `frontend/src/pages/finanzas/CreditosPage.vue`
    - CRUD interface with DataTable
    - Display credit utilization percentage (balance/limit × 100) or "N/A" when limit=0
    - Validation for monetary fields (0.00–999,999,999.99)
    - _Requirements: 4.1, 4.5, 4.6, 4.7, 26.1, 26.2_

  - [x] 12.3 Implement Expenses/Income (GastosIngresos) page
    - Create `frontend/src/pages/finanzas/GastosIngresosPage.vue`
    - CRUD interface with category selector, type toggle (income/expense), date picker
    - Bar/line chart of expenses and income grouped by category over selectable time period (daily, weekly, monthly, yearly)
    - Display only user-created categories in income chart; exclude system categories from deletion
    - Show totals for income and expenses in selected period (2 decimal places)
    - Create `frontend/src/components/charts/FinanceChart.vue` chart wrapper
    - _Requirements: 5.1, 5.5, 5.6, 5.9, 26.1, 26.2, 26.3_

  - [x] 12.4 Implement Debts (Deudas) page
    - Create `frontend/src/pages/finanzas/DeudasPage.vue`
    - CRUD interface showing: remaining balance, estimated payoff date, total interest cost per debt
    - Display aggregate total debt and aggregate monthly payment
    - _Requirements: 6.1, 6.5, 6.6, 26.1, 26.2_

  - [x] 12.5 Implement Contributions (Aportaciones) page
    - Create `frontend/src/pages/finanzas/AportacionesPage.vue`
    - CRUD interface with frequency selector (weekly/biweekly/monthly)
    - Display projected annual contribution per schedule and aggregate total
    - _Requirements: 7.1, 7.5, 26.1, 26.2_

  - [x] 12.6 Implement Afore (Pension) page
    - Create `frontend/src/pages/finanzas/AforePage.vue`
    - CRUD interface with provider name and balance
    - Display total Afore balance and days since last update
    - _Requirements: 8.1, 8.5, 8.7, 26.1, 26.2_

  - [x] 12.7 Implement GBM Portfolio page
    - Create `frontend/src/pages/finanzas/GbmPage.vue`
    - Excel file upload (.xlsx, max 5MB) with drag-and-drop or file picker
    - Display positions table: ticker, shares, avg cost, current value, gain/loss %
    - Display total portfolio value
    - Show skipped row count after upload
    - _Requirements: 10.1, 10.3, 10.5, 10.6, 10.9, 26.1, 26.2_

  - [x] 12.8 Implement Net Worth (Patrimonio) page
    - Create `frontend/src/pages/finanzas/PatrimonioPage.vue`
    - Display calculated patrimonio_neto formatted to 2 decimal places (es-MX)
    - Breakdown: assets (ahorro, afore, gbm) vs liabilities (deudas, creditos)
    - Handle partial data — show warning for missing modules
    - _Requirements: 9.1, 9.2, 9.3, 9.5, 26.1, 26.2_

  - [x] 12.9 Implement Update Tracker display and warnings
    - Display days since last update for each module on /finanzas dashboard
    - Orange badge for modules not updated in 30+ days
    - Red badge for modules not updated in 90+ days
    - "Not yet configured" for modules with no records
    - Convert UTC timestamps to user's local timezone for display
    - _Requirements: 17.2, 17.3, 17.4, 17.5, 17.6_

  - [x] 12.10 Implement Pinia finance store
    - Create `frontend/src/stores/finance.ts` (Pinia)
    - State: data for each financial module, loading flags, error states
    - Actions: fetch, create, update, delete for each module
    - Getters: totals, aggregations, formatted values
    - _Requirements: 21.3_

- [x] 13. Frontend — AI Advisor and Learning
  - [x] 13.1 Implement Fina Advisor page and chat components
    - Create `frontend/src/pages/advisor/AdvisorPage.vue`
    - Create `frontend/src/components/advisor/ChatWindow.vue` — scrollable message list + input field
    - Create `frontend/src/components/advisor/ChatMessage.vue` — individual message bubble (user vs Fina)
    - Create `frontend/src/stores/advisor.ts` (Pinia) — conversation state, messages, loading
    - Send messages via POST /api/advisor/message; display responses
    - Handle AI unavailable state (display fallback message)
    - Resume conversation from last state within same session
    - Display formatted optimizer results (instrument table with allocations)
    - _Requirements: 14.1, 14.2, 14.6, 14.7, 14.8, 15.5_

  - [x] 13.2 Implement Learning pages
    - Create `frontend/src/pages/learning/CoursesPage.vue` — list courses with title, description, lesson count, progress %
    - Create `frontend/src/pages/learning/LessonPage.vue` — lesson content display, mark complete button
    - Create `frontend/src/stores/learning.ts` (Pinia) — courses, lessons, progress
    - Visually mark completed lessons
    - Display recommendation for uncompleted prior lessons (no strict gating)
    - _Requirements: 18.2, 18.3, 18.4, 18.7_

- [x] 14. Accessibility and internationalization
  - [x] 14.1 Apply es-MX locale formatting and accessibility across SPA
    - Render all UI text in Spanish (es-MX): labels, error messages, navigation, instructions
    - Format monetary values per es-MX locale ($1,234.56)
    - Format dates per es-MX locale (dd/mm/yyyy)
    - Ensure all interactive elements accessible via keyboard (Tab, Enter, Escape)
    - Use semantic HTML (nav, main, section, article, button, label)
    - Add ARIA attributes where needed for screen reader compatibility
    - All form inputs have associated labels (for/id or aria-label)
    - Maintain 4.5:1 contrast ratio for normal text, 3:1 for large text (light + dark modes)
    - Images/icons with meaning have alt/aria-label; decorative use aria-hidden="true"
    - Visible focus indicators on all interactive elements
    - _Requirements: 26.1, 26.2, 26.3, 26.4, 26.5, 26.6, 26.7, 26.8, 26.9_

- [x] 15. Checkpoint - Full frontend verification
  - Ensure all tests pass, ask the user if questions arise.

- [x] 16. API Response consistency and error handling
  - [x] 16.1 Implement global exception handlers and response envelope
    - Add FastAPI exception handlers for: ValidationError, EncryptionError, AuthError, NotFoundError, RateLimitError
    - Ensure all responses follow envelope: { "success": bool, "data": T|null, "error": { "code": str, "message": str, "fields"?: dict }|null }
    - Return appropriate HTTP codes: 200, 201, 400, 401, 403, 404, 429, 500, 503, 504
    - Never expose stack traces or internal paths in error responses
    - Field-level validation error breakdown in 400 responses
    - 5-second timeout on all operations (504 if exceeded)
    - Database connection pool exhaustion → 503 after 5-second queue
    - _Requirements: 20.1, 20.2, 20.3, 20.4, 20.5, 20.9, 25.8_

  - [ ]* 16.2 Write property test for API Response Envelope
    - **Property 19: API Response Envelope Consistency** — All responses conform to { success, data, error } structure with exactly one of data or error non-null
    - **Validates: Requirements 20.2**

- [x] 17. CI/CD Pipeline and deployment configuration
  - [x] 17.1 Create GitHub Actions workflow for CI/CD
    - Create `.github/workflows/deploy.yml` triggered on push to `prd` branch
    - Stages: install dependencies → lint → unit tests → build SPA → deploy
    - Halt on any stage failure; report via GitHub Actions status
    - Use GitHub Secrets for AWS credentials, Firebase config, FERNET_KEY, DB connection string
    - Do not expose secrets in logs
    - Target completion within 10 minutes
    - _Requirements: 22.1, 22.2, 22.3, 22.6, 22.7_

  - [x] 17.2 Configure SPA deployment to S3 + CloudFront
    - Deploy SPA build artifacts to AWS S3 bucket
    - Invalidate CloudFront cache on deployment
    - Configure S3 for static hosting with public access blocked (OAC for CloudFront)
    - Configure CloudFront custom error page → index.html for 404s (SPA routing)
    - Enable HTTPS via CloudFront with TLS 1.2+
    - _Requirements: 22.4, 23.1, 23.4, 23.5, 23.6_

  - [x] 17.3 Configure backend deployment to EC2
    - Deploy FastAPI app to EC2 t2.micro with Uvicorn
    - Configure security group: inbound 443 (HTTPS) and 22 (SSH restricted IP)
    - Configure RDS security group: inbound only from EC2 security group on 5432
    - SSL/TLS for database connection
    - Run database migrations before activating new code
    - _Requirements: 22.5, 22.8, 23.2, 23.7, 23.8, 19.9_

  - [x] 17.4 Configure RDS PostgreSQL instance
    - Set up RDS db.t3.micro with 20GB storage (Free Tier)
    - Enable encryption at rest (AES-256)
    - Configure SSL/TLS for connections
    - Configure automated backups
    - _Requirements: 23.3, 24.8, 19.1, 19.9_

- [x] 18. Final integration and wiring
  - [x] 18.1 Wire all backend routers into FastAPI main app
    - Register all routers in `backend/main.py` with proper prefixes
    - Register all middleware (auth, rate limiter, CORS, security headers, gzip)
    - Configure startup event: validate FERNET_KEY, initialize DB connection pool, create tables
    - Configure shutdown event: close DB connections
    - _Requirements: 11.5, 20.1, 20.6, 20.7, 20.8_

  - [x] 18.2 Wire all frontend pages into router and stores
    - Ensure all page components registered in router
    - Connect all pages to appropriate Pinia stores
    - Verify lazy loading of all route components
    - Test auth guard on all protected routes
    - Verify production bundle under 500KB gzipped (initial load)
    - _Requirements: 21.4, 21.6, 21.8, 2.9_

  - [ ]* 18.3 Write integration tests for full API flows
    - Test full request cycle: auth → CRUD → encrypted storage → decrypted response
    - Test rate limiting (100 req/min)
    - Test GBM Excel upload end-to-end
    - Test Fina advisor conversation flow (mocked Bedrock)
    - Test cache behavior (hit/miss/invalidate)
    - Test update tracker timestamps
    - _Requirements: 20.1–20.9, 25.1_

- [x] 19. Final checkpoint - Full platform verification
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation at major integration boundaries
- Property tests validate universal correctness properties from the design document
- Unit tests validate specific examples and edge cases
- Backend uses Python (FastAPI, SQLAlchemy, Pydantic, Hypothesis for property tests, pytest)
- Frontend uses TypeScript (Vue 3, Pinia, Tailwind CSS, PrimeVue 4, Vitest for tests)
- Local development uses SQLite fallback; CI uses PostgreSQL service container
- All monetary fields stored as encrypted TEXT (Fernet); never as numeric DB types

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1", "1.2"] },
    { "id": 1, "tasks": ["1.3", "1.4", "1.6"] },
    { "id": 2, "tasks": ["1.5", "1.7", "2.1", "2.2", "2.3", "2.4"] },
    { "id": 3, "tasks": ["2.5", "4.1", "4.2", "4.3", "4.4"] },
    { "id": 4, "tasks": ["4.5", "4.6", "4.7", "4.8", "4.9"] },
    { "id": 5, "tasks": ["4.10", "4.12", "6.1"] },
    { "id": 6, "tasks": ["4.11", "4.13", "4.14", "6.2", "6.3"] },
    { "id": 7, "tasks": ["6.4", "6.5", "7.1"] },
    { "id": 8, "tasks": ["7.2", "7.3", "8.1"] },
    { "id": 9, "tasks": ["7.4", "10.1", "10.2"] },
    { "id": 10, "tasks": ["10.3", "10.4", "10.5"] },
    { "id": 11, "tasks": ["10.6", "10.7"] },
    { "id": 12, "tasks": ["12.1", "12.2", "12.3", "12.4", "12.5", "12.6", "12.7", "12.10"] },
    { "id": 13, "tasks": ["12.8", "12.9", "13.1", "13.2"] },
    { "id": 14, "tasks": ["14.1", "16.1"] },
    { "id": 15, "tasks": ["16.2", "17.1"] },
    { "id": 16, "tasks": ["17.2", "17.3", "17.4"] },
    { "id": 17, "tasks": ["18.1", "18.2"] },
    { "id": 18, "tasks": ["18.3"] }
  ]
}
```
