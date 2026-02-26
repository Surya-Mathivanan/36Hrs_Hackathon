# Campus Carbon Footprint Analyzer – Full API Working Details

This document describes **all major APIs** in the project, how they work, what they return, and how they are used in the application. All endpoints listed here have been wired into the UI and/or tested via scripts and browser, and are currently **working as expected** for the hackathon use case.

---

## 1. Authentication & Access Model

There are two authentication mechanisms in this project:

1. **Session-based login (browser)**
2. **Token-based API access (JWT)**

### 1.1 Session-Based Login (Browser)

- **Endpoint:** `POST /login`
- **Used by:** `login.html` form
- **Flow:**
  1. User submits username and password.
  2. Backend looks up user in `users` table.
  3. If password matches (plain or hashed), Flask session is created:
     - `session['user_id']` = user ID
     - `session['username']` = username
  4. User is redirected to `/data-input`.

**Protection decorator:**

```python
@login_required
```

- Applied to: `/data-input` route.
- If `user_id` is not in session, user is redirected back to `/login`.

### 1.2 API Token (JWT) – For Programmatic Clients

- **Endpoint:** `POST /api/login`
- **Purpose:** Issue JWT token for API calls.
- **Request (JSON):**

```json
{
  "username": "admin",
  "password": "admin123"
}
```

- **Response (on success):**

```json
{
  "token": "<jwt_token_string>",
  "username": "admin"
}
```

The token is signed with `SESSION_SECRET` and is valid for **24 hours**.

**Usage:**

Include the token in the `Authorization` header:

```http
Authorization: Bearer <jwt_token_string>
```

**Protection decorator:**

```python
@api_token_required
```

- Accepts **either**:
  - Valid session (user logged in via browser), OR
  - Valid JWT token in `Authorization: Bearer ...` header.
- Applied to: `/api/data`, `/api/human_data`, `/api/upload_csv`.

---

## 2. Web Page Routes

### 2.1 `GET /` – Dashboard Page

- **Handler:** `index()`
- **Auth:** Public (no login required).
- **Returns:** `templates/dashboard.html`
- **Usage:**
  - Main landing page for all users (students, staff, guests).
  - JavaScript (`dashboard.js`) calls `/api/dashboard` and `/api/recommendations` to populate data.

### 2.2 `GET /login` – Login Page

- **Handler:** `login()` (GET branch)
- **Auth:** Public.
- **Returns:** `templates/login.html`
- **Usage:**
  - Admins open this page to log in and access data input features.

### 2.3 `POST /login` – Perform Login

- **Handler:** `login()` (POST branch)
- **Auth:** Public (but sets session on success).
- **Request:** Form-encoded
  - `username`
  - `password`
- **Logic:**
  1. Look up user in `users` table with `SELECT * FROM users WHERE username = %s`.
  2. Compare password:
     - Supports **plain text** (`user['password'] == password`).
     - Supports **SHA-256 hash** (for users like `surya`):

       ```python
       import hashlib
       hashed_password = hashlib.sha256(password.encode()).hexdigest()
       if user['password'] == password or user['password'] == hashed_password:
           # success
       ```
  3. On success:
     - Set `session['user_id']` and `session['username']`.
     - Redirect to `/data-input`.
  4. On failure:
     - Re-render `login.html` with error message `"Invalid credentials"`.

- **Status:** Working; tested with `admin/admin123` and `surya/surya123`.

### 2.4 `GET /data-input` – Admin Data Input Page

- **Handler:** `data_input()`
- **Auth:** Protected by `@login_required`.
- **Returns:** `templates/data_input.html`
- **Usage:**
  - Admin form for activity data (electricity, diesel, LPG, waste).
  - Admin form for human population (students, staff).
  - CSV upload section.

If not logged in, user is redirected to `/login`.

### 2.5 `GET /logout` – Logout

- **Handler:** `logout()`
- **Auth:** Session-based.
- **Effect:**
  - Clears session via `session.clear()`.
  - Redirects to `/` (dashboard).

---

## 3. Core Data APIs

These APIs power the dashboard and data entry features.

### 3.1 `POST /api/login` – API Token Login

- **Auth:** Public (but returns token on success).
- **Purpose:** Generate JWT token for programmatic access.
- **Request (JSON):**

```json
{
  "username": "admin",
  "password": "admin123"
}
```

- **Success Response (200):**

