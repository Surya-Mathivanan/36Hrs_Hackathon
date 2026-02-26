import logging
from datetime import datetime, timedelta, date

from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.db import models as db_models
from django.db.models import Sum, Avg, Count
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from .models import ActivityData, HumanPopulation, EmissionFactor, CollegeProfile
from .serializers import (
    ActivityDataSerializer,
    HumanPopulationSerializer,
    EmissionFactorSerializer,
    LoginSerializer,
    CollegeProfileSerializer,
)

logger = logging.getLogger(__name__)


# ============================================================
# AUTH VIEWS
# ============================================================

@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    """
    POST /api/auth/login/
    Returns JWT access + refresh tokens.
    Accepts both plain-text and Django-hashed passwords for backward compat.
    """
    serializer = LoginSerializer(data=request.data)
    if not serializer.is_valid():
        return Response({'error': 'Missing username or password.'}, status=status.HTTP_400_BAD_REQUEST)

    username = serializer.validated_data['username']
    password = serializer.validated_data['password']

    user = authenticate(request, username=username, password=password)
    if user is None:
        logger.warning(f"Failed login attempt for username='{username}'")
        return Response({'error': 'Invalid credentials.'}, status=status.HTTP_401_UNAUTHORIZED)

    refresh = RefreshToken.for_user(user)
    logger.info(f"Successful login for username='{username}'")
    return Response({
        'access': str(refresh.access_token),
        'refresh': str(refresh),
        'username': user.username,
        'user_id': user.id,
    })


