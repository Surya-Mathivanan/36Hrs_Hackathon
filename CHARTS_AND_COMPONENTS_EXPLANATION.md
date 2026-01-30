# Dashboard Charts & UI Components – Explanation

This document explains **every chart and key UI component** in the Campus Carbon Footprint Analyzer: what it shows, how it is calculated, which API powers it, and how the data flows from the backend to the Chart.js visualizations.

Files involved:
- Frontend: `templates/dashboard.html`, `static/js/dashboard.js`, `static/css/style.css`
- Backend API: `/api/dashboard`, `/api/recommendations`, `/api/human_cumulative_stats`

---

## 1. KPI Cards (Top Summary Tiles)

Located at the top of `dashboard.html`:

- **Total Emissions** (`#totalEmissions`)
- **Change vs Previous Period** (`#percentChange`)
- **Biggest Source** (`#biggestSource`, `#biggestSourcePercent`)
- **Total Energy** (`#energySaved`)

### 1.1 Data Source

- API: `GET /api/dashboard`
- Returned JSON section:

```json
{
  "kpis": {
    "total_emissions": 12.34,
    "percent_change": 5.6,
    "biggest_source": "electricity",
    "biggest_source_percent": 45.3,
    "energy_saved": 12345
  },
  ...
}
```

### 1.2 Calculations (Backend)

From `app.py` → `get_dashboard_data()`:

1. **Total Emissions (Tonnes CO₂e)**
   - For each `activity_data` record:
     - `emissions_tonnes = raw_value * factor / 1000` (factor from `emission_factors`).
   - `total_emissions = sum(emissions_tonnes)` over the selected date range.

2. **Percent Change vs Previous Period**
   - Current window: `[start_date, end_date]` (selected from the dashboard dropdown).
   - Previous window: same number of days **immediately before** `start_date`.
   - `percent_change = (current_total - prev_total) / prev_total * 100` (if `prev_total > 0`).

3. **Biggest Source & Percentage**
   - Emissions grouped by `source_type`.
   - `biggest_source` = source with maximum total emissions.
   - `biggest_source_percent = biggest_source_emissions / total_emissions * 100`.

4. **Total Energy (kWh Consumed)**
   - Sum of `raw_value` where `source_type = 'electricity'` (no factor applied; pure consumption).

### 1.3 Rendering (Frontend)

`updateDashboard()` calls `updateKPIs(kpis)` in `dashboard.js`:

- Formats numbers with `toFixed` and `toLocaleString`.
- Adds arrow for change:
  - `↑` red if emissions increased.
  - `↓` green if emissions decreased.
- Converts `biggest_source` from `"bus_diesel"` to readable text (first letter capital + space).

These tiles give a **high-level summary** of emissions for the selected time period.

---

## 2. Total Emissions Trend Chart

Element:
- `<canvas id="trendChart"></canvas>` inside **"Total Emissions Trend"** card.

### 2.1 Chart Type

- Library: **Chart.js**
- Type: `line`
- Function: `updateTrendChart(trendData, labelKey, days)`

### 2.2 Data Source

- API: `GET /api/dashboard`
- The function chooses which field to use based on selected time range (`days`):
  - `days ≤ 7`: `data.daily_trend` with label key `"date"`.
  - `7 < days ≤ 90`: `data.weekly_trend` with label key `"label"`.
  - `days > 90`: `data.monthly_trend` with label key `"month"`.

Example structure:

```json
"daily_trend": [
  {"date": "2025-11-10", "emissions": 0.85},
  {"date": "2025-11-11", "emissions": 1.05}
],
"weekly_trend": [
  {"label": "2025-W45", "emissions": 3.20}
],
"monthly_trend": [
  {"month": "2025-11", "emissions": 10.50}
]
```

### 2.3 Calculations (Backend)

From `get_dashboard_data()`:

- Daily:
  - Group by calendar date.
  - `daily_data[date] += emissions_tonnes`.
- Weekly:
  - ISO week label: `"YYYY-Www"` (e.g., `"2025-W45"`).
  - `weekly_data[label] += emissions_tonnes`.
- Monthly:
  - Month key: `"YYYY-MM"`.
  - `monthly_data[month] += emissions_tonnes`.

These aggregates are then sorted and returned as arrays.

### 2.4 Label Formatting (Frontend)

Inside `updateTrendChart`:

- For `labelKey === 'date'`:
  - Convert to `Date`, show as `"Nov 10"` (month + day).
- For `labelKey === 'label'` (weeks):
  - `"2025-W45"` → `"Week 45"`.
- For `labelKey === 'month'`:
  - `"2025-11"` → `"Nov 2025"`.

This chart allows the viewer to see **how total emissions change over time** with the appropriate granularity.

---

## 3. Monthly, Yearly, and Weekly Comparison Bar Charts

