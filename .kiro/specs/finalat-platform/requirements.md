# Requirements Document

## Introduction

Finalat is a full-stack financial advisory and personal finance management platform for Mexico. It combines an AI-powered investment advisor ("Fina") with a comprehensive financial dashboard for tracking savings, credit cards, expenses/income, debts, contributions, and net worth. The platform targets Mexican individual investors and households, providing instrument-level rate comparisons, portfolio optimization, and guided financial education.

The system is deployed on AWS Free Tier (S3 + CloudFront, Lambda + API Gateway, RDS PostgreSQL) with Firebase Authentication and Amazon Bedrock for AI inference.

---

## Glossary

- **Finalat**: The full platform product described in this document.
- **Fina**: The AI-powered investment advisor agent embedded in the platform.
- **User**: An authenticated individual using Finalat via Firebase Auth (email/password or Google OAuth).
- **Dashboard**: The financial sub-application showing savings, credit cards, expenses, debts, contributions, and net worth.
- **Instrument**: A financial product (e.g., CETES, Nu México, Ualá) with a defined annual rate, term, risk level, liquidity tier, and contribution limits.
- **Portfolio**: A user's allocation of capital across one or more financial Instruments.
- **Ahorro**: Savings accounts or high-yield instruments tracked in the platform.
- **Creditos**: Credit card accounts tracked in the Dashboard.
- **Gastos_Ingresos**: The expense and income tracking module.
- **Deudas**: Personal debts tracked with payment schedules.
- **Aportaciones**: Recurring contribution schedules (weekly, biweekly, monthly).
- **Afore**: Mexican mandatory pension fund tracking.
- **Patrimonio_Neto**: Net worth, auto-calculated from all financial modules.
- **GBM_Portfolio**: Investment portfolio imported from GBM Hombroker via Excel file.
- **Encryption_Service**: The component responsible for AES-256 (Fernet) field-level encryption of monetary amounts and sensitive descriptions.
- **Rate_Scraper**: The component that fetches current instrument rates from financial providers (Nu, Ualá, CETES/Banxico, Stori, Mercado Pago, Klar, Finsus, Didi).
- **Optimizer**: The greedy investment allocation algorithm that distributes capital across Instruments.
- **State_Machine**: The deterministic conversation engine that drives the Fina advisor chat flow.
- **Cache**: The in-memory LRU cache (max 500 entries, 5-minute TTL) scoped per user.
- **CI_CD_Pipeline**: The GitHub Actions workflow that builds and deploys the platform on every push to the `prd` branch.
- **API_Gateway**: AWS API Gateway (or FastAPI on EC2) that routes HTTP requests to backend Lambda functions or the FastAPI app.
- **Auth_Service**: Firebase Authentication handling email/password and Google OAuth login flows.
- **JWT_Verifier**: The backend component that validates Firebase ID tokens (RS256) against Google's public X.509 certificates.
- **SPA**: The Vue 3 single-page application served from S3 + CloudFront.
- **Update_Tracker**: The component that records when a user last updated each financial module and reminds them to update on schedule.
- **Learning_System**: The course and lesson management module covering financial education content.
- **Category**: A label used to classify income or expense entries in Gastos_Ingresos.
- **Tiered_Rate**: A rate structure where the return percentage depends on the invested amount range.

---

## Requirements

### Requirement 1: User Authentication and Session Management

**User Story:** As a visitor, I want to register and log in using my email/password or Google account, so that my financial data is securely isolated from other users.

#### Acceptance Criteria

1. THE Auth_Service SHALL support registration via email and password, and via Google OAuth.
2. WHEN a User registers with email and password, THE Auth_Service SHALL validate that the email follows a valid format and that the password is at least 8 characters long, then create a Firebase account and assign a unique Firebase UID (user_id).
3. IF a User attempts to register with an email that is already associated with an existing account, THEN THE Auth_Service SHALL reject the registration and return an error message indicating the email is already in use.
4. WHEN a User authenticates successfully, THE Auth_Service SHALL issue a Firebase ID token (RS256-signed JWT) to the SPA within 3 seconds of the authentication request.
5. IF a User provides invalid credentials during login, THEN THE Auth_Service SHALL reject the authentication attempt and display an error message indicating that the credentials are incorrect, without revealing whether the email or password was wrong.
6. WHEN the SPA makes an API request, THE SPA SHALL include the Firebase ID token as a Bearer token in the Authorization header.
7. WHEN an API request is received, THE JWT_Verifier SHALL validate the Bearer token against Google's public X.509 certificates without using a service account.
8. IF the Bearer token is missing, expired, or has an invalid signature, THEN THE API_Gateway SHALL return an HTTP 401 response, reject the request, and not execute any downstream logic.
9. THE JWT_Verifier SHALL extract the user_id (Firebase UID) from the validated token and scope all database operations to that user_id.
10. WHEN a User logs out, THE SPA SHALL clear the local Firebase ID token and redirect the User to the /login route within 1 second.
11. IF the Firebase ID token expires while the User is actively using the SPA, THEN THE SPA SHALL attempt to refresh the token silently without interrupting the User's current workflow.

---

### Requirement 2: Financial Dashboard — Layout and Navigation

**User Story:** As an authenticated User, I want a financial dashboard with clear navigation, so that I can quickly access each financial module.

#### Acceptance Criteria

