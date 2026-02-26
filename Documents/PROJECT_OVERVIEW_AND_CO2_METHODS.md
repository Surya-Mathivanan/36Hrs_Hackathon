# Campus Carbon Footprint Analyzer – Project Overview & CO₂ Methodology

## 1. Project Purpose

The **Campus Carbon Footprint Analyzer** is a full‑stack web application built for **KIT – Kalaignar Karunanidhi Institute of Technology** to:

- **Measure**: Track day‑to‑day and long‑term carbon emissions from all major campus activities.
- **Analyze**: Break down emissions by source (electricity, transport, canteen, waste, human population) and by time (daily, weekly, monthly, yearly).
- **Act**: Provide data‑driven **recommendations** so the campus can systematically reduce its carbon footprint.

It directly supports **UN Sustainable Development Goal 13 – Climate Action** by turning raw consumption data (kWh, litres, kg, headcount) into clear, visual insights and practical action plans.

---

## 2. Why This Project? (Motivation)

Most campuses face the same challenges:

1. **No central view of emissions**
   - Energy bills, fuel usage, canteen gas, and waste data are scattered across departments.
   - No single dashboard shows the *total* climate impact of the campus.

2. **Decisions based on guesswork**
   - Without numbers, initiatives like "install solar" or "replace lights" are hard to justify.
   - Management cannot easily see which area (electricity, buses, canteen, waste) is the biggest problem.

3. **No way to measure progress**
   - Even if some actions are taken, it is hard to prove:
     - "Did emissions actually go down this semester?"
     - "Which project gave the maximum reduction?"

4. **Hackathon core requirement: Human CO₂**
   - Typical tools only track **indirect emissions** (electricity, fuel, waste).
   - This project also includes a **core feature**: *Human CO₂ Emissions* based on campus population (students + staff), treated in a scientifically correct way.

**This project solves these problems** by providing:

- A **single dashboard** for all campus emission sources.
- Clear **KPIs** and charts, updated from real data.
- A dedicated **human emissions module** to link population data with overall footprint.
- An intelligent **recommendation engine** that converts data into action.

---

## 3. High‑Level System Design

The application is a classic **three‑layer** system:

1. **Frontend (User Interface)**
   - Templates: `templates/dashboard.html`, `templates/data_input.html`, `templates/login.html`, `templates/base.html`.
   - JavaScript:
     - `static/js/dashboard.js` – loads dashboard data, builds charts, shows KPIs and recommendations.
     - `static/js/data_input.js` – handles data entry forms and CSV uploads.
   - CSS:
     - `static/css/style.css` – dark mode + light mode, layout and cards.
     - `static/css/holo-toggle.css` – animated theme toggle switch.

2. **Backend (Flask API)** – `app.py`
   - Web pages: `/`, `/login`, `/data-input`.
   - Public APIs:
     - `/api/dashboard` – main dashboard data.
     - `/api/recommendations` – detailed recommendations.
   - Protected APIs (require login / token):
     - `/api/data` – activity data (electricity, transport, canteen, waste).
     - `/api/human_data` – human population data.
     - `/api/human_cumulative_stats` – all‑time human CO₂ statistics.
     - `/api/upload_csv` – bulk CSV upload.

3. **Database (MySQL)**
   - Tables:
     - `users` – admin accounts.
     - `emission_factors` – CO₂ per unit for each source.
     - `activity_data` – daily activity values (kWh, litres, kg).
     - `human_population` – daily students, staff, total population.
   - Initialization: `database/schema.sql`, `database/human_population_schema.sql`, `database/init_db.py`.

---

## 4. What Is New / Special in This Project?

This project goes beyond a basic CRUD dashboard. Key innovations:

### 4.1 Human CO₂ Emissions – Core Hackathon Feature

- Dedicated `human_population` table to track **students + staff per day**.
- Scientific approximation: **1 kg CO₂ per person per day** from respiration.
- Calculates both **daily** and **cumulative** human CO₂ in tonnes.
- Displays:
  - Average students, staff, and total population.
  - Total human emissions over the selected period.
  - Detailed daily/weekly/monthly graphs in the dashboard API.
- Treats respiration correctly as part of the **short‑term carbon cycle**, and uses it mainly to understand **per‑person footprint**, not as something to reduce directly.

### 4.2 Unified Multi‑Source Emission Tracking

The system combines several emission sources under the same formula and dashboard:

