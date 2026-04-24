# packmanager — Project Memory

## Stack

| Layer | Tech |
|-------|------|
| Backend | Python / FastAPI, Uvicorn |
| Database | MongoDB Atlas, cluster `pawstraining`, motor async driver |
| File storage | Cloudinary (cloud name: `dyuksod2i`) |
| Hosting | Railway |
| Frontend | React 19, Create React App + craco, Tailwind CSS, Radix UI |

## URLs

| Service | URL |
|---------|-----|
| Backend (Railway) | https://packmanager-production-dfd2.up.railway.app |
| Frontend (Railway) | https://frontend-production-d4977.up.railway.app |

## Railway

- Project name: **alluring-mercy**
- Project ID: `daa530f3-005a-46fb-ae7d-cc1372737317`
- Environment: `production` (ID: `cea78451-6128-43cb-b7e7-fe319c3ba63c`)
- Backend service: **packmanager** (ID: `b69effe0-0ad1-4623-be92-4943417f9681`)
- Frontend service: **frontend** (ID: `2fb20633-d376-4a8e-b92f-176d1949d11a`)
- API token: `40aae0e3-a193-4a4e-afbb-85487b0f6dcc`
  - Used via Railway GraphQL API (not CLI — CLI v4 rejects non-browser tokens)
  - Endpoint: `https://backboard.railway.app/graphql/v2`
  - Auth header: `Authorization: Bearer <token>`

## Key files

- `backend/server.py` — entire FastAPI app (monolithic)
- `backend/requirements.txt` — Python dependencies
- `frontend/src/App.js` — entire React app (monolithic)
- `frontend/src/lib/api.js` — all API call wrappers
- `frontend/railway.json` — Railway build/start config for frontend

## Environment variables

### Backend (Railway service: packmanager)
```
MONGO_URL
DB_NAME
JWT_SECRET
DEMO_ADMIN_EMAIL
DEMO_ADMIN_PASSWORD
DEMO_ADMIN_NAME
CORS_ORIGINS
CLOUDINARY_CLOUD_NAME=dyuksod2i
CLOUDINARY_API_KEY=569632736354531
CLOUDINARY_API_SECRET=ueJOoWr8_DDnhK1PwCJ_gAFvhxc
```

### Frontend (Railway service: frontend)
```
REACT_APP_BACKEND_URL=https://packmanager-production-dfd2.up.railway.app
```

## Completed tasks

| Task | Description | Commit |
|------|-------------|--------|
| Task 1 | Enforce 10 MB upload size limit | `9786361` |
| Task 2 | (see git log) | — |
| Task 3 | Add MongoDB indexes on startup | `cfef8c0` |
| Task 4 | Paginate admin bookings endpoint in MongoDB | `7287e94` |
| Task 5 | Cloudinary integration — replace local `./backend/storage/` with Cloudinary uploads under `pawstraining/` folder | `618658c` |
| Task 6 | Pin bcrypt to 4.0.1 to fix passlib warning | `0afbdde` |
| Deploy frontend | Railway config (`frontend/railway.json`), service created and deployed | `58b9885` |
| Task 4 frontend | Pagination support in BookingsView — reads `{bookings, total, page, total_pages}` from API, shows prev/next controls | `(latest)` |
| Frontend build fix | Switch to Dockerfile builder, fix CRA/Node20 ajv conflicts, disable ESLint plugin, stub ForkTsChecker, pin serve@13 | `b78466f` |
| Backend Cloudinary fix | Add missing CLOUDINARY_* env vars to Railway backend service (were causing CRASHED state) | `2026-04-24` |

## API shape — GET /api/admin/bookings

Backend returns (since Task 4):
```json
{
  "bookings": [...],
  "total": 42,
  "page": 1,
  "limit": 20,
  "total_pages": 3
}
```

Query params accepted: `status_filter`, `program_id`, `week_start`, `search`, `page` (default 1), `limit` (default 20).

## Deployment workflow

- Every `git push` to `main` triggers auto-deploy on Railway for both services.
- **Important:** Auto-deploy from git push is unreliable — use `latestCommit: true` in the API call to force the latest commit.
- To force a manual deploy via API:
  ```bash
  curl -s -X POST https://backboard.railway.app/graphql/v2 \
    -H "Authorization: Bearer 40aae0e3-a193-4a4e-afbb-85487b0f6dcc" \
    -H "Content-Type: application/json" \
    -d '{"query": "mutation { serviceInstanceDeploy(serviceId: \"<SERVICE_ID>\", environmentId: \"cea78451-6128-43cb-b7e7-fe319c3ba63c\", latestCommit: true) }"}'
  ```
