"""
MongoDB Repositories (Data Access Layer) for Smart Public Bus System.
Provides strongly-typed, sanitized, and serialized document access.
"""

from datetime import datetime
from bson import ObjectId
from django.contrib.auth.hashers import make_password, check_password
from .connection import get_database


def clean_mongo_doc(doc):
    """Recursively converts BSON ObjectId and datetimes to JSON/Python serializable formats."""
    if doc is None:
        return None
    if isinstance(doc, list):
        return [clean_mongo_doc(item) for item in doc]
    if isinstance(doc, dict):
        result = {}
        for k, v in doc.items():
            if k == '_id':
                result['id'] = str(v)
            elif isinstance(v, ObjectId):
                result[k] = str(v)
            elif isinstance(v, datetime):
                result[k] = v.isoformat()
            elif isinstance(v, (dict, list)):
                result[k] = clean_mongo_doc(v)
            else:
                result[k] = v
        return result
    return doc


class BaseRepository:
    def __init__(self, collection_name):
        self.collection_name = collection_name

    @property
    def col(self):
        return get_database()[self.collection_name]

    def find_one(self, query):
        doc = self.col.find_one(query)
        return clean_mongo_doc(doc)

    def find_all(self, query=None, sort=None, limit=0):
        query = query or {}
        cursor = self.col.find(query)
        if sort:
            cursor = cursor.sort(sort)
        if limit > 0:
            cursor = cursor.limit(limit)
        return [clean_mongo_doc(d) for d in cursor]

    def count(self, query=None):
        query = query or {}
        return self.col.count_documents(query)

    def insert(self, data):
        if 'created_at' not in data:
            data['created_at'] = datetime.utcnow().isoformat()
        res = self.col.insert_one(data)
        data['id'] = str(res.inserted_id)
        data.pop('_id', None)
        return clean_mongo_doc(data)

    def update(self, query, data):
        data['updated_at'] = datetime.utcnow().isoformat()
        self.col.update_one(query, {'$set': data})
        return self.find_one(query)

    def delete(self, query):
        res = self.col.delete_one(query)
        return res.deleted_count > 0


class UserRepository(BaseRepository):
    def __init__(self):
        super().__init__('users')

    def get_by_id(self, user_id):
        return self.find_one({"user_id": user_id})

    def get_by_username(self, username):
        return self.find_one({"username": username})

    def get_by_email(self, email):
        return self.find_one({"email": email})

    def create_user(self, username, email, password, role='passenger', full_name='', phone=''):
        # Auto-generate next user_id
        count = self.count() + 1
        user_id = f"U{count:03d}"
        user_doc = {
            "user_id": user_id,
            "username": username,
            "email": email,
            "password_hash": make_password(password),
            "role": role,  # 'admin', 'manager', 'driver', 'passenger'
            "full_name": full_name or username.title(),
            "phone": phone,
            "active": True,
            "created_at": datetime.utcnow().isoformat()
        }
        return self.insert(user_doc)

    def verify_password(self, user, raw_password):
        if not user or 'password_hash' not in user:
            return False
        return check_password(raw_password, user['password_hash'])

    def update_password(self, user_id, new_password):
        return self.update({"user_id": user_id}, {"password_hash": make_password(new_password)})


class BusRepository(BaseRepository):
    def __init__(self):
        super().__init__('buses')

    def get_by_id(self, bus_id):
        return self.find_one({"bus_id": bus_id})

    def get_by_number(self, bus_number):
        return self.find_one({"bus_number": bus_number})

    def list_all(self):
        return self.find_all(sort=[("bus_number", 1)])

    def list_available(self):
        return self.find_all({"status": "Available"}, sort=[("capacity", -1)])

    def create(self, bus_data):
        if 'bus_id' not in bus_data or not bus_data['bus_id']:
            count = self.count() + 1
            bus_data['bus_id'] = f"B{count:03d}"
        return self.insert(bus_data)


class DriverRepository(BaseRepository):
    def __init__(self):
        super().__init__('drivers')

    def get_by_id(self, driver_id):
        return self.find_one({"driver_id": driver_id})

    def list_all(self):
        return self.find_all(sort=[("name", 1)])

    def list_active(self):
        return self.find_all({"status": "Active"}, sort=[("name", 1)])

    def create(self, driver_data):
        if 'driver_id' not in driver_data or not driver_data['driver_id']:
            count = self.count() + 1
            driver_data['driver_id'] = f"D{count:03d}"
        return self.insert(driver_data)


class StopRepository(BaseRepository):
    def __init__(self):
        super().__init__('bus_stops')

    def get_by_id(self, stop_id):
        return self.find_one({"stop_id": stop_id})

    def list_all(self):
        return self.find_all(sort=[("name", 1)])

    def get_by_ids(self, stop_ids):
        return self.find_all({"stop_id": {"$in": stop_ids}})

    def create(self, stop_data):
        if 'stop_id' not in stop_data or not stop_data['stop_id']:
            count = self.count() + 1
            stop_data['stop_id'] = f"S{count:03d}"
        return self.insert(stop_data)


class RouteRepository(BaseRepository):
    def __init__(self):
        super().__init__('routes')

    def get_by_id(self, route_id):
        return self.find_one({"route_id": route_id})

    def list_all(self):
        return self.find_all(sort=[("route_number", 1)])

    def list_active(self):
        return self.find_all({"active": True}, sort=[("route_number", 1)])

    def create(self, route_data):
        if 'route_id' not in route_data or not route_data['route_id']:
            count = self.count() + 1
            route_data['route_id'] = f"R{count:03d}"
        return self.insert(route_data)


