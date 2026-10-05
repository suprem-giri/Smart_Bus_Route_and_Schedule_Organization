"""
Transport Manager Views: Demand Management, Optimization Execution, Timetable Scheduling, and Reports.
"""

from datetime import datetime
import json
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib import messages
from .auth_views import role_required
from ..database.repositories import (
    RouteRepository, BusRepository, StopRepository, ScheduleRepository,
    DemandRepository, OptimizationResultRepository, DriverRepository
)
from ..algorithms.optimizer import run_fleet_optimization


@role_required(['admin', 'manager'])
def manager_dashboard_view(request):
    """Manager Dashboard with Fleet & Demand Analytics."""
    route_repo = RouteRepository()
    bus_repo = BusRepository()
    demand_repo = DemandRepository()
    opt_repo = OptimizationResultRepository()

    routes = route_repo.list_active()
    buses = bus_repo.list_all()
    recent_opts = opt_repo.list_recent(limit=5)
    latest_opt = recent_opts[0] if recent_opts else None

    # Aggregate demand
    demand_by_route = demand_repo.get_aggregate_demand_by_route()
    total_demand_passengers = sum(d['total_passengers'] for d in demand_by_route)

    # Route names map for charts
    routes_map = {r['route_id']: r.get('route_number', r['route_id']) for r in routes}

    chart_labels = [routes_map.get(d['route_id'], d['route_id']) for d in demand_by_route[:8]]
    chart_data = [d['total_passengers'] for d in demand_by_route[:8]]

    context = {
        'total_routes': len(routes),
        'total_buses': len(buses),
        'total_demand_passengers': total_demand_passengers,
        'recent_opts': recent_opts,
        'latest_opt': latest_opt,
        'chart_labels_json': json.dumps(chart_labels),
        'chart_data_json': json.dumps(chart_data),
    }
    return render(request, 'manager/dashboard.html', context)


@role_required(['admin', 'manager'])
def demand_records_view(request):
    """View and Add Passenger Demand Records."""
    demand_repo = DemandRepository()
    route_repo = RouteRepository()
    stop_repo = StopRepository()

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'add_demand':
            route_id = request.POST.get('route_id')
            stop_id = request.POST.get('stop_id')
            date = request.POST.get('date') or datetime.utcnow().strftime('%Y-%m-%d')
            time_period = request.POST.get('time_period', '08:00-09:00')
            try:
                passengers = int(request.POST.get('passenger_count', 0))
                if passengers < 0:
                    raise ValueError
            except ValueError:
                messages.error(request, "Passenger count must be a non-negative number.")
                return redirect('manager_demand')

            demand_repo.create({
                'route_id': route_id,
                'stop_id': stop_id,
                'date': date,
                'time_period': time_period,
                'passenger_count': passengers
            })
            messages.success(request, f"Demand record of {passengers} passengers added successfully.")
            return redirect('manager_demand')

        elif action == 'generate_simulation':
            # Generate realistic multi-period test demand records
            generate_simulated_demand()
            messages.success(request, "Simulated multi-period demand data successfully generated.")
            return redirect('manager_demand')

    # Filtering
    route_filter = request.GET.get('route_id')
    period_filter = request.GET.get('time_period')
    demand_records = demand_repo.list_by_route_and_period(route_id=route_filter, time_period=period_filter)

    routes = route_repo.list_active()
    stops = stop_repo.list_all()

    context = {
        'demand_records': demand_records[:100],
        'total_records_count': len(demand_records),
        'routes': routes,
        'stops': stops,
        'route_filter': route_filter,
        'period_filter': period_filter
    }
    return render(request, 'manager/demand.html', context)


