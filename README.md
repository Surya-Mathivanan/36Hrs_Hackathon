# Campus Carbon Footprint Analyzer

A comprehensive full-stack web application for tracking, analyzing, and reducing campus carbon emissions. Built for educational institutions to measure their environmental impact and take data-driven climate action.

**Backend**: Django 4.2 + Django REST Framework | **Frontend**: React 19 + Vite | **Database**: PostgreSQL | **Authentication**: JWT (JSON Web Tokens)

---


## Project Purpose & Vision

The Campus Carbon Footprint Analyzer addresses a critical gap in environmental management for educational institutions. Universities and colleges are large-scale consumers of resources—electricity for buildings and labs, fuel for transport fleets, gas for canteens, and generators of significant waste. However, most institutions lack a centralized system to:

1. **Aggregate** disparate consumption data from multiple departments
2. **Calculate** standardized carbon emissions using scientific conversion factors
3. **Visualize** trends over time to identify patterns
4. **Recommend** actionable strategies for emission reduction
5. **Track progress** toward sustainability goals

### UN SDG Alignment

This project directly supports **United Nations Sustainable Development Goal 13: Climate Action** by providing institutions with the tools to measure, manage, and reduce their carbon footprint systematically.

---

## Why This Project Exists

### The Problem

Educational institutions face several challenges in carbon management:

| Challenge               | Impact                                                                      |
| ----------------------- | --------------------------------------------------------------------------- |
| **Data Fragmentation**  | Energy bills, fuel receipts, and waste records scattered across departments |
| **No Standardization**  | Different units (kWh, liters, kg) make aggregation difficult                |
| **Lack of Visibility**  | No single dashboard showing total campus emissions                          |
| **Guesswork Decisions** | Without data, sustainability initiatives are hard to justify                |
| **Progress Tracking**   | Difficult to prove if emissions actually decreased after interventions      |

### The Solution

This platform provides:

- **Unified Dashboard**: Single source of truth for all emission sources
- **Scientific Accuracy**: Industry-standard emission factors (IPCC/EPA methodologies)
- **Visual Analytics**: Interactive charts showing trends, comparisons, and breakdowns
- **Smart Recommendations**: AI-like suggestions based on your largest emission sources
- **Human Emissions Module**: Unique tracking of metabolic CO₂ from campus population

---

---
## OutPut Images
![alt text](assets/HomePage.png)

![alt text](<assets/admin page 1.png>)

![alt text](<assets/csv file page.png>)

---



## System Architecture

### Three-Layer Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    PRESENTATION LAYER                            │
│  React 19 + Vite + Chart.js + React Router DOM                  │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐             │
│  │  Dashboard   │ │  Data Input  │ │    Login     │             │
│  │    Page      │ │    Page      │ │    Page      │             │
│  └──────────────┘ └──────────────┘ └──────────────┘             │
└───────────────────────────┬─────────────────────────────────────┘
                            │ HTTP/REST API (JSON)
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                    APPLICATION LAYER                             │
│  Django 4.2 + Django REST Framework + SimpleJWT                 │
│  ┌────────────────────────────────────────────────────────┐     │
│  │  Views: Authentication | Dashboard | Data Management   │     │
│  │  Serializers: Data validation & transformation         │     │
│  │  Models: ORM mapping to database tables                │     │
│  └────────────────────────────────────────────────────────┘     │
└───────────────────────────┬─────────────────────────────────────┘
                            │ SQL (psycopg2)
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                     DATA LAYER                                   │
│  PostgreSQL Database                                            │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌────────────┐ │
│  │   Activity  │ │   Human     │ │  Emission   │ │  College   │ │
│  │    Data     │ │  Population │ │   Factors   │ │  Profile   │ │
│  └─────────────┘ └─────────────┘ └─────────────┘ └────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

---

## Technology Stack Deep Dive

### Why Django + Django REST Framework?

**Django** was chosen as the backend framework for several strategic reasons:

1. **Rapid Development**: Django's "batteries-included" philosophy provides authentication, ORM, admin interface, and security features out of the box.

2. **Security**: Built-in protection against SQL injection, XSS, CSRF, and clickjacking—critical for handling institutional data.

3. **Scalability**: Django's ORM efficiently handles complex queries with PostgreSQL, enabling the dashboard to aggregate years of data quickly.

4. **Admin Interface**: Django's built-in admin panel provides a backup interface for data management.

**Django REST Framework (DRF)** extends Django with:

- **Serializers**: Automatic data validation and transformation between Python objects and JSON
- **ViewSets/Decorators**: Clean API endpoint definitions using `@api_view` decorator
- **Browsable API**: Self-documenting API interface for testing
- **Pagination & Filtering**: Built-in support for large dataset handling

### Why React + Vite?

**React** was selected for the frontend because:

1. **Component Architecture**: Reusable components (Sidebar, KPI Cards, Charts) make the codebase maintainable
2. **State Management**: React's Context API (`AuthContext`) elegantly handles global authentication state
3. **Ecosystem**: Chart.js integration via `react-chartjs-2` provides production-ready visualizations
4. **Developer Experience**: JSX syntax and React DevTools simplify debugging

**Vite** as the build tool:

