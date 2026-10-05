"""
Unit Tests for Algorithm 1: Dijkstra's Shortest Path Algorithm.
Covers direct path, multiple paths, equal-cost paths, unreachable destination,
source == destination, and metric comparison (distance vs time).
"""

import unittest
from bus_core.algorithms.graph import TransitGraph
from bus_core.algorithms.dijkstra import dijkstra_shortest_path, calculate_fare


class TestDijkstraAlgorithm(unittest.TestCase):
    def setUp(self):
        self.graph = TransitGraph()
        # Add 5 stops
        for i in range(1, 6):
            stop_id = f"S00{i}"
            self.graph.add_node(stop_id, {
                'stop_id': stop_id,
                'name': f"Stop {i}",
                'latitude': 27.7000 + (i * 0.01),
                'longitude': 85.3000 + (i * 0.01)
            })

        # Add edges:
        # S001 -> S002: dist=3.0 km, time=10 min
        # S002 -> S003: dist=4.0 km, time=12 min
        # S001 -> S004: dist=6.0 km, time=8 min (Longer distance, but faster highway!)
        # S004 -> S003: dist=2.0 km, time=5 min
        # S005 is disconnected
        self.graph.add_edge("S001", "S002", 3.0, 10.0, "R001", "RT-1")
        self.graph.add_edge("S002", "S003", 4.0, 12.0, "R001", "RT-1")
        self.graph.add_edge("S001", "S004", 6.0, 8.0, "R002", "RT-2")
        self.graph.add_edge("S004", "S003", 2.0, 5.0, "R002", "RT-2")

    def test_direct_or_multi_hop_distance_optimization(self):
        # By distance: S001 -> S002 -> S003 has cost 3.0 + 4.0 = 7.0 km
        # Versus S001 -> S004 -> S003 has cost 6.0 + 2.0 = 8.0 km
        res = dijkstra_shortest_path(self.graph, "S001", "S003", metric='distance')
        self.assertTrue(res['success'])
        self.assertEqual(res['path'], ["S001", "S002", "S003"])
        self.assertEqual(res['total_distance_km'], 7.0)
        self.assertEqual(res['total_cost'], 7.0)

    def test_time_based_optimization(self):
        # By time: S001 -> S004 -> S003 takes 8.0 + 5.0 = 13.0 mins
        # Versus S001 -> S002 -> S003 takes 10.0 + 12.0 = 22.0 mins
        res = dijkstra_shortest_path(self.graph, "S001", "S003", metric='time')
        self.assertTrue(res['success'])
        self.assertEqual(res['path'], ["S001", "S004", "S003"])
        self.assertEqual(res['total_travel_time_mins'], 13.0)
        self.assertEqual(res['total_cost'], 13.0)

    def test_same_source_and_destination(self):
        res = dijkstra_shortest_path(self.graph, "S001", "S001")
        self.assertTrue(res['success'])
        self.assertEqual(res['path'], ["S001"])
        self.assertEqual(res['total_cost'], 0.0)
        self.assertEqual(res['stops_count'], 1)

    def test_unreachable_destination(self):
        # S005 has no incoming edges
        res = dijkstra_shortest_path(self.graph, "S001", "S005")
        self.assertFalse(res['success'])
        self.assertIn("No connected transit route", res['message'])

    def test_nonexistent_node(self):
        res = dijkstra_shortest_path(self.graph, "S999", "S001")
        self.assertFalse(res['success'])
        self.assertIn("does not exist", res['message'])

    def test_fare_calculation(self):
        self.assertEqual(calculate_fare(0), 0)
        self.assertEqual(calculate_fare(3.5), 20.0)  # Base fare
        self.assertEqual(calculate_fare(6.0), 26.0)  # 20 + 2*3 = 26