class ScheduleRepository(BaseRepository):
    def __init__(self):
        super().__init__('schedules')

    def get_by_id(self, schedule_id):
        return self.find_one({"schedule_id": schedule_id})

    def list_all(self):
        return self.find_all(sort=[("departure_time", 1)])

    def list_by_route(self, route_id):
        return self.find_all({"route_id": route_id}, sort=[("departure_time", 1)])

    def create(self, schedule_data):
        if 'schedule_id' not in schedule_data or not schedule_data['schedule_id']:
            count = self.count() + 1
            schedule_data['schedule_id'] = f"SCH{count:03d}"
        return self.insert(schedule_data)


class TripRepository(BaseRepository):
    def __init__(self):
        super().__init__('trips')

    def get_by_id(self, trip_id):
        return self.find_one({"trip_id": trip_id})

    def list_all(self, limit=50):
        return self.find_all(sort=[("date", -1), ("scheduled_departure", -1)], limit=limit)

    def list_by_driver(self, driver_id):
        return self.find_all({"driver_id": driver_id}, sort=[("date", -1), ("scheduled_departure", -1)])

    def create(self, trip_data):
        if 'trip_id' not in trip_data or not trip_data['trip_id']:
            count = self.count() + 1
            trip_data['trip_id'] = f"TRP{count:03d}"
        return self.insert(trip_data)

    def update_status(self, trip_id, status, notes=None, current_stop_id=None, delay_minutes=None):
        data = {"status": status}
        if notes is not None:
            data["notes"] = notes
        if current_stop_id is not None:
            data["current_stop_id"] = current_stop_id
        if delay_minutes is not None:
            data["delay_minutes"] = delay_minutes
        if status == "Departed" and "actual_departure" not in data:
            data["actual_departure"] = datetime.now().strftime("%H:%M")
        elif status == "Completed" and "actual_arrival" not in data:
            data["actual_arrival"] = datetime.now().strftime("%H:%M")
        updated = self.update({"trip_id": trip_id}, data)
        if status in ("Completed", "Cancelled"):
            self.clear_location(trip_id)
            updated = self.get_by_id(trip_id)
        return updated

    def update_location(self, trip_id, latitude, longitude, accuracy=None, speed=None):
        location = {
            "latitude": latitude,
            "longitude": longitude,
            "location_updated_at": datetime.utcnow().isoformat() + "Z",
        }
        if accuracy is not None:
            location["location_accuracy_m"] = accuracy
        if speed is not None:
            location["location_speed_mps"] = speed
        return self.update({"trip_id": trip_id}, location)

    def clear_location(self, trip_id):
        self.col.update_one(
            {"trip_id": trip_id},
            {
                "$unset": {
                    "latitude": "",
                    "longitude": "",
                    "location_updated_at": "",
                    "location_accuracy_m": "",
                    "location_speed_mps": "",
                },
                "$set": {"updated_at": datetime.utcnow().isoformat()},
            },
        )
        return self.get_by_id(trip_id)


class DemandRepository(BaseRepository):
    def __init__(self):
        super().__init__('demand_records')

    def get_by_id(self, demand_id):
        return self.find_one({"demand_id": demand_id})

    def list_all(self, limit=200):
        return self.find_all(sort=[("date", -1), ("time_period", 1)], limit=limit)

    def list_by_route_and_period(self, route_id=None, time_period=None, date=None):
        query = {}
        if route_id:
            query['route_id'] = route_id
        if time_period:
            query['time_period'] = time_period
        if date:
            query['date'] = date
        return self.find_all(query, sort=[("passenger_count", -1)])

    def get_aggregate_demand_by_route(self, time_period=None, date=None):
        """Returns total passenger demand grouped by route_id."""
        match_stage = {}
        if time_period:
            match_stage['time_period'] = time_period
        if date:
            match_stage['date'] = date

        pipeline = []
        if match_stage:
            pipeline.append({'$match': match_stage})
        pipeline.append({
            '$group': {
                '_id': '$route_id',
                'total_passengers': {'$sum': '$passenger_count'},
                'record_count': {'$sum': 1},
                'stops_count': {'$addToSet': '$stop_id'}
            }
        })
        pipeline.append({'$sort': {'total_passengers': -1}})

        res = list(self.col.aggregate(pipeline))
        results = []
        for item in res:
            results.append({
                'route_id': item['_id'],
                'total_passengers': item['total_passengers'],
                'record_count': item['record_count'],
                'unique_stops': len(item['stops_count'])
            })
        return results

    def create(self, demand_data):
        if 'demand_id' not in demand_data or not demand_data['demand_id']:
            count = self.count() + 1
            demand_data['demand_id'] = f"DEM{count:04d}"
        return self.insert(demand_data)

    def batch_insert(self, records):
        if not records:
            return 0
        current_count = self.count()
        for idx, rec in enumerate(records, start=current_count + 1):
            if 'demand_id' not in rec or not rec['demand_id']:
                rec['demand_id'] = f"DEM{idx:04d}"
            if 'created_at' not in rec:
                rec['created_at'] = datetime.utcnow().isoformat()
        res = self.col.insert_many(records)
        return len(res.inserted_ids)


class OptimizationResultRepository(BaseRepository):
    def __init__(self):
        super().__init__('optimization_results')

    def get_by_id(self, optimization_id):
        return self.find_one({"optimization_id": optimization_id})

    def list_recent(self, limit=20):
        return self.find_all(sort=[("timestamp", -1)], limit=limit)

    def create(self, opt_data):
        if 'optimization_id' not in opt_data or not opt_data['optimization_id']:
            count = self.count() + 1
            opt_data['optimization_id'] = f"OPT{count:03d}"
        if 'timestamp' not in opt_data:
            opt_data['timestamp'] = datetime.utcnow().isoformat()
        return self.insert(opt_data)
