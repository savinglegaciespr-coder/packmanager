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
- Email handling: full notification workflow implemented, outgoing emails logged internally until SMTP is added later
- Logo: temporary placeholder now, swappable logo support included
- Language priority: Spanish-first with English toggle

## Architecture Decisions
- **Frontend:** React + React Router single-page app with public routes and protected admin workspace
- **Backend:** FastAPI with JWT-based admin auth and multipart upload handling
- **Database:** MongoDB with string UUID identifiers to avoid ObjectId serialization issues
- **Storage:** protected local file storage for uploaded documents and brand logo assets
- **Business Config Layer:** settings document drives business name, slogan, contact details, notification email, terminology, colors, and logo
- **Email Workflow:** branded internal email log collection used for booking submitted / approved / rejected notifications
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

## What’s Been Implemented
### 2026-03-11
- Built bilingual public landing page with premium dark styling, responsive layout, language toggle, hero, programs, process, and contact sections
- Built full public booking flow with live weekly availability, required uploads, and Pending Review reservation creation
- Updated the public dog form to use Spanish-only wording for the key fields, removed manual age entry, and added automatic age calculation from the dog's birth date
- Extended admin settings with configurable currency (USD/EUR/GBP) and dynamic landing content controls for hero copy, CTA labels, and the existing hero feature cards
- Added a weekly operational view in admin capacity to show each week’s assigned dogs with booking/payment/vaccination statuses for faster operations review
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
- Clarified the reservation review modal with explicit field labels and automatic read-only intake/delivery dates derived from the booking’s selected week and stored program duration
- Replaced the booking week selector with a monthly visual calendar interface that reuses existing weekly capacity data, color-codes availability, and preserves the current booking/capacity logic across desktop and mobile
- Added frontend-only email confirmation validation in the public booking form, including a confirm-email field, valid email format checks, and clear mismatch messaging without changing stored booking data
- Standardized the vaccination declaration field across the public and manual booking forms as a simple yes/no selector labeled “Vacunas al día,” while preserving the separate certificate upload/review workflow
- Aligned the manual booking modal with the intended reservation workflow by using birth date as the editable age source, auto-calculating age/intake/delivery dates, and making derived date fields read-only
- Updated manual booking week selection to reuse live weekly capacity data, visually mark unavailable weeks, and block manual reservations from exceeding configured weekly occupancy
- Improved admin weekly capacity visibility by separating confirmed, pending, and available counts across dashboard occupancy, capacity management, and weekly operational views
- Implemented FastAPI backend for public config, programs, weeks, booking submission, admin auth, dashboard, bookings, settings, logo upload, document access, and capacity management
- Added weekly capacity engine with multi-week occupancy protection, override support, and 24-hour pending expiration logic
- Added admin workspace with dashboard charts/metrics, bookings filters, detail dialog, document status controls, manual booking creation, programs management, capacity controls, settings, and email log view
- Seeded demo admin, programs, weekly capacity override, sample bookings, and sample email logs for populated first launch experience
- Added reusable regression coverage via backend tests and completed browser flow verification

## Prioritized Backlog
1. Add richer chart drill-downs and exportable reporting
2. Split large frontend file into smaller modules for maintainability
3. Add optional status-change email toggles from admin settings
4. Add richer business branding controls (more palette fields / media management)
5. Add audit history for booking updates and document review actions

## Remaining Features by Priority
### P0
- None for MVP scope

### P1
- Modularize frontend/admin components into smaller files
- Add richer admin notes history / change history per booking
- Add better empty states and bulk admin actions

### P2
- SMTP credential entry + real email sending
- richer analytics filters and CSV exports
- additional white-label business presets for other service businesses

## Next Tasks List
- Keep the seeded demo data stable while real branding content is added
- Replace placeholder logo with final uploaded brand asset when available
- Optional next phase: real SMTP delivery, modular refactor, and expanded admin reporting