1. WHEN a User accesses the /finanzas route, THE Dashboard SHALL render a persistent sidebar with a minimum width of 200px and a maximum width of 280px, and a main content area occupying the remaining viewport width.
2. THE Dashboard SHALL provide navigation links to the following sub-routes: /finanzas/ahorro, /finanzas/creditos, /finanzas/gastos-ingresos, /finanzas/deudas, /finanzas/aportaciones, /finanzas/afore, /finanzas/patrimonio, /finanzas/gbm.
3. WHEN a navigation link is clicked, THE Dashboard SHALL visually indicate the active link by applying a distinct style to the currently selected route and render the corresponding sub-route content in the main content area within 300ms.
4. THE SPA SHALL apply a fixed TopNav with the Finalat logo on the left, navigation links in the center, and a User avatar with a dropdown menu on the right, where the TopNav height does not exceed 64px.
5. THE SPA SHALL support a dark mode toggled via the `html.dark` CSS class using Tailwind CSS, applying the theme change to all Dashboard components within 100ms of the toggle action.
6. THE SPA SHALL render correctly on viewports between 320px and 1024px or wider, collapsing the sidebar into a hamburger menu on viewports below 768px.
7. WHILE a User is unauthenticated, THE SPA SHALL restrict access to /finanzas and all sub-routes and redirect the User to /login within 500ms, without displaying protected content at any point during the redirect.
8. IF a User navigates to a sub-route that does not match any of the defined navigation links, THEN THE Dashboard SHALL display an error message indicating the requested module was not found, and provide a link to return to /finanzas.
9. WHEN the /finanzas route loads, THE Dashboard SHALL render the sidebar, TopNav, and main content area within 2 seconds on a standard 3G connection.

---

### Requirement 3: Savings (Ahorro) Module

**User Story:** As an authenticated User, I want to record and view my savings accounts, so that I can track my total saved capital.

#### Acceptance Criteria

1. THE Dashboard SHALL allow a User to create, read, update, and delete savings entries in the ahorro table, where each entry contains a monetary amount between 0.01 and 999,999,999.99 and an account name of no more than 100 characters.
2. WHEN a savings entry is written to the database, THE Encryption_Service SHALL encrypt the monetary amount using AES-256 (Fernet) before storage and complete the operation within 500 milliseconds.
3. WHEN a savings entry is read from the database, THE Encryption_Service SHALL decrypt the monetary amount before returning it to the SPA and complete the operation within 500 milliseconds.
4. THE API_Gateway SHALL scope all ahorro queries to the authenticated User's user_id, returning only entries belonging to that user and returning an empty list when no entries exist.
5. THE Dashboard SHALL display the aggregate total savings amount after decryption, formatted to two decimal places in the user's locale, and updated each time the savings list is retrieved.
6. IF a savings entry with a monetary value fails decryption, THEN THE Encryption_Service SHALL return an error indication and THE API_Gateway SHALL exclude that entry from the response and return a partial result with an error indicator specifying the count of entries that failed decryption.
7. IF a User submits a savings entry with a monetary amount outside the range of 0.01 to 999,999,999.99 or with a missing account name, THEN THE API_Gateway SHALL reject the request with a validation error message indicating which field is invalid and SHALL NOT persist the entry.
8. WHEN a User deletes a savings entry, THE Dashboard SHALL request confirmation before submitting the deletion, and THE API_Gateway SHALL verify the entry belongs to the authenticated User's user_id before removing it.
9. IF the database is unreachable when a savings operation is attempted, THEN THE API_Gateway SHALL return an error response within 5 seconds indicating the service is temporarily unavailable and SHALL NOT alter any persisted data.

---

### Requirement 4: Credit Cards (Creditos) Module

**User Story:** As an authenticated User, I want to track my credit card balances and limits, so that I can monitor my credit utilization.

#### Acceptance Criteria

1. THE Dashboard SHALL allow a User to create, read, update, and delete credit card records in the creditos table.
2. WHEN a credit card record is written, THE Encryption_Service SHALL encrypt all monetary fields (balance, limit, minimum payment) using AES-256 (Fernet) before persisting the record.
3. WHEN a credit card record is read, THE Encryption_Service SHALL decrypt all monetary fields before returning them to the SPA.
4. THE API_Gateway SHALL scope all creditos queries to the authenticated User's user_id.
5. WHEN a credit card record is read and the credit limit is greater than zero, THE Dashboard SHALL display credit utilization as a percentage (balance ÷ limit × 100) rounded to two decimal places.
6. IF the credit limit field is zero, THEN THE Dashboard SHALL display utilization as "N/A" instead of performing the division.
7. WHEN a User submits a credit card record, THE Dashboard SHALL validate that the balance field is between 0.00 and 999,999,999.99, the limit field is between 0.00 and 999,999,999.99, and the minimum payment field is between 0.00 and 999,999,999.99, rejecting the submission with an error message indicating which field is out of range if validation fails.
8. IF the Encryption_Service fails to encrypt or decrypt a monetary field, THEN THE API_Gateway SHALL reject the operation and return an error message indicating that the record could not be processed.
9. IF a User attempts to access or modify a credit card record that does not belong to their user_id, THEN THE API_Gateway SHALL reject the request and return an authorization error.

---

### Requirement 5: Expenses and Income (Gastos_Ingresos) Module

**User Story:** As an authenticated User, I want to record and categorize my expenses and income, so that I can understand my cash flow.

#### Acceptance Criteria