def generate_simulated_demand():
    """Generates realistic passenger demand records across peaks and off-peak."""
    import random
    demand_repo = DemandRepository()
    route_repo = RouteRepository()

    routes = route_repo.list_active()
    today = datetime.utcnow().strftime('%Y-%m-%d')

    periods = {
        '08:00-09:00': (120, 260),  # Morning peak
        '09:00-10:00': (100, 220),  # Late morning
        '12:00-13:00': (40, 90),    # Midday off-peak
        '17:00-18:00': (140, 290),  # Evening peak
        '18:00-19:00': (90, 180),   # Post evening peak
    }

    records = []
    for r in routes:
        stops = r.get('stops', [])
        for period, (low, high) in periods.items():
            for s in stops[:4]:  # key boarding stops
                count = random.randint(low // len(stops[:4]), high // len(stops[:4]))
                records.append({
                    'route_id': r['route_id'],
                    'stop_id': s,
                    'date': today,
                    'time_period': period,
                    'passenger_count': count
                })

    demand_repo.batch_insert(records)


@role_required(['admin', 'manager'])
def optimize_schedule_view(request):
    """
    Runs Route and Schedule Optimization (Algorithms 2 & 3).
    Displays comparison with Baseline and quantitative improvement metrics.
    """
    time_period = request.GET.get('time_period', '08:00-09:00')
    scenario_name = request.GET.get('scenario_name', f"Peak Demand Optimization ({time_period})")

    opt_result = None
    if request.method == 'POST' or request.GET.get('run') == '1':
        opt_result = run_fleet_optimization(
            time_period=time_period,
            scenario_name=scenario_name
        )
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse(opt_result)

    # Load latest optimization run if not running a new one
    if not opt_result:
        opt_repo = OptimizationResultRepository()
        recent = opt_repo.list_recent(limit=1)
        if recent:
            opt_result = recent[0]

    context = {
        'time_period': time_period,
        'scenario_name': scenario_name,
        'opt_result': opt_result,
    }
    return render(request, 'manager/optimize.html', context)


@role_required(['admin', 'manager'])
def optimization_reports_view(request):
    """Comparative Reports with Chart.js visualization."""
    opt_repo = OptimizationResultRepository()
    opt_id = request.GET.get('opt_id')

    if opt_id:
        result = opt_repo.get_by_id(opt_id)
    else:
        recent = opt_repo.list_recent(limit=1)
        result = recent[0] if recent else None

    all_opts = opt_repo.list_recent(limit=10)

    # Chart data extraction
    labels = []
    baseline_waits = []
    opt_waits = []
    baseline_utils = []
    opt_utils = []

    if result and 'route_comparison' in result:
        for rc in result['route_comparison']:
            labels.append(rc.get('route_name', rc.get('route_id', '')))
            baseline_waits.append(rc.get('baseline_waiting_mins', 0))
            opt_waits.append(rc.get('optimized_waiting_mins', 0))
            baseline_utils.append(rc.get('baseline_utilization_pct', 0))
            opt_utils.append(rc.get('optimized_utilization_pct', 0))

    context = {
        'result': result,
        'all_opts': all_opts,
        'chart_labels_json': json.dumps(labels),
        'chart_baseline_waits_json': json.dumps(baseline_waits),
        'chart_opt_waits_json': json.dumps(opt_waits),
        'chart_baseline_utils_json': json.dumps(baseline_utils),
        'chart_opt_utils_json': json.dumps(opt_utils),
    }
    return render(request, 'manager/reports.html', context)


@role_required(['admin', 'manager'])
def schedules_manage_view(request):
    """Timetable & Schedule Management."""
    sched_repo = ScheduleRepository()
    route_repo = RouteRepository()
    bus_repo = BusRepository()
    driver_repo = DriverRepository()

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'add_schedule':
            sched_repo.create({
                'route_id': request.POST.get('route_id'),
                'bus_id': request.POST.get('bus_id'),
                'driver_id': request.POST.get('driver_id'),
                'departure_time': request.POST.get('departure_time'),
                'arrival_time': request.POST.get('arrival_time'),
                'frequency_mins': int(request.POST.get('frequency_mins', 20)),
                'day_of_week': request.POST.get('day_of_week', 'All Days'),
                'status': 'Active'
            })
            messages.success(request, "Schedule added successfully.")
            return redirect('manager_schedules')

        elif action == 'delete_schedule':
            sched_id = request.POST.get('schedule_id')
            sched_repo.delete({'schedule_id': sched_id})
            messages.info(request, f"Schedule {sched_id} deleted.")
            return redirect('manager_schedules')

    schedules = sched_repo.list_all()
    routes = route_repo.list_active()
    buses = bus_repo.list_all()
    drivers = driver_repo.list_active()

    context = {
        'schedules': schedules,
        'routes': routes,
        'buses': buses,
        'drivers': drivers,
    }
    return render(request, 'manager/schedules.html', context)
