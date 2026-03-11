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