- **Fast HMR (Hot Module Replacement)**: Instant updates during development
- **Optimized Production Builds**: Tree-shaking and code splitting reduce bundle size
- **Modern ES Modules**: Native ESM support for faster development

### Why PostgreSQL?

**PostgreSQL** was chosen over SQLite or MySQL for these reasons:

1. **Production Readiness**: PostgreSQL is designed for concurrent access and high availability—essential if multiple administrators use the system simultaneously

2. **Advanced Data Types**: Native support for DATE, JSON, and ARRAY types simplifies the activity data storage

3. **Window Functions & Aggregations**: Efficient SQL queries for dashboard aggregations (SUM, AVG, COUNT across date ranges)

4. **Cloud Compatibility**: Easy deployment on Supabase, Neon, Railway, or AWS RDS for production

5. **Data Integrity**: Foreign key constraints and ACID compliance ensure data consistency

6. **Scalability**: Can handle millions of records (years of daily campus data) without performance degradation

### Why JWT Authentication?

**JSON Web Tokens (JWT)** via `djangorestframework-simplejwt` provide:

1. **Stateless Authentication**: Server doesn't need to store session data—tokens are self-contained
2. **Cross-Domain Support**: Frontend (localhost:5173) and backend (localhost:8000) can run on different ports/domains
3. **Token Refresh**: Short-lived access tokens (24h) with longer refresh tokens (7d) balance security and UX
4. **Fine-Grained Permissions**: Easy to implement role-based access control (admin vs viewer)

---

## Database Design & Rationale

### Schema Overview

```
┌──────────────────────────────────────────────────────────────────┐
│                     EMISSION_FACTOR                              │
├──────────────────────────────────────────────────────────────────┤
│  id (PK)          │  Auto-generated primary key                  │
│  source_type      │  Unique identifier (electricity, bus_diesel)  │
│  factor           │  Conversion factor (e.g., 0.708 kg CO₂/kWh)   │
│  factor_unit      │  Unit description for display                 │
└──────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────┐
│                     ACTIVITY_DATA                                │
├──────────────────────────────────────────────────────────────────┤
│  id (PK)          │  Auto-generated primary key                  │
│  date             │  Date of measurement (YYYY-MM-DD)             │
│  source_type (FK) │  References emission factor                   │
│  raw_value        │  Measured quantity (kWh, liters, kg)          │
│  unit             │  Display unit                                 │
│  created_at       │  Timestamp of record creation                 │
└──────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────┐
│                   HUMAN_POPULATION                               │
├──────────────────────────────────────────────────────────────────┤
│  id (PK)          │  Auto-generated primary key                  │
│  date (Unique)    │  Date of headcount (one record per day)       │
│  student_count    │  Number of students on campus                 │
│  staff_count      │  Number of staff on campus                    │
│  created_at       │  Timestamp of record creation                 │
└──────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────┐
│                   COLLEGE_PROFILE                                │
├──────────────────────────────────────────────────────────────────┤
│  id (PK, Fixed=1) │  Singleton pattern - one row only             │
│  college_name     │  Institution name displayed on dashboard      │
│  tagline          │  Custom message (e.g., "Supporting SDG 13")   │
│  address          │  Physical address                             │
│  contact_email    │  Support email                                │
│  contact_phone    │  Support phone                                │
│  website          │  Institution website URL                      │
│  logo_emoji       │  Visual identifier (🏫)                       │
│  established_year │  For display purposes                         │
│  updated_at       │  Last modification timestamp                  │
└──────────────────────────────────────────────────────────────────┘
```

### Why This Schema Design?

#### EmissionFactor as a Separate Table

Instead of hardcoding factors in the application, they are stored in the database because:

1. **Configurability**: Administrators can update factors without code changes (e.g., when grid electricity becomes cleaner)
2. **Multi-Region Support**: Different countries have different grid emission factors
3. **Audit Trail**: Changes to conversion factors are tracked
4. **Extensibility**: Easy to add new emission sources

#### ActivityData Normalization

Activity data is stored in a normalized format (`date`, `source_type`, `raw_value`, `unit`) rather than pre-calculated emissions because:

1. **Data Integrity**: Raw values are immutable facts; calculated emissions depend on factors that might change
2. **Flexibility**: If emission factors are updated, emissions can be recalculated dynamically
3. **Storage Efficiency**: Raw values (integers) take less space than calculated emissions (floats)

#### HumanPopulation Separate Table

Human emissions are tracked separately because:

1. **Different Calculation**: Human emissions use a fixed formula (1 kg CO₂/person/day) rather than lookup factors
2. **Different Input**: Requires student_count and staff_count, not a single raw_value
3. **Unique Insights**: Enables per-capita emission analysis (emissions per student)
4. **Upsert Pattern**: Population data is often updated retrospectively (one update_or_create per date)

#### CollegeProfile Singleton

The singleton pattern (always row id=1) for college profile ensures:

1. **Consistency**: Exactly one configuration exists—no ambiguity
2. **Simplicity**: No need for complex foreign key relationships
3. **Caching**: Dashboard can cache profile data confidently

---

## Backend Implementation Details

### Models (`api/models.py`)

#### `EmissionFactor` Model

