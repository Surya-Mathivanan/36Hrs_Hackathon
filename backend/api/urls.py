from django.urls import path
from . import views

urlpatterns = [
    # Auth
    path('auth/login/', views.login_view, name='api-login'),
    path('auth/refresh/', views.refresh_token_view, name='api-token-refresh'),
    path('auth/me/', views.me_view, name='api-me'),

    # Dashboard & Public endpoints
    path('dashboard/', views.get_dashboard_data, name='api-dashboard'),
    path('recommendations/', views.get_recommendations, name='api-recommendations'),
    path('emission_factors/', views.get_emission_factors, name='api-emission-factors'),
    path('human_cumulative_stats/', views.human_cumulative_stats, name='api-human-cumulative'),

    # Protected data entry endpoints
    path('data/', views.add_activity_data, name='api-add-data'),
    path('upload_csv/', views.upload_csv, name='api-upload-csv'),
    path('human_data/', views.add_human_data, name='api-human-data'),
    # Admin actions (JWT protected)
    path('admin/reset/', views.reset_data, name='api-reset-data'),

    # College profile (public GET, protected PUT)
    path('college_profile/', views.get_college_profile, name='api-college-profile'),
    path('college_profile/update/', views.update_college_profile, name='api-college-profile-update'),
]
