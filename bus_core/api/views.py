"""
Django REST Framework API ViewSets and Endpoints for Smart Public Bus System.
"""

import math
from datetime import datetime, timedelta, timezone
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from ..database.repositories import (
    StopRepository, RouteRepository, BusRepository, DriverRepository,
    ScheduleRepository, DemandRepository, OptimizationResultRepository, TripRepository
)
from ..algorithms.graph import TransitGraph
from ..algorithms.dijkstra import dijkstra_shortest_path
from ..algorithms.optimizer import run_fleet_optimization


def _distance_km(point_a, point_b):
    """Return the great-circle distance between two latitude/longitude pairs."""
    earth_radius_km = 6371.0
    lat_a, lon_a = map(math.radians, point_a)
    lat_b, lon_b = map(math.radians, point_b)
    lat_delta = lat_b - lat_a
    lon_delta = lon_b - lon_a
    value = (
        math.sin(lat_delta / 2) ** 2
        + math.cos(lat_a) * math.cos(lat_b) * math.sin(lon_delta / 2) ** 2
    )
    return 2 * earth_radius_km * math.asin(math.sqrt(value))


def _estimate_stop_arrivals(trip, route, stops_by_id):
    """Build provisional, schedule-informed ETAs for the stops ahead of a bus."""
    route_stop_ids = route.get("stops", [])
    route_stops = [
        stops_by_id[stop_id]
        for stop_id in route_stop_ids
        if stop_id in stops_by_id
        and stops_by_id[stop_id].get("latitude") is not None
        and stops_by_id[stop_id].get("longitude") is not None
    ]
    if not route_stops:
        return []

    bus_point = (trip["latitude"], trip["longitude"])
    stop_points = [
        (float(stop["latitude"]), float(stop["longitude"]))
        for stop in route_stops
    ]
    nearest_index = min(
        range(len(stop_points)),
        key=lambda index: _distance_km(bus_point, stop_points[index]),
    )
    if _distance_km(bus_point, stop_points[nearest_index]) <= 0.15:
        nearest_index += 1
    upcoming_stops = route_stops[nearest_index:]
    if not upcoming_stops:
        return []

    total_distance = float(route.get("total_distance_km") or 0)
    total_duration = float(route.get("estimated_duration_mins") or 0)
    average_speed_kmh = total_distance * 60 / total_duration if total_duration else 20
    average_speed_kmh = min(max(average_speed_kmh, 10), 40)
    gps_speed_mps = trip.get("location_speed_mps")
    if gps_speed_mps is not None and 1 <= gps_speed_mps * 3.6 <= 80:
        average_speed_kmh = gps_speed_mps * 3.6

    detail_by_stop = {
        detail.get("stop_id"): detail
        for detail in route.get("stop_details", [])
    }
    minutes = (
        _distance_km(bus_point, stop_points[nearest_index]) / average_speed_kmh * 60
        if nearest_index < len(stop_points)
        else 0
    )
    arrivals = []
    for index, stop in enumerate(upcoming_stops):
        if index > 0:
            detail = detail_by_stop.get(stop.get("stop_id"), {})
            leg_minutes = detail.get("time_from_prev_mins")
            if leg_minutes is None:
                previous_point = stop_points[nearest_index + index - 1]
                current_point = stop_points[nearest_index + index]
                leg_minutes = _distance_km(previous_point, current_point) / average_speed_kmh * 60
            minutes += max(float(leg_minutes), 0)
        arrivals.append({
            "stop_id": stop.get("stop_id"),
            "name": stop.get("name", stop.get("stop_id", "Bus stop")),
            "eta_minutes": max(1, round(minutes)),
        })
    return arrivals


class StopListAPIView(APIView):
    """API endpoint to retrieve all bus stops with geographic coordinates."""
    def get(self, request):
        repo = StopRepository()
        stops = repo.list_all()
        return Response({'count': len(stops), 'results': stops})


class RouteListAPIView(APIView):
    """API endpoint to retrieve all routes with stop sequences."""
    def get(self, request):
        repo = RouteRepository()
        routes = repo.list_active()
        return Response({'count': len(routes), 'results': routes})