```python
class EmissionFactor(models.Model):
    source_type = models.CharField(max_length=100, unique=True)
    factor = models.FloatField()
    factor_unit = models.CharField(max_length=50)
```

**Why these fields?**

- `source_type`: Acts as both identifier and human-readable label (electricity, bus_diesel)
- `factor`: The conversion coefficient—float allows decimal precision
- `factor_unit`: Display string explaining what the factor means (kg CO₂e/kWh)

**Meta Configuration:**

- `db_table = 'emission_factors'`: Explicit table naming for SQL clarity

#### `ActivityData` Model

```python
class ActivityData(models.Model):
    SOURCE_CHOICES = [
        ('electricity', 'Electricity'),
        ('bus_diesel', 'Bus Diesel'),
        ('canteen_lpg', 'Canteen LPG'),
        ('waste_landfill', 'Waste (Landfill)'),
    ]
    date = models.DateField()
    source_type = models.CharField(max_length=100, choices=SOURCE_CHOICES)
    raw_value = models.FloatField()
    unit = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
```

**Why these fields?**

- `SOURCE_CHOICES`: Enforces data integrity—only valid source types allowed
- `DateField` (not DateTimeField): Campus data is recorded daily; time is irrelevant
- `raw_value`: Float accommodates decimal measurements (e.g., 1234.56 kWh)
- `unit`: Stored because the same source might have different units in different contexts
- `created_at`: Audit trail for when data was entered

**Property Method:**

```python
@property
def emissions_tonnes(self):
    """Calculate CO2e emissions in tonnes."""
    try:
        factor = EmissionFactor.objects.get(source_type=self.source_type)
        return (self.raw_value * factor.factor) / 1000
    except EmissionFactor.DoesNotExist:
        return 0.0
```

**Why a property?**

- Calculated on-demand, not stored—prevents data inconsistency if factors change
- Uses try/except for defensive programming—graceful degradation if factor missing
- Division by 1000 converts kg to tonnes (standard reporting unit)

#### `HumanPopulation` Model

```python
class HumanPopulation(models.Model):
    date = models.DateField(unique=True)
    student_count = models.IntegerField()
    staff_count = models.IntegerField()
```

**Why `unique=True` on date?**

- Ensures exactly one population record per day
- Prevents duplicate entries and data confusion
- Database-level constraint is more reliable than application logic

**Property Methods:**

```python
@property
def total_count(self):
    return self.student_count + self.staff_count

@property
def emissions_tonnes(self):
    """1 kg CO2 per person per day."""
    return self.total_count * 1.0 / 1000
```

**Scientific Rationale:**

- Humans exhale approximately 1 kg of CO₂ per day through respiration
- This is part of the short-term carbon cycle and doesn't contribute to climate change directly
- However, tracking it provides understanding of campus population density impact

#### `CollegeProfile` Model

```python
class CollegeProfile(models.Model):
    college_name = models.CharField(max_length=200, default='KIT Campus')
    tagline = models.CharField(max_length=300, default='Supporting UN SDG 13: Climate Action')
    # ... other fields

    @classmethod
    def get_singleton(cls):
        """Always return the single profile row, creating it if missing."""
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj
```

**Why Singleton Pattern?**

- `get_or_create(pk=1)`: Ensures row 1 always exists
- Simplifies views—no need to check if profile exists
- Enables public dashboard to always display college info

---

### Serializers (`api/serializers.py`)

Serializers transform Python model instances to/from JSON. DRF serializers also provide validation.

#### `ActivityDataSerializer`

```python
class ActivityDataSerializer(serializers.ModelSerializer):
    emissions_tonnes = serializers.ReadOnlyField()

    class Meta:
        model = ActivityData
        fields = ['id', 'date', 'source_type', 'raw_value', 'unit', 'emissions_tonnes', 'created_at']
```

**Why `ReadOnlyField` for emissions?**

- Prevents clients from sending calculated emissions (would be a security vulnerability)
- Ensures emissions are always calculated server-side from raw values

**Validation Methods:**

```python
def validate_source_type(self, value):
    allowed = ['electricity', 'bus_diesel', 'canteen_lpg', 'waste_landfill']
    if value not in allowed:
        raise serializers.ValidationError(f"Invalid source_type...")
    return value

def validate_raw_value(self, value):
    if value <= 0:
        raise serializers.ValidationError("raw_value must be positive.")
    return value
```

**Why explicit validation?**

- `source_type`: Double-validation (model has choices, but serializer enforces for API clarity)
- `raw_value`: Negative consumption is physically impossible—catches data entry errors early

#### `HumanPopulationSerializer`

```python
class HumanPopulationSerializer(serializers.ModelSerializer):
    total_count = serializers.ReadOnlyField()
    emissions_tonnes = serializers.ReadOnlyField()
```

**Why include calculated fields?**

- Frontend needs these for immediate display after creating/updating population data
- Avoids requiring a second API call to get calculated totals

---

### Views (`api/views.py`)

Views handle HTTP requests and return responses. This project uses function-based views with `@api_view` decorator for clarity.

#### Authentication Views

**`login_view`** - POST `/api/auth/login/`