Three bar charts show comparisons across different time scales.

### 3.1 Monthly Comparison

- Element: `<canvas id="monthlyBarChart"></canvas>`
- Function: `updateMonthlyBarChart(monthlyData)`
- Chart type: `bar`

**Data:**
- From `GET /api/dashboard` → `monthly_trend` array.
- X-axis: month labels (e.g., `"2025-11"`).
- Y-axis: monthly emissions (tonnes CO₂e).

**Purpose:**
- Compare emissions month by month (over full available data).

---

### 3.2 Yearly Comparison

- Element: `<canvas id="yearlyBarChart"></canvas>`
- Function: `updateYearlyBarChart(yearlyData)`
- Chart type: `bar`

**Data:**
- From `GET /api/dashboard` → `yearly_comparison` array.

Example:

```json
"yearly_comparison": [
  {"year": 2024, "emissions": 120.5},
  {"year": 2025, "emissions": 98.3}
]
```

**Purpose:**
- Show long-term progress year over year.

---

### 3.3 Weekly Comparison

- Element: `<canvas id="weeklyBarChart"></canvas>`
- Function: `updateWeeklyBarChart(weeklyData)`
- Chart type: `bar`

**Data:**
- From `GET /api/dashboard` → `weekly_comparison` array.

Example:

```json
"weekly_comparison": [
  {"label": "2025-W44", "emissions": 3.5},
  {"label": "2025-W45", "emissions": 4.2}
]
```

**Purpose:**
- Highlight weekly variation in emissions (useful for operations planning).

---

## 4. Source Breakdown Donut Chart

Element:
- `<canvas id="donutChart"></canvas>` under **"Emissions Breakdown by Source"**.

### 4.1 Chart Type

- Type: `doughnut`
- Function: `updateDonutChart(sourceData)`

### 4.2 Data Source

- From `GET /api/dashboard` → `source_breakdown` array.

Example:

```json
"source_breakdown": [
  {"source": "electricity", "emissions": 5.23, "percentage": 45.3},
  {"source": "bus_diesel", "emissions": 3.10, "percentage": 26.9},
  {"source": "canteen_lpg", "emissions": 2.00, "percentage": 17.3},
  {"source": "waste_landfill", "emissions": 1.20, "percentage": 10.4}
]
```

### 4.3 Calculations (Backend)

- Sum emissions by `source_type` from `activity_data` for the selected date range.
- Also compute `percentage = emissions / total_emissions * 100`.

### 4.4 Tooltip Explanation

The frontend customizes the tooltip:

```js
label: function(context) {
  const label = context.label || '';
  const value = context.parsed || 0;
  const total = context.dataset.data.reduce((a, b) => a + b, 0);
  const percentage = ((value / total) * 100).toFixed(1);
  return `${label}: ${value.toFixed(2)} tonnes (${percentage}%)`;
}
```

This chart visually answers the question: **“Which activity contributes the most to our emissions?”**

---

## 5. Human CO₂ Emissions – UI Components & Charts

The Human CO₂ section is the **core feature** of the project.

### 5.1 Human KPIs (Population Summary)

Elements inside **Human CO₂ Emissions** section:

- `#humanTotalCount` – Average total population (students + staff) in the selected range.
- `#humanStudentCount` – Average student count.
- `#humanStaffCount` – Average staff count.
- (Optional/previously planned) `#humanTotalEmissions` – total human emissions in tonnes.

**Data Source:**

- `GET /api/dashboard` → `human_emissions` object:

```json
"human_emissions": {
  "total_emissions": 3.30,
  "avg_student_count": 2200,
  "avg_staff_count": 100,
  "avg_total_count": 2300,
  ...
}
```

**Calculation:**

- `avg_student_count` and `avg_staff_count` are averages over the selected date range.
- `avg_total_count = avg_student_count + avg_staff_count`.
- `total_emissions` is the sum of per-day human emissions (tonnes) across the selected range.

**Rendering:**

- `updateDashboard()` calls `updateHumanKPIs(data.human_emissions)`.
- `updateHumanKPIs` fills the KPI values and logs them for debugging.

> These KPIs answer: "On average, how many people are on campus, and what is the associated human CO₂?"

---

### 5.2 Cumulative Statistics (All Time)

Elements:

- `#cumulativeTotalEmissions` – All-time human emissions (tonnes CO₂).
- `#cumulativeDays` – Number of days recorded in `human_population` table.
- `#cumulativeAvgPopulation` – Average population per day over **all-time**.

**Data Source:**

- API: `GET /api/human_cumulative_stats`

Response example:

```json
{
  "total_emissions": 3.30,
  "total_records": 3,
  "average_students": 2100,
  "average_staff": 50,
  "average_population": 2150
}
```

**Rendering:**

