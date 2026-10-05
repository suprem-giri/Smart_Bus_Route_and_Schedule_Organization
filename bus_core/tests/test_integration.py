"""
Integration and API Tests for Smart Public Bus Route & Schedule Optimization System.
Tests Django views, REST API endpoints, Dijkstra calculation API, and optimization execution.
"""

from django.test import TestCase, Client
from django.urls import reverse
from bus_core.database.repositories import (
    UserRepository, StopRepository, RouteRepository, BusRepository,
    ScheduleRepository, TripRepository, DemandRepository
)


class IntegrationAndAPITestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user_repo = UserRepository()
        self.stop_repo = StopRepository()
        self.route_repo = RouteRepository()
        self.bus_repo = BusRepository()
        self.trip_repo = TripRepository()

        # Ensure demo stops exist
        if not self.stop_repo.get_by_id("S001"):
            self.stop_repo.insert({
                'stop_id': 'S001', 'name': 'Ratna Park', 'code': 'RPC',
                'latitude': 27.7058, 'longitude': 85.3157, 'zone': 'Central',
                'facilities': ['Shelter'], 'is_terminal': True
            })
        if not self.stop_repo.get_by_id("S002"):
            self.stop_repo.insert({
                'stop_id': 'S002', 'name': 'Maitighar', 'code': 'MMJ',
                'latitude': 27.6936, 'longitude': 85.3218, 'zone': 'Central',
                'facilities': ['Shelter'], 'is_terminal': False
            })
        if not self.stop_repo.get_by_id("S003"):
            self.stop_repo.insert({
                'stop_id': 'S003', 'name': 'Baneshwor', 'code': 'BCH',
                'latitude': 27.6915, 'longitude': 85.3420, 'zone': 'East',
                'facilities': ['Shelter'], 'is_terminal': False
            })

        # Ensure route exists connecting them
        if not self.route_repo.get_by_id("R001"):
            self.route_repo.insert({
                'route_id': 'R001', 'route_number': 'RT-01', 'route_name': 'Test Route',
                'stops': ['S001', 'S002', 'S003'],
                'stop_details': [
                    {'stop_id': 'S001', 'sequence': 1, 'distance_from_prev_km': 0.0, 'time_from_prev_mins': 0},
                    {'stop_id': 'S002', 'sequence': 2, 'distance_from_prev_km': 1.5, 'time_from_prev_mins': 6},
                    {'stop_id': 'S003', 'sequence': 3, 'distance_from_prev_km': 2.3, 'time_from_prev_mins': 9},
                ],
                'total_distance_km': 3.8, 'estimated_duration_mins': 15, 'base_fare': 20.0, 'active': True
            })

    def test_passenger_home_page(self):
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Smart")
        self.assertContains(response, "Dijkstra")

    def test_passenger_route_search_page(self):
        response = self.client.get(reverse('route_search'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Dijkstra Shortest Path Route Finder")

    def test_passenger_route_search_execution(self):
        response = self.client.get(reverse('route_search'), {
            'source': 'S001',
            'destination': 'S003',
            'metric': 'distance'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Optimal Journey Path Map")
        self.assertContains(response, "Turn-by-Turn Transit Itinerary")

    def test_routes_list_page(self):
        response = self.client.get(reverse('routes_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Public Bus Routes & Timetables")

    def test_stops_list_page(self):
        response = self.client.get(reverse('stops_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Bus Stops Directory")

    def test_api_stops_endpoint(self):
        response = self.client.get(reverse('api_stops'))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('results', data)
        self.assertGreater(data['count'], 0)

    def test_api_routes_endpoint(self):
        response = self.client.get(reverse('api_routes'))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('results', data)
        self.assertGreater(data['count'], 0)

    def test_api_shortest_path_endpoint(self):
        response = self.client.get(reverse('api_shortest_path'), {
            'source': 'S001',
            'destination': 'S003',
            'metric': 'distance'
        })
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['path'], ['S001', 'S002', 'S003'])
        self.assertEqual(data['total_distance_km'], 3.8)
        self.assertGreater(data['execution_time_ms'], 0)

    def test_api_shortest_path_missing_params(self):
        response = self.client.get(reverse('api_shortest_path'), {'source': 'S001'})
        self.assertEqual(response.status_code, 400)

    def test_api_optimize_endpoint(self):
        response = self.client.post(
            reverse('api_optimize'),
            data={'time_period': '08:00-09:00', 'scenario_name': 'Test API Scenario'},
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertIn('improvements', data)
        self.assertIn('metrics_baseline', data)
        self.assertIn('metrics_optimized', data)

    def test_auth_login_and_role_redirect(self):
        # Admin login
        response = self.client.post(reverse('login'), {
            'username': 'admin',
            'password': 'admin123'
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        # Should be redirected to admin dashboard
        self.assertContains(response, "Administration & System Control")