```python
@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    serializer = LoginSerializer(data=request.data)
    # ... validation ...
    user = authenticate(request, username=username, password=password)
    if user is None:
        return Response({'error': 'Invalid credentials.'}, status=401)

    refresh = RefreshToken.for_user(user)
    return Response({
        'access': str(refresh.access_token),
        'refresh': str(refresh),
        'username': user.username,
        'user_id': user.id,
    })
```

**Why this implementation?**

- Uses Django's built-in `authenticate()`—secure password verification
- `RefreshToken.for_user()` generates JWT tokens with user claims embedded
- Returns both tokens—access for API calls, refresh for renewal

**`refresh_token_view`** - POST `/api/auth/refresh/`

```python
@api_view(['POST'])
@permission_classes([AllowAny])
def refresh_token_view(request):
    refresh_token = request.data.get('refresh')
    refresh = RefreshToken(refresh_token)
    return Response({'access': str(refresh.access_token)})
```

**Why separate refresh endpoint?**

- Access tokens are short-lived (24h) for security
- Refresh tokens (7d) allow users to stay logged in without re-entering credentials
- If access token is stolen, it's useless after 24h

#### Dashboard View

**`get_dashboard_data`** - GET `/api/dashboard/?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD`

This is the most complex view (~200 lines). It aggregates data for all dashboard charts.

**Query Parameters:**

- `start_date`, `end_date`: Date range filter (defaults to last 365 days)

**Why date range filtering?**

- Allows historical analysis (compare this year vs last year)
- Prevents loading all data (performance optimization)
- Enables drill-down (view specific months or quarters)

**Aggregation Logic:**

```python
# Filter activity data by date range
activity_qs = ActivityData.objects.filter(date__range=[start_date, end_date])

# Calculate KPIs
total_emissions = sum(a.emissions_tonnes for a in activity_qs)

# Group by source for breakdown
source_breakdown = {}
for a in activity_qs:
    source_breakdown[a.source_type] = source_breakdown.get(a.source_type, 0) + a.emissions_tonnes

# Time-series aggregation for charts
daily_data = {}
for a in activity_qs:
    key = str(a.date)
    daily_data[key] = daily_data.get(key, 0) + a.emissions_tonnes
```

**Why Python aggregation instead of SQL GROUP BY?**

- Django ORM makes Python-level aggregation readable
- Need to access `emissions_tonnes` property which is Python-calculated
- Dataset sizes (campus data) are small enough that Python aggregation is fast

**Response Structure:**

```json
{
  "kpis": {
    "total_emissions": 123.45,
    "percent_change": -5.2,
    "biggest_source": "electricity",
    "biggest_source_percent": 65.3,
    "energy_saved": 45678
  },
  "daily_trend": [{"date": "2025-01-01", "emissions": 10.5}, ...],
  "monthly_trend": [{"month": "2025-01", "emissions": 315.2}, ...],
  "source_breakdown": [{"source": "electricity", "emissions": 80.5, "percentage": 65.3}, ...],
  "human_emissions": { ... }
}
```

**Why this structure?**

- Pre-calculates everything the frontend needs in one request
- Minimizes frontend data processing
- Chart-ready format—no transformation needed

#### Recommendations View

**`get_recommendations`** - GET `/api/recommendations/`

Generates personalized emission reduction recommendations based on the largest emission source.

```python
# Find top source by emissions
source_totals = {}
for a in ActivityData.objects.all():
    em = a.emissions_tonnes
    source_totals[a.source_type] = source_totals.get(a.source_type, 0) + em
top_source = max(source_totals.items(), key=lambda x: x[1])
```

**Why this approach?**

- Recommendations should target the biggest impact area first
- Uses all historical data (not just date range) for complete picture

**Recommendation Map:**

```python
rec_map = {
    'electricity': {
        'title': '⚡ Electricity: Your #1 Emission Source',
        'description': f'Electricity contributes {em:.2f} tonnes CO₂...',
        'priority': 'High',
        'impact': 'High',
        'actionable_steps': [
            'Conduct energy audit...',
            'Replace bulbs with LED...',
            'Install motion sensors...',
        ],
        'expected_reduction': '30-50% reduction',
        'cost': 'Medium to High (Initial) | High ROI (2-5 years)',
    },
    # ... similar for bus_diesel, canteen_lpg, waste_landfill
}
```

**Why hardcoded recommendations?**

- Emission reduction strategies are well-established (IPCC guidelines)
- Provides immediate value without ML complexity
- Can be extended to database-driven recommendations later

#### Data Entry Views

**`add_activity_data`** - POST `/api/data/`

```python
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_activity_data(request):
    serializer = ActivityDataSerializer(data=request.data)
    # ... validation ...

    # Verify emission factor exists
    if not EmissionFactor.objects.filter(source_type=source_type).exists():
        return Response({'error': 'No emission factor configured...'}, status=400)

    instance = serializer.save()
    return Response({
        'message': 'Data added successfully.',
        'data': ActivityDataSerializer(instance).data
    }, status=201)
```

**Why check emission factor before saving?**

- Prevents orphaned data (activity record without conversion factor)
- Provides clear error message to admin
- Ensures data integrity

**`upload_csv`** - POST `/api/upload_csv/`

