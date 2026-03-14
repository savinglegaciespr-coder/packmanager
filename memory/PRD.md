# PRD — PAWS TRAINING MVP

## Original Problem Statement
Build a full-stack private web application for a dog training business called **PAWS TRAINING** with the slogan **BY PET LOVERS SITTING**.

MVP scope:
- landing page
- client booking flow
- admin dashboard
- weekly capacity logic
- document validation
- email notifications

Excluded:
- client accounts / portals
- chat systems
- WhatsApp integrations
- dog progress photo/video uploads
- external third-party integrations

Brand / UX requirements:
- dark background with black, white, silver, and red accents
- premium, modern, polished, trustworthy aesthetic
- responsive on desktop, tablet, mobile
- Spanish default with visible English toggle

Core business rules:
- operational calendar starts at March 30, 2026 and continues dynamically into future weeks/years
- default capacity is 8 dogs per week
- admin can override weekly capacity
- 6-day program occupies one week; multi-week programs occupy consecutive weeks
- prevent overbooking across all affected weeks
- public booking must collect owner info, dog info, payment proof, vaccination certificate
- submitted bookings start as Pending Review and temporarily reserve capacity
- pending reservations expire after 24 hours if not reviewed
- admin validates payment proof, vaccination certificate, and eligibility before final approval
- admin dashboard must show metrics, charts, bookings management, service management, weekly capacity, settings, and manual booking creation
- uploaded documents must remain admin-only

## User Choices
- Initial admin login: safe default demo admin
- Email handling: Gmail SMTP fully configured and working
- Logo: temporary placeholder now, swappable logo support included
- Language priority: Spanish-first with English toggle

## Architecture Decisions
- **Frontend:** React + React Router single-page app with public routes and protected admin workspace
- **Backend:** FastAPI with JWT-based admin auth and multipart upload handling
- **Database:** MongoDB with string UUID identifiers to avoid ObjectId serialization issues
- **Storage:** protected local file storage for uploaded documents and brand logo assets
- **Business Config Layer:** settings document drives business name, slogan, contact details, notification email, terminology, colors, and logo
- **Email Workflow:** Gmail SMTP delivery for booking submitted / approved / rejected notifications
- **Capacity Engine:** week-based occupancy calculations across single-week and multi-week programs with automatic stale pending expiry

## User Personas
- **Dog Owner:** wants a simple bilingual booking flow, clear weekly availability, and confidence that documents were submitted correctly
- **Business Admin:** needs fast review tools for bookings, documents, weekly occupancy, revenue visibility, and service/configuration management
- **Business Operator / Future Reuse Admin:** wants configurable business settings so the same architecture can support a similar service business later

## Core Requirements (Static)
- premium bilingual landing page
- visible weekly capacity and availability labels
- public booking with required payment and vaccine uploads
- admin login and private dashboard
- program management and weekly capacity overrides
- manual admin booking creation
- document review workflow with protected file access
- seeded launch data for March 30 and April 6, 2026
- branded notification workflow for booking submitted / approved / rejected

