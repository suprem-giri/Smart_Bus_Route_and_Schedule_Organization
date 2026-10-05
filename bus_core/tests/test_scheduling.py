"""
Unit Tests for Algorithm 2: Demand-Based Service Frequency.
Covers low/medium/high demand, zero demand, insufficient available buses,
capacity constraint validation, and invalid inputs.
"""

import unittest
from bus_core.algorithms.scheduling import demand_based_scheduling


class TestSchedulingAlgorithm(unittest.TestCase):
    def test_sufficient_capacity(self):
        # Demand: 120 passengers, Bus Capacity: 40, Available: 4 buses, Round-trip: 40 mins
        # Required trips = ceil(120 / 40) = 3 trips
        res = demand_based_scheduling(
            demand_D=120,
            capacity_C=40,
            available_buses_B=4,
            round_trip_time_T=40,
            planning_period_mins=60
        )
        self.assertEqual(res['required_trips'], 3)
        self.assertEqual(res['feasible_trips'], 3)
        self.assertEqual(res['satisfied_demand'], 120)
        self.assertEqual(res['unmet_demand'], 0)
        self.assertEqual(res['service_interval_mins'], 20.0)  # 60 / 3
        self.assertEqual(res['average_waiting_time_mins'], 10.0)  # 20 / 2
        self.assertTrue(res['is_capacity_sufficient'])

    def test_insufficient_buses_unmet_demand(self):
        # Demand: 200 passengers, Bus Capacity: 40 (needs 5 trips), but only 2 buses available
        res = demand_based_scheduling(
            demand_D=200,
            capacity_C=40,
            available_buses_B=2,
            round_trip_time_T=50,
            planning_period_mins=60
        )
        self.assertEqual(res['required_trips'], 5)
        self.assertEqual(res['feasible_trips'], 2)
        self.assertEqual(res['satisfied_demand'], 80)
        self.assertEqual(res['unmet_demand'], 120)
        self.assertFalse(res['is_capacity_sufficient'])
        self.assertEqual(res['buses_needed_for_full_demand'], 5)

    def test_zero_demand(self):
        res = demand_based_scheduling(
            demand_D=0,
            capacity_C=45,
            available_buses_B=2,
            round_trip_time_T=30
        )
        self.assertEqual(res['required_trips'], 0)
        self.assertEqual(res['feasible_trips'], 0)
        self.assertEqual(res['unmet_demand'], 0)
        self.assertIsNone(res['service_interval_mins'])
        self.assertIsNone(res['average_waiting_time_mins'])

    def test_zero_available_buses(self):
        res = demand_based_scheduling(
            demand_D=100,
            capacity_C=50,
            available_buses_B=0,
            round_trip_time_T=40
        )
        self.assertEqual(res['required_trips'], 2)
        self.assertEqual(res['feasible_trips'], 0)
        self.assertEqual(res['unmet_demand'], 100)
        self.assertFalse(res['is_capacity_sufficient'])

    def test_invalid_parameters_raise_value_error(self):
        with self.assertRaises(ValueError):
            demand_based_scheduling(demand_D=-10, capacity_C=40, available_buses_B=2, round_trip_time_T=30)
        with self.assertRaises(ValueError):
            demand_based_scheduling(demand_D=50, capacity_C=0, available_buses_B=2, round_trip_time_T=30)
        with self.assertRaises(ValueError):
            demand_based_scheduling(demand_D=50, capacity_C=40, available_buses_B=-1, round_trip_time_T=30)
        with self.assertRaises(ValueError):
            demand_based_scheduling(demand_D=50, capacity_C=40, available_buses_B=2, round_trip_time_T=0)