```python
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_csv(request):
    records = request.data.get('records')
    # ... validation ...

    validated = []
    for idx, rec in enumerate(records, start=1):
        # Validate each record
        # ... date parsing, value validation ...
        validated.append(ActivityData(...))

    ActivityData.objects.bulk_create(validated)
    return Response({'success': True, 'message': f'{len(validated)} records inserted.'})
```

**Why bulk_create?**

- Importing years of historical data (thousands of records)
- Individual `save()` calls would be prohibitively slow
- `bulk_create` does single INSERT statement—much faster

**Why JSON payload instead of file upload?**

- Frontend parses CSV and validates format before sending
- Better error handling (can report which row failed)
- Consistent with REST API design (JSON payloads)

**`add_human_data`** - POST `/api/human_data/`

```python
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_human_data(request):
    # ... validation ...

    # Upsert on date
    instance, created = HumanPopulation.objects.update_or_create(
        date=rec_date_parsed,
        defaults={'student_count': student_count, 'staff_count': staff_count}
    )
```

**Why `update_or_create`?**

- Population data is often corrected or updated
- Prevents duplicate entries for same date
- Atomic operation—thread-safe

#### Admin Views

**`reset_data`** - DELETE `/api/admin/reset/`

```python
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def reset_data(request):
    ActivityData.objects.all().delete()
    HumanPopulation.objects.all().delete()
    return Response({'success': True, 'message': 'All data cleared.'})
```

**Why include this dangerous operation?**

- Useful for development/testing
- Allows fresh start for new academic year
- Protected by authentication
- Can be restricted to superusers in production

---

### Management Commands (`api/management/commands/seed_data.py`)

**Purpose:** Initialize database with essential data

```python
class Command(BaseCommand):
    def handle(self, *args, **options):
        # 1. Emission factors
        EMISSION_FACTORS = [
            ('electricity',   0.708, 'kg_co2e_per_kwh'),
            ('bus_diesel',    2.68,  'kg_co2e_per_liter'),
            ('canteen_lpg',   2.93,  'kg_co2e_per_kg'),
            ('waste_landfill',1.25,  'kg_co2e_per_kg'),
            ('human_daily',   1.0,   'kg_co2e_per_person_per_day'),
        ]

        # 2. Admin user
        User.objects.create_superuser('admin', 'admin@campus.edu', 'admin123')

        # 3. Sample activity data (for demo purposes)
```

**Why seed data?**

- Emission factors are required for calculations—app won't work without them
- Default admin allows immediate login after setup
- Sample data demonstrates dashboard functionality

---

## Frontend Implementation Details

### Project Structure

```
frontend/src/
├── main.jsx              # React entry point - renders App into DOM
├── App.jsx               # Router configuration, layout wrapper
├── index.css             # Global styles, CSS variables, dark theme
├── context/
│   └── AuthContext.jsx   # JWT auth state management
├── services/
│   └── api.js            # Axios HTTP client, API functions
├── components/
│   ├── Sidebar.jsx       # Navigation sidebar
│   └── Loader.jsx        # Loading spinner
└── pages/
    ├── LoginPage.jsx     # Authentication form
    ├── DashboardPage.jsx # Main analytics dashboard
    ├── DataInputPage.jsx # Data entry forms
    └── AdminPage.jsx     # Admin tools
```

### AuthContext (`context/AuthContext.jsx`)

Manages global authentication state using React Context API.

```javascript
export function AuthProvider({ children }) {
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        // Check localStorage on mount
        const token = localStorage.getItem('access_token');
        const username = localStorage.getItem('username');
        if (token && username) {
            setUser({ username });
        }
        setLoading(false);
    }, []);

    const login = async (username, password) => {
        const response = await apiLogin(username, password);
        const { access, refresh, username: uname } = response.data;
        localStorage.setItem('access_token', access);
        localStorage.setItem('refresh_token', refresh);
        localStorage.setItem('username', uname);
        setUser({ username: uname });
    };

    const logout = () => {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('username');
        setUser(null);
    };
```

**Why Context API over Redux?**

- Simple state shape (just user object)
- No complex reducers or actions needed
- Built into React—no additional dependencies
- Sufficient for this application's scope

**Why localStorage?**

- Tokens persist across browser sessions
- User stays logged in after closing/reopening browser
- Simple to implement

### API Service (`services/api.js`)

Centralized HTTP client with interceptors.

```javascript
const api = axios.create({
  baseURL: API_URL,
  headers: { "Content-Type": "application/json" },
});

// Request interceptor - attach JWT token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("access_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor - auto-refresh on 401
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      const refreshToken = localStorage.getItem("refresh_token");
      if (refreshToken) {
        try {
          const res = await axios.post(`${API_URL}/auth/refresh/`, {
            refresh: refreshToken,
          });
          localStorage.setItem("access_token", res.data.access);
          originalRequest.headers.Authorization = `Bearer ${res.data.access}`;
          return api(originalRequest);
        } catch {
          // Refresh failed - logout
          localStorage.clear();
          window.location.href = "/login";
        }
      }
    }
    return Promise.reject(error);
  },
);
```

**Why interceptors?**

- **Request interceptor**: Automatically adds auth header to every request—no need to manually attach token each time
- **Response interceptor**: Handles token expiration transparently—user experience is seamless