- **Electricity** usage (kWh → kg CO₂e → tonnes).
- **Bus Diesel** (litres → kg CO₂e → tonnes).
- **Canteen LPG** (kg → kg CO₂e → tonnes).
- **Waste to landfill** (kg → kg CO₂e → tonnes).
- **Human population** (people → kg CO₂ → tonnes).

All of these are visible in one place with consistent units (**tonnes CO₂e**).

### 4.3 Smart Dashboard Analytics

The `/api/dashboard` endpoint computes:

- **Total emissions** for the selected date range.
- **Percent change** vs. the previous period with the same length.
- **Biggest emission source** and its percentage share.
- **Energy consumed** (total kWh) for electricity.
- Time‑series aggregations:
  - Daily trend.
  - Weekly comparison.
  - Monthly and yearly comparisons.
- Combined human emissions data:
  - Daily/weekly/monthly trends.
  - Average population.
  - Population + emissions table.

### 4.4 Enhanced Recommendations Engine

The recommendations API (`/api/recommendations`) reads real emission data and returns:

- **Dynamic source‑specific recommendations** for the biggest source (electricity, transport, canteen, waste).
- Always‑included categories:
  - Human emissions context.
  - Data‑driven decision making.
  - Green campus initiatives.
  - Infrastructure upgrades.
  - Quick wins.
- Each recommendation includes:
  - Title, description, priority, impact.
  - 5–10 **actionable steps**.
  - Expected reduction range.
  - Cost level.
  - Timeframe.

The frontend renders these as **expandable cards** with color‑coded priority badges.

### 4.5 Robust Data Entry & Validation

- **Admin data form** with clear source types and automatic units.
- **CSV upload** with strict date validation (rejects invalid formats like `2IS-08-16`).
- Clear error messages for invalid inputs (dates, counts, missing fields).
- All database access uses **parameterized queries** to prevent SQL injection.

---

## 5. CO₂ Calculation Methodology

This section explains **exactly** how the project converts raw data into CO₂ emissions.

There are two main paths:

1. **Activity‑based emissions** (electricity, fuel, gas, waste) – using standard emission factors.
2. **Human respiration emissions** – using a simplified factor per person per day.

### 5.1 Emission Factors & Activity Data

#### 5.1.1 Emission Factors Table

The MySQL table `emission_factors` stores the conversion factors used to turn raw activity data into CO₂ equivalent (CO₂e):

- `source_type` – e.g. `electricity`, `bus_diesel`, `canteen_lpg`, `waste_landfill`.
- `factor` – numeric value, e.g. `0.708`.
- `factor_unit` – description, e.g. `kg CO₂e/kWh`.

Example (from `README.md`):

| Source Type        | Factor | Unit              |
|--------------------|--------|-------------------|
| electricity        | 0.708  | kg CO₂e / kWh     |
| bus_diesel         | 2.68   | kg CO₂e / litre   |
| canteen_lpg        | 2.93   | kg CO₂e / kg      |
| waste_landfill     | 1.25   | kg CO₂e / kg      |

These factors are based on standard emission inventories and can be adjusted per country or grid.

#### 5.1.2 Activity Data Table

The `activity_data` table stores daily raw values:

- `date` – e.g. `2025-11-14`.
- `source_type` – matches a row in `emission_factors`.
- `raw_value` – numeric consumption (e.g. `1500` kWh, `50` litres).
- `unit` – for reference (kWh, litres, kg).

#### 5.1.3 Core Formula – Activity Emissions

For each activity record, the backend (`/api/dashboard`) computes:

> **Emissions (tonnes CO₂e) = raw_value × emission_factor / 1000**

Where:

- `raw_value` is in kWh / litres / kg.
- `emission_factor` is in kg CO₂e per unit.
- Division by `1000` converts **kg** to **tonnes**.

This is visible in `app.py`:

```python
(a.raw_value * e.factor / 1000) as emissions_tonnes
```

##### Example 1 – Electricity

- Raw electricity use: **1,000 kWh**.
- Factor: **0.708 kg CO₂e/kWh**.

Calculation:

- Emissions (kg) = 1,000 × 0.708 = **708 kg CO₂e**.
- Emissions (tonnes) = 708 / 1000 = **0.708 tonnes CO₂e**.

##### Example 2 – Bus Diesel

- Diesel usage: **200 litres**.
- Factor: **2.68 kg CO₂e/litre**.

Calculation:

