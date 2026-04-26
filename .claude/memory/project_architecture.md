# Project Architecture

- **Monolito**: backend en `backend/server.py`, frontend en `frontend/src/App.js`
- **Storage**: Cloudinary only; no archivos locales
- **Auth**: JWT con roles `superadmin`, `admin`, `operator`
- **Telegram**: integración activa; no tocar sin autorización
- **Deploy**: Railway vía GraphQL
- **Branch**: `main` protegida