**Why `originalRequest._retry` flag?**

- Prevents infinite loops if refresh token is also invalid
- Ensures refresh attempt happens only once per failed request

### DashboardPage (`pages/DashboardPage.jsx`)

The main analytics interface (~400 lines).

**Chart Registration:**

```javascript
ChartJS.register(
  CategoryScale, // X-axis categories (dates)
  LinearScale, // Y-axis numeric values
  PointElement, // Line chart points
  LineElement, // Line chart lines
  BarElement, // Bar chart bars
  ArcElement, // Doughnut segments
  Title,
  Tooltip,
  Legend,
  Filler, // Chart plugins
);
```

**Why register only needed components?**

- Tree-shaking—reduces bundle size
- Chart.js v3+ requires explicit registration

**Date Range Handling:**

```javascript
function getDateRange(days) {
  const end = new Date();
  const start = new Date();
  start.setDate(start.getDate() - days);
  return {
    start: start.toISOString().split("T")[0],
    end: end.toISOString().split("T")[0],
  };
}
```

**Why ISO string splitting?**

- `toISOString()` returns `YYYY-MM-DDTHH:mm:ss.sssZ`
- Splitting on 'T' gives just the date part `YYYY-MM-DD`
- Backend expects date in this format

**KPI Card Component:**

```javascript
function KpiCard({ icon, title, value, unit, accent }) {
  return (
    <div className={`kpi-card ${accent ? "human-kpi-card" : ""}`}>
      <div className="kpi-icon">{icon}</div>
      <div className="kpi-content">
        <h3>{title}</h3>
        <p className="kpi-value">{value ?? "--"}</p>
        <p className="kpi-unit">{unit}</p>
      </div>
    </div>
  );
}
```

**Why separate component?**

- Reusable across different KPIs
- Consistent styling
- Easy to add new KPIs

**Chart Data Transformation:**

```javascript
// Transform API response to Chart.js format
const trendChartData = {
  labels: data.daily_trend.map((d) => fmtLabel("date", d.date)),
  datasets: [
    {
      label: "Total Emissions (Tonnes CO₂)",
      data: data.daily_trend.map((d) => d.emissions),
      borderColor: "#00d4aa",
      backgroundColor: "rgba(0, 212, 170, 0.1)",
      fill: true,
      tension: 0.4, // Smooth curves
    },
  ],
};
```

**Why map data?**

- API returns array of objects `[{date, emissions}, ...]`
- Chart.js needs separate arrays for labels and data
- `fmtLabel` converts ISO dates to human-readable format ("Jan 15")

### DataInputPage (`pages/DataInputPage.jsx`)

Multi-tab interface for data entry.

**Source Unit Mapping:**

```javascript
const SOURCE_UNIT_MAP = {
  electricity: "kWh",
  bus_diesel: "Liters",
  canteen_lpg: "kg",
  waste_landfill: "kg",
};
```

**Why hardcoded mapping?**

- Units are standardized for each source type
- Prevents unit confusion (e.g., entering liters for electricity)
- Auto-populates unit field when source is selected

**CSV Upload Flow:**

```javascript
const handleCSVUpload = async (file) => {
  const text = await file.text();
  const lines = text.trim().split("\n");
  const headers = lines[0].split(",").map((h) => h.trim());

  // Validate headers
  const required = ["date", "source_type", "raw_value", "unit"];
  const missing = required.filter((h) => !headers.includes(h));
  if (missing.length > 0) {
    setError(`Missing columns: ${missing.join(", ")}`);
    return;
  }

  // Parse records
  const records = lines.slice(1).map((line) => {
    const values = line.split(",");
    return {
      date: values[0].trim(),
      source_type: values[1].trim(),
      raw_value: parseFloat(values[2]),
      unit: values[3].trim(),
    };
  });

  // Send to API
  await uploadCSV(records);
};
```

**Why client-side validation?**

- Immediate feedback to user—no server round-trip
- Reduces server load
- Can show specific line numbers with errors

---

## Authentication & Security

### JWT Token Flow

```
┌─────────────┐         ┌─────────────┐         ┌─────────────┐
│   Client    │         │   Backend   │         │  Database   │
└──────┬──────┘         └──────┬──────┘         └──────┬──────┘
       │                       │                       │
       │  POST /auth/login/    │                       │
       │  {username, password} │                       │
       │──────────────────────>│                       │
       │                       │  authenticate()       │
       │                       │──────────────────────>│
       │                       │<──────────────────────│
       │                       │                       │
       │                       │  Generate JWT         │
       │                       │  (access + refresh)   │
       │                       │                       │
       │  {access, refresh}    │                       │
       │<──────────────────────│                       │
       │                       │                       │
       │  Store tokens in      │                       │
       │  localStorage         │                       │
       │                       │                       │
       │  GET /api/data/       │                       │
       │  Authorization:       │                       │
       │  Bearer <access>      │                       │
       │──────────────────────>│                       │
       │                       │  Validate JWT         │
       │                       │  signature            │
       │                       │                       │
       │  Response data        │                       │
       │<──────────────────────│                       │
       │                       │                       │
```

### Security Measures

