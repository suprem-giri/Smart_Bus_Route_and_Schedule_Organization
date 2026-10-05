"""
URL Configuration for bus_core application.
Maps views for Passenger, Transport Manager, Admin, Driver, and REST API.
"""

from django.urls import path
from .views import (
    passenger_views,
    auth_views,
    manager_views,
    admin_views,
    driver_views
)
from .api import views as api_views

urlpatterns = [
    # --- Passenger Portal (Public) ---
    path('', passenger_views.home_view, name='home'),
    path('route-search/', passenger_views.route_search_view, name='route_search'),
    path('routes/', passenger_views.routes_list_view, name='routes_list'),
    path('stops/', passenger_views.stops_list_view, name='stops_list'),

    # --- Authentication ---
    path('login/', auth_views.login_view, name='login'),
    path('register/', auth_views.register_view, name='register'),
    path('logout/', auth_views.logout_view, name='logout'),

    # --- Transport Manager Portal ---
    path('manager/', manager_views.manager_dashboard_view, name='manager_dashboard'),
    path('manager/demand/', manager_views.demand_records_view, name='manager_demand'),
    path('manager/optimize/', manager_views.optimize_schedule_view, name='manager_optimize'),
    path('manager/reports/', manager_views.optimization_reports_view, name='manager_reports'),
    path('manager/schedules/', manager_views.schedules_manage_view, name='manager_schedules'),

    # --- Admin Portal ---
    path('admin-panel/', admin_views.admin_dashboard_view, name='admin_dashboard'),
    path('admin-panel/buses/', admin_views.buses_manage_view, name='admin_buses'),
    path('admin-panel/drivers/', admin_views.drivers_manage_view, name='admin_drivers'),
    path('admin-panel/stops/', admin_views.stops_manage_view, name='admin_stops'),
    path('admin-panel/routes/', admin_views.routes_manage_view, name='admin_routes'),
    path('admin-panel/users/', admin_views.users_manage_view, name='admin_users'),

    # --- Driver Portal ---
    path('driver/', driver_views.driver_dashboard_view, name='driver_dashboard'),

    # --- REST API Endpoints ---
    path('api/stops/', api_views.StopListAPIView.as_view(), name='api_stops'),
    path('api/routes/', api_views.RouteListAPIView.as_view(), name='api_routes'),
    path('api/buses/', api_views.BusListAPIView.as_view(), name='api_buses'),
    path('api/shortest-path/', api_views.ShortestPathAPIView.as_view(), name='api_shortest_path'),
    path('api/demand/', api_views.DemandAPIView.as_view(), name='api_demand'),
    path('api/optimize/', api_views.OptimizeScheduleAPIView.as_view(), name='api_optimize'),
    path('api/optimization-results/', api_views.OptimizationResultsAPIView.as_view(), name='api_optimization_results'),
    path('api/live-buses/', api_views.LiveBusListAPIView.as_view(), name='api_live_buses'),
    path('api/trips/<str:trip_id>/location/', api_views.TripLocationAPIView.as_view(), name='api_trip_location'),
    path('api/trips/<str:trip_id>/status/', api_views.TripStatusUpdateAPIView.as_view(), name='api_trip_status_update'),
]