- Emissions (kg) = 200 × 2.68 = **536 kg CO₂e**.
- Emissions (tonnes) = 536 / 1000 = **0.536 tonnes CO₂e**.

##### Example 3 – Canteen LPG

- LPG consumption: **50 kg**.
- Factor: **2.93 kg CO₂e/kg**.

Calculation:

- Emissions (kg) = 50 × 2.93 = **146.5 kg CO₂e**.
- Emissions (tonnes) = 146.5 / 1000 ≈ **0.147 tonnes CO₂e**.

##### Example 4 – Waste to Landfill

- Solid waste to landfill: **100 kg**.
- Factor: **1.25 kg CO₂e/kg**.

Calculation:

- Emissions (kg) = 100 × 1.25 = **125 kg CO₂e**.
- Emissions (tonnes) = 125 / 1000 = **0.125 tonnes CO₂e**.

All these source‑level emissions are then **summed** to get total emissions for the selected date range.

### 5.2 Human CO₂ Emissions (Core Feature)

Human respiration is modeled with a simplified but reasonable assumption:

> **Each person emits ~1.0 kg CO₂ per day through breathing.**

The `human_population` table stores:

- `date` – day of measurement.
- `student_count` – number of students on campus.
- `staff_count` – number of staff on campus.
- `total_count` – total people on campus (auto‑computed in DB).

#### 5.2.1 Daily Human CO₂ Calculation

For a given day:

- Total people = `student_count + staff_count`.
- Emit factor = 1.0 kg CO₂/person/day.

Formula in `app.py` (`/api/human_data`):

```python
total_people = student_count + staff_count
emissions_kg = total_people * 1.0  # kg CO2 per person per day
emissions_tonnes = emissions_kg / 1000
```

So:

> **Human emissions (tonnes) = (students + staff) × 1.0 / 1000**

##### Example – Human CO₂ for One Day

- Students: **2,300**
- Staff: **0** (for simplicity)

Total people = 2,300.

- Emissions (kg) = 2,300 × 1.0 = **2,300 kg CO₂**.
- Emissions (tonnes) = 2,300 / 1000 = **2.30 tonnes CO₂**.

This value is returned under `this_day_emissions_tonnes` and also included in the dashboard’s human emissions section.

#### 5.2.2 Cumulative Human CO₂

To get **all‑time human emissions**, the backend uses SQL:

```sql
SELECT
    SUM(total_count * 1.0 / 1000) as total_emissions,
    COUNT(*) as record_count,
    AVG(student_count) as avg_students,
    AVG(staff_count) as avg_staff
FROM human_population;
```

From this, the API returns:

- `total_emissions_tonnes` – sum of all daily human emissions.
- `total_records` – how many days of data are recorded.
- `average_students`, `average_staff`, `average_population`.

These power the **Cumulative Statistics (All Time)** cards in `dashboard.html`.

### 5.3 Aggregation & Dashboard Metrics

Once emissions per record are known, the dashboard performs several aggregations:

1. **Total Emissions**
   - Sum of all `emissions_tonnes` from `activity_data` in the selected date range.

2. **Biggest Source**
   - Sum `emissions_tonnes` grouped by `source_type`.
   - The source with the highest total is the **biggest source**.

3. **Percent Change vs Previous Period**

- Let:
  - `current_total` = total emissions between `start_date` and `end_date`.
  - `prev_total` = emissions in the **previous window** of the same length.

Then:

> **Percent change = (current_total − prev_total) / prev_total × 100** (if `prev_total > 0`).

4. **Energy Consumed (kWh)**
   - For all records where `source_type = 'electricity'`, sum `raw_value` to get total kWh consumed.

5. **Time Series**
   - Dates are converted to daily, weekly (`year-week`), monthly (`YYYY-MM`), and yearly (`YYYY`) buckets.
   - Emissions are summed into each bucket for trend charts.

6. **Human Emissions Analytics**
   - Same aggregation logic applied to human emissions (`human_daily_data`, `human_weekly_data`, etc.).
   - Additionally, averages of student and staff counts are computed over the selected range.

### 5.4 End‑to‑End Example Day

For a single day, the system might receive:

- Electricity: 1,000 kWh.
- Bus diesel: 200 litres.
- Canteen LPG: 50 kg.
- Waste to landfill: 100 kg.
- Students: 2,300; Staff: 200.

**Step 1 – Convert all to tonnes CO₂e**