| Measure              | Implementation            | Purpose                                     |
| -------------------- | ------------------------- | ------------------------------------------- |
| **CORS**             | `django-cors-headers`     | Restricts API access to configured origins  |
| **CSRF**             | Django middleware         | Protects against cross-site request forgery |
| **SQL Injection**    | Django ORM                | Parameterized queries prevent injection     |
| **XSS**              | React auto-escaping       | Prevents script injection in JSX            |
| **Password Hashing** | Django `create_superuser` | PBKDF2 hashing with salt                    |
| **HTTPS Ready**      | Django settings           | Enforce HTTPS in production                 |
| **Input Validation** | DRF Serializers           | Type checking and bounds validation         |

---

## API Documentation

### Complete Endpoint Reference

#### Public Endpoints

| Endpoint                       | Method | Auth | Description                             |
| ------------------------------ | ------ | ---- | --------------------------------------- |
| `/api/dashboard/`              | GET    | No   | Get dashboard data with KPIs and charts |
| `/api/recommendations/`        | GET    | No   | Get emission reduction recommendations  |
| `/api/emission_factors/`       | GET    | No   | List all emission conversion factors    |
| `/api/human_cumulative_stats/` | GET    | No   | Get all-time human emissions statistics |
| `/api/college_profile/`        | GET    | No   | Get college branding information        |
| `/api/auth/login/`             | POST   | No   | Obtain JWT access and refresh tokens    |
| `/api/auth/refresh/`           | POST   | No   | Refresh access token                    |

#### Protected Endpoints (JWT Required)

| Endpoint                       | Method | Description                            |
| ------------------------------ | ------ | -------------------------------------- |
| `/api/auth/me/`                | GET    | Get current user info                  |
| `/api/data/`                   | POST   | Add single activity record             |
| `/api/upload_csv/`             | POST   | Bulk upload activity records           |
| `/api/human_data/`             | POST   | Add/update human population data       |
| `/api/admin/reset/`            | DELETE | Clear all activity and population data |
| `/api/college_profile/update/` | PATCH  | Update college profile                 |

### Request/Response Examples

#### Login

**Request:**

```json
POST /api/auth/login/
{
    "username": "admin",
    "password": "admin123"
}
```

**Response:**

```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "username": "admin",
  "user_id": 1
}
```

#### Add Activity Data

**Request:**

```json
POST /api/data/
Authorization: Bearer <access_token>
{
    "date": "2025-01-15",
    "source_type": "electricity",
    "raw_value": 120000,
    "unit": "kWh"
}
```

**Response:**

```json
{
  "message": "Data added successfully.",
  "data": {
    "id": 1,
    "date": "2025-01-15",
    "source_type": "electricity",
    "raw_value": 120000.0,
    "unit": "kWh",
    "emissions_tonnes": 84.96,
    "created_at": "2025-01-15T10:30:00Z"
  }
}
```

#### Dashboard Query

**Request:**

```
GET /api/dashboard/?start_date=2025-01-01&end_date=2025-01-31
```

**Response:**

```json
{
  "kpis": {
    "total_emissions": 245.8,
    "percent_change": -3.2,
    "biggest_source": "electricity",
    "biggest_source_percent": 68.5,
    "energy_saved": 15420
  },
  "daily_trend": [
    { "date": "2025-01-01", "emissions": 8.5 },
    { "date": "2025-01-02", "emissions": 7.9 }
  ],
  "source_breakdown": [
    { "source": "electricity", "emissions": 168.4, "percentage": 68.5 },
    { "source": "bus_diesel", "emissions": 45.2, "percentage": 18.4 }
  ],
  "human_emissions": {
    "total_emissions": 32.1,
    "avg_student_count": 3000,
    "avg_staff_count": 400
  }
}
```

---

## Emission Calculation Methodology

### The Formula

All emissions are calculated using the industry-standard formula:

```
Emissions (Tonnes CO₂e) = (Raw Consumption × Emission Factor) ÷ 1000
```

### Emission Factors Used

| Source            | Factor | Unit               | Source                   |
| ----------------- | ------ | ------------------ | ------------------------ |
| Electricity       | 0.708  | kg CO₂e/kWh        | India grid average (CEA) |
| Bus Diesel        | 2.68   | kg CO₂e/Liter      | IPCC default             |
| Canteen LPG       | 2.93   | kg CO₂e/kg         | IPCC default             |
| Waste (Landfill)  | 1.25   | kg CO₂e/kg         | IPCC default             |
| Human (Metabolic) | 1.0    | kg CO₂e/person/day | Scientific estimate      |

### Calculation Examples

**Electricity:**

```
Input: 120,000 kWh
Calculation: 120,000 × 0.708 ÷ 1000 = 84.96 Tonnes CO₂e
```

**Bus Diesel:**

```
Input: 5,000 Liters
Calculation: 5,000 × 2.68 ÷ 1000 = 13.4 Tonnes CO₂e
```

**Human Population:**

```
Input: 3,000 students + 400 staff = 3,400 people
Calculation: 3,400 × 1.0 ÷ 1000 = 3.4 Tonnes CO₂e/day
```

### Scientific Rationale

**Electricity Factor (0.708 kg CO₂e/kWh):**

