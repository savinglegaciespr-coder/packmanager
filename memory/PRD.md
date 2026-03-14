# PAWS TRAINING - Product Requirements Document

## Original Problem Statement
Build a full-stack private web application for a dog training business called "PAWS TRAINING".

**MVP Scope:** Landing page, client booking flow, admin dashboard. Weekly capacity logic (8 dogs/week, starting March 30, 2026). Document validation (payment proof, vaccination certificate). Email notifications for booking statuses. Exclude client accounts, chat, etc.

**Branding & UI:** Dark theme: black, white, silver, red accents. Premium, modern, responsive. Bilingual: Spanish (default) and English.

## Tech Stack
- **Frontend:** React, Tailwind CSS, Shadcn/UI, Recharts, React Router
- **Backend:** FastAPI (Python), Pydantic, Motor (async MongoDB driver)
- **Database:** MongoDB
- **Auth:** JWT
- **Email:** Gmail SMTP
- **Image Processing:** Pillow, pyheif (HEIC conversion)

## Architecture
Single-page monolith: entire frontend in `/app/frontend/src/App.js`, backend in `/app/backend/server.py`.

## Admin Credentials
- Email: admin@pawstraining.com
- Password: PawsAdmin2026!

## Completed Features (All Tested & Verified)
1. Bilingual landing page (ES/EN) with configurable hero, programs, contact
2. Public booking form with calendar-based week selection, deposit policy checkbox
3. Admin login with JWT authentication
4. Admin dashboard with financial metrics (deposits, final payments, outstanding balance)
5. Reservations management with filters, search, detail dialog
6. Manual booking creation for admin
7. Program CRUD with configurable deposits (fixed/percentage)
8. Weekly capacity control
9. Weekly operations view
10. Operations screen (large display optimized)
11. Settings panel (business info, SMTP, landing content, currency, hero image)
12. Two-stage payment system (deposit + final payment)
13. Client final payment portal via secure token link
14. Gmail SMTP email notifications
15. HEIC to JPEG conversion for mobile uploads
16. **Advanced Document Viewer** - Rich preview modal with image zoom/pan, PDF embedding, fallback for unsupported types, open in new tab, download (Completed & Tested Feb 2026)

## Key API Endpoints
- `POST /api/auth/login` - Admin login
- `GET /api/admin/dashboard` - Dashboard metrics
- `GET /api/admin/bookings` - List all bookings
- `PATCH /api/admin/bookings/{id}` - Update booking
- `POST /api/admin/bookings/manual` - Create manual booking
- `GET /api/admin/documents/{booking_id}/{doc_type}` - Serve documents
- `POST /api/admin/bookings/{id}/final-payment-proof` - Upload final payment
- `GET /api/public/booking-payment/{token}` - Client payment page
- `POST /api/public/booking-payment/{token}/upload` - Client upload final payment

## Database Collections
- **bookings**: Full booking data including documents, payment status, scheduling
- **programs**: Training program config with deposit rules
- **settings**: Business config, SMTP credentials, landing content
- **admins**: Admin user credentials
- **email_logs**: Sent email records
- **capacity_overrides**: Per-week capacity customizations

## Backlog / Future Tasks
- Refactor `server.py` into modular FastAPI routers
- Refactor `App.js` into smaller page/component files
- No pending feature requests from user
