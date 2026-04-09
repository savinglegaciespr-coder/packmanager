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
16. Advanced Document Viewer — Rich preview modal with image zoom/pan, PDF embedding
17. Initialization Resilience — Auto-retry, error state, API timeout
18. Health endpoint for Kubernetes deployment
19. **Role-Based Access Control (RBAC)** — Three roles (superadmin, admin, operator) with granular permissions. Superadmin: full access + user management. Admin: create up to 3 operators. Operator: read-only dashboards/bookings. User management UI with role badges. Settings restricted to superadmin only. (Completed & Tested Feb 2026)
20. **RBAC Endpoint Enforcement** — All backend endpoints now enforce role restrictions. Superadmin-only: settings, programs CRUD, capacity write. Admin+superadmin: dashboard, email-logs, manual booking, final payment upload. Operator: bookings (financial data stripped), status-only PATCH, documents. Frontend nav gated per role. (Completed & Tested Feb 2026)
21. **RBAC Frontend UI Enforcement** — Complete DOM-level role restrictions. Operator booking detail hides price/deposit/balance/overall payment, shows only Paid/Pending status, form limited to status dropdown only. Admin hides Programs/Capacity/Settings. Navigation items dynamically built per role. Operator redirects to /admin/bookings on login. (Completed & Tested Feb 2026)
22. **Change Password** — All roles can change their own password via sidebar modal. Backend validates current password, enforces 8-char minimum. Uses existing bcrypt/passlib hashing. (Completed & Tested Feb 2026)

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