- Electricity: 1,000 × 0.708 / 1000 = 0.708 t.
- Diesel: 200 × 2.68 / 1000 = 0.536 t.
- LPG: 50 × 2.93 / 1000 ≈ 0.147 t.
- Waste: 100 × 1.25 / 1000 = 0.125 t.
- Human: (2,300 + 200) × 1.0 / 1000 = 2.5 t.

**Step 2 – Summarize**

- Total activity emissions = 0.708 + 0.536 + 0.147 + 0.125 ≈ **1.516 tonnes CO₂e**.
- Human emissions = **2.50 tonnes CO₂**.
- Combined **absolute** impact for the day ≈ **4.016 tonnes CO₂e** (if you wish to show it).

The dashboard then uses these numbers in KPIs, charts, and recommendations.

---

## 6. Data Entry & Workflows

### 6.1 Admin Activity Data Entry

1. Admin logs in via `/login` (e.g. `admin` / `admin123`).
2. Navigates to `/data-input`.
3. Selects:
   - Date.
   - Source type (electricity, bus_diesel, canteen_lpg, waste_landfill).
   - Raw value.
   - Unit (auto‑suggested based on source type).
4. Submits form → backend writes to `activity_data`.
5. Dashboard refreshes and shows updated charts.

### 6.2 Human Population Data Entry

1. Admin goes to Human CO₂ section in the data input page.
2. Enters:
   - Date.
   - Student count.
   - Staff count.
3. Backend:
   - Validates non‑negative integers.
   - Inserts or updates record in `human_population`.
   - Computes daily emissions and cumulative stats.
4. Frontend shows confirmation with:
   - This day’s population and emissions.
   - Cumulative totals (emissions, records, averages).
5. Dashboard’s **Human CO₂** section uses this data for KPIs and charts.

### 6.3 CSV Upload Workflow

- Admin can upload CSVs containing multiple `activity_data` rows.
- Backend:
  - Parses each row.
  - Validates date format (`YYYY-MM-DD`) using `datetime.strptime` – invalid rows like `2IS-08-16` are rejected with row‑specific error messages.
  - Valid records are inserted into `activity_data`.

This allows **bulk import** of historical meter readings.

---

## 7. Recommendations Engine (How It Uses the Data)

The recommendations API:

1. Reads total emissions per source from `activity_data` + `emission_factors`.
2. Reads total and average population from `human_population`.
3. Identifies the **top emission source**.
4. Builds a list of recommendation objects, including:
   - Source‑specific strategies for the top source.
   - Campus‑wide strategies (data, culture, infrastructure, quick wins).

Each recommendation includes:

- **Title & description** – explains the problem and context.
- **Priority** – High / Medium / Low.
- **Impact** – how much it can reduce emissions.
- **Actionable steps** – concrete actions your campus can implement.
- **Expected reduction** – estimated percentage.
- **Cost & timeframe** – to help plan and justify investments.

The dashboard displays these in an interactive section:

- Summary banner: total recommendations, high priority count, potential reduction.
- Cards: click to expand and see full details.

This turns the dashboard from a **monitoring tool** into a **decision‑support system**.

---

## 8. How This Project Supports KIT & SDG 13

1. **Quantifies the campus footprint** in a transparent way.
2. **Engages students and staff** through a visual dashboard and human CO₂ feature.
3. **Supports admin decisions** with hard numbers and clear recommendations.
4. **Enables reporting** to management, accreditation bodies, and sustainability rankings.
5. Provides a foundation for future **AI/ML forecasting**, **OCR bill scanning**, and **automated data pipelines**.

By combining **technical accuracy** (correct CO₂ calculations) with a **user‑friendly interface** and a **human‑focused core feature**, this project is a strong, complete solution for monitoring and reducing campus carbon emissions.

---

## 9. Future Enhancements

Some planned or possible next steps:

- Predictive analytics (e.g., SARIMA/ML models) to forecast future emissions.
- Automated ingestion from smart meters and IoT sensors.
- Department‑wise or building‑wise breakdowns.
- Public leaderboard for departments/hostels with the lowest per‑person emissions.
- Exportable reports (PDF/Excel) for audits and accreditation.

---

**Summary:**

The **Campus Carbon Footprint Analyzer** is a complete solution that not only tracks electricity, transport, canteen, and waste emissions using standard factors, but also adds a scientifically grounded **Human CO₂ Emissions** core feature. It offers a clear methodology for **how CO₂ is calculated**, **multiple ways of aggregating and analyzing data**, and an advanced **recommendation engine** to convert data into real climate action on campus.