1. THE Dashboard SHALL allow a User to create, read, update, and delete entries in the gastos_ingresos table, each associated with exactly one Category, where each entry contains a type (income or expense), a monetary amount between 0.01 and 999,999,999.99, a description of at most 500 characters, and a date.
2. WHEN a gastos_ingresos entry is written, THE Encryption_Service SHALL encrypt the monetary amount and description using AES-256 (Fernet) before persisting the entry.
3. WHEN a gastos_ingresos entry is read, THE Encryption_Service SHALL decrypt the monetary amount and description before returning them to the SPA.
4. THE API_Gateway SHALL scope all gastos_ingresos queries to the authenticated User's user_id, returning only entries belonging to that User.
5. THE Dashboard SHALL provide a bar chart or line chart of expenses and income grouped by Category over a selectable time period, where the selectable time period options include at minimum daily, weekly, monthly, and yearly groupings.
6. THE Dashboard SHALL display only dynamic (user-created) categories in the income chart, excluding system categories "Creditos" and "Sueldo" from user deletion or modification.
7. WHEN a new User account is created, THE API_Gateway SHALL seed the following default categories for that User: Sueldo, Creditos, Prestamos, Otros.
8. IF a User attempts to delete or modify the "Creditos" or "Sueldo" categories, THEN THE API_Gateway SHALL return an HTTP 403 response with an error message indicating the category is protected and cannot be deleted or modified.
9. THE Dashboard SHALL display a summary of total income and total expenses for the selected period after decryption, showing each total as a numeric value with two decimal places.
10. IF a User attempts to create or update a gastos_ingresos entry with a missing or invalid category, an amount outside the range 0.01 to 999,999,999.99, or a description exceeding 500 characters, THEN THE API_Gateway SHALL reject the request and return an error message indicating the validation failure.
11. IF the Encryption_Service fails to encrypt or decrypt a gastos_ingresos entry, THEN THE API_Gateway SHALL return an error message indicating the operation could not be completed, without exposing internal details.
12. IF a User attempts to access or modify a gastos_ingresos entry belonging to another User, THEN THE API_Gateway SHALL return an HTTP 403 response.

---

### Requirement 6: Debts (Deudas) Module

**User Story:** As an authenticated User, I want to track my personal debts with payment schedules, so that I can plan my repayment strategy.

#### Acceptance Criteria

1. THE Dashboard SHALL allow a User to create, read, update, and delete debt records in the deudas table, where each record contains a creditor name (max 100 characters), total debt amount (0.01–999,999,999.99), monthly payment amount (0.01–999,999,999.99), interest rate (0.00–100.00), and start date.
2. WHEN a debt record is written, THE Encryption_Service SHALL encrypt the total debt amount and monthly payment amount using AES-256 (Fernet) before storage.
3. WHEN a debt record is read, THE Encryption_Service SHALL decrypt the encrypted fields before returning them to the SPA.
4. THE API_Gateway SHALL scope all deudas queries to the authenticated User's user_id.
5. THE Dashboard SHALL display for each debt: remaining balance, estimated payoff date (calculated from total amount, monthly payment, and interest rate), and total interest cost.
6. THE Dashboard SHALL display the aggregate total debt amount and the aggregate monthly payment across all debt records.
7. IF a User submits a debt record with any field outside its valid range or with missing required fields, THEN THE API_Gateway SHALL reject the request with a validation error message indicating which field is invalid.
8. IF the Encryption_Service fails on a debt record, THEN THE API_Gateway SHALL exclude that record and return a partial result with an error count.
9. IF a User attempts to access or modify a debt record belonging to another User, THEN THE API_Gateway SHALL return an HTTP 403 response.

---

### Requirement 7: Contributions (Aportaciones) Module

**User Story:** As an authenticated User, I want to define recurring contribution schedules, so that I can track how much I plan to save or invest periodically.

#### Acceptance Criteria

1. THE Dashboard SHALL allow a User to create, read, update, and delete contribution schedules in the aportaciones table, where each schedule contains a contribution amount (0.01–999,999,999.99), frequency (weekly, biweekly, or monthly), target instrument or account name (max 100 characters), and start date.
2. WHEN a contribution schedule is written, THE Encryption_Service SHALL encrypt the contribution amount using AES-256 (Fernet) before storage.
3. WHEN a contribution schedule is read, THE Encryption_Service SHALL decrypt the contribution amount before returning it to the SPA.
4. THE API_Gateway SHALL scope all aportaciones queries to the authenticated User's user_id.
5. THE Dashboard SHALL display the projected annual contribution for each schedule (amount × frequency multiplier: weekly=52, biweekly=26, monthly=12) and the aggregate annual contribution total across all schedules.
6. IF a User submits a contribution schedule with an invalid frequency value (not weekly, biweekly, or monthly), an amount outside the valid range, or a missing target name, THEN THE API_Gateway SHALL reject the request with a validation error.
7. IF the Encryption_Service fails on a contribution record, THEN THE API_Gateway SHALL exclude that record and return a partial result with an error count.

---

### Requirement 8: Afore (Pension Fund) Module

**User Story:** As an authenticated User, I want to track my Afore balance and contributions, so that I can monitor my retirement savings.

#### Acceptance Criteria

