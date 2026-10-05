"""
Algorithm 1: Dijkstra's Shortest Path Algorithm for Public Bus Transit Networks.
Calculates the minimum-cost path between bus stops based on distance (km) or travel time (minutes).
"""

import heapq
import time


def calculate_fare(distance_km):
    """
    Standard progressive fare rule:
    Base fare: 20 for first 4 km, then +3 per additional km.
    """
    if distance_km <= 0:
        return 0
    if distance_km <= 4.0:
        return 20.0
    extra_km = distance_km - 4.0
    return round(20.0 + (extra_km * 3.0), 2)


def dijkstra_shortest_path(graph, source_id, destination_id, metric='distance'):
    """
    Executes Dijkstra's Algorithm on TransitGraph.
    
    Args:
        graph (TransitGraph): The transit graph containing nodes and adjacency lists.
        source_id (str): Source bus stop ID (e.g., 'S001').
        destination_id (str): Destination bus stop ID (e.g., 'S008').
        metric (str): 'distance' (default) or 'time'.
        
    Returns:
        dict: Detailed result containing success flag, path nodes, path details,
              total distance, total time, estimated fare, and algorithm execution time.
    """
    start_time = time.perf_counter()

    if source_id not in graph.nodes:
        return {
            'success': False,
            'message': f"Source stop '{source_id}' does not exist in the network.",
            'path': [],
            'cost': None
        }

    if destination_id not in graph.nodes:
        return {
            'success': False,
            'message': f"Destination stop '{destination_id}' does not exist in the network.",
            'path': [],
            'cost': None
        }

    # Case: Source and destination are identical
    if source_id == destination_id:
        source_node = graph.nodes[source_id]
        return {
            'success': True,
            'message': 'Source and destination are the same bus stop.',
            'metric_used': metric,
            'total_cost': 0.0,
            'total_distance_km': 0.0,
            'total_travel_time_mins': 0.0,
            'estimated_fare': 0.0,
            'stops_count': 1,
            'path': [source_id],
            'path_details': [{
                'stop_id': source_id,
                'name': source_node.get('name', ''),
                'latitude': source_node.get('latitude', 0.0),
                'longitude': source_node.get('longitude', 0.0),
                'cumulative_dist_km': 0.0,
                'cumulative_time_mins': 0.0,
                'route_number': None
            }],
            'execution_time_ms': round((time.perf_counter() - start_time) * 1000, 3)
        }

    # Step 1: Initialize distances and previous pointers
    distances = {node_id: float('inf') for node_id in graph.nodes}
    previous_node = {node_id: None for node_id in graph.nodes}
    previous_edge = {node_id: None for node_id in graph.nodes}

    # Step 2: Distance to source is 0
    distances[source_id] = 0.0

    # Step 3: Insert (0, source) into min-priority queue
    # Format in heap: (cost, stop_id)
    pq = [(0.0, source_id)]

    visited = set()

    # Step 4: Min-heap processing
    while pq:
        current_cost, u = heapq.heappop(pq)

        if current_cost > distances[u]:
            continue

        if u in visited:
            continue
        visited.add(u)

        if u == destination_id:
            break

        for edge in graph.get_neighbors(u):
            v = edge.to_stop_id
            if v not in distances:
                distances[v] = float('inf')

            weight = edge.weight(metric)
            new_cost = current_cost + weight

            if new_cost < distances[v]:
                distances[v] = new_cost
                previous_node[v] = u
                previous_edge[v] = edge
                heapq.heappush(pq, (new_cost, v))

    # Step 5: Check if reachable
    if distances[destination_id] == float('inf'):
        exec_time = round((time.perf_counter() - start_time) * 1000, 3)
        return {
            'success': False,
            'message': f"No connected transit route exists between '{graph.nodes[source_id].get('name')}' and '{graph.nodes[destination_id].get('name')}'.",
            'path': [],
            'cost': None,
            'execution_time_ms': exec_time
        }

    # Step 6: Reconstruct the path backwards
    path = []
    curr = destination_id
    edges_traversed = []

    while curr is not None:
        path.append(curr)
        edge = previous_edge[curr]
        if edge is not None:
            edges_traversed.append(edge)
        curr = previous_node[curr]

    path.reverse()
    edges_traversed.reverse()

    # Step 7: Calculate totals and structured path details
    total_dist = sum(e.distance_km for e in edges_traversed)
    total_time = sum(e.travel_time_mins for e in edges_traversed)

    path_details = []
    cum_dist = 0.0
    cum_time = 0.0

    for i, stop_id in enumerate(path):
        node = graph.nodes.get(stop_id, {})
        edge_used = edges_traversed[i - 1] if i > 0 else None

        if edge_used:
            cum_dist += edge_used.distance_km
            cum_time += edge_used.travel_time_mins

        path_details.append({
            'sequence': i + 1,
            'stop_id': stop_id,
            'name': node.get('name', stop_id),
            'latitude': float(node.get('latitude', 0.0)),
            'longitude': float(node.get('longitude', 0.0)),
            'zone': node.get('zone', ''),
            'cumulative_dist_km': round(cum_dist, 2),
            'cumulative_time_mins': round(cum_time, 1),
            'segment_distance_km': round(edge_used.distance_km, 2) if edge_used else 0.0,
            'segment_time_mins': round(edge_used.travel_time_mins, 1) if edge_used else 0.0,
            'route_id': edge_used.route_id if edge_used else None,
            'route_number': edge_used.route_number if edge_used else None,
        })

    # Identify routes used and transfer points
    routes_used = []
    for e in edges_traversed:
        if e.route_number and e.route_number not in routes_used:
            routes_used.append(e.route_number)

    exec_time = round((time.perf_counter() - start_time) * 1000, 3)

    return {
        'success': True,
        'metric_used': metric,
        'total_cost': round(distances[destination_id], 2),
        'total_distance_km': round(total_dist, 2),
        'total_travel_time_mins': round(total_time, 1),
        'estimated_fare': calculate_fare(total_dist),
        'stops_count': len(path),
        'path': path,
        'path_details': path_details,
        'routes_used': routes_used,
        'transfers_count': max(0, len(routes_used) - 1),
        'execution_time_ms': exec_time
    }
