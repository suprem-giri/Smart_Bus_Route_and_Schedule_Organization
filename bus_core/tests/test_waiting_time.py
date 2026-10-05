"""
Unit Tests for Algorithm 4: Waiting-Time Estimation.
"""

import unittest
from bus_core.algorithms.waiting_time import estimate_waiting_time, estimate_waiting_time_safe


class TestWaitingTimeAlgorithm(unittest.TestCase):
    def test_valid_intervals(self):
        self.assertEqual(estimate_waiting_time(10), 5.0)
        self.assertEqual(estimate_waiting_time(15), 7.5)
        self.assertEqual(estimate_waiting_time(20.4), 10.2)

    def test_invalid_intervals_raise_error(self):
        with self.assertRaises(ValueError):
            estimate_waiting_time(0)
        with self.assertRaises(ValueError):
            estimate_waiting_time(-5)
        with self.assertRaises(ValueError):
            estimate_waiting_time(None)

    def test_safe_wrapper(self):
        self.assertEqual(estimate_waiting_time_safe(10), 5.0)
        self.assertEqual(estimate_waiting_time_safe(0, default=0.0), 0.0)
        self.assertEqual(estimate_waiting_time_safe(-10, default=-1), -1)