1. THE Dashboard SHALL allow a User to create, read, update, and delete Afore records in the afore table, where each record contains an Afore provider name (max 100 characters), current balance (0.01–999,999,999.99), and last update date.
2. WHEN an Afore record is written, THE Encryption_Service SHALL encrypt the balance amount using AES-256 (Fernet) before storage.
3. WHEN an Afore record is read, THE Encryption_Service SHALL decrypt the balance before returning it to the SPA.
4. THE API_Gateway SHALL scope all afore queries to the authenticated User's user_id.
5. THE Dashboard SHALL display the total Afore balance across all provider records.
6. IF a User submits an Afore record with a balance outside the valid range or a missing provider name, THEN THE API_Gateway SHALL reject the request with a validation error.
7. THE Update_Tracker SHALL record the last update timestamp for the Afore module and THE Dashboard SHALL display how many days have elapsed since the last update.

---

### Requirement 9: Net Worth (Patrimonio_Neto) Module

**User Story:** As an authenticated User, I want to see my calculated net worth, so that I have a single view of my overall financial health.

#### Acceptance Criteria

1. WHEN a User accesses the /finanzas/patrimonio route, THE Dashboard SHALL calculate Patrimonio_Neto as: (total ahorro + total Afore balance + total GBM_Portfolio value) minus (total deudas remaining balance + total creditos balance).
2. THE Dashboard SHALL display the Patrimonio_Neto value formatted to two decimal places in the user's locale.
3. THE Dashboard SHALL display a breakdown showing each component's contribution to the net worth calculation (savings, Afore, GBM portfolio as assets; debts and credit card balances as liabilities).
4. WHEN any underlying module data changes (ahorro, creditos, deudas, afore, gbm), THE Dashboard SHALL recalculate Patrimonio_Neto on the next access to the /finanzas/patrimonio route.
5. IF any component module returns an error or partial data, THEN THE Dashboard SHALL display the net worth calculation using only the successfully retrieved components and indicate which modules could not be included.
6. THE API_Gateway SHALL scope all component queries to the authenticated User's user_id when computing Patrimonio_Neto.

---

### Requirement 10: GBM Portfolio Import Module

**User Story:** As an authenticated User, I want to import my GBM Hombroker investment portfolio from an Excel file, so that I can include it in my net worth and track my market investments.

#### Acceptance Criteria

1. THE Dashboard SHALL allow a User to upload an Excel file (.xlsx) containing their GBM Hombroker portfolio data via the /finanzas/gbm route.
2. WHEN an Excel file is uploaded, THE API_Gateway SHALL parse the file and extract investment positions including: ticker symbol, number of shares, average cost per share, and current market value.
3. THE API_Gateway SHALL validate the uploaded file format and reject files that are not valid .xlsx format or exceed 5MB in size, returning an error message indicating the rejection reason.
4. WHEN GBM portfolio data is persisted, THE Encryption_Service SHALL encrypt monetary values (average cost, market value) using AES-256 (Fernet).
5. THE Dashboard SHALL display each position with: ticker, shares, average cost, current value, and gain/loss percentage calculated as ((current value - (shares × average cost)) / (shares × average cost)) × 100.
6. THE Dashboard SHALL display the total portfolio value as the sum of all position current values.
7. THE API_Gateway SHALL scope all GBM portfolio queries to the authenticated User's user_id.
8. WHEN a User uploads a new Excel file, THE API_Gateway SHALL replace the existing portfolio data for that User with the new data (full replacement, not merge).
9. IF the Excel file contains rows with missing required fields (ticker, shares, or cost), THEN THE API_Gateway SHALL skip those rows, import the valid rows, and return a response indicating how many rows were skipped and why.

---

### Requirement 11: Encryption Service

**User Story:** As a platform operator, I want all sensitive monetary data encrypted at rest, so that a database breach does not expose user financial information.

#### Acceptance Criteria

1. THE Encryption_Service SHALL use AES-256 encryption via the Fernet symmetric encryption scheme for all field-level encryption operations.
2. THE Encryption_Service SHALL encrypt all monetary amount fields and sensitive description fields before they are persisted to the database.
3. THE Encryption_Service SHALL decrypt encrypted fields when they are read from the database before returning them to the API layer.
4. THE Encryption_Service SHALL use a single encryption key stored as an environment variable (FERNET_KEY) and never hardcoded in source code.
5. IF the FERNET_KEY environment variable is missing or invalid at application startup, THEN THE API_Gateway SHALL fail to start and log an error indicating the encryption key is not configured.
6. IF a decryption operation fails (due to key mismatch, corrupted data, or invalid token), THEN THE Encryption_Service SHALL raise an identifiable exception that the calling module can catch and handle according to its own error policy.
7. THE Encryption_Service SHALL complete encryption or decryption of a single field within 50 milliseconds under normal load.
8. THE Encryption_Service SHALL NOT log or expose plaintext values of encrypted fields in any error messages, stack traces, or application logs.

---

### Requirement 12: Rate Scraper and Instrument Data

**User Story:** As an authenticated User interacting with Fina, I want access to current financial instrument rates, so that the advisor can recommend optimal allocations based on real data.

#### Acceptance Criteria

