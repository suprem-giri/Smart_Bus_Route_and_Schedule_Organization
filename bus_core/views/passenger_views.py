"""
Passenger-facing views for Route Search, Interactive Network Maps, Timetables, and Stops.
"""

from django.shortcuts import render
from django.http import JsonResponse
from ..database.repositories import StopRepository, RouteRepository, BusRepository, ScheduleRepository
from ..algorithms.graph import TransitGraph
from ..algorithms.dijkstra import dijkstra_shortest_path


def home_view(request):
    """Passenger Homepage & Transit Network Overview."""
    stop_repo = StopRepository()
    route_repo = RouteRepository()
    bus_repo = BusRepository()

    stops = stop_repo.list_all()
    routes = route_repo.list_active()
    buses = bus_repo.list_all()

    context = {
        'total_stops': len(stops),
        'total_routes': len(routes),
        'total_buses': len(buses),
        'stops': stops,
        'routes': routes[:6],
    }
    return render(request, 'passenger/home.html', context)


def route_search_view(request):
    """
    Find Minimum-Cost Path between bus stops using Algorithm 1: Dijkstra.
    Supports distance-based and travel time-based optimization.
    """
    stop_repo = StopRepository()
    route_repo = RouteRepository()

    stops = sorted(stop_repo.list_all(), key=lambda s: s.get('name', ''))
    source_id = request.GET.get('source', '')
    destination_id = request.GET.get('destination', '')
    metric = request.GET.get('metric', 'distance')

    result = None
    if source_id and destination_id:
        graph = TransitGraph.from_database(stop_repo, route_repo)
        result = dijkstra_shortest_path(graph, source_id, destination_id, metric=metric)

        # If AJAX request, return JSON
        if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.GET.get('format') == 'json':
            return JsonResponse(result)

    context = {
        'stops': stops,
        'source_id': source_id,
        'destination_id': destination_id,
        'metric': metric,
        'result': result,
    }
    return render(request, 'passenger/route_search.html', context)


def routes_list_view(request):
    """List of all bus routes with details and stops."""
    route_repo = RouteRepository()
    stop_repo = StopRepository()
    sched_repo = ScheduleRepository()

    routes = route_repo.list_active()
    stops_map = {s['stop_id']: s for s in stop_repo.list_all()}

    enriched_routes = []
    for r in routes:
        stops_in_route = [stops_map.get(sid, {'name': sid, 'stop_id': sid}) for sid in r.get('stops', [])]
        schedules = sched_repo.list_by_route(r['route_id'])
        enriched_routes.append({
            'route': r,
            'stops': stops_in_route,
            'schedules': schedules
        })

    context = {
        'routes': enriched_routes
    }
    return render(request, 'passenger/routes_list.html', context)


def stops_list_view(request):
    """Bus Stops Directory with Interactive Map."""
    stop_repo = StopRepository()
    route_repo = RouteRepository()

    stops = stop_repo.list_all()
    routes = route_repo.list_active()

    # Calculate routes serving each stop
    stop_routes = {s['stop_id']: [] for s in stops}
    for r in routes:
        for sid in r.get('stops', []):
            if sid in stop_routes:
                stop_routes[sid].append(r['route_number'])

    enriched_stops = []
    for s in stops:
        s_copy = dict(s)
        s_copy['serving_routes'] = stop_routes.get(s['stop_id'], [])
        enriched_stops.append(s_copy)

    context = {
        'stops': enriched_stops
    }
    return render(request, 'passenger/stops_list.html', context)
