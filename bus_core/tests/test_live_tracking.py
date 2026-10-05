import json
from unittest.mock import patch

from django.test import Client, TestCase
from django.urls import reverse

from bus_core.database.repositories import (
    BusRepository,
    DriverRepository,
    RouteRepository,
    StopRepository,
    TripRepository,
)


class LiveTrackingApiTests(TestCase):
    def setUp(self):
        self.client = Client()
        session = self.client.session
        session["user"] = {
            "user_id": "U001",
            "username": "driver-example",
            "role": "driver",
            "full_name": "Driver Example",
        }
        session.save()

    @patch.object(TripRepository, "update_location")
    @patch.object(TripRepository, "get_by_id")
    @patch.object(DriverRepository, "find_one")
    def test_driver_can_share_valid_location_for_assigned_active_trip(
        self, find_driver, get_trip, update_location
    ):
        find_driver.return_value = {"driver_id": "D001"}
        get_trip.return_value = {
            "trip_id": "TRP001",
            "driver_id": "D001",
            "status": "In Transit",
        }
        update_location.return_value = {
            "location_updated_at": "2026-10-05T10:00:00Z",
        }

        response = self.client.post(
            reverse("api_trip_location", args=["TRP001"]),
            data=json.dumps({
                "latitude": 27.7,
                "longitude": 85.3,
                "accuracy": 8,
                "speed": 4,
            }),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        update_location.assert_called_once_with(
            "TRP001", 27.7, 85.3, accuracy=8.0, speed=4.0
        )

    @patch.object(TripRepository, "update_location")
    @patch.object(TripRepository, "get_by_id")
    @patch.object(DriverRepository, "find_one")
    def test_driver_cannot_share_location_outside_coordinate_ranges(
        self, find_driver, get_trip, update_location
    ):
        find_driver.return_value = {"driver_id": "D001"}
        get_trip.return_value = {
            "trip_id": "TRP001",
            "driver_id": "D001",
            "status": "In Transit",
        }

        response = self.client.post(
            reverse("api_trip_location", args=["TRP001"]),
            data=json.dumps({"latitude": 91, "longitude": 85.3}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        update_location.assert_not_called()

    @patch.object(TripRepository, "get_by_id")
    @patch.object(DriverRepository, "find_one")
    def test_driver_cannot_update_another_drivers_trip(self, find_driver, get_trip):
        find_driver.return_value = {"driver_id": "D001"}
        get_trip.return_value = {
            "trip_id": "TRP002",
            "driver_id": "D002",
            "status": "In Transit",
        }

        response = self.client.post(
            reverse("api_trip_location", args=["TRP002"]),
            data=json.dumps({"latitude": 27.7, "longitude": 85.3}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 403)

    def test_location_endpoint_rejects_missing_csrf_token(self):
        client = Client(enforce_csrf_checks=True)
        session = client.session
        session["user"] = {
            "user_id": "U001",
            "username": "driver-example",
            "role": "driver",
            "full_name": "Driver Example",
        }
        session.save()

        response = client.post(
            reverse("api_trip_location", args=["TRP001"]),
            data=json.dumps({"latitude": 27.7, "longitude": 85.3}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 403)

    @patch.object(StopRepository, "list_all")
    @patch.object(BusRepository, "list_all")
    @patch.object(RouteRepository, "list_active")
    @patch.object(TripRepository, "find_all")
    def test_live_bus_feed_includes_upcoming_stop_eta(
        self, find_trips, list_routes, list_buses, list_stops
    ):
        find_trips.return_value = [{
            "trip_id": "TRP001",
            "bus_id": "B001",
            "route_id": "R001",
            "status": "In Transit",
            "latitude": 27.7058,
            "longitude": 85.3157,
            "location_updated_at": "2026-10-05T10:00:00Z",
        }]
        list_routes.return_value = [{
            "route_id": "R001",
            "route_number": "RT-01",
            "route_name": "Central Route",
            "stops": ["S001", "S002", "S003"],
            "stop_details": [
                {"stop_id": "S001", "time_from_prev_mins": 0},
                {"stop_id": "S002", "time_from_prev_mins": 6},
                {"stop_id": "S003", "time_from_prev_mins": 9},
            ],
            "total_distance_km": 3.8,
            "estimated_duration_mins": 15,
        }]
        list_buses.return_value = [{"bus_id": "B001", "bus_number": "BA 1 PA 1234"}]
        list_stops.return_value = [
            {"stop_id": "S001", "name": "Start", "latitude": 27.7058, "longitude": 85.3157},
            {"stop_id": "S002", "name": "Middle", "latitude": 27.6936, "longitude": 85.3218},
            {"stop_id": "S003", "name": "End", "latitude": 27.6915, "longitude": 85.3420},
        ]

        response = self.client.get(reverse("api_live_buses"))

        self.assertEqual(response.status_code, 200)
        bus = response.json()["results"][0]
        self.assertEqual(bus["route_number"], "RT-01")
        self.assertEqual(bus["stop_arrivals"][0]["name"], "Middle")
        self.assertEqual(bus["stop_arrivals"][0]["eta_minutes"], 6)
        self.assertEqual(bus["stop_arrivals"][1]["eta_minutes"], 15)

    @patch("bus_core.views.driver_views.ScheduleRepository")
    @patch("bus_core.views.driver_views.StopRepository")
    @patch("bus_core.views.driver_views.RouteRepository")
    @patch("bus_core.views.driver_views.TripRepository")
    @patch("bus_core.views.driver_views.BusRepository")
    @patch("bus_core.views.driver_views.DriverRepository")
    def test_driver_dashboard_exposes_gps_controls_for_active_trips(
        self, driver_repo, bus_repo, trip_repo, route_repo, stop_repo, schedule_repo
    ):
        driver_repo.return_value.find_one.return_value = {
            "driver_id": "D001",
            "name": "Driver Example",
            "assigned_bus_id": "B001",
        }
        bus_repo.return_value.get_by_id.return_value = {"bus_id": "B001"}
        trip_repo.return_value.find_all.return_value = [{
            "trip_id": "TRP001",
            "driver_id": "D001",
            "route_id": "R001",
            "status": "In Transit",
            "date": "2026-10-05",
        }]
        route_repo.return_value.list_active.return_value = []
        stop_repo.return_value.list_all.return_value = []

        response = self.client.get(reverse("driver_dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Share GPS")
        self.assertContains(response, "/api/trips/TRP001/location/")
