# Campus Carbon Footprint Analyzer

A full-stack web application for tracking and analyzing campus carbon emissions.  
**Backend**: Django REST Framework | **Frontend**: React + Vite | **Database**: PostgreSQL

---

## 🏗️ Project Structure

```
36Hrs_Hackathon-main/
├── backend/                   # Django REST API
│   ├── core/                  # Django project settings, URLs
│   ├── api/                   # App: models, views, serializers, URLs
│   │   └── management/commands/seed_data.py
│   ├── .env                   # Backend environment variables
│   ├── requirements.txt
│   └── manage.py
│
└── frontend/                  # React + Vite app
    ├── src/
    │   ├── context/AuthContext.jsx
    │   ├── services/api.js
    │   ├── components/Sidebar.jsx
    │   ├── pages/
    │   │   ├── DashboardPage.jsx
    │   │   ├── LoginPage.jsx
    │   │   └── DataInputPage.jsx
    │   ├── App.jsx
    │   └── index.css
    ├── .env
    └── vite.config.js
```

---

## ⚙️ Backend Setup (Django)

### 1. Install dependencies
```bash
cd backend
pip install -r requirements.txt
```

### 2. Configure `.env`
Edit `backend/.env` with your PostgreSQL URL:
```env
DATABASE_URL=postgresql://user:password@host:5432/campus_carbon
SECRET_KEY=your-long-random-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
CORS_ALLOWED_ORIGINS=http://localhost:5173,http://localhost:3000
```

### 3. Run migrations
```bash
python manage.py makemigrations api
python manage.py migrate
```

### 4. Seed data (emission factors + admin user + sample data)
```bash
python manage.py seed_data
```
Default admin credentials: **admin / admin123**

### 5. Start the backend
```bash
python manage.py runserver
```
Backend will be running at **http://localhost:8000**

---

## 🎨 Frontend Setup (React)

### 1. Install dependencies
```bash
cd frontend
npm install
```

### 2. Configure `.env` (optional, default is localhost:8000)
```env
VITE_API_URL=http://localhost:8000/api
```

### 3. Start the dev server
```bash
npm run dev
```
Frontend will be at **http://localhost:5173**

---

## 🔌 API Endpoints

### Public
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/dashboard/` | Full dashboard data with date filters |
| GET | `/api/recommendations/` | Emission reduction recommendations |
| GET | `/api/emission_factors/` | List emission conversion factors |
| GET | `/api/human_cumulative_stats/` | All-time human emission stats |

### Auth
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/login/` | Login → returns JWT access + refresh tokens |
| POST | `/api/auth/refresh/` | Refresh access token |
| GET | `/api/auth/me/` | Current user info |

### Protected (Bearer JWT required)
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/data/` | Add single activity record |
| POST | `/api/human_data/` | Add/update human population data |
| POST | `/api/upload_csv/` | Bulk insert records via JSON |

---

## 🔐 Security Notes

- JWT tokens (access: 24h, refresh: 7d) stored in `localStorage`
- Django `authenticate()` uses bcrypt-hashed passwords via `create_superuser`
- CORS restricted to configured origins
- SQL injection protected via Django ORM
- Change `SECRET_KEY` and `DEBUG=False` before any production deployment

---

## 📦 Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.11+, Django 4.2+, DRF 3.14+ |
| Auth | DRF SimpleJWT |
| Database | PostgreSQL (psycopg2-binary) |
| Frontend | React 18, Vite |
| Charts | Chart.js + react-chartjs-2 |
| HTTP Client | Axios |
| Routing | React Router DOM |
