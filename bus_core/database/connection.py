"""
MongoDB Connection Manager and Collection Initialization.
Provides centralized access to the MongoDB client and databases with auto-indexing.
"""

import logging
from django.conf import settings
from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.errors import ConnectionFailure, PyMongoError

logger = logging.getLogger(__name__)

_mongo_client = None
_mongo_db = None


def get_mongo_client():
    """
    Returns a singleton MongoClient instance.
    """
    global _mongo_client
    if _mongo_client is None:
        uri = getattr(settings, 'MONGODB_URI', 'mongodb://localhost:27017/')
        try:
            _mongo_client = MongoClient(
                uri,
                serverSelectionTimeoutMS=3000,
                connectTimeoutMS=3000,
                maxPoolSize=50
            )
            # Ping database to confirm connection
            _mongo_client.admin.command('ping')
            logger.info("MongoDB client connected successfully.")
        except ConnectionFailure as e:
            logger.error(f"Failed to connect to MongoDB at {uri}: {e}")
            raise
    return _mongo_client


def get_database():
    """
    Returns the MongoDB database handle.
    """
    global _mongo_db
    if _mongo_db is None:
        client = get_mongo_client()
        db_name = getattr(settings, 'MONGODB_NAME', 'smart_bus_optimization_db')
        _mongo_db = client[db_name]
        ensure_indexes(_mongo_db)
    return _mongo_db


def ensure_indexes(db):
    """
    Ensures optimal indexes exist for all application collections.
    """
    try:
        # Users indexes
        db.users.create_index([("user_id", ASCENDING)], unique=True)
        db.users.create_index([("username", ASCENDING)], unique=True)
        db.users.create_index([("email", ASCENDING)], unique=True)

        # Buses indexes
        db.buses.create_index([("bus_id", ASCENDING)], unique=True)
        db.buses.create_index([("bus_number", ASCENDING)], unique=True)
        db.buses.create_index([("status", ASCENDING)])

        # Drivers indexes
        db.drivers.create_index([("driver_id", ASCENDING)], unique=True)
        db.drivers.create_index([("license_number", ASCENDING)], unique=True)
        db.drivers.create_index([("status", ASCENDING)])

        # Bus Stops indexes
        db.bus_stops.create_index([("stop_id", ASCENDING)], unique=True)
        db.bus_stops.create_index([("name", ASCENDING)])
        db.bus_stops.create_index([("latitude", ASCENDING), ("longitude", ASCENDING)])

        # Routes indexes
        db.routes.create_index([("route_id", ASCENDING)], unique=True)
        db.routes.create_index([("route_number", ASCENDING)], unique=True)
        db.routes.create_index([("active", ASCENDING)])

        # Schedules indexes
        db.schedules.create_index([("schedule_id", ASCENDING)], unique=True)
        db.schedules.create_index([("route_id", ASCENDING)])
        db.schedules.create_index([("bus_id", ASCENDING)])

        # Trips indexes
        db.trips.create_index([("trip_id", ASCENDING)], unique=True)
        db.trips.create_index([("driver_id", ASCENDING)])
        db.trips.create_index([("date", ASCENDING), ("status", ASCENDING)])

        # Demand records indexes
        db.demand_records.create_index([("demand_id", ASCENDING)], unique=True, sparse=True)
        db.demand_records.create_index([
            ("route_id", ASCENDING),
            ("stop_id", ASCENDING),
            ("date", ASCENDING),
            ("time_period", ASCENDING)
        ])

        # Optimization results indexes
        db.optimization_results.create_index([("optimization_id", ASCENDING)], unique=True)
        db.optimization_results.create_index([("timestamp", DESCENDING)])

        logger.info("MongoDB indexes verified.")
    except PyMongoError as e:
        logger.warning(f"Error ensuring MongoDB indexes: {e}")