```json
{
  "token": "<jwt_token>",
  "username": "admin"
}
```

- **Error Responses:**
  - `400` if username/password missing.
  - `500` on DB error.
  - `401` if credentials invalid.

- **Status:** Working; token generation tested and used by protected APIs when needed.

---

### 3.2 `POST /api/data` – Add Activity Data

- **Decorator:** `@api_token_required`
- **Auth:** Requires:
  - Logged-in session **or**
  - Valid JWT token.

- **Purpose:** Insert a single record into `activity_data` (electricity, diesel, LPG, waste).

- **Request (JSON):**

```json
{
  "date": "2025-11-14",
  "source_type": "electricity",
  "raw_value": 1500,
  "unit": "kWh"
}
```

- **Validation:**
  - All fields must be present.
  - If any are missing → `400 {"error": "Missing required fields"}`.

- **DB Operation:**

```sql
INSERT INTO activity_data (date, source_type, raw_value, unit)
VALUES (%s, %s, %s, %s);
```

- **Success Response (201):**

```json
{"message": "Data added successfully"}
```

- **Error Response (500):**

```json
{"error": "Failed to insert data"}
```

- **Status:** Working; used via admin UI and compatible with token-based clients.

---

### 3.3 `POST /api/human_data` – Add Human Population Data (CORE FEATURE)

- **Decorator:** `@api_token_required`
- **Auth:** Requires session or JWT.
- **Purpose:** Store daily population (students + staff) and compute both daily and cumulative human CO₂.

- **Request (JSON):**

```json
{
  "date": "2025-11-14",
  "student_count": 3000,
  "staff_count": 400
}
```

- **Validation:**
  - `date`, `student_count`, `staff_count` must be present.
  - Counts must be integers and **non-negative**.

- **DB Operation:**

```sql
INSERT INTO human_population (date, student_count, staff_count)
VALUES (%s, %s, %s)
ON DUPLICATE KEY UPDATE
    student_count = VALUES(student_count),
    staff_count = VALUES(staff_count);
```

- **CO₂ Calculation:**

```python
total_people = student_count + staff_count
emissions_kg = total_people * 1.0  # kg CO2 per person per day
emissions_tonnes = emissions_kg / 1000
```

- **Cumulative Stats Query:**

```sql
SELECT
    SUM(total_count * 1.0 / 1000) as total_emissions,
    COUNT(*) as record_count,
    AVG(student_count) as avg_students,
    AVG(staff_count) as avg_staff
FROM human_population;
```

- **Success Response (201):**

```json
{
  "message": "Human population data added successfully",
  "data": {
    "date": "2025-11-14",
    "student_count": 3000,
    "staff_count": 400,
    "total_count": 3400,
    "this_day_emissions_tonnes": 3.4
  },
  "cumulative_stats": {
    "total_emissions_tonnes": 12.5,
    "total_records": 5,
    "average_students": 2800,
    "average_staff": 350,
    "average_population": 3150
  }
}
```

- **Error Responses:**
  - `400` for missing fields or invalid counts.
  - `500` on DB error.

- **Status:**
  - Verified via `test_api_response.py` (sends sample data, checks structure and cumulative stats).
  - Integrated into UI: success message on data input page and Human CO₂ cards on dashboard.

---

### 3.4 `GET /api/dashboard` – Main Dashboard Data (Public)

- **Auth:** Public (no login required).
- **Purpose:** Provide all data required by `dashboard.js` to render:
  - KPI cards
  - Trend charts
  - Source breakdown
  - Human CO₂ analytics

- **Query Parameters (optional):**
  - `start_date=YYYY-MM-DD`
  - `end_date=YYYY-MM-DD`

If not provided, defaults to the last **180 days**.

- **Processing Steps:**
  1. Normalize `start_date` and `end_date`.
  2. Query `activity_data` joined with `emission_factors` to compute `emissions_tonnes`.
  3. Aggregate into daily, weekly, monthly, yearly buckets.
  4. Compute total emissions, percent change vs previous period, biggest source and its share.
  5. Compute electricity energy consumed (sum of `raw_value` where `source_type = 'electricity'`).
  6. Query `human_population` and compute:
     - Human total emissions.
     - Average student/staff/total counts.
     - Human daily/weekly/monthly trends.

- **Response Shape (simplified):**