1. THE Rate_Scraper SHALL fetch current annual rates for the following instruments: Nu México, Ualá, CETES (via Banxico), Stori, Mercado Pago, Klar, Finsus, and Didi.
2. THE Rate_Scraper SHALL store fetched rates with the following attributes for each Instrument: name, annual rate (percentage), minimum investment amount, maximum investment amount (if applicable), term (days or "liquid"), risk level (low/medium/high), liquidity tier (immediate/1-day/28-day/custom), and last updated timestamp.
3. THE Rate_Scraper SHALL support Tiered_Rate structures where instruments offer different rates based on invested amount ranges (e.g., Nu: 15.5% for 0–50k, 14.5% for 50k–200k).
4. WHEN a rate fetch fails for a specific instrument, THE Rate_Scraper SHALL retain the previously stored rate and update the last_fetch_status to "error" with a timestamp, without affecting rates for other instruments.
5. THE API_Gateway SHALL expose a GET endpoint that returns the current instrument rate data to authenticated Users, returning only instruments where last_fetch_status is "success" unless explicitly requested otherwise.
6. THE Rate_Scraper SHALL be invocable on-demand via an API endpoint (restricted to admin or scheduled triggers) and SHALL complete a full scrape cycle within 60 seconds.
7. IF an instrument's rate data has not been successfully updated in more than 7 days, THEN THE API_Gateway SHALL flag that instrument as "stale" in the response.

---

### Requirement 13: Investment Optimizer (Greedy Allocation Algorithm)

**User Story:** As an authenticated User, I want the system to recommend how to distribute my investment capital across available instruments, so that I maximize my returns within my risk and liquidity constraints.

#### Acceptance Criteria

