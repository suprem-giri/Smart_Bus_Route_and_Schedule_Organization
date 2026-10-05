"""
Graph Representation of Public Bus Transit Network.
Represents bus stops as vertices (nodes) and route segments as directed/bidirectional edges.
"""

from collections import defaultdict
import math


class TransitEdge:
    def __init__(self, from_stop_id, to_stop_id, distance_km, travel_time_mins, route_id, route_number=""):
        self.from_stop_id = from_stop_id
        self.to_stop_id = to_stop_id
        self.distance_km = float(distance_km)
        self.travel_time_mins = float(travel_time_mins)
        self.route_id = route_id
        self.route_number = route_number

    def weight(self, metric='distance'):
        if metric == 'time':
            return self.travel_time_mins
        return self.distance_km


def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculates great-circle distance between two geographic coordinates in kilometers."""
    R = 6371.0  # Earth radius in kilometers
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return round(R * c, 2)


class TransitGraph:
    def __init__(self):
        self.nodes = {}  # stop_id -> stop_dict
        self.adj = defaultdict(list)  # stop_id -> list of TransitEdge

    def add_node(self, stop_id, stop_data):
        self.nodes[stop_id] = stop_data

    def add_edge(self, from_stop, to_stop, distance_km, travel_time_mins, route_id, route_number=""):
        edge = TransitEdge(from_stop, to_stop, distance_km, travel_time_mins, route_id, route_number)
        self.adj[from_stop].append(edge)

    def get_neighbors(self, stop_id):
        return self.adj.get(stop_id, [])

    @classmethod
    def from_database(cls, stop_repo, route_repo):
        """Constructs transit graph directly from MongoDB stops and routes collections."""
        graph = cls()

        # Load all stops
        stops = stop_repo.list_all()
        for s in stops:
            graph.add_node(s['stop_id'], s)

        # Load all active routes and construct edges between consecutive stops
        routes = route_repo.list_active()
        for r in routes:
            route_id = r.get('route_id')
            route_number = r.get('route_number', '')
            stops_list = r.get('stops', [])
            stop_details = {sd['stop_id']: sd for sd in r.get('stop_details', [])}

            for i in range(len(stops_list) - 1):
                u = stops_list[i]
                v = stops_list[i + 1]

                # Extract distance and time
                sd = stop_details.get(v, {})
                dist = sd.get('distance_from_prev_km')
                time_mins = sd.get('time_from_prev_mins')

                # Fallback to coordinate distance if not specified
                if dist is None or dist <= 0:
                    u_node = graph.nodes.get(u)
                    v_node = graph.nodes.get(v)
                    if u_node and v_node:
                        dist = haversine_distance(
                            float(u_node.get('latitude', 0)), float(u_node.get('longitude', 0)),
                            float(v_node.get('latitude', 0)), float(v_node.get('longitude', 0))
                        )
                        # Assume average urban bus speed 20 km/h
                        time_mins = max(3, round((dist / 20.0) * 60))
                    else:
                        dist = 2.0
                        time_mins = 6

                if time_mins is None or time_mins <= 0:
                    time_mins = max(3, round((dist / 20.0) * 60))

                # Add directed edge for route flow
                graph.add_edge(u, v, dist, time_mins, route_id, route_number)

        return graph