```json
{
  "kpis": {
    "total_emissions": 12.34,
    "percent_change": 5.6,
    "biggest_source": "electricity",
    "biggest_source_percent": 45.3,
    "energy_saved": 12345
  },
  "daily_trend": [ {"date": "2025-11-10", "emissions": 0.85}, ... ],
  "weekly_trend": [ {"label": "2025-W45", "emissions": 3.2}, ... ],
  "monthly_trend": [ {"month": "2025-11", "emissions": 10.5}, ... ],
  "source_breakdown": [
    {"source": "electricity", "emissions": 5.23, "percentage": 45.3},
    {"source": "bus_diesel", "emissions": 3.10, "percentage": 26.9}
  ],
  "weekly_comparison": [ ... ],
  "yearly_comparison": [ ... ],
  "human_emissions": {
    "total_emissions": 3.3,
    "avg_student_count": 2200,
    "avg_staff_count": 100,
    "avg_total_count": 2300,
    "daily_trend": [ ... ],
    "weekly_trend": [ ... ],
    "monthly_trend": [ ... ],
    "population_data": [
      {
        "date": "2025-11-14",
        "students": 3000,
        "staff": 400,
        "total": 3400,
        "emissions": 3.4
      }
    ]
  }
}
```

- **Status:**
  - Working; used by `static/js/dashboard.js` to render all dashboard elements.
  - Used with both default and custom date ranges.

---

### 3.5 `GET /api/recommendations` – Enhanced Recommendations

- **Auth:** Public.
- **Purpose:** Provide **actionable strategies** to reduce emissions, based on real data.

- **Backend Logic:**
  1. Query `activity_data` + `emission_factors` to get total emissions per `source_type`.
  2. Query `human_population` for human CO₂ stats.
  3. Identify **top emission source**.
  4. Build a list of recommendations (9+ total) including:
     - Top source category (electricity / bus_diesel / canteen_lpg / waste_landfill).
     - Human emissions context.
     - Data-driven, green campus, infrastructure, quick wins.

- **Response (simplified):**

```json
{
  "recommendations": [
    {
      "title": "⚡ Electricity: Your #1 Emission Source",
      "description": "...",
      "priority": "High",
      "impact": "High",
      "actionable_steps": ["...", "..."],
      "expected_reduction": "30-50% reduction in electricity-based emissions",
      "cost": "Medium to High (Initial) | High ROI (2-5 years)",
      "timeframe": "6-18 months for full implementation"
    },
    {
      "title": "⭐ Quick Wins: Immediate Actions",
      "priority": "High",
      "impact": "Medium",
      "actionable_steps": ["TODAY: ...", "THIS WEEK: ..."]
    },
    { "title": "👥 Human CO₂: An Indirect Factor", ... }
  ],
  "summary": {
    "total_recommendations": 9,
    "high_priority": 4,
    "estimated_total_reduction": "50-70% achievable with full implementation",
    "message": "Start with \"Quick Wins\" and \"High Priority\" items for maximum immediate impact!"
  }
}
```

- **Status:**
  - Working; integrated into dashboard recommendations section.
  - Verified logically and syntactically (`py_compile` and manual tests).

---

### 3.6 `GET /api/human_cumulative_stats` – Human CO₂ All-Time Stats

- **Auth:** Public (used by dashboard without login).
- **Purpose:** Provide **all‑time** statistics for human population emissions.

- **DB Query:**

```sql
SELECT
    SUM(total_count * 1.0 / 1000) as total_emissions,
    COUNT(*) as record_count,
    AVG(student_count) as avg_students,
    AVG(staff_count) as avg_staff
FROM human_population;
```

- **Response (JSON):**

```json
{
  "total_emissions": 3.30,
  "total_records": 3,
  "average_students": 2100,
  "average_staff": 50,
  "average_population": 2150
}
```

- **Usage:**
  - `dashboard.js` uses this to fill the **Cumulative Statistics (All Time)** cards under the Human CO₂ section.

- **Status:** Working; errors handled with `500 {"error": "Internal error"}` if DB fails.

---

### 3.7 `POST /api/upload_csv` – Bulk CSV Upload

- **Decorator:** `@api_token_required`
- **Auth:** Requires session or JWT.
- **Purpose:** Insert multiple activity records in one call (used by CSV import in admin UI).

- **Expected Payload (JSON):**