## What's Been Implemented
### 2026-03-11
- Built bilingual public landing page with premium dark styling, responsive layout, language toggle, hero, programs, process, and contact sections
- Built full public booking flow with live weekly availability, required uploads, and Pending Review reservation creation
- Updated the public dog form to use Spanish-only wording for the key fields, removed manual age entry, and added automatic age calculation from the dog's birth date
- Extended admin settings with configurable currency (USD/EUR/GBP) and dynamic landing content controls for hero copy, CTA labels, and the existing hero feature cards
- Added a weekly operational view in admin capacity to show each week's assigned dogs with booking/payment/vaccination statuses for faster operations review
- Replaced the floating Emergent badge with a natural footer for public/admin layouts and applied currency-aware formatting to prices, summaries, dashboard revenue, and price-related internal emails
- Refined USD formatting to always use symbol-first values like $420 across the UI and emails, and added a dedicated separate admin view: Vista semanal / Weekly Operations
- Added a second separate admin operational display mode: Modo Operaciones / Operations Screen, built for large screens/TVs with operational-only summary cards, grouped weekly dog assignments, and 30-second auto-refresh
- Cleaned launch data from April 13, 2026 onward by removing future demo/test bookings, clearing future occupancy, and restoring clean weekly availability for real operations
- Added configurable Landing Hero Image controls in admin settings with URL support and file-upload support, while keeping the existing landing layout and default dog hero fallback when no custom image is set
- Refined the landing hero into a reusable premium image frame with a controlled 4:5 portrait container, stronger CTA hierarchy, improved spacing, and more polished feature cards for any admin-uploaded hero image
- Removed all text overlay from the hero image area and restored the right side to a large clean full-height visual panel that adapts to any uploaded hero image without affecting layout integrity
- Finalized the hero image as a true full-height right-column panel with no overlay, no card styling, and exact height alignment to the left hero content for a premium SaaS-style landing layout
- Completed a manual deployment-readiness pass: verified supervisor is already configured/running in the environment, confirmed frontend/API health responses, and replaced external fallback landing images with local bundled assets for safer deployment behavior
- Removed demo admin credentials from the public login experience and from the public config response, while keeping the existing authentication system unchanged
- Updated the dog birth date field in the public booking form to use a native mobile-friendly date picker with future dates blocked, while preserving the existing automatic age calculation behavior
- Improved admin mobile responsiveness with a more usable small-screen layout, larger touch targets, and mobile-safe modal dialogs/action bars while preserving desktop behavior and business logic
- Improved public mobile booking form usability by applying mobile-friendly input types (email/tel/number) and tightening the booking-page header spacing so the form content sits higher on small screens
- Hid admin access controls from the public interface for non-authenticated visitors, while keeping the direct `/admin/login` route available and preserving existing authentication logic
- Replaced internal email logging mode with real Gmail SMTP delivery, added masked SMTP settings in admin configuration, and verified real send flows for booking submission, admin notification, approval, and rejection
- Clarified the reservation review modal with explicit field labels and automatic read-only intake/delivery dates derived from the booking's selected week and stored program duration
- Replaced the booking week selector with a monthly visual calendar interface that reuses existing weekly capacity data, color-codes availability, and preserves the current booking/capacity logic across desktop and mobile
- Added frontend-only email confirmation validation in the public booking form, including a confirm-email field, valid email format checks, and clear mismatch messaging without changing stored booking data
- Standardized the vaccination declaration field across the public and manual booking forms as a simple yes/no selector labeled "Vacunas al día," while preserving the separate certificate upload/review workflow
- Aligned the manual booking modal with the intended reservation workflow by using birth date as the editable age source, auto-calculating age/intake/delivery dates, and making derived date fields read-only
- Updated manual booking week selection to reuse live weekly capacity data, visually mark unavailable weeks, and block manual reservations from exceeding configured weekly occupancy
- Improved admin weekly capacity visibility by separating confirmed, pending, and available counts across dashboard occupancy, capacity management, and weekly operational views
- Implemented FastAPI backend for public config, programs, weeks, booking submission, admin auth, dashboard, bookings, settings, logo upload, document access, and capacity management
- Added weekly capacity engine with multi-week occupancy protection, override support, and 24-hour pending expiration logic
- Added admin workspace with dashboard charts/metrics, bookings filters, detail dialog, document status controls, manual booking creation, programs management, capacity controls, settings, and email log view
- Seeded demo admin, programs, weekly capacity override, sample bookings, and sample email logs for populated first launch experience
- Added reusable regression coverage via backend tests and completed browser flow verification

### 2026-03-14
- Fixed email notification system: made send_email_via_smtp async (uses asyncio.to_thread for non-blocking SMTP), added detailed SMTP logging, backfilled old email logs with proper delivery_status field
- Verified all 4 email flows work: new booking (admin + client), approval, rejection — all via real Gmail SMTP
- Testing agent confirmed 100% pass rate (7/7 backend tests, all frontend elements functional)

### 2026-03-14 (continued)
- Implemented two-stage payment system: Deposit (existing payment_proof/payment_status) + Final Payment (new final_payment_proof/final_payment_status)
- Added computed overall_payment_status: Deposit Pending → Deposit Verified → Balance Pending → Paid in Full
- Admin booking dialog: separate deposit/final payment verification controls, final payment proof upload, overall payment badge
- Reservations table: overall_payment_status badge column replaces old single docs column
- Dashboard metrics: deposits_pending, deposits_verified, balance_pending, paid_in_full
- Weekly operations and operations screen views show overall_payment_status
- Public booking form relabeled: "Comprobante de depósito" / "Deposit proof"
- Admin can upload final payment proof via POST /api/admin/bookings/{id}/final-payment-proof
- Migration backfills existing bookings with final_payment_status: "Pending Review"
- Bilingual translations (ES/EN) for all new labels and status values
- Testing agent: 100% pass (12/12 backend, all frontend verified)