- `updateCumulativeStats()` fetches this endpoint on page load.
- Safely checks for each element ID before assigning `textContent`.

> This card group provides a **lifetime summary** of human population impact, independent of the current date filter.

---

### 5.3 Human Trend Chart (Optional)

If you add `<canvas id="humanTrendChart"></canvas>` to the template, the function `updateHumanTrendChart(humanData, days)` is ready to render it.

**Data:**

- Uses `human_emissions.daily_trend`, `weekly_trend`, or `monthly_trend` from `/api/dashboard`, similar to the main trend chart.

**Purpose:**

- Show how human emissions change over time when population varies (exams, holidays, events).

---

### 5.4 Human Breakdown Donut Chart (Population Split)

If the corresponding `<canvas id="humanBreakdownChart">` is added:

- `updateHumanBreakdownChart(humanData)` draws a donut chart showing **students vs staff**.

**Data:**

- From `human_emissions.avg_student_count` and `avg_staff_count`.

**Tooltip:**

- Shows counts and percentages for students and staff.

> This chart visually explains the **composition of campus population**, useful when discussing per-person emissions.

---

### 5.5 Human Comparison Mixed Chart (Population vs Emissions)

With `<canvas id="humanComparisonChart"></canvas>` present, `updateHumanComparisonChart(humanData, days)` renders a **combined bar + line chart**:

- Bars: students and staff counts.
- Line: CO₂ emissions for those same dates.

**Data Source:**

- `human_emissions.population_data` from `/api/dashboard`:

```json
"population_data": [
  {
    "date": "2025-11-14",
    "students": 3000,
    "staff": 400,
    "total": 3400,
    "emissions": 3.4
  },
  ...
]
```

**Purpose:**

- Show how **changes in population** map to **changes in emissions**, using dual y-axes (population vs tonnes CO₂).

---

## 6. Recommendations Section (Cards UI)

Elements:

- Section: `<div class="recommendations-section">` in `dashboard.html`.
- Container: `<div id="recommendationsContainer" class="recommendations-container">`.

### 6.1 Data Source

- API: `GET /api/recommendations`

Response structure:

```json
{
  "recommendations": [
    { "title": "⚡ Electricity: Your #1 Emission Source", ... },
    { "title": "⭐ Quick Wins: Immediate Actions", ... },
    { "title": "🌱 Green Campus Initiative", ... },
    ...
  ],
  "summary": {
    "total_recommendations": 9,
    "high_priority": 4,
    "estimated_total_reduction": "50-70% achievable with full implementation",
    "message": "Start with Quick Wins..."
  }
}
```

### 6.2 Rendering (Frontend)

- `loadRecommendations()`:
  - Creates a **summary banner** with total recommendations and potential reduction.
  - For each recommendation:
    - Builds a card (`.recommendation-card`) with:
      - Title and description.
      - Priority and impact badges.
      - Prompt: `"⬇️ Click for X action steps"`.
      - Hidden `steps-container` containing actionable steps, impact, cost, timeframe.
  - Clicking a card calls `toggleSteps(index)` to expand/collapse the detailed steps.

**Purpose:**

- Provide a **narrative layer** over the numeric data.
- Translate charts and KPIs into **practical actions** the campus can perform.

---

## 7. Time Period Selector (Date Range Component)

Element:

```html
<select id="dateRange" onchange="updateDashboard()">
  <option value="7">Last Week</option>
  <option value="30">Last 30 Days</option>
  <option value="90">Last 3 Months</option>
  <option value="180">Last 6 Months</option>
  <option value="365" selected>Last Year</option>
</select>
```

### 7.1 Behavior

- When the user changes this dropdown, `updateDashboard()` is called.
- `updateDashboard()`:
  1. Computes `start_date` and `end_date` based on number of days selected.
  2. Calls `/api/dashboard?start_date=...&end_date=...`.
  3. Updates KPIs and all charts in one go.

**Purpose:**

- Give the viewer control over the **time window** for analysis, while the backend and frontend automatically adjust chart granularity.

---

## 8. Overall Data Flow Summary

1. **User opens dashboard** (`/`).
2. On `DOMContentLoaded`, `dashboard.js` runs:
   - `updateDashboard()` → `/api/dashboard`.
   - `loadRecommendations()` → `/api/recommendations`.
   - `updateCumulativeStats()` → `/api/human_cumulative_stats`.
3. Backend queries MySQL, calculates all aggregates and returns JSON.
4. Frontend:
   - Fills KPI cards.
   - Draws trend, bar, and donut charts with **Chart.js**.
   - Updates Human CO₂ KPIs and (optionally) human-specific charts.
   - Renders recommendation cards with expandable action steps.

Together, these components transform raw data into a **complete visual story**:
- **Where emissions come from**,
- **How they change over time**, and
- **What actions the campus should take next.**