class BusListAPIView(APIView):
    """API endpoint to retrieve bus fleet status."""
    def get(self, request):
        repo = BusRepository()
        status_filter = request.query_params.get('status')
        if status_filter:
            buses = repo.find_all({'status': status_filter})
        else:
            buses = repo.list_all()
        return Response({'count': len(buses), 'results': buses})


class ShortestPathAPIView(APIView):
    """
    Executes Dijkstra's Shortest Path Algorithm between source and destination stops.
    Query parameters:
    - source: Source stop_id (e.g. S001)
    - destination: Destination stop_id (e.g. S008)
    - metric: 'distance' (default) or 'time'
    """
    def get(self, request):
        source = request.query_params.get('source')
        destination = request.query_params.get('destination')
        metric = request.query_params.get('metric', 'distance')

        if not source or not destination:
            return Response(
                {'error': 'Both "source" and "destination" stop IDs are required parameters.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        stop_repo = StopRepository()
        route_repo = RouteRepository()
        graph = TransitGraph.from_database(stop_repo, route_repo)

        result = dijkstra_shortest_path(graph, source, destination, metric=metric)
        if not result['success']:
            return Response(result, status=status.HTTP_404_NOT_FOUND)

        return Response(result, status=status.HTTP_200_OK)


class DemandAPIView(APIView):
    """API endpoint to get aggregate demand or create new passenger demand records."""
    def get(self, request):
        repo = DemandRepository()
        time_period = request.query_params.get('time_period')
        date = request.query_params.get('date')

        if request.query_params.get('aggregate') == 'true':
            data = repo.get_aggregate_demand_by_route(time_period=time_period, date=date)
        else:
            data = repo.list_by_route_and_period(time_period=time_period, date=date)
        return Response({'count': len(data), 'results': data})

    def post(self, request):
        repo = DemandRepository()
        data = request.data
        required_fields = ['route_id', 'stop_id', 'passenger_count']
        for rf in required_fields:
            if rf not in data:
                return Response({'error': f"Field '{rf}' is required."}, status=status.HTTP_400_BAD_REQUEST)

        created = repo.create({
            'route_id': data['route_id'],
            'stop_id': data['stop_id'],
            'date': data.get('date'),
            'time_period': data.get('time_period', '08:00-09:00'),
            'passenger_count': int(data['passenger_count'])
        })
        return Response(created, status=status.HTTP_201_CREATED)


class OptimizeScheduleAPIView(APIView):
    """
    Executes Demand Scheduling & Greedy Bus Allocation optimization.
    Returns comparison metrics between baseline uniform allocation and optimized schedule.
    """
    def post(self, request):
        time_period = request.data.get('time_period', '08:00-09:00')
        scenario_name = request.data.get('scenario_name', f"Optimization ({time_period})")

        opt_result = run_fleet_optimization(time_period=time_period, scenario_name=scenario_name)
        if not opt_result.get('success'):
            return Response(opt_result, status=status.HTTP_400_BAD_REQUEST)

        return Response(opt_result, status=status.HTTP_200_OK)


class OptimizationResultsAPIView(APIView):
    """API endpoint to retrieve previous optimization result runs."""
    def get(self, request):
        repo = OptimizationResultRepository()
        results = repo.list_recent(limit=20)
        return Response({'count': len(results), 'results': results})


class TripStatusUpdateAPIView(APIView):
    """API endpoint for drivers or IoT devices to update live trip status."""
    def patch(self, request, trip_id):
        repo = TripRepository()
        trip = repo.get_by_id(trip_id)
        if not trip:
            return Response({'error': f"Trip '{trip_id}' not found."}, status=status.HTTP_404_NOT_FOUND)

        new_status = request.data.get('status')
        notes = request.data.get('notes')
        current_stop_id = request.data.get('current_stop_id')
        delay_minutes = request.data.get('delay_minutes')

        updated = repo.update_status(
            trip_id=trip_id,
            status=new_status,
            notes=notes,
            current_stop_id=current_stop_id,
            delay_minutes=delay_minutes
        )
        return Response(updated, status=status.HTTP_200_OK)


class LiveBusListAPIView(APIView):
    """Public feed containing recent positions from active trips and stop ETAs."""

    def get(self, request):
        cutoff = (datetime.now(timezone.utc) - timedelta(minutes=3)).isoformat()
        trips = TripRepository().find_all({
            "status": {"$in": ["In Transit", "Departed", "Delayed"]},
            "location_updated_at": {"$gte": cutoff},
        })
        routes_by_id = {
            route["route_id"]: route
            for route in RouteRepository().list_active()
        }
        buses_by_id = {
            bus["bus_id"]: bus
            for bus in BusRepository().list_all()
        }
        stops_by_id = {
            stop["stop_id"]: stop
            for stop in StopRepository().list_all()
        }

        live_buses = []
        for trip in trips:
            route = routes_by_id.get(trip.get("route_id"))
            if not route:
                continue
            bus = buses_by_id.get(trip.get("bus_id"), {})
            live_buses.append({
                "trip_id": trip.get("trip_id"),
                "bus_number": bus.get("bus_number", trip.get("bus_id", "Bus")),
                "route_number": route.get("route_number", route.get("route_id")),
                "route_name": route.get("route_name", ""),
                "latitude": trip.get("latitude"),
                "longitude": trip.get("longitude"),
                "updated_at": trip.get("location_updated_at"),
                "accuracy_m": trip.get("location_accuracy_m"),
                "stop_arrivals": _estimate_stop_arrivals(trip, route, stops_by_id),
            })
        return Response({"count": len(live_buses), "results": live_buses})


@method_decorator(csrf_protect, name="dispatch")
class TripLocationAPIView(APIView):
    """Accept or clear a driver's GPS location for their own active trip."""

    def _owned_trip(self, request, trip_id):
        user = request.session.get("user")
        if not user or user.get("role") != "driver":
            return None, Response(
                {"error": "A signed-in driver account is required."},
                status=status.HTTP_403_FORBIDDEN,
            )
        driver = DriverRepository().find_one({"name": user.get("full_name")})
        if not driver:
            return None, Response(
                {"error": "No driver profile is linked to this account."},
                status=status.HTTP_403_FORBIDDEN,
            )
        trip = TripRepository().get_by_id(trip_id)
        if not trip:
            return None, Response(
                {"error": "Trip not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        if trip.get("driver_id") != driver.get("driver_id"):
            return None, Response(
                {"error": "You can only share the location of your assigned trip."},
                status=status.HTTP_403_FORBIDDEN,
            )
        return trip, None

    def post(self, request, trip_id):
        trip, error_response = self._owned_trip(request, trip_id)
        if error_response:
            return error_response
        if trip.get("status") not in ("In Transit", "Departed", "Delayed"):
            return Response(
                {"error": "Location sharing is available only for active trips."},
                status=status.HTTP_409_CONFLICT,
            )

        try:
            latitude = float(request.data.get("latitude"))
            longitude = float(request.data.get("longitude"))
            accuracy = request.data.get("accuracy")
            speed = request.data.get("speed")
            accuracy = float(accuracy) if accuracy is not None else None
            speed = float(speed) if speed is not None else None
        except (TypeError, ValueError):
            return Response(
                {"error": "Latitude and longitude must be valid numbers."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if (
            not math.isfinite(latitude)
            or not math.isfinite(longitude)
            or not -90 <= latitude <= 90
            or not -180 <= longitude <= 180
            or (accuracy is not None and (not math.isfinite(accuracy) or accuracy < 0))
            or (speed is not None and (not math.isfinite(speed) or speed < 0))
        ):
            return Response(
                {"error": "GPS coordinates, accuracy, or speed are outside valid ranges."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        updated = TripRepository().update_location(
            trip_id,
            latitude,
            longitude,
            accuracy=accuracy,
            speed=speed,
        )
        return Response(
            {"message": "Bus location updated.", "updated_at": updated.get("location_updated_at")},
            status=status.HTTP_200_OK,
        )

    def delete(self, request, trip_id):
        trip, error_response = self._owned_trip(request, trip_id)
        if error_response:
            return error_response
        TripRepository().clear_location(trip_id)
        return Response(status=status.HTTP_204_NO_CONTENT)
