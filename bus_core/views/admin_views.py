"""
Admin Views: Complete CRUD Management for Buses, Drivers, Bus Stops, Routes, and Users.
"""

from django.shortcuts import render, redirect
from django.contrib import messages
from .auth_views import role_required
from ..database.repositories import (
    BusRepository, DriverRepository, StopRepository, RouteRepository,
    UserRepository, TripRepository
)


@role_required(['admin'])
def admin_dashboard_view(request):
    """Admin Master Overview."""
    bus_repo = BusRepository()
    driver_repo = DriverRepository()
    stop_repo = StopRepository()
    route_repo = RouteRepository()
    user_repo = UserRepository()
    trip_repo = TripRepository()

    context = {
        'total_buses': bus_repo.count(),
        'total_drivers': driver_repo.count(),
        'total_stops': stop_repo.count(),
        'total_routes': route_repo.count(),
        'total_users': user_repo.count(),
        'total_trips': trip_repo.count(),
        'available_buses': bus_repo.count({'status': 'Available'}),
        'active_drivers': driver_repo.count({'status': 'Active'}),
    }
    return render(request, 'admin/dashboard.html', context)


@role_required(['admin'])
def buses_manage_view(request):
    """Bus Fleet CRUD."""
    bus_repo = BusRepository()
    driver_repo = DriverRepository()
    route_repo = RouteRepository()

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'create':
            bus_data = {
                'bus_number': request.POST.get('bus_number').strip(),
                'registration_number': request.POST.get('registration_number').strip(),
                'capacity': int(request.POST.get('capacity', 40)),
                'model': request.POST.get('model', 'Standard Urban Bus').strip(),
                'bus_type': request.POST.get('bus_type', 'Standard'),
                'status': request.POST.get('status', 'Available'),
                'assigned_driver_id': request.POST.get('assigned_driver_id', ''),
                'assigned_route_id': request.POST.get('assigned_route_id', ''),
            }
            bus_repo.create(bus_data)
            messages.success(request, f"Bus {bus_data['bus_number']} created.")
        elif action == 'update':
            bus_id = request.POST.get('bus_id')
            update_data = {
                'capacity': int(request.POST.get('capacity', 40)),
                'model': request.POST.get('model').strip(),
                'bus_type': request.POST.get('bus_type'),
                'status': request.POST.get('status'),
                'assigned_driver_id': request.POST.get('assigned_driver_id', ''),
                'assigned_route_id': request.POST.get('assigned_route_id', ''),
            }
            bus_repo.update({'bus_id': bus_id}, update_data)
            messages.success(request, f"Bus {bus_id} updated.")
        elif action == 'delete':
            bus_id = request.POST.get('bus_id')
            bus_repo.delete({'bus_id': bus_id})
            messages.info(request, f"Bus {bus_id} deleted.")
        return redirect('admin_buses')

    buses = bus_repo.list_all()
    drivers = driver_repo.list_all()
    routes = route_repo.list_all()
    return render(request, 'admin/buses.html', {'buses': buses, 'drivers': drivers, 'routes': routes})


@role_required(['admin'])
def drivers_manage_view(request):
    """Driver Directory CRUD."""
    driver_repo = DriverRepository()
    bus_repo = BusRepository()

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'create':
            driver_data = {
                'name': request.POST.get('name').strip(),
                'license_number': request.POST.get('license_number').strip(),
                'phone': request.POST.get('phone').strip(),
                'experience_years': int(request.POST.get('experience_years', 3)),
                'status': request.POST.get('status', 'Active'),
                'assigned_bus_id': request.POST.get('assigned_bus_id', '')
            }
            driver_repo.create(driver_data)
            messages.success(request, f"Driver {driver_data['name']} added.")
        elif action == 'update':
            driver_id = request.POST.get('driver_id')
            update_data = {
                'name': request.POST.get('name').strip(),
                'phone': request.POST.get('phone').strip(),
                'experience_years': int(request.POST.get('experience_years', 3)),
                'status': request.POST.get('status'),
                'assigned_bus_id': request.POST.get('assigned_bus_id', '')
            }
            driver_repo.update({'driver_id': driver_id}, update_data)
            messages.success(request, f"Driver {driver_id} updated.")
        elif action == 'delete':
            driver_id = request.POST.get('driver_id')
            driver_repo.delete({'driver_id': driver_id})
            messages.info(request, f"Driver {driver_id} removed.")
        return redirect('admin_drivers')

    drivers = driver_repo.list_all()
    buses = bus_repo.list_all()
    return render(request, 'admin/drivers.html', {'drivers': drivers, 'buses': buses})


