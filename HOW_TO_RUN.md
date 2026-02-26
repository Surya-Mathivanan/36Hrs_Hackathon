# 🚀 How to Run — Campus Carbon Footprint Analyzer

> **Stack:** Django REST Backend + React Frontend + PostgreSQL Database

---

## ✅ Prerequisites

Make sure the following are installed on your system:

| Tool | Version | Check Command |
|------|---------|---------------|
| Python | 3.11+ | `python --version` |
| Node.js | 18+ | `node --version` |
| npm | 9+ | `npm --version` |
| PostgreSQL DB | Any (local or cloud) | — |

---

## 📁 Project Structure

```
36Hrs_Hackathon-main/
├── backend/      ← Django REST API  (runs on port 8000)
├── frontend/     ← React + Vite app (runs on port 5173)
├── Documents/    ← Project docs & presentations
├── README.md
└── HOW_TO_RUN.md ← You are here
```

---

## STEP 1 — Set Up the Database

You need a **PostgreSQL** database. You can use any of these:

| Option | How to Get URL |
|--------|---------------|
| **Local PostgreSQL** | Install from https://www.postgresql.org/download/ |
| **Supabase (free cloud)** | https://supabase.com → New project → Settings → Database |
| **Neon (free cloud)** | https://neon.tech → New project → Connection string |
| **Railway (free cloud)** | https://railway.app → New PostgreSQL → Connect |

Your database URL will look like:
```
postgresql://username:password@host:port/database_name
```

---

## STEP 2 — Configure the Backend `.env`

Open `backend/.env` and fill in your values:

```env
# 🔴 REQUIRED — paste your PostgreSQL connection URL here
DATABASE_URL=postgresql://your_user:your_password@your_host:5432/your_db_name

# 🔴 REQUIRED — generate any long random string (e.g., 50 chars)
SECRET_KEY=replace-this-with-a-long-random-secret-key-50chars

# Development settings
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
CORS_ALLOWED_ORIGINS=http://localhost:5173,http://localhost:3000
ACCESS_TOKEN_LIFETIME_HOURS=24
```

> 💡 **Tip:** To generate a secret key, run:
> ```bash
> python -c "import secrets; print(secrets.token_urlsafe(50))"
> ```

> ⚠️ **Cloud DB SSL Note:** Cloud databases (Supabase, Neon, Railway) require SSL.
> The app handles this automatically.
> For **local PostgreSQL only**, open `backend/core/settings.py` and remove:
> ```python
> 'OPTIONS': {'sslmode': 'require'},
> ```

---

## STEP 3 — Install Backend Dependencies

Open a terminal and run:

```bash
cd backend
pip install -r requirements.txt
```

This installs: `django`, `djangorestframework`, `djangorestframework-simplejwt`, `django-cors-headers`, `psycopg2-binary`, `python-dotenv`

---

## STEP 4 — Set Up the Database Schema

Run Django migrations to create all tables:

```bash
cd backend
python manage.py migrate
```

You should see output like:
```
Applying api.0001_initial... OK
Applying auth.0001_initial... OK
...
```

---

## STEP 5 — Seed Initial Data

This command creates the **admin user**, **emission factors**, and **sample activity data**:

```bash
python manage.py seed_data
```

Output:
```
✅ Emission factor [electricity] created
✅ Emission factor [bus_diesel] created
✅ Emission factor [canteen_lpg] created
✅ Emission factor [waste_landfill] created
✅ Admin user created (admin / admin123)
✅ Inserted 54 sample activity records
✅ Inserted 12 sample human population records
🎯 Database seeding completed successfully!
```

---

## STEP 6 — Start the Backend Server

```bash
cd backend
python manage.py runserver
```

You should see:
```
Starting development server at http://127.0.0.1:8000/
```

✅ **Backend is now running at:** `http://localhost:8000`

Test it: Open `http://localhost:8000/api/dashboard/` in your browser — you should see JSON data.

---

## STEP 7 — Install Frontend Dependencies

Open a **new/second terminal** and run:

```bash
cd frontend
npm install
```

---

## STEP 8 — Start the Frontend

```bash
cd frontend
npm run dev
```

You should see:
```
VITE v7.x.x  ready in 300ms
➜  Local:   http://localhost:5173/
```

✅ **Frontend is now running at:** `http://localhost:5173`

---

## 🎉 Open the App

Go to **http://localhost:5173** in your browser.

| Page | URL | Auth Required? |
|------|-----|----------------|
| Dashboard | `http://localhost:5173/` | ❌ Public |
| Admin Login | `http://localhost:5173/login` | ❌ — |
| Data Input | `http://localhost:5173/data-input` | ✅ Login first |

**Login credentials:**
- Username: `admin`
- Password: `admin123`

---

## 🔁 Quick Start (After First Setup)

Once everything is set up, just run these two commands in separate terminals:

**Terminal 1 — Backend:**
```bash
cd backend
python manage.py runserver
```

**Terminal 2 — Frontend:**
```bash
cd frontend
npm run dev
```

---

## 🛠️ Troubleshooting

### ❌ `DB_PASSWORD not found` or `DATABASE_URL` error
→ Make sure `backend/.env` exists and `DATABASE_URL` is set correctly.

### ❌ `connection refused` on port 5432
→ Your PostgreSQL server isn't running, or the host/port in `DATABASE_URL` is wrong.

### ❌ `SSL connection required` error
→ You're connecting to a cloud DB. The app handles this automatically. If you still get this error, check that your `DATABASE_URL` starts with `postgresql://` (not `postgres://`).

### ❌ `CORS blocked` in browser
→ Make sure `backend/.env` has:
```
CORS_ALLOWED_ORIGINS=http://localhost:5173
```
Then restart the backend (`Ctrl+C` → `python manage.py runserver`).

### ❌ `Module not found` on npm run dev
→ Run `npm install` inside the `frontend/` folder again.

### ❌ Charts not showing on dashboard
→ The dashboard needs data in the DB. Run `python manage.py seed_data` in the backend folder. Also make sure both backend (port 8000) and frontend (port 5173) are running simultaneously.

### ❌ Login says `Invalid credentials`
→ Make sure you ran `python manage.py seed_data`. The admin user is created by that command.

---

## 🔐 Default Credentials

| Username | Password |
|----------|----------|
| `admin` | `admin123` |

> Change this in production via Django admin panel: `http://localhost:8000/admin/`

---

## 📦 All API Endpoints (Reference)

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `GET` | `/api/dashboard/` | Public | Dashboard data + charts |
| `GET` | `/api/recommendations/` | Public | Reduction recommendations |
| `GET` | `/api/emission_factors/` | Public | CO₂ conversion factors |
| `GET` | `/api/human_cumulative_stats/` | Public | All-time population stats |
| `POST` | `/api/auth/login/` | Public | Login → JWT tokens |
| `POST` | `/api/auth/refresh/` | Public | Refresh access token |
| `GET` | `/api/auth/me/` | 🔒 JWT | Current user info |
| `POST` | `/api/data/` | 🔒 JWT | Add activity data |
| `POST` | `/api/human_data/` | 🔒 JWT | Add population data |
| `POST` | `/api/upload_csv/` | 🔒 JWT | Bulk CSV upload |

---

*Built for KIT — Kalaignar Karunanidhi Institute of Technology | UN SDG 13: Climate Action*