1. THE Optimizer SHALL accept as input: total capital to invest (positive number), risk tolerance (low, medium, or high), liquidity preference (immediate, short-term, or flexible), and maximum number of instruments to use (1–10).
2. THE Optimizer SHALL use a greedy algorithm that iterates through instruments sorted by annual rate (descending) and allocates capital to each instrument up to its maximum contribution limit or the remaining unallocated capital, whichever is smaller.
3. THE Optimizer SHALL respect instrument constraints: minimum investment amounts (skip instruments where remaining capital is below minimum), maximum investment amounts (cap allocation at maximum), and tiered rates (apply the rate corresponding to the allocated amount tier).
4. THE Optimizer SHALL filter instruments based on the User's risk tolerance (exclude instruments with risk level exceeding the User's preference) and liquidity preference (exclude instruments with liquidity tier below the User's requirement).
5. THE Optimizer SHALL return: a list of recommended allocations (instrument name, allocated amount, expected annual return for that allocation), total expected annual return, and any unallocated capital remaining.
6. IF the total capital is less than the minimum investment of all available instruments after filtering, THEN THE Optimizer SHALL return an empty allocation list with a message indicating insufficient capital for available instruments.
7. THE Optimizer SHALL complete the allocation computation within 200 milliseconds for up to 50 instruments.
8. THE Optimizer SHALL NOT allocate to more instruments than the specified maximum number, stopping allocation once the limit is reached even if capital remains.

---

### Requirement 14: Fina AI Advisor — State Machine and Conversation Flow

**User Story:** As an authenticated User, I want to interact with an AI investment advisor (Fina) through a guided conversation, so that I receive personalized investment recommendations.

#### Acceptance Criteria

1. THE State_Machine SHALL implement a deterministic conversation flow with the following states: WELCOME → COLLECT_CAPITAL → COLLECT_RISK → COLLECT_LIQUIDITY → COLLECT_MAX_INSTRUMENTS → GENERATE_RECOMMENDATION → PRESENT_RESULTS → FOLLOW_UP.
2. WHEN a User initiates a conversation with Fina, THE State_Machine SHALL start in the WELCOME state and present a greeting message explaining the advisor's capabilities.
3. IN each collection state (COLLECT_CAPITAL, COLLECT_RISK, COLLECT_LIQUIDITY, COLLECT_MAX_INSTRUMENTS), THE State_Machine SHALL prompt the User for the specific input, validate the response, and transition to the next state only when valid input is received.
4. IF a User provides invalid input in any collection state, THEN THE State_Machine SHALL remain in the current state and prompt the User again with a clarifying message explaining the expected format.
5. WHEN the State_Machine reaches GENERATE_RECOMMENDATION, THE system SHALL invoke the Optimizer with the collected parameters and transition to PRESENT_RESULTS with the allocation output.
6. IN the PRESENT_RESULTS state, THE system SHALL format the Optimizer output into a user-friendly message showing each recommended instrument, allocated amount, and expected return.
7. IN the FOLLOW_UP state, THE State_Machine SHALL offer the User options to: adjust parameters and regenerate, ask questions about specific instruments, or end the conversation.
8. THE State_Machine SHALL persist the conversation state per User session so that if the User navigates away and returns, the conversation resumes from the last state within the same session.
9. THE State_Machine SHALL impose a maximum of 20 interactions per conversation session to prevent infinite loops, transitioning to a terminal state with a summary message after reaching the limit.

---

### Requirement 15: Fina AI Advisor — LLM Integration (Amazon Bedrock)

**User Story:** As an authenticated User, I want Fina to use natural language understanding to interpret my inputs and generate human-like responses, so that the conversation feels natural.

#### Acceptance Criteria

1. THE Fina advisor SHALL use Amazon Bedrock (Claude model) to generate natural language responses within the conversation flow.
2. WHEN the State_Machine requires a response to be generated, THE system SHALL construct a prompt containing: the current state context, the User's input, the conversation history (last 5 messages), and any relevant instrument data.
3. THE system SHALL send the constructed prompt to Amazon Bedrock and receive a generated response within 10 seconds; if the response exceeds 10 seconds, THE system SHALL return a timeout message to the User.
4. THE system SHALL constrain LLM outputs to financial advisory content only by including system-level instructions in the prompt that restrict the model from discussing non-financial topics.
5. IF the Amazon Bedrock API returns an error or is unavailable, THEN THE system SHALL fall back to a pre-defined template response appropriate to the current state and inform the User that the AI service is temporarily limited.
6. THE system SHALL NOT send any User financial data (encrypted or plaintext amounts) to the LLM; only aggregate parameters (total capital number, risk preference, liquidity preference) SHALL be included in prompts.
7. THE system SHALL log each Bedrock API call with: timestamp, state, token count, and latency, without logging the User's personal financial details.
8. THE system SHALL enforce a maximum prompt size of 4000 tokens and truncate conversation history if necessary to stay within the limit.

---

### Requirement 16: Caching Layer

**User Story:** As a platform operator, I want frequently accessed data cached in memory, so that repeated requests are served faster and reduce database load.

#### Acceptance Criteria

1. THE Cache SHALL implement an LRU (Least Recently Used) eviction policy with a maximum of 500 entries.
2. THE Cache SHALL apply a TTL (Time To Live) of 5 minutes to each entry; after 5 minutes, the entry SHALL be considered expired and removed on next access or eviction cycle.
3. THE Cache SHALL be scoped per user_id, ensuring that cached data for one User is never returned to another User.
4. WHEN an API request is received for data that exists in the Cache and has not expired, THE API_Gateway SHALL return the cached data without querying the database.
5. WHEN an API request is received for data that is not in the Cache or has expired, THE API_Gateway SHALL query the database, store the result in the Cache, and return the data.
6. WHEN a write operation (create, update, delete) is performed on a module, THE Cache SHALL invalidate all entries related to that module for the affected User.
7. IF the Cache reaches its maximum capacity of 500 entries and a new entry must be added, THEN THE Cache SHALL evict the least recently used entry to make room.
8. THE Cache SHALL operate entirely in-memory within the application process and SHALL NOT require an external caching service.

---

### Requirement 17: Update Tracker and Reminders

**User Story:** As an authenticated User, I want to be reminded when I haven't updated a financial module recently, so that my data stays current and my net worth calculation is accurate.

#### Acceptance Criteria

1. THE Update_Tracker SHALL record the timestamp of the last successful write operation (create, update, or delete) for each financial module (ahorro, creditos, gastos_ingresos, deudas, aportaciones, afore, gbm) per User.
2. WHEN a User accesses the /finanzas route, THE Dashboard SHALL display for each module: the number of days since the last update.
3. IF a module has not been updated in more than 30 days, THEN THE Dashboard SHALL display a visual warning indicator (e.g., orange badge) next to that module's navigation link.
4. IF a module has not been updated in more than 90 days, THEN THE Dashboard SHALL display a critical warning indicator (e.g., red badge) next to that module's navigation link.
5. IF a module has never been updated (no records exist), THEN THE Dashboard SHALL display a "Not yet configured" indicator instead of days since last update.
6. THE Update_Tracker timestamps SHALL be stored in UTC and converted to the User's local timezone for display.
7. THE API_Gateway SHALL expose a GET endpoint that returns the last update timestamps for all modules for the authenticated User.

---

### Requirement 18: Learning System (Financial Education)

**User Story:** As an authenticated User, I want to access structured financial education content, so that I can improve my financial literacy alongside using the platform tools.

#### Acceptance Criteria

1. THE Learning_System SHALL organize content into courses, where each course contains one or more lessons presented in a defined sequential order.
2. THE Dashboard SHALL provide a /aprendizaje route that displays available courses with: course title, description, number of lessons, and the User's completion progress (percentage of lessons completed).
3. WHEN a User selects a course, THE Dashboard SHALL display the list of lessons in order, with completed lessons visually marked.
4. WHEN a User completes a lesson (navigates to the end of the lesson content), THE Learning_System SHALL record the completion for that User and update the course progress percentage.
5. THE Learning_System SHALL track progress per User, so that each User has independent completion state.
6. THE API_Gateway SHALL scope all learning progress queries to the authenticated User's user_id.
7. IF a User attempts to access a lesson in a course where the previous lesson has not been completed, THEN THE Learning_System SHALL allow access (no strict sequential gating) but SHALL display a recommendation to complete prior lessons first.
8. THE course and lesson content SHALL be stored in the database and manageable by an admin (future requirement), not hardcoded in the frontend.

---

### Requirement 19: Database Schema and Data Layer

**User Story:** As a platform operator, I want a well-defined relational database schema, so that all financial data is consistently stored, queryable, and protected by referential integrity.

#### Acceptance Criteria

1. THE database SHALL be PostgreSQL hosted on AWS RDS (Free Tier: db.t3.micro, 20GB storage).
2. THE database schema SHALL include the following tables: users, ahorro, creditos, gastos_ingresos, deudas, aportaciones, afore, gbm_portfolio, categories, instruments, courses, lessons, lesson_progress, conversation_sessions, and update_tracker.
3. ALL tables containing user data SHALL include a user_id column (VARCHAR, Firebase UID) with a foreign key reference to the users table.
4. ALL monetary amount columns SHALL be stored as TEXT type (to hold Fernet-encrypted ciphertext), not as numeric types.
5. THE database SHALL enforce NOT NULL constraints on all required fields as specified in each module's acceptance criteria.
6. THE database SHALL include indexes on user_id columns for all user-scoped tables to optimize query performance.
7. THE database schema SHALL include created_at and updated_at timestamp columns (UTC) on all tables, with updated_at automatically set on each modification.
8. IF a User is deleted from the users table, THEN ALL related records across all user-scoped tables SHALL be cascade-deleted.
9. THE database connection SHALL use SSL/TLS encryption in transit between the application and RDS instance.

---

### Requirement 20: API Design and Error Handling

**User Story:** As a frontend developer, I want a consistent RESTful API with predictable error responses, so that I can reliably integrate the SPA with the backend.

#### Acceptance Criteria

1. THE API_Gateway SHALL expose RESTful endpoints following the pattern: GET /api/{module} (list), POST /api/{module} (create), PUT /api/{module}/{id} (update), DELETE /api/{module}/{id} (delete), where {module} is one of: ahorro, creditos, gastos-ingresos, deudas, aportaciones, afore, gbm, categories, instruments, courses, lessons.
2. ALL API responses SHALL use JSON format with a consistent envelope structure: { "success": boolean, "data": object|array|null, "error": { "code": string, "message": string } | null }.
3. THE API_Gateway SHALL return the following HTTP status codes consistently: 200 (success), 201 (created), 400 (validation error), 401 (unauthorized), 403 (forbidden), 404 (not found), 500 (internal server error).
4. WHEN a validation error occurs, THE API_Gateway SHALL return a 400 response with an error object containing a field-level breakdown of which fields failed validation and why.
5. WHEN an unexpected error occurs, THE API_Gateway SHALL return a 500 response with a generic error message and SHALL NOT expose stack traces, internal paths, or database details in the response.
6. ALL API endpoints (except /api/auth/login and /api/auth/register) SHALL require a valid Bearer token in the Authorization header.
7. THE API_Gateway SHALL implement rate limiting of 100 requests per minute per user_id, returning HTTP 429 when the limit is exceeded.
8. THE API_Gateway SHALL include CORS headers allowing requests only from the configured SPA domain (CloudFront distribution URL).
9. ALL API endpoints SHALL respond within 5 seconds under normal load; if a response cannot be generated within 5 seconds, THE API_Gateway SHALL return a 504 Gateway Timeout response.

---

### Requirement 21: Frontend Architecture (Vue 3 SPA)

**User Story:** As a frontend developer, I want a well-structured Vue 3 application with clear component boundaries and state management, so that the codebase is maintainable and extensible.

#### Acceptance Criteria

1. THE SPA SHALL be built with Vue 3 (Composition API), Vue Router, Pinia for state management, and Tailwind CSS for styling.
2. THE SPA SHALL organize components into: layout components (TopNav, Sidebar, MainContent), page components (one per route), and reusable UI components (forms, charts, modals, buttons).
3. THE SPA SHALL use Pinia stores scoped by domain: authStore (authentication state), financeStore (financial module data), advisorStore (Fina conversation state), and learningStore (course progress).
4. THE SPA SHALL implement route guards that check authentication state before rendering protected routes, redirecting to /login if the User is not authenticated.
5. THE SPA SHALL use Axios (or fetch with an interceptor) to attach the Firebase ID token to all API requests and handle 401 responses by attempting token refresh before retrying the request once.
6. THE SPA SHALL lazy-load route components to minimize initial bundle size, with the core shell (TopNav, Sidebar, Router) loaded in the initial bundle.
7. THE SPA SHALL display loading indicators during API calls and error messages when API calls fail, without crashing the application.
8. THE SPA build SHALL produce a production bundle under 500KB (gzipped) for the initial load, excluding lazy-loaded chunks.
9. THE SPA SHALL use environment variables (VITE_API_URL, VITE_FIREBASE_CONFIG) for configuration, never hardcoding API URLs or Firebase credentials in source code.

---

### Requirement 22: CI/CD Pipeline (GitHub Actions)

**User Story:** As a platform operator, I want automated builds and deployments triggered by pushes to the production branch, so that releases are consistent and repeatable.

#### Acceptance Criteria

1. THE CI_CD_Pipeline SHALL trigger on every push to the `prd` branch in the GitHub repository.
2. THE CI_CD_Pipeline SHALL execute the following stages in order: install dependencies, run linting, run unit tests, build the SPA production bundle, and deploy.
3. IF any stage fails, THEN THE CI_CD_Pipeline SHALL halt execution, not proceed to deployment, and report the failure via GitHub Actions status.
4. THE CI_CD_Pipeline SHALL deploy the SPA build artifacts to the configured AWS S3 bucket and invalidate the CloudFront distribution cache.
5. THE CI_CD_Pipeline SHALL deploy the backend application to the configured compute target (Lambda or EC2) with the latest code.
6. THE CI_CD_Pipeline SHALL use GitHub Secrets for all sensitive configuration values (AWS credentials, Firebase config, FERNET_KEY, database connection string) and SHALL NOT expose them in logs.
7. THE CI_CD_Pipeline SHALL complete the full build and deployment process within 10 minutes under normal conditions.
8. THE CI_CD_Pipeline SHALL run database migrations (if any) as part of the deployment stage before the new backend code becomes active.

---

### Requirement 23: Infrastructure and Deployment (AWS Free Tier)

**User Story:** As a platform operator, I want the system deployed on AWS Free Tier services, so that I can run the platform at minimal cost during early stages.

#### Acceptance Criteria

1. THE SPA SHALL be hosted on an AWS S3 bucket configured for static website hosting, served through an AWS CloudFront distribution with HTTPS enabled.
2. THE backend SHALL be deployed as either AWS Lambda functions behind API Gateway, or as a FastAPI application on an EC2 t2.micro instance (Free Tier eligible).
3. THE database SHALL be hosted on AWS RDS PostgreSQL (db.t3.micro, Free Tier eligible) with 20GB of allocated storage.
4. ALL data in transit SHALL be encrypted using TLS 1.2 or higher (HTTPS for all endpoints, SSL for database connections).
5. THE CloudFront distribution SHALL be configured with a custom error page that serves index.html for all 404 responses (SPA routing support).
6. THE S3 bucket SHALL be configured with public access blocked; only CloudFront SHALL have read access via an Origin Access Identity (OAI) or Origin Access Control (OAC).
7. THE EC2 instance (if used) SHALL be configured with a security group allowing inbound traffic only on ports 443 (HTTPS) and 22 (SSH from a restricted IP range).
8. THE RDS instance SHALL be configured with a security group allowing inbound connections only from the application compute resource (Lambda VPC or EC2 security group).
9. THE system SHALL remain within AWS Free Tier limits for the first 12 months of operation under expected usage (up to 100 concurrent users, 10,000 API requests per day).

---

### Requirement 24: Security and Data Protection

**User Story:** As a User, I want my financial data protected against unauthorized access, injection attacks, and data leaks, so that I can trust the platform with sensitive information.

#### Acceptance Criteria

1. ALL user inputs SHALL be validated and sanitized on the backend before processing, rejecting any input that contains SQL injection patterns, XSS payloads, or exceeds defined length limits.
2. THE API_Gateway SHALL use parameterized queries (or an ORM with parameterized query generation) for all database operations, never constructing SQL queries via string concatenation.
3. THE SPA SHALL sanitize all user-generated content before rendering it in the DOM to prevent cross-site scripting (XSS) attacks.
4. THE system SHALL enforce the principle of least privilege: each User can only access and modify their own data, verified on every API request via the user_id extracted from the JWT.
5. THE API_Gateway SHALL set the following security headers on all responses: Content-Security-Policy, X-Content-Type-Options: nosniff, X-Frame-Options: DENY, Strict-Transport-Security with max-age of at least 31536000.
6. THE system SHALL NOT store passwords directly; Firebase Authentication handles all credential storage and verification.
7. ALL application logs SHALL exclude sensitive data (passwords, tokens, decrypted financial amounts, full account numbers).
8. THE database backups SHALL be encrypted at rest using AWS RDS encryption (AES-256).
9. IF more than 5 consecutive failed login attempts occur for the same email within 15 minutes, THEN THE Auth_Service SHALL temporarily lock the account for 15 minutes and return an error message indicating the account is temporarily locked.

---

### Requirement 25: Performance and Scalability

**User Story:** As a User, I want the platform to respond quickly and remain available under expected load, so that my experience is not degraded.

#### Acceptance Criteria

1. ALL API endpoints SHALL respond within 2 seconds for 95% of requests under normal load (up to 100 concurrent users).
2. THE SPA initial page load (Time to First Contentful Paint) SHALL be under 3 seconds on a 4G connection.
3. THE Cache SHALL reduce database query load by serving repeated read requests from memory, achieving a cache hit rate of at least 60% for read-heavy modules (ahorro, creditos, gastos_ingresos) under typical usage patterns.
4. THE Optimizer algorithm SHALL complete within 200 milliseconds for inputs of up to 50 instruments.
5. THE database SHALL handle up to 1000 rows per user-scoped table without degradation beyond the 2-second response time threshold.
6. THE SPA SHALL implement pagination for list views, displaying a maximum of 50 entries per page with next/previous navigation, to avoid loading unbounded result sets.
7. THE API_Gateway SHALL support gzip compression for all JSON responses exceeding 1KB in size.
8. IF the system detects that database connection pool is exhausted, THEN THE API_Gateway SHALL queue requests for up to 5 seconds before returning a 503 Service Unavailable response.

---

### Requirement 26: Accessibility and Internationalization

**User Story:** As a User with accessibility needs, I want the platform to be usable with assistive technologies, and as a Mexican User, I want content presented in Spanish with proper locale formatting.

#### Acceptance Criteria

1. THE SPA SHALL render all UI text in Spanish (Mexico locale: es-MX) by default, including labels, error messages, navigation items, and instructional text.
2. THE SPA SHALL format all monetary values according to the es-MX locale (e.g., $1,234.56 with comma as thousands separator and period as decimal separator, or as appropriate for the locale).
3. THE SPA SHALL format all dates according to the es-MX locale (dd/mm/yyyy or localized format).
4. ALL interactive elements in the SPA SHALL be accessible via keyboard navigation (Tab, Enter, Escape) without requiring a mouse.
5. THE SPA SHALL use semantic HTML elements (nav, main, section, article, button, label) and ARIA attributes where necessary to ensure screen reader compatibility.
6. ALL form inputs SHALL have associated labels (via `for`/`id` attributes or aria-label) that describe their purpose.
7. THE SPA SHALL maintain a minimum color contrast ratio of 4.5:1 for normal text and 3:1 for large text, in both light and dark modes, conforming to WCAG 2.1 Level AA.
8. ALL images and icons with semantic meaning SHALL include alt text or aria-label attributes; decorative images SHALL use aria-hidden="true" or empty alt attributes.
9. THE SPA SHALL ensure that focus indicators are visible on all interactive elements when navigated via keyboard.