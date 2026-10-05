"""
Algorithm 2: Demand-Based Service Frequency.
Calculates required trips, feasible service frequency, suggested headway interval,
and estimated passenger waiting time based on demand and fleet capacity constraints.
"""

import math
from .waiting_time import estimate_waiting_time_safe


def demand_based_scheduling(demand_D, capacity_C, available_buses_B, round_trip_time_T, planning_period_mins=60, turnaround_time_mins=10):
    """
    Executes Demand-Based Service Frequency calculation according to Section 4.3.5.

    Args:
        demand_D (int or float): Estimated passenger demand for the time period.
        capacity_C (int): Effective passenger capacity per bus trip.
        available_buses_B (int): Number of buses allocated/available for the route.
        round_trip_time_T (float): Route round trip time in minutes (one-way * 2 or loop).
        planning_period_mins (int): Planning duration in minutes (default: 60 for 1-hour window).
        turnaround_time_mins (int): Buffer/recovery time at terminal in minutes (default: 10).

    Returns:
        dict: Detailed scheduling metrics including required trips, feasible trips,
              service interval, waiting time, unmet demand, and utilization.
    """
    # 1. Validation
    if demand_D < 0:
        raise ValueError("Passenger demand D must be non-negative (>= 0).")
    if capacity_C <= 0:
        raise ValueError("Effective bus capacity C must be positive (> 0).")
    if available_buses_B < 0:
        raise ValueError("Available buses B must be non-negative (>= 0).")
    if round_trip_time_T <= 0:
        raise ValueError("Round-trip time T must be positive (> 0).")

    effective_cycle_time = round_trip_time_T + turnaround_time_mins

    # 2. Required trips to satisfy full passenger demand
    if demand_D == 0:
        required_trips = 0
    else:
        required_trips = math.ceil(demand_D / capacity_C)

    # 3. Available service capacity (maximum trips possible given available buses and cycle time)
    # A single bus can perform (planning_period_mins / effective_cycle_time) trips in the period.
    # For a 1-hour period with cycle time >= 60, each bus can make at most 1 trip.
    trips_per_bus = max(1.0, planning_period_mins / effective_cycle_time)
    max_service_capacity_trips = math.floor(available_buses_B * trips_per_bus)

    # If buses are assigned and required trips > 0, at least min(available_buses_B, required_trips)
    if available_buses_B > 0 and required_trips > 0:
        max_service_capacity_trips = max(max_service_capacity_trips, available_buses_B)

    # Feasible trips bounded by available fleet
    feasible_trips = min(required_trips, max_service_capacity_trips) if available_buses_B > 0 else 0

    # 4. Service interval (Headway in minutes)
    if feasible_trips > 0:
        # e.g., 60 mins / 4 trips = 15 mins interval
        service_interval_mins = round(planning_period_mins / feasible_trips, 1)
        est_waiting_time = estimate_waiting_time_safe(service_interval_mins)
    else:
        service_interval_mins = None
        est_waiting_time = None

    # Capacity provided and unmet demand
    total_offered_capacity = feasible_trips * capacity_C
    satisfied_demand = min(demand_D, total_offered_capacity)
    unmet_demand = max(0, demand_D - total_offered_capacity)

    satisfaction_rate = round((satisfied_demand / demand_D * 100), 1) if demand_D > 0 else 100.0

    # Bus seat utilization percentage: (demand served / offered capacity)
    if total_offered_capacity > 0:
        bus_utilization_pct = min(100.0, round((satisfied_demand / total_offered_capacity) * 100, 1))
    else:
        bus_utilization_pct = 0.0

    # Fleet requirements: Minimum buses needed for full demand
    buses_needed_for_full_demand = math.ceil(required_trips / trips_per_bus) if trips_per_bus > 0 else required_trips

    return {
        'demand': demand_D,
        'bus_capacity': capacity_C,
        'available_buses': available_buses_B,
        'round_trip_time_mins': round_trip_time_T,
        'effective_cycle_time_mins': effective_cycle_time,
        'planning_period_mins': planning_period_mins,
        'required_trips': required_trips,
        'feasible_trips': feasible_trips,
        'service_interval_mins': service_interval_mins,
        'average_waiting_time_mins': est_waiting_time,
        'offered_capacity': total_offered_capacity,
        'satisfied_demand': satisfied_demand,
        'unmet_demand': unmet_demand,
        'satisfaction_rate_pct': satisfaction_rate,
        'bus_utilization_pct': bus_utilization_pct,
        'buses_needed_for_full_demand': buses_needed_for_full_demand,
        'is_capacity_sufficient': unmet_demand == 0
    }