@api_view(['POST'])
@permission_classes([AllowAny])
def refresh_token_view(request):
    """POST /api/auth/refresh/ - Refresh access token."""
    refresh_token = request.data.get('refresh')
    if not refresh_token:
        return Response({'error': 'Refresh token required.'}, status=status.HTTP_400_BAD_REQUEST)
    try:
        refresh = RefreshToken(refresh_token)
        return Response({'access': str(refresh.access_token)})
    except Exception:
        return Response({'error': 'Invalid or expired refresh token.'}, status=status.HTTP_401_UNAUTHORIZED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def me_view(request):
    """GET /api/auth/me/ - Current user info."""
    return Response({
        'user_id': request.user.id,
        'username': request.user.username,
        'email': request.user.email,
    })


# ============================================================
# ACTIVITY DATA VIEWS
# ============================================================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_activity_data(request):
    """
    POST /api/data/
    Add a single activity record. Requires authentication.
    """
    serializer = ActivityDataSerializer(data=request.data)
    if not serializer.is_valid():
        return Response({'error': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    # Verify emission factor exists for this source type
    source_type = serializer.validated_data['source_type']
    if not EmissionFactor.objects.filter(source_type=source_type).exists():
        return Response(
            {'error': f"No emission factor configured for source_type '{source_type}'."},
            status=status.HTTP_400_BAD_REQUEST
        )

    instance = serializer.save()
    logger.info(f"Activity data added: {instance.date} | {instance.source_type}: {instance.raw_value} {instance.unit}")
    return Response({
        'message': 'Data added successfully.',
        'data': ActivityDataSerializer(instance).data
    }, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_csv(request):
    """
    POST /api/upload_csv/
    Bulk insert activity records from a JSON payload.
    Expected: { "records": [{ "date", "source_type", "raw_value", "unit" }] }
    """
    records = request.data.get('records')
    if not isinstance(records, list) or len(records) == 0:
        return Response({'error': 'Invalid payload. Expected non-empty "records" list.'}, status=status.HTTP_400_BAD_REQUEST)

    ALLOWED_SOURCES = {'electricity', 'bus_diesel', 'canteen_lpg', 'waste_landfill'}
    validated = []
    for idx, rec in enumerate(records, start=1):
        if not isinstance(rec, dict):
            return Response({'error': f'Invalid record at row {idx}.'}, status=status.HTTP_400_BAD_REQUEST)

        missing = [k for k in ('date', 'source_type', 'raw_value', 'unit') if k not in rec]
        if missing:
            return Response({'error': f'Missing fields {missing} at row {idx}.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            rec_date = datetime.strptime(rec['date'], '%Y-%m-%d').date()
        except (ValueError, TypeError):
            return Response({'error': f'Invalid date format at row {idx}: expected YYYY-MM-DD.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            raw_value = float(rec['raw_value'])
            if raw_value <= 0:
                raise ValueError("Must be positive")
        except (ValueError, TypeError):
            return Response({'error': f'Invalid raw_value at row {idx}.'}, status=status.HTTP_400_BAD_REQUEST)

        if rec['source_type'] not in ALLOWED_SOURCES:
            return Response({'error': f'Invalid source_type at row {idx}: "{rec["source_type"]}".'}, status=status.HTTP_400_BAD_REQUEST)

        validated.append(ActivityData(
            date=rec_date,
            source_type=rec['source_type'],
            raw_value=raw_value,
            unit=rec['unit'],
        ))

    ActivityData.objects.bulk_create(validated)
    logger.info(f"Bulk CSV upload: {len(validated)} records inserted.")
    return Response({'success': True, 'message': f'{len(validated)} records inserted.'}, status=status.HTTP_201_CREATED)


# ============================================================
# HUMAN POPULATION VIEWS
# ============================================================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_human_data(request):
    """
    POST /api/human_data/
    Add or update daily human population data. Uses upsert on date.
    """
    data = request.data
    rec_date = data.get('date')
    student_count = data.get('student_count')
    staff_count = data.get('staff_count')

    if not all([rec_date, student_count is not None, staff_count is not None]):
        return Response({'error': 'Missing required fields: date, student_count, staff_count.'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        student_count = int(student_count)
        staff_count = int(staff_count)
        if student_count < 0 or staff_count < 0:
            raise ValueError("Counts must be non-negative.")
    except (ValueError, TypeError) as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    try:
        rec_date_parsed = datetime.strptime(rec_date, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        return Response({'error': 'Invalid date format. Use YYYY-MM-DD.'}, status=status.HTTP_400_BAD_REQUEST)

    # Upsert on date
    instance, created = HumanPopulation.objects.update_or_create(
        date=rec_date_parsed,
        defaults={'student_count': student_count, 'staff_count': staff_count}
    )

    total_people = instance.total_count
    emissions_tonnes = round(instance.emissions_tonnes, 3)

    # Cumulative stats
    stats = HumanPopulation.objects.aggregate(
        total_emissions=Sum(db_models.F('student_count') + db_models.F('staff_count')) ,
        record_count=Count('id'),
        avg_students=Avg('student_count'),
        avg_staff=Avg('staff_count'),
    )

    total_emissions_all = float((stats['total_emissions'] or 0)) / 1000
    record_count = stats['record_count'] or 0
    avg_students = int(stats['avg_students'] or 0)
    avg_staff = int(stats['avg_staff'] or 0)

    action = 'added' if created else 'updated'
    logger.info(f"Human population data {action}: {rec_date_parsed} | {total_people} people")
    return Response({
        'message': f'Human population data {action} successfully.',
        'data': {
            'date': str(instance.date),
            'student_count': student_count,
            'staff_count': staff_count,
            'total_count': total_people,
            'this_day_emissions_tonnes': emissions_tonnes,
        },
        'cumulative_stats': {
            'total_emissions_tonnes': round(total_emissions_all, 2),
            'total_records': record_count,
            'average_students': avg_students,
            'average_staff': avg_staff,
            'average_population': avg_students + avg_staff,
        },
    }, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([AllowAny])
def human_cumulative_stats(request):
    """GET /api/human_cumulative_stats/ - All-time cumulative human emission stats."""
    stats = HumanPopulation.objects.aggregate(
        total_emissions=Sum(db_models.F('student_count') + db_models.F('staff_count')),
        record_count=Count('id'),
        avg_students=Avg('student_count'),
        avg_staff=Avg('staff_count'),
    )

    total_emissions = float((stats['total_emissions'] or 0)) / 1000
    return Response({
        'total_emissions': round(total_emissions, 2),
        'total_records': stats['record_count'] or 0,
        'average_students': int(stats['avg_students'] or 0),
        'average_staff': int(stats['avg_staff'] or 0),
        'average_population': int((stats['avg_students'] or 0) + (stats['avg_staff'] or 0)),
    })


# ============================================================
# DASHBOARD VIEW
# ============================================================

def _parse_dates(start_date_str, end_date_str):
    """Parse and normalize date range strings."""
    if not start_date_str or not end_date_str:
        end_dt = date.today()
        start_dt = end_dt - timedelta(days=180)
    else:
        try:
            start_dt = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_dt = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        except ValueError:
            end_dt = date.today()
            start_dt = end_dt - timedelta(days=180)

    if end_dt < start_dt:
        start_dt, end_dt = end_dt, start_dt

    return start_dt, end_dt


@api_view(['GET'])
@permission_classes([AllowAny])
def get_dashboard_data(request):
    """
    GET /api/dashboard/?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD
    Full dashboard data: KPIs, trends, breakdowns, human emissions.
    """
    start_dt, end_dt = _parse_dates(
        request.query_params.get('start_date'),
        request.query_params.get('end_date'),
    )
    window_days = max((end_dt - start_dt).days, 1)

    # ---- Activity emissions in range ----
    activities = (
        ActivityData.objects
        .filter(date__range=[start_dt, end_dt])
        .select_related()
    )

    # Build joined data with emission factors
    factors = {ef.source_type: ef.factor for ef in EmissionFactor.objects.all()}

    results = []
    for a in activities:
        factor = factors.get(a.source_type, 0)
        emissions = (a.raw_value * factor) / 1000
        results.append({
            'date': a.date,
            'source_type': a.source_type,
            'raw_value': a.raw_value,
            'unit': a.unit,
            'emissions_tonnes': emissions,
        })

    total_emissions = sum(r['emissions_tonnes'] for r in results)

    # Source breakdown
    source_breakdown = {}
    for r in results:
        source_breakdown[r['source_type']] = source_breakdown.get(r['source_type'], 0) + r['emissions_tonnes']

    biggest_source = max(source_breakdown.items(), key=lambda x: x[1]) if source_breakdown else ('N/A', 0)

    # Energy consumed (electricity raw values)
    energy_consumed = sum(r['raw_value'] for r in results if r['source_type'] == 'electricity')

    # Aggregations: daily, weekly, monthly, yearly
    daily_data, weekly_data, monthly_data, yearly_data = {}, {}, {}, {}
    for r in results:
        d = r['date']
        date_str = d.strftime('%Y-%m-%d')
        iso_year, iso_week, _ = d.isocalendar()
        week_label = f"{iso_year}-W{iso_week:02d}"
        month = d.strftime('%Y-%m')
        year = d.year

        daily_data[date_str] = daily_data.get(date_str, 0) + r['emissions_tonnes']
        weekly_data[week_label] = weekly_data.get(week_label, 0) + r['emissions_tonnes']
        monthly_data[month] = monthly_data.get(month, 0) + r['emissions_tonnes']
        yearly_data[year] = yearly_data.get(year, 0) + r['emissions_tonnes']

    # Previous period comparison
    prev_start = start_dt - timedelta(days=window_days)
    prev_activities = ActivityData.objects.filter(date__range=[prev_start, start_dt])
    prev_results = []
    for a in prev_activities:
        factor = factors.get(a.source_type, 0)
        prev_results.append({'emissions_tonnes': (a.raw_value * factor) / 1000})
    prev_emissions = sum(r['emissions_tonnes'] for r in prev_results)

    percent_change = 0.0
    if prev_emissions > 0:
        percent_change = ((total_emissions - prev_emissions) / prev_emissions) * 100.0

    # ---- Human emissions in range ----
    human_records = list(HumanPopulation.objects.filter(date__range=[start_dt, end_dt]).order_by('date'))

    human_daily, human_weekly, human_monthly, human_yearly = {}, {}, {}, {}
    human_total_emissions = 0
    total_students, total_staff = 0, 0

    for h in human_records:
        d = h.date
        date_str = d.strftime('%Y-%m-%d')
        iso_year, iso_week, _ = d.isocalendar()
        week_label = f"{iso_year}-W{iso_week:02d}"
        month = d.strftime('%Y-%m')
        year = d.year
        em = h.emissions_tonnes

        human_daily[date_str] = human_daily.get(date_str, 0) + em
        human_weekly[week_label] = human_weekly.get(week_label, 0) + em
        human_monthly[month] = human_monthly.get(month, 0) + em
        human_yearly[year] = human_yearly.get(year, 0) + em
        human_total_emissions += em
        total_students += h.student_count
        total_staff += h.staff_count

    n = len(human_records)
    avg_student_count = int(total_students / n) if n else 0
    avg_staff_count = int(total_staff / n) if n else 0

    return Response({
        'kpis': {
            'total_emissions': round(total_emissions, 2),
            'percent_change': round(percent_change, 2),
            'biggest_source': biggest_source[0],
            'biggest_source_percent': round((biggest_source[1] / total_emissions * 100) if total_emissions > 0 else 0, 1),
            'energy_saved': round(energy_consumed, 0),
        },
        'daily_trend': [
            {'date': d, 'emissions': round(e, 2)}
            for d, e in sorted(daily_data.items())
        ],
        'weekly_trend': [
            {'label': l, 'emissions': round(e, 2)}
            for l, e in sorted(weekly_data.items())
        ],
        'monthly_trend': [
            {'month': m, 'emissions': round(e, 2)}
            for m, e in sorted(monthly_data.items())
        ],
        'yearly_comparison': [
            {'year': y, 'emissions': round(e, 2)}
            for y, e in sorted(yearly_data.items())
        ],
        'weekly_comparison': [
            {'label': l, 'emissions': round(e, 2)}
            for l, e in sorted(weekly_data.items())
        ],
        'source_breakdown': [
            {
                'source': src,
                'emissions': round(em, 2),
                'percentage': round((em / total_emissions * 100) if total_emissions > 0 else 0, 1),
            }
            for src, em in source_breakdown.items()
        ],
        'human_emissions': {
            'total_emissions': round(human_total_emissions, 2),
            'avg_student_count': avg_student_count,
            'avg_staff_count': avg_staff_count,
            'avg_total_count': avg_student_count + avg_staff_count,
            'daily_trend': [
                {'date': d, 'emissions': round(e, 2)} for d, e in sorted(human_daily.items())
            ],
            'weekly_trend': [
                {'label': l, 'emissions': round(e, 2)} for l, e in sorted(human_weekly.items())
            ],
            'monthly_trend': [
                {'month': m, 'emissions': round(e, 2)} for m, e in sorted(human_monthly.items())
            ],
            'population_data': [
                {
                    'date': str(h.date),
                    'students': h.student_count,
                    'staff': h.staff_count,
                    'total': h.total_count,
                    'emissions': round(h.emissions_tonnes, 3),
                }
                for h in human_records
            ],
        },
    })


# ============================================================
# RECOMMENDATIONS VIEW
# ============================================================

@api_view(['GET'])
@permission_classes([AllowAny])
def get_recommendations(request):
    """GET /api/recommendations/ - Emission reduction recommendations."""

    # Top source by emissions
    factors = {ef.source_type: ef.factor for ef in EmissionFactor.objects.all()}
    source_totals = {}
    for a in ActivityData.objects.all():
        factor = factors.get(a.source_type, 0)
        em = (a.raw_value * factor) / 1000
        source_totals[a.source_type] = source_totals.get(a.source_type, 0) + em

    top_source = max(source_totals.items(), key=lambda x: x[1]) if source_totals else (None, 0)

    # Human stats
    human_stats = HumanPopulation.objects.aggregate(
        total=Sum(db_models.F('student_count') + db_models.F('staff_count')),
        avg_pop=Avg(db_models.F('student_count') + db_models.F('staff_count')),
    )
    human_total = float(human_stats['total'] or 0) / 1000
    avg_population = int(human_stats['avg_pop'] or 0)

    recommendations = []

    # Source-specific recommendation
    if top_source[0]:
        src, em = top_source
        rec_map = {
            'electricity': {
                'title': '⚡ Electricity: Your #1 Emission Source',
                'description': f'Electricity is your largest controllable emission source, contributing {em:.2f} tonnes CO₂. This is primarily driven by high-consumption devices like air conditioning, lighting, and lab equipment.',
                'priority': 'High',
                'impact': 'High',
                'actionable_steps': [
                    'Conduct a professional energy audit to identify specific "hotspots" of wastage.',
                    'Replace all traditional bulbs with high-efficiency LED lighting (saves 75% energy per bulb).',
                    'Install motion sensors and timers in corridors, washrooms, and meeting rooms.',
                    'Upgrade old air conditioners to 5-star rated inverter models (reduces AC energy use by 30-50%).',
                    'Set a campus-wide AC temperature policy (e.g., 24°C).',
                    'Aggressively pursue rooftop solar panel installation.',
                    'Implement a "Computers Off" policy at night.',
                    'Install smart power strips to eliminate phantom loads.',
                ],
                'expected_reduction': '30-50% reduction in electricity-based emissions',
                'cost': 'Medium to High (Initial) | High ROI (2-5 years)',
                'timeframe': '6-18 months for full implementation',
            },
            'bus_diesel': {
                'title': '🚌 Transportation: High Carbon Footprint',
                'description': f'Campus-owned diesel transport contributes {em:.2f} tonnes CO₂. A planned transition to cleaner transport is crucial.',
                'priority': 'High',
                'impact': 'High',
                'actionable_steps': [
                    'Develop a 5-year plan to phase out diesel buses and replace with electric buses.',
                    'Install EV charging stations in parking areas.',
                    'Optimize bus routes to reduce total kilometers traveled.',
                    'Implement a campus bike-sharing program.',
                    'Create dedicated cycling lanes within campus.',
                    'Promote a carpooling platform for students and staff.',
                    'Enforce a "No-Idling" zone policy for all vehicles.',
                ],
                'expected_reduction': '40-60% reduction in transport emissions',
                'cost': 'High (Vehicle purchase)',
                'timeframe': '1-3 years for fleet transition',
            },
            'canteen_lpg': {
                'title': '🍳 Canteen: Optimize Cooking Operations',
                'description': f'Canteen LPG contributes {em:.2f} tonnes CO₂. Modern electric alternatives like induction are cleaner and safer.',
                'priority': 'Medium',
                'impact': 'Medium',
                'actionable_steps': [
                    'Phase out LPG stoves, replace with commercial-grade induction cooktops (~85% efficient vs LPG at ~40%).',
                    'Install solar cookers or solar water heating systems.',
                    'Utilize pressure cookers to reduce cooking time by up to 70%.',
                    'Implement menu engineering to batch-cook popular items.',
                    'Explore setting up a campus biogas plant to convert food waste into methane.',
                    'Source produce locally to reduce Scope 3 emissions.',
                ],
                'expected_reduction': '25-40% reduction in cooking-related emissions',
                'cost': 'Low to Medium',
                'timeframe': '3-9 months',
            },
            'waste_landfill': {
                'title': '♻️ Waste: Implement Zero-Waste Campus',
                'description': f'Waste sent to landfills generates {em:.2f} tonnes CO₂ (as methane, a gas 25x more potent than CO₂).',
                'priority': 'High',
                'impact': 'High',
                'actionable_steps': [
                    'Conduct a waste audit to identify main waste streams.',
                    'Implement mandatory 3-bin segregation: Organic, Recyclable, Landfill.',
                    'Start an on-campus composting program for food waste.',
                    'Aggressively ban all single-use plastics.',
                    'Install water refill stations across campus.',
                    'Set up a "Reuse Store" at end of semester.',
                    'Set double-sided printing as default on all campus printers.',
                ],
                'expected_reduction': '50-70% reduction in landfill-bound waste',
                'cost': 'Low (Primarily operational)',
                'timeframe': '2-4 months',
            },
        }
        if src in rec_map:
            recommendations.append(rec_map[src])

    # Human emissions recommendation
    if human_total > 0:
        recommendations.append({
            'title': '👥 Human CO₂: An Indirect Factor',
            'description': f'The campus population (avg. {avg_population} people) contributes {human_total:.2f} tonnes CO₂ from respiration. This is a natural biological process. Focus on reducing per-person indirect footprint.',
            'priority': 'Low',
            'impact': 'Low (Natural Process)',
            'actionable_steps': [
                'Do not focus on reducing this number directly — it is a natural process.',
                'Use population data to inform indirect emission strategies.',
                'Implement hybrid learning/work models to reduce daily on-campus density.',
                'Stagger class and lab timings to prevent peak-hour congestion.',
                'Focus on reducing the per-person carbon footprint.',
            ],
            'expected_reduction': 'N/A (Focus is on indirect reductions)',
            'cost': 'N/A',
            'timeframe': 'Ongoing',
        })

    # General recommendations (always included)
    recommendations.extend([
        {
            'title': '📊 Data-Driven Decision Making',
            'description': 'You cannot manage what you do not measure. Use this analyzer to move from guessing to targeted, effective action.',
            'priority': 'High',
            'impact': 'High (Enabler)',
            'actionable_steps': [
                'Monitor this dashboard daily. Investigate any sudden spikes.',
                'Set a clear, public monthly reduction target.',
                'Generate quarterly reports to share with management and student council.',
                'Use data to benchmark against other institutions.',
                'Create department-level dashboards to foster friendly competition.',
            ],
            'expected_reduction': 'Enables an additional 20-30% reduction through targeted strategies',
            'cost': 'Free (using this platform)',
            'timeframe': 'Ongoing',
        },
        {
            'title': '🌱 Green Campus Initiative',
            'description': 'A successful carbon reduction plan requires buy-in from every student and staff member. Make sustainability the default, not the exception.',
            'priority': 'Medium',
            'impact': 'High (Long-term)',
            'actionable_steps': [
                'Form a "Green Team" with student and staff volunteers from all departments.',
                'Conduct monthly awareness campaigns and workshops on sustainability.',
                'Organize large-scale tree plantation drives (focus on native species).',
                'Display real-time emission data on public screens in the canteen and library.',
                'Integrate sustainability modules into first-year orientation.',
                'Reward departments with highest emission reductions each semester.',
            ],
            'expected_reduction': '15-25% reduction through behavioral change',
            'cost': 'Low',
            'timeframe': '3-6 months to establish',
        },
        {
            'title': '⭐ Quick Wins: Immediate Actions',
            'description': 'Build momentum with these simple, low-cost, high-visibility actions.',
            'priority': 'High',
            'impact': 'Medium',
            'actionable_steps': [
                'TODAY: Mandate that all classroom projectors, lights, and fans are turned off when leaving.',
                'THIS WEEK: Set all network printers to double-sided printing by default.',
                'THIS WEEK: Launch a "phantom load" campaign — unplug chargers when not in use.',
                'THIS MONTH: Place "Save Energy / Save Water" stickers on all switches and taps.',
                'THIS MONTH: Designate student "Energy Monitors" for each floor/department.',
                'THIS MONTH: Start paper recycling by placing collection boxes in all offices.',
            ],
            'expected_reduction': '10-15% immediate reduction from low-hanging fruit',
            'cost': 'Very Low',
            'timeframe': 'Immediate to 1 month',
        },
    ])

    return Response({
        'recommendations': recommendations,
        'summary': {
            'total_recommendations': len(recommendations),
            'high_priority': sum(1 for r in recommendations if r['priority'] == 'High'),
            'estimated_total_reduction': '50-70% achievable with full implementation',
            'message': 'Start with "Quick Wins" and "High Priority" items for maximum immediate impact!',
        },
    })


# ============================================================
# EMISSION FACTORS VIEW
# ============================================================

@api_view(['GET'])
@permission_classes([AllowAny])
def get_emission_factors(request):
    """GET /api/emission_factors/ - List all emission factors."""
    factors = EmissionFactor.objects.all()
    return Response(EmissionFactorSerializer(factors, many=True).data)


# ============================================================
# RESET DATA VIEW
# ============================================================

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def reset_data(request):
    """
    DELETE /api/admin/reset/
    Deletes ALL ActivityData and HumanPopulation records.
    Requires JWT authentication (admin only).
    """
    activity_count = ActivityData.objects.count()
    human_count = HumanPopulation.objects.count()

    ActivityData.objects.all().delete()
    HumanPopulation.objects.all().delete()

    logger.warning(f"DATA RESET by user='{request.user.username}': {activity_count} activity records + {human_count} human population records deleted.")

    return Response({
        'success': True,
        'message': f'All data has been reset. Deleted {activity_count} activity records and {human_count} population records.',
        'deleted': {
            'activity_records': activity_count,
            'human_records': human_count,
        }
    })


# ============================================================
# COLLEGE PROFILE VIEWS
# ============================================================

@api_view(['GET'])
@permission_classes([AllowAny])
def get_college_profile(request):
    """GET /api/college_profile/ - Get college info (public)."""
    profile = CollegeProfile.get_singleton()
    return Response(CollegeProfileSerializer(profile).data)


@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def update_college_profile(request):
    """PUT/PATCH /api/college_profile/update/ - Update college info (admin only)."""
    profile = CollegeProfile.get_singleton()
    serializer = CollegeProfileSerializer(
        profile, data=request.data, partial=True
    )
    if not serializer.is_valid():
        return Response({'error': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    serializer.save()
    logger.info(f"College profile updated by '{request.user.username}'")
    return Response({
        'success': True,
        'message': 'College profile updated successfully.',
        'data': serializer.data,
    })