```json
{
  "records": [
    {
      "date": "2025-11-10",
      "source_type": "electricity",
      "raw_value": 1200,
      "unit": "kWh"
    },
    {
      "date": "2025-11-10",
      "source_type": "bus_diesel",
      "raw_value": 50,
      "unit": "L"
    }
  ]
}
```

- **Validation:** For each row:
  - Must be an object with keys `date`, `source_type`, `raw_value`, `unit`.
  - `date` must be in `YYYY-MM-DD` format (strict check using `datetime.strptime`).
  - `raw_value` must be numeric (convertible to `float`).

- **Error Handling:**
  - If `records` is missing/empty or not a list → `400 {"error": "Invalid CSV format."}`.
  - If any row is invalid → `400` with a precise message, e.g.:

    ```json
    {"error": "Invalid date format at row 9: \"2IS-08-16\" (expected YYYY-MM-DD)"}
    ```

  - On DB failure → `500 {"error": "Failed to insert CSV data."}`.

- **DB Operation:**

```sql
INSERT INTO activity_data (date, source_type, raw_value, unit)
VALUES (%s, %s, %s, %s)
```
(using `executemany` for efficiency)

- **Success Response (201):**

```json
{"success": true, "message": "N records inserted."}
```

- **Status:** Working; tested with valid and invalid CSV data through the UI and logs (e.g., date validation errors).

---

## 4. Debug / Utility Endpoints

### 4.1 `POST /debug/reset_admin` – Reset Admin Password (Development Only)

- **Auth:** Only active when `FLASK_DEBUG` is truthy.
- **Purpose:** Quickly reset or create the `admin` user with password `admin123` during development.

- **Logic:**
  1. Tries to `UPDATE users SET password = 'admin123' WHERE username = 'admin'`.
  2. If no rows updated, `INSERT INTO users (username, password) VALUES ('admin', 'admin123')`.
  3. Commits transaction.

- **Response:**
  - `200 {"message": "Admin password reset to admin123"}` on success.
  - `404 {"error": "Not found"}` if `DEBUG_MODE` is false.
  - `500 {"error": "Database connection error"}` / `{"error": "Internal error"}` on failure.

- **Status:** Available for development; **should not be exposed in production**.

---

## 5. Summary of API Status

All key APIs in `app.py` are **implemented, integrated, and working** for the hackathon demo:

| Endpoint                       | Method | Auth           | Purpose                                           | Status   |
|--------------------------------|--------|----------------|---------------------------------------------------|----------|
| `/`                            | GET    | Public         | Render main dashboard                             | Working  |
| `/login`                       | GET    | Public         | Render login page                                 | Working  |
| `/login`                       | POST   | Public         | Perform login, create session                     | Working  |
| `/logout`                      | GET    | Session        | Clear session, redirect to `/`                    | Working  |
| `/data-input`                  | GET    | Session        | Admin data input page                             | Working  |
| `/api/login`                   | POST   | Public         | Issue JWT token                                   | Working  |
| `/api/data`                    | POST   | Session/JWT    | Add activity record                               | Working  |
| `/api/human_data`              | POST   | Session/JWT    | Add human population + return cumulative stats    | Working  |
| `/api/dashboard`               | GET    | Public         | Full dashboard data (all sources + human)         | Working  |
| `/api/recommendations`         | GET    | Public         | Smart recommendations based on emission data      | Working  |
| `/api/human_cumulative_stats`  | GET    | Public         | All‑time human CO₂ stats                          | Working  |
| `/api/upload_csv`              | POST   | Session/JWT    | Bulk insert activity data from CSV                | Working  |
| `/debug/reset_admin`           | POST   | Debug only     | Reset/create admin user                           | Working* |

`Working*` = intended for development/debugging, not for production use.

---

### 6. How Frontend Uses These APIs

- `dashboard.html` + `dashboard.js`:
  - Calls `/api/dashboard` to get all KPIs and charts.
  - Calls `/api/human_cumulative_stats` for cumulative human stats cards.
  - Calls `/api/recommendations` to render recommendation cards.

- `data_input.html` + `data_input.js`:
  - Submits activity data through `/api/data` (with token/session).
  - Submits human population data through `/api/human_data`.
  - Uploads CSV via `/api/upload_csv` with detailed error handling.

- `login.html`:
  - Uses `/login` for browser sessions.
  - Optionally, `/api/login` can be used for external clients.

All of these flows have been exercised during development, and log output shows correct behavior (status codes, data shapes, and calculations) across the full pipeline.