- Based on India's national grid emission factor published by Central Electricity Authority (CEA)
- Represents average emissions from coal, gas, hydro, nuclear, and renewable mix
- Updated annually as grid becomes cleaner

**Transport Fuel Factors:**

- IPCC (Intergovernmental Panel on Climate Change) default values
- Accounts for complete combustion of fuel
- Includes both CO₂ and non-CO₂ greenhouse gases (converted to CO₂ equivalent)

**Waste Factor (1.25 kg CO₂e/kg):**

- Accounts for methane generation from organic waste decomposition
- Methane has 28x global warming potential compared to CO₂
- Factor varies by waste composition and landfill management

**Human Metabolic Factor (1.0 kg CO₂/person/day):**

- Average adult exhales ~1 kg CO₂ per day through respiration
- Based on metabolic rate studies
- Represents carbon cycling through biological processes
- **Note:** Human respiration is part of the short-term carbon cycle (plants → food → CO₂ → plants), so these emissions are "carbon neutral" in the long term. However, tracking them provides insight into population density and associated operational loads (HVAC, etc.).

---

## Setup & Installation

### Prerequisites

| Tool       | Version | Check Command      |
| ---------- | ------- | ------------------ |
| Python     | 3.11+   | `python --version` |
| Node.js    | 18+     | `node --version`   |
| npm        | 9+      | `npm --version`    |
| PostgreSQL | 12+     | `psql --version`   |

### Backend Setup

```bash
# 1. Navigate to backend
cd backend

# 2. Create virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment variables
# Create .env file:
cat > .env << EOF
DATABASE_URL=postgresql://user:password@localhost:5432/campus_carbon
SECRET_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(50))")
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
CORS_ALLOWED_ORIGINS=http://localhost:5173,http://localhost:3000
ACCESS_TOKEN_LIFETIME_HOURS=24
EOF

# 5. Run migrations
python manage.py makemigrations api
python manage.py migrate

# 6. Seed database with initial data
python manage.py seed_data

# 7. Start development server
python manage.py runserver
# Server runs at http://localhost:8000
```

### Frontend Setup

```bash
# 1. Navigate to frontend
cd frontend

# 2. Install dependencies
npm install

# 3. Configure environment (optional)
cat > .env << EOF
VITE_API_URL=http://localhost:8000/api
EOF

# 4. Start development server
npm run dev
# Server runs at http://localhost:5173
```

### Access the Application

- **Dashboard (Public)**: http://localhost:5173/
- **Admin Login**: http://localhost:5173/login
- **Default Credentials**: admin / admin123
- **API Root**: http://localhost:8000/api/

---

## Deployment Guide

### Production Checklist

#### Backend Security

```python
# backend/.env
DEBUG=False
SECRET_KEY=<generate-new-strong-key>
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
CORS_ALLOWED_ORIGINS=https://yourdomain.com
```

#### Database

- Use managed PostgreSQL (AWS RDS, Supabase, Neon)
- Enable SSL connections
- Regular backups
- Connection pooling (pgbouncer) for high traffic

#### Static Files (if adding Django Admin)

```bash
python manage.py collectstatic
# Serve with nginx or CDN
```

#### Frontend Build

```bash
cd frontend
npm run build
# Deploy dist/ folder to static hosting (Vercel, Netlify, AWS S3)
```

#### Environment Variables for Production

**Backend (.env):**

```
DATABASE_URL=postgresql://user:pass@host:5432/dbname?sslmode=require
SECRET_KEY=<50+ character random string>
DEBUG=False
ALLOWED_HOSTS=api.yourcampus.edu
CORS_ALLOWED_ORIGINS=https://dashboard.yourcampus.edu
```

**Frontend (.env):**

```
VITE_API_URL=https://api.yourcampus.edu/api
```

### Docker Deployment (Optional)

```dockerfile
# Dockerfile.backend
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "core.wsgi:application"]
```

```dockerfile
# Dockerfile.frontend
FROM node:18-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
```

### Scaling Considerations

1. **Database**: Add read replicas for dashboard queries
2. **Caching**: Implement Redis caching for emission factors and dashboard data
3. **CDN**: Serve frontend static files from CDN
4. **Load Balancer**: Multiple backend instances behind nginx/ALB

---

## Troubleshooting

### Common Issues

**"No module named 'psycopg2'"**

```bash
pip install psycopg2-binary
```

**"CORS error in browser"**

- Check `CORS_ALLOWED_ORIGINS` includes frontend URL
- Verify backend is running and accessible

**"Migration errors"**

```bash
python manage.py migrate --run-syncdb
```

**"Cannot connect to PostgreSQL"**

- Verify DATABASE_URL format
- Check PostgreSQL is running
- For cloud DBs, ensure IP is whitelisted

### Getting Help

- Check `Documents/` folder for detailed documentation
- Review API responses in browser Network tab
- Check Django logs: `python manage.py runserver` output

---

## License

This project was developed for educational purposes and hackathon demonstration.

---

## Acknowledgments

- **IPCC** for emission factor methodologies
- **Central Electricity Authority (India)** for grid emission factors
- **UN SDG 13** for climate action inspiration

---

_Built with ❤️ for sustainable campuses_
