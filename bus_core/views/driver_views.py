"""
Driver Portal Views: View Assigned Bus, Routes, Schedules, and Update Live Trip Status.
"""

from datetime import datetime
from django.shortcuts import render, redirect
from django.contrib import messages
from .auth_views import role_required
from ..database.repositories import (
    DriverRepository, BusRepository, ScheduleRepository, TripRepository,
    RouteRepository, StopRepository
)


@role_required(['admin', 'driver'])
def driver_dashboard_view(request):
    """Driver Dashboard: Assigned Bus, Route, and Today's Active Trips."""
    user = request.session.get('user', {})
    driver_repo = DriverRepository()
    bus_repo = BusRepository()
    trip_repo = TripRepository()
    route_repo = RouteRepository()
    stop_repo = StopRepository()
    sched_repo = ScheduleRepository()

    # Find driver record matching current user's name or full_name
    driver = driver_repo.find_one({"name": user.get('full_name')})
    if not driver:
        # Fallback to first active driver if logged in as admin or demo
        drivers = driver_repo.list_active()
        driver = drivers[0] if drivers else None

    driver_id = driver.get('driver_id') if driver else None
    assigned_bus = None
    if driver and driver.get('assigned_bus_id'):
        assigned_bus = bus_repo.get_by_id(driver['assigned_bus_id'])
    elif driver:
        # Search bus where assigned_driver_id matches
        assigned_bus = bus_repo.find_one({'assigned_driver_id': driver['driver_id']})

    # Today's trips
    today = datetime.utcnow().strftime('%Y-%m-%d')
    trips = trip_repo.find_all({'driver_id': driver_id, 'date': today}) if driver_id else []
    if not trips and driver_id:
        trips = trip_repo.list_by_driver(driver_id)[:10]

    # Handle status updates
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'update_trip_status':
            trip_id = request.POST.get('trip_id')
            new_status = request.POST.get('status')
            notes = request.POST.get('notes', '')
            delay = int(request.POST.get('delay_minutes', 0))
            current_stop = request.POST.get('current_stop_id')

            trip_repo.update_status(
                trip_id=trip_id,
                status=new_status,
                notes=notes,
                current_stop_id=current_stop,
                delay_minutes=delay
            )
            messages.success(request, f"Trip {trip_id} status updated to '{new_status}'.")
            return redirect('driver_dashboard')

        elif action == 'create_trip':
            # Driver starts a new trip run
            schedule_id = request.POST.get('schedule_id', '')
            route_id = request.POST.get('route_id')
            now_time = datetime.now().strftime('%H:%M')
            new_trip = {
                'schedule_id': schedule_id,
                'route_id': route_id,
                'bus_id': assigned_bus.get('bus_id') if assigned_bus else '',
                'driver_id': driver_id,
                'date': today,
                'status': 'In Transit',
                'scheduled_departure': now_time,
                'actual_departure': now_time,
                'current_stop_id': request.POST.get('start_stop_id', ''),
                'delay_minutes': 0,
                'notes': 'Trip initiated by driver.'
            }
            trip_repo.create(new_trip)
            messages.success(request, "New trip started successfully!")
            return redirect('driver_dashboard')

    routes = route_repo.list_active()
    stops = stop_repo.list_all()

    context = {
        'driver': driver,
        'assigned_bus': assigned_bus,
        'trips': trips,
        'routes': routes,
        'stops': stops,
        'can_track_location': user.get('role') == 'driver',
    }
    return render(request, 'driver/dashboard.html', context)