### 2026-03-14 (deposit config)
- Added configurable deposit settings to each program: deposit_type (percentage/fixed) and deposit_value
- Deposit computation: percentage mode = price * value / 100; fixed mode = min(value, price); balance = price - deposit
- Program cards and form show deposit type, value, and computed deposit/balance split
- Booking detail dialog shows deposit_amount and balance_amount
- Public booking success panel shows deposit and balance breakdown
- Dashboard financial metrics: total_deposit_expected, total_deposit_collected, total_balance_expected, total_balance_collected
- Dashboard cards: "Depósitos cobrados" and "Saldo por cobrar"
- Migration backfills existing programs with deposit_type=percentage, deposit_value=50
- Backward compatibility: old bookings without deposit config in snapshot default to 100% deposit
- Bilingual translations (ES/EN) for all new labels
- Testing agent: 100% pass (13/13 backend, all frontend verified)

### 2026-03-14 (deposit-first flow)
- Implemented deposit-first booking flow: clients submit only deposit proof during booking
- Added final_payment_token (secrets.token_urlsafe) to every booking for secure link access
- New public endpoints: GET /api/public/booking-payment/{token} (booking summary), POST .../upload (final payment proof)
- When admin verifies deposit (payment_status → Verified), system sends email with secure /payment/{token} link
- Client opens link → sees booking summary (owner, dog, program, deposit ✓, remaining balance) + upload form
- Upload guards: blocks if deposit not verified, blocks re-upload if already submitted
- Admin notification email sent when client uploads final payment proof
- New FinalPaymentPage component with bilingual support (ES/EN), error handling for invalid tokens
- Route: /payment/:token — public, no auth required
- FRONTEND_URL env var added for email link generation
- Testing agent: 100% pass (10/10 backend, all frontend verified)

### 2026-03-14 (financial dashboard + email policy)
- Enhanced financial dashboard with dedicated Financial Summary card: 4 colored boxes (Deposits collected green, Final payments blue, Outstanding yellow, Total revenue white)
- Replaced revenue chart with Payment Breakdown chart: 3 colored bars per month (deposits, final payments, outstanding)
- Added total_revenue_collected metric (deposit_collected + balance_collected)
- Added per-month payment tracking (payment_summary) in dashboard data
- Updated deposit-verified email: includes non-refundable deposit policy notice (ES: "AVISO IMPORTANTE", EN: "IMPORTANT NOTICE") and secure /payment/{token} upload link
- Bilingual translations for all new financial labels
- Testing agent: 100% pass (8/8 backend, all frontend verified)

### 2026-03-14 (deposit policy notice on booking form)
- Added visible deposit policy notice (yellow box) above submit button on public booking form
- Non-refundable deposit policy text in both ES/EN
- Required checkbox: "Entiendo y acepto la política de depósito no reembolsable"
- Submit button disabled until checkbox is checked
- Form validation blocks submission if policy not accepted
- Bilingual translations for policy title, text, and acceptance label

### 2026-03-14 (mobile file upload preview fix)
- Added HEIC/HEIF file support: auto-converts to JPEG during upload using pillow-heif for browser compatibility
- Updated save_upload to store content_type in file info dict
- Document endpoint returns FileResponse with explicit media_type from stored content_type or extension fallback
- Frontend image preview: images open in an overlay modal with close button instead of new tab
- Frontend PDF preview: PDFs open in new browser tab for viewing
- Installed pillow + pillow-heif packages
- Testing agent: 100% pass (8/8 backend, all frontend verified)

## Prioritized Backlog
1. Add richer chart drill-downs and exportable reporting
2. Split large frontend file into smaller modules for maintainability
3. Add optional status-change email toggles from admin settings
4. Add richer business branding controls (more palette fields / media management)
5. Add audit history for booking updates and document review actions

## Remaining Features by Priority
### P0
- None for MVP scope — all core features implemented and working

### P1
- Modularize frontend/admin components into smaller files
- Add richer admin notes history / change history per booking
- Add better empty states and bulk admin actions

### P2
- Richer analytics filters and CSV exports
- Additional white-label business presets for other service businesses
- Refactor backend/server.py into modular routers

## Next Tasks List
- Keep the seeded demo data stable while real branding content is added
- Replace placeholder logo with final uploaded brand asset when available
- Optional next phase: modular refactor and expanded admin reporting