@role_required(['admin'])
def stops_manage_view(request):
    """Bus Stops CRUD with GPS Coordinates."""
    stop_repo = StopRepository()

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'create':
            facilities = [f.strip() for f in request.POST.get('facilities', '').split(',') if f.strip()]
            stop_data = {
                'name': request.POST.get('name').strip(),
                'code': request.POST.get('code', '').strip().upper(),
                'latitude': float(request.POST.get('latitude', 27.7000)),
                'longitude': float(request.POST.get('longitude', 85.3000)),
                'zone': request.POST.get('zone', 'Central').strip(),
                'facilities': facilities,
                'is_terminal': request.POST.get('is_terminal') == 'on'
            }
            stop_repo.create(stop_data)
            messages.success(request, f"Stop '{stop_data['name']}' added.")
        elif action == 'update':
            stop_id = request.POST.get('stop_id')
            facilities = [f.strip() for f in request.POST.get('facilities', '').split(',') if f.strip()]
            update_data = {
                'name': request.POST.get('name').strip(),
                'code': request.POST.get('code', '').strip().upper(),
                'latitude': float(request.POST.get('latitude', 27.7000)),
                'longitude': float(request.POST.get('longitude', 85.3000)),
                'zone': request.POST.get('zone', 'Central').strip(),
                'facilities': facilities,
                'is_terminal': request.POST.get('is_terminal') == 'on'
            }
            stop_repo.update({'stop_id': stop_id}, update_data)
            messages.success(request, f"Stop {stop_id} updated.")
        elif action == 'delete':
            stop_id = request.POST.get('stop_id')
            stop_repo.delete({'stop_id': stop_id})
            messages.info(request, f"Stop {stop_id} deleted.")
        return redirect('admin_stops')

    stops = stop_repo.list_all()
    return render(request, 'admin/stops.html', {'stops': stops})


@role_required(['admin'])
def routes_manage_view(request):
    """Route Management with Ordered Stops Sequence."""
    route_repo = RouteRepository()
    stop_repo = StopRepository()

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'create':
            stops_raw = request.POST.getlist('stops')
            if not stops_raw:
                stops_raw = [s.strip() for s in request.POST.get('stops_csv', '').split(',') if s.strip()]

            route_data = {
                'route_number': request.POST.get('route_number').strip(),
                'route_name': request.POST.get('route_name').strip(),
                'stops': stops_raw,
                'total_distance_km': float(request.POST.get('total_distance_km', 15.0)),
                'estimated_duration_mins': int(request.POST.get('estimated_duration_mins', 45)),
                'base_fare': float(request.POST.get('base_fare', 20.0)),
                'active': request.POST.get('active') == 'on'
            }
            route_repo.create(route_data)
            messages.success(request, f"Route '{route_data['route_name']}' created.")
        elif action == 'delete':
            route_id = request.POST.get('route_id')
            route_repo.delete({'route_id': route_id})
            messages.info(request, f"Route {route_id} deleted.")
        return redirect('admin_routes')

    routes = route_repo.list_all()
    stops = stop_repo.list_all()
    return render(request, 'admin/routes.html', {'routes': routes, 'stops': stops})


@role_required(['admin'])
def users_manage_view(request):
    """User and Role Management."""
    user_repo = UserRepository()

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'update_role':
            user_id = request.POST.get('user_id')
            new_role = request.POST.get('role')
            user_repo.update({'user_id': user_id}, {'role': new_role})
            messages.success(request, f"User {user_id} role updated to {new_role}.")
        elif action == 'delete':
            user_id = request.POST.get('user_id')
            user_repo.delete({'user_id': user_id})
            messages.info(request, f"User {user_id} deleted.")
        return redirect('admin_users')

    users = user_repo.find_all(sort=[("created_at", -1)])
    return render(request, 'admin/users.html', {'users': users})
