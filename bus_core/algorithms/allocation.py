"""
Algorithm 3: Greedy Bus Allocation Heuristic.
Assigns available fleet vehicles to routes based on demand priority and capacity matching.
Includes baseline comparison generator for academic evaluation.
"""

import math
import copy
from .scheduling import demand_based_scheduling
from .waiting_time import estimate_waiting_time_safe


def baseline_uniform_allocation(routes_data, buses_data, planning_period_mins=60):
    """
    Simulates a standard traditional baseline:
    Uniform or naive round-robin bus distribution across routes without demand-based optimization.
    """
    total_buses = len(buses_data)
    num_routes = len(routes_data)
    if num_routes == 0:
        return {'routes': [], 'metrics': {}}

    # Naive uniform split: each route gets equal share of buses
    buses_per_route = max(1, total_buses // num_routes)
    unassigned_buses = list(buses_data)

    route_results = []
    total_demand = 0
    total_satisfied = 0
    total_unmet = 0
    total_capacity = 0
    waiting_times = []
    utilizations = []

    for route in routes_data:
        r_id = route['route_id']
        r_name = route.get('route_name', r_id)
        demand = float(route.get('demand', 0))
        duration = float(route.get('estimated_duration_mins', 45))
        round_trip = duration * 2

        # Assign first N buses
        assigned = []
        for _ in range(buses_per_route):
            if unassigned_buses:
                assigned.append(unassigned_buses.pop(0))

        bus_count = len(assigned)
        avg_capacity = sum(b.get('capacity', 40) for b in assigned) / bus_count if bus_count > 0 else 40

        sched = demand_based_scheduling(
            demand_D=demand,
            capacity_C=avg_capacity,
            available_buses_B=bus_count,
            round_trip_time_T=round_trip,
            planning_period_mins=planning_period_mins
        )

        total_demand += demand
        total_satisfied += sched['satisfied_demand']
        total_unmet += sched['unmet_demand']
        total_capacity += sched['offered_capacity']

        if sched['average_waiting_time_mins'] is not None:
            waiting_times.append(sched['average_waiting_time_mins'])
        if sched['feasible_trips'] > 0:
            utilizations.append(sched['bus_utilization_pct'])

        route_results.append({
            'route_id': r_id,
            'route_name': r_name,
            'demand': demand,
            'buses_assigned': assigned,
            'bus_count': bus_count,
            'feasible_trips': sched['feasible_trips'],
            'service_interval_mins': sched['service_interval_mins'],
            'avg_waiting_time_mins': sched['average_waiting_time_mins'],
            'offered_capacity': sched['offered_capacity'],
            'satisfied_demand': sched['satisfied_demand'],
            'unmet_demand': sched['unmet_demand'],
            'bus_utilization_pct': sched['bus_utilization_pct']
        })

    avg_wait = round(sum(waiting_times) / len(waiting_times), 1) if waiting_times else 0.0
    avg_util = round(sum(utilizations) / len(utilizations), 1) if utilizations else 0.0

    return {
        'routes': route_results,
        'metrics': {
            'total_demand': total_demand,
            'total_satisfied': total_satisfied,
            'total_unmet': total_unmet,
            'total_capacity': total_capacity,
            'avg_waiting_time_mins': avg_wait,
            'avg_bus_utilization_pct': avg_util,
            'buses_used': total_buses - len(unassigned_buses)
        }
    }


def greedy_bus_allocation(routes_data, buses_data, planning_period_mins=60):
    """
    Executes Algorithm 3: Greedy Bus Allocation Heuristic.

    1. Sort routes by descending priority based on estimated demand.
    2. For each route in sorted routes:
         - Determine route's estimated capacity requirement.
         - Find available buses that satisfy basic capacity constraints.
         - Select feasible bus with closest suitable capacity.
         - Assign bus to route.
    3. If no suitable bus remains, record unmet demand for the route.
    4. Return assignments, comparative baseline, and metric summaries.
    """
    # Create working copies
    routes = copy.deepcopy(routes_data)
    available_buses = copy.deepcopy(buses_data)

    # 1. Sort routes descending by demand
    sorted_routes = sorted(routes, key=lambda r: float(r.get('demand', 0)), reverse=True)

    # Calculate target buses needed per route
    assignments = {r['route_id']: [] for r in sorted_routes}
    unmet_summary = {}

    # Initial pass: Allocate at least 1 bus to every route that has active demand
    for r in sorted_routes:
        r_id = r['route_id']
        demand = float(r.get('demand', 0))
        if demand > 0 and available_buses:
            # Pick a bus with capacity closest to route demand (or smallest sufficient)
            best_idx = 0
            min_diff = float('inf')
            for i, bus in enumerate(available_buses):
                diff = abs(bus.get('capacity', 40) - demand)
                if diff < min_diff:
                    min_diff = diff
                    best_idx = i
            bus_to_assign = available_buses.pop(best_idx)
            assignments[r_id].append(bus_to_assign)

    # Secondary greedy pass: Allocate remaining buses to routes with highest remaining unsatisfied demand
    while available_buses:
        # Evaluate remaining demand for each route
        routes_with_deficit = []
        for r in sorted_routes:
            r_id = r['route_id']
            demand = float(r.get('demand', 0))
            duration = float(r.get('estimated_duration_mins', 45))
            round_trip = duration * 2
            current_buses = assignments[r_id]

            # Current capacity
            current_cap = sum(b.get('capacity', 40) for b in current_buses)
            # Cycle multiplier
            trips_per_bus = max(1.0, planning_period_mins / (round_trip + 10))
            total_current_capacity = math.floor(current_cap * trips_per_bus)

            deficit = demand - total_current_capacity
            if deficit > 0:
                routes_with_deficit.append((deficit, r_id, r))

        if not routes_with_deficit:
            # All demand satisfied across all routes! Assign remaining buses to most loaded route for frequency boost
            if sorted_routes:
                highest_route = sorted_routes[0]['route_id']
                assignments[highest_route].append(available_buses.pop(0))
            else:
                break
            continue

        # Sort deficit descending
        routes_with_deficit.sort(key=lambda x: x[0], reverse=True)
        target_deficit, target_route_id, target_route = routes_with_deficit[0]

        # Greedy choice: pick bus that closest matches deficit
        best_idx = 0
        min_diff = float('inf')
        for i, bus in enumerate(available_buses):
            diff = abs(bus.get('capacity', 40) - target_deficit)
            if diff < min_diff:
                min_diff = diff
                best_idx = i

        bus_to_assign = available_buses.pop(best_idx)
        assignments[target_route_id].append(bus_to_assign)

    # 3. Construct detailed route schedules and compute metrics
    optimized_route_results = []
    total_demand = 0
    total_satisfied = 0
    total_unmet = 0
    total_capacity = 0
    waiting_times = []
    utilizations = []

    for r in sorted_routes:
        r_id = r['route_id']
        r_name = r.get('route_name', r_id)
        demand = float(r.get('demand', 0))
        duration = float(r.get('estimated_duration_mins', 45))
        round_trip = duration * 2

        assigned = assignments[r_id]
        bus_count = len(assigned)
        avg_capacity = sum(b.get('capacity', 40) for b in assigned) / bus_count if bus_count > 0 else 40

        sched = demand_based_scheduling(
            demand_D=demand,
            capacity_C=avg_capacity,
            available_buses_B=bus_count,
            round_trip_time_T=round_trip,
            planning_period_mins=planning_period_mins
        )

        total_demand += demand
        total_satisfied += sched['satisfied_demand']
        total_unmet += sched['unmet_demand']
        total_capacity += sched['offered_capacity']

        if sched['average_waiting_time_mins'] is not None:
            waiting_times.append(sched['average_waiting_time_mins'])
        if sched['feasible_trips'] > 0:
            utilizations.append(sched['bus_utilization_pct'])

        if sched['unmet_demand'] > 0:
            unmet_summary[r_id] = {
                'route_name': r_name,
                'unmet_passengers': sched['unmet_demand'],
                'additional_buses_needed': sched['buses_needed_for_full_demand'] - bus_count
            }

        optimized_route_results.append({
            'route_id': r_id,
            'route_name': r_name,
            'demand': demand,
            'buses_assigned': assigned,
            'bus_count': bus_count,
            'feasible_trips': sched['feasible_trips'],
            'service_interval_mins': sched['service_interval_mins'],
            'avg_waiting_time_mins': sched['average_waiting_time_mins'],
            'offered_capacity': sched['offered_capacity'],
            'satisfied_demand': sched['satisfied_demand'],
            'unmet_demand': sched['unmet_demand'],
            'bus_utilization_pct': sched['bus_utilization_pct'],
            'is_capacity_sufficient': sched['is_capacity_sufficient']
        })

    avg_wait = round(sum(waiting_times) / len(waiting_times), 1) if waiting_times else 0.0
    avg_util = round(sum(utilizations) / len(utilizations), 1) if utilizations else 0.0

    return {
        'routes': optimized_route_results,
        'unmet_summary': unmet_summary,
        'metrics': {
            'total_demand': total_demand,
            'total_satisfied': total_satisfied,
            'total_unmet': total_unmet,
            'total_capacity': total_capacity,
            'avg_waiting_time_mins': avg_wait,
            'avg_bus_utilization_pct': avg_util,
            'buses_used': len(buses_data) - len(available_buses),
            'unassigned_buses_count': len(available_buses)
        }
    }
