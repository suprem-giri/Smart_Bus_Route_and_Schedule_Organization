"""
Optimization Orchestrator for Smart Public Bus System.
Executes the full pipeline: data ingestion -> demand aggregation -> baseline & greedy allocation
-> before/after comparison metrics calculation -> persistence in MongoDB.
"""

import time
from datetime import datetime
from .allocation import baseline_uniform_allocation, greedy_bus_allocation
from ..database.repositories import (
    RouteRepository, BusRepository, DemandRepository, OptimizationResultRepository
)


def run_fleet_optimization(time_period=None, date=None, scenario_name="Automated Transit Schedule Optimization"):
    """
    Executes end-to-end route and schedule optimization.
    
    Args:
        time_period (str): Optional time period filter, e.g. "08:00-09:00".
        date (str): Optional date filter, e.g. "2026-10-04".
        scenario_name (str): Label for the optimization run.

    Returns:
        dict: Complete optimization results with baseline comparison and improvements.
    """
    start_clock = time.perf_counter()

    route_repo = RouteRepository()
    bus_repo = BusRepository()
    demand_repo = DemandRepository()
    opt_repo = OptimizationResultRepository()

    # 1. Fetch active routes
    active_routes = route_repo.list_active()
    if not active_routes:
        return {
            'success': False,
            'message': 'No active routes found in the database to optimize.'
        }

    # 2. Fetch available buses
    available_buses = bus_repo.list_available()
    if not available_buses:
        # Fallback to in-service buses if none marked strictly "Available"
        available_buses = bus_repo.list_all()

    if not available_buses:
        return {
            'success': False,
            'message': 'No buses found in the database to allocate.'
        }

    # 3. Retrieve passenger demand per route
    aggregate_demand = demand_repo.get_aggregate_demand_by_route(time_period=time_period, date=date)
    demand_map = {item['route_id']: item['total_passengers'] for item in aggregate_demand}

    # Prepare route data enriched with demand
    prepared_routes = []
    for r in active_routes:
        r_id = r.get('route_id')
        # Default nominal demand if no specific records exist
        demand = demand_map.get(r_id, 120)
        prepared_routes.append({
            'route_id': r_id,
            'route_name': r.get('route_name', r_id),
            'route_number': r.get('route_number', ''),
            'demand': demand,
            'estimated_duration_mins': r.get('estimated_duration_mins', 45),
            'stops_count': len(r.get('stops', []))
        })

    # 4. Run Baseline Allocation
    baseline_result = baseline_uniform_allocation(prepared_routes, available_buses)

    # 5. Run Greedy Optimization Heuristic
    optimized_result = greedy_bus_allocation(prepared_routes, available_buses)

    # 6. Calculate comparative improvement metrics
    base_m = baseline_result['metrics']
    opt_m = optimized_result['metrics']

    # Waiting time reduction %
    if base_m.get('avg_waiting_time_mins', 0) > 0:
        wait_reduction_pct = round(
            ((base_m['avg_waiting_time_mins'] - opt_m['avg_waiting_time_mins']) / base_m['avg_waiting_time_mins']) * 100, 1
        )
    else:
        wait_reduction_pct = 0.0

    # Utilization gain %
    util_gain_pct = round(opt_m.get('avg_bus_utilization_pct', 0) - base_m.get('avg_bus_utilization_pct', 0), 1)

    # Unmet demand reduction %
    if base_m.get('total_unmet', 0) > 0:
        unmet_reduction_pct = round(
            ((base_m['total_unmet'] - opt_m['total_unmet']) / base_m['total_unmet']) * 100, 1
        )
    else:
        unmet_reduction_pct = 100.0 if opt_m.get('total_unmet', 0) == 0 else 0.0

    exec_time_ms = round((time.perf_counter() - start_clock) * 1000, 2)

    result_payload = {
        'optimization_id': f"OPT{int(time.time())}",
        'scenario_name': scenario_name,
        'timestamp': datetime.utcnow().isoformat(),
        'parameters': {
            'time_period': time_period or 'All / Peak Analysis',
            'date': date or datetime.utcnow().strftime('%Y-%m-%d'),
            'total_routes': len(prepared_routes),
            'total_buses_pool': len(available_buses),
            'planning_period_mins': 60
        },
        'metrics_baseline': base_m,
        'metrics_optimized': opt_m,
        'improvements': {
            'waiting_time_reduction_pct': wait_reduction_pct,
            'utilization_gain_pct': util_gain_pct,
            'unmet_demand_reduction_pct': unmet_reduction_pct
        },
        'unmet_summary': optimized_result.get('unmet_summary', {}),
        'route_comparison': [
            {
                'route_id': opt_r['route_id'],
                'route_name': opt_r['route_name'],
                'demand': opt_r['demand'],
                'baseline_buses': next((b['bus_count'] for b in baseline_result['routes'] if b['route_id'] == opt_r['route_id']), 0),
                'optimized_buses': opt_r['bus_count'],
                'baseline_waiting_mins': next((b['avg_waiting_time_mins'] for b in baseline_result['routes'] if b['route_id'] == opt_r['route_id']), 0),
                'optimized_waiting_mins': opt_r['avg_waiting_time_mins'],
                'baseline_utilization_pct': next((b['bus_utilization_pct'] for b in baseline_result['routes'] if b['route_id'] == opt_r['route_id']), 0),
                'optimized_utilization_pct': opt_r['bus_utilization_pct'],
                'optimized_service_interval_mins': opt_r['service_interval_mins'],
                'buses_assigned': [b['bus_number'] for b in opt_r['buses_assigned']]
            }
            for opt_r in optimized_result['routes']
        ],
        'execution_time_ms': exec_time_ms,
        'success': True
    }

    # Save to MongoDB
    try:
        opt_repo.create(result_payload)
    except Exception as e:
        # Don't let write failure crash the return
        pass

    return result_payload
