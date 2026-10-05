"""
Unit Tests for Algorithm 3: Greedy Bus Allocation Heuristic and Baseline Comparison.
"""

import unittest
from bus_core.algorithms.allocation import greedy_bus_allocation, baseline_uniform_allocation


class TestAllocationAlgorithm(unittest.TestCase):
    def setUp(self):
        # 3 routes with varied demand
        self.routes = [
            {'route_id': 'R001', 'route_name': 'Route Low', 'demand': 40, 'estimated_duration_mins': 30},
            {'route_id': 'R002', 'route_name': 'Route Medium', 'demand': 100, 'estimated_duration_mins': 40},
            {'route_id': 'R003', 'route_name': 'Route High', 'demand': 250, 'estimated_duration_mins': 45}
        ]

        # 6 buses with varied capacity
        self.buses = [
            {'bus_id': 'B1', 'bus_number': 'BUS-01', 'capacity': 30},
            {'bus_id': 'B2', 'bus_number': 'BUS-02', 'capacity': 35},
            {'bus_id': 'B3', 'bus_number': 'BUS-03', 'capacity': 50},
            {'bus_id': 'B4', 'bus_number': 'BUS-04', 'capacity': 55},
            {'bus_id': 'B5', 'bus_number': 'BUS-05', 'capacity': 55},
            {'bus_id': 'B6', 'bus_number': 'BUS-06', 'capacity': 60}
        ]

    def test_greedy_prioritizes_high_demand(self):
        result = greedy_bus_allocation(self.routes, self.buses)
        routes_res = {r['route_id']: r for r in result['routes']}

        # High demand route should get more buses than low demand route
        self.assertGreater(routes_res['R003']['bus_count'], routes_res['R001']['bus_count'])
        self.assertEqual(result['metrics']['buses_used'], 6)
        self.assertEqual(result['metrics']['unassigned_buses_count'], 0)

    def test_greedy_outperforms_uniform_baseline_on_unmet_demand(self):
        baseline = baseline_uniform_allocation(self.routes, self.buses)
        greedy = greedy_bus_allocation(self.routes, self.buses)

        # Baseline assigns 2 buses uniformly to each route
        # Route 3 (250 passengers) will suffer severe unmet demand in baseline
        self.assertLessEqual(greedy['metrics']['total_unmet'], baseline['metrics']['total_unmet'])
        # Greedy achieves higher total satisfied demand
        self.assertGreaterEqual(greedy['metrics']['total_satisfied'], baseline['metrics']['total_satisfied'])
