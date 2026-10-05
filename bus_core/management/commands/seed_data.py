"""
Management command to seed the MongoDB database with realistic public transit data.
Includes stops, routes, buses, drivers, default users, passenger demand records, and schedules.
"""

from datetime import datetime
from django.core.management.base import BaseCommand
from bus_core.database.connection import get_database, ensure_indexes
from bus_core.database.repositories import (
    UserRepository, BusRepository, DriverRepository, StopRepository,
    RouteRepository, ScheduleRepository, TripRepository, DemandRepository
)


class Command(BaseCommand):
    help = "Populate MongoDB with realistic urban bus transit data"

    def handle(self, *args, **options):
        db = get_database()
        ensure_indexes(db)
        self.stdout.write(self.style.NOTICE("Clearing existing sample transit collections..."))

        # Clear collections
        for col_name in ['users', 'buses', 'drivers', 'bus_stops', 'routes', 'schedules', 'trips', 'demand_records', 'optimization_results']:
            db[col_name].delete_many({})

        self.stdout.write("1. Creating Users for all roles...")
        user_repo = UserRepository()
        user_repo.create_user('admin', 'admin@smartbus.org', 'admin123', role='admin', full_name='System Administrator', phone='+977-9801000001')
        user_repo.create_user('manager', 'manager@smartbus.org', 'manager123', role='manager', full_name='Aarav Sharma (Transport Ops)', phone='+977-9801000002')
        user_repo.create_user('driver1', 'driver1@smartbus.org', 'driver123', role='driver', full_name='Ram Bahadur Thapa', phone='+977-9841234501')
        user_repo.create_user('driver2', 'driver2@smartbus.org', 'driver123', role='driver', full_name='Krishna Shrestha', phone='+977-9841234502')
        user_repo.create_user('passenger1', 'passenger@example.com', 'passenger123', role='passenger', full_name='Pooja Adhikari', phone='+977-9860123456')

        self.stdout.write("2. Creating Bus Stops with Geographic Coordinates...")
        stop_repo = StopRepository()
        stops_data = [
            {'stop_id': 'S001', 'name': 'Ratna Park Central Terminal', 'code': 'RPC', 'latitude': 27.7058, 'longitude': 85.3157, 'zone': 'City Center', 'facilities': ['Shelter', 'Digital Display', 'Seating', 'Lighting'], 'is_terminal': True},
            {'stop_id': 'S002', 'name': 'Maitighar Mandala Junction', 'code': 'MMJ', 'latitude': 27.6936, 'longitude': 85.3218, 'zone': 'City Center', 'facilities': ['Shelter', 'Lighting'], 'is_terminal': False},
            {'stop_id': 'S003', 'name': 'Baneshwor Chok Hub', 'code': 'BCH', 'latitude': 27.6915, 'longitude': 85.3420, 'zone': 'East Zone', 'facilities': ['Shelter', 'Digital Display', 'Lighting'], 'is_terminal': False},
            {'stop_id': 'S004', 'name': 'Koteshwor Interchange', 'code': 'KTW', 'latitude': 27.6775, 'longitude': 85.3486, 'zone': 'East Hub', 'facilities': ['Shelter', 'Digital Display', 'Seating', 'Lighting'], 'is_terminal': True},
            {'stop_id': 'S005', 'name': 'Lagankhel Bus Park (Patan)', 'code': 'LGK', 'latitude': 27.6672, 'longitude': 85.3228, 'zone': 'South Hub', 'facilities': ['Shelter', 'Digital Display', 'Seating', 'Lighting'], 'is_terminal': True},
            {'stop_id': 'S006', 'name': 'Jawalakhel Chok', 'code': 'JWL', 'latitude': 27.6738, 'longitude': 85.3122, 'zone': 'South Zone', 'facilities': ['Shelter', 'Lighting'], 'is_terminal': False},
            {'stop_id': 'S007', 'name': 'Tripureshwor Cultural Crossing', 'code': 'TPR', 'latitude': 27.6953, 'longitude': 85.3124, 'zone': 'City Center', 'facilities': ['Shelter', 'Lighting'], 'is_terminal': False},
            {'stop_id': 'S008', 'name': 'Kalanki Mobility Hub', 'code': 'KLK', 'latitude': 27.6939, 'longitude': 85.2818, 'zone': 'West Hub', 'facilities': ['Shelter', 'Digital Display', 'Seating', 'Lighting'], 'is_terminal': True},
            {'stop_id': 'S009', 'name': 'Swayambhu Ring Road', 'code': 'SWY', 'latitude': 27.7150, 'longitude': 85.2860, 'zone': 'West Zone', 'facilities': ['Shelter', 'Lighting'], 'is_terminal': False},
            {'stop_id': 'S010', 'name': 'Balaju Bypass Terminal', 'code': 'BLJ', 'latitude': 27.7335, 'longitude': 85.3025, 'zone': 'North-West Hub', 'facilities': ['Shelter', 'Digital Display', 'Seating'], 'is_terminal': True},
            {'stop_id': 'S011', 'name': 'Maharajgunj Chakrapath', 'code': 'MRG', 'latitude': 27.7360, 'longitude': 85.3312, 'zone': 'North Hub', 'facilities': ['Shelter', 'Lighting'], 'is_terminal': False},
            {'stop_id': 'S012', 'name': 'Sukedhara Chok', 'code': 'SKD', 'latitude': 27.7280, 'longitude': 85.3470, 'zone': 'North-East Zone', 'facilities': ['Shelter'], 'is_terminal': False},
            {'stop_id': 'S013', 'name': 'Chabahil Stupa Chok', 'code': 'CBH', 'latitude': 27.7174, 'longitude': 85.3482, 'zone': 'East Zone', 'facilities': ['Shelter', 'Lighting'], 'is_terminal': False},
            {'stop_id': 'S014', 'name': 'Gaushala Airport Gateway', 'code': 'GSL', 'latitude': 27.7062, 'longitude': 85.3495, 'zone': 'East Zone', 'facilities': ['Shelter', 'Digital Display'], 'is_terminal': False},
            {'stop_id': 'S015', 'name': 'Thapathali Bridge', 'code': 'TPH', 'latitude': 27.6908, 'longitude': 85.3178, 'zone': 'South Central', 'facilities': ['Shelter', 'Lighting'], 'is_terminal': False},
        ]
        for s in stops_data:
            stop_repo.insert(s)

        self.stdout.write("3. Creating Bus Routes...")
        route_repo = RouteRepository()
        routes_data = [
            {
                'route_id': 'R001',
                'route_number': 'RT-01',
                'route_name': 'East-West Main Spine (Kalanki - Ratna Park - Koteshwor)',
                'stops': ['S008', 'S007', 'S001', 'S002', 'S003', 'S004'],
                'stop_details': [
                    {'stop_id': 'S008', 'sequence': 1, 'distance_from_prev_km': 0.0, 'time_from_prev_mins': 0},
                    {'stop_id': 'S007', 'sequence': 2, 'distance_from_prev_km': 3.5, 'time_from_prev_mins': 12},
                    {'stop_id': 'S001', 'sequence': 3, 'distance_from_prev_km': 1.8, 'time_from_prev_mins': 7},
                    {'stop_id': 'S002', 'sequence': 4, 'distance_from_prev_km': 1.5, 'time_from_prev_mins': 6},
                    {'stop_id': 'S003', 'sequence': 5, 'distance_from_prev_km': 2.3, 'time_from_prev_mins': 9},
                    {'stop_id': 'S004', 'sequence': 6, 'distance_from_prev_km': 2.0, 'time_from_prev_mins': 8},
                ],
                'total_distance_km': 11.1,
                'estimated_duration_mins': 42,
                'base_fare': 25.0,
                'active': True
            },
            {
                'route_id': 'R002',
                'route_number': 'RT-02',
                'route_name': 'North-South Patan Express (Balaju - Ratna Park - Lagankhel)',
                'stops': ['S010', 'S009', 'S001', 'S015', 'S006', 'S005'],
                'stop_details': [
                    {'stop_id': 'S010', 'sequence': 1, 'distance_from_prev_km': 0.0, 'time_from_prev_mins': 0},
                    {'stop_id': 'S009', 'sequence': 2, 'distance_from_prev_km': 2.6, 'time_from_prev_mins': 9},
                    {'stop_id': 'S001', 'sequence': 3, 'distance_from_prev_km': 3.2, 'time_from_prev_mins': 14},
                    {'stop_id': 'S015', 'sequence': 4, 'distance_from_prev_km': 1.9, 'time_from_prev_mins': 8},
                    {'stop_id': 'S006', 'sequence': 5, 'distance_from_prev_km': 2.1, 'time_from_prev_mins': 9},
                    {'stop_id': 'S005', 'sequence': 6, 'distance_from_prev_km': 1.4, 'time_from_prev_mins': 6},
                ],
                'total_distance_km': 11.2,
                'estimated_duration_mins': 46,
                'base_fare': 25.0,
                'active': True
            },
            {
                'route_id': 'R003',
                'route_number': 'RT-03',
                'route_name': 'Ring Road North Arc (Kalanki - Balaju - Maharajgunj - Chabahil - Koteshwor)',
                'stops': ['S008', 'S009', 'S010', 'S011', 'S012', 'S013', 'S014', 'S004'],
                'stop_details': [
                    {'stop_id': 'S008', 'sequence': 1, 'distance_from_prev_km': 0.0, 'time_from_prev_mins': 0},
                    {'stop_id': 'S009', 'sequence': 2, 'distance_from_prev_km': 2.5, 'time_from_prev_mins': 8},
                    {'stop_id': 'S010', 'sequence': 3, 'distance_from_prev_km': 2.8, 'time_from_prev_mins': 9},
                    {'stop_id': 'S011', 'sequence': 4, 'distance_from_prev_km': 3.1, 'time_from_prev_mins': 10},
                    {'stop_id': 'S012', 'sequence': 5, 'distance_from_prev_km': 1.8, 'time_from_prev_mins': 6},
                    {'stop_id': 'S013', 'sequence': 6, 'distance_from_prev_km': 1.4, 'time_from_prev_mins': 5},
                    {'stop_id': 'S014', 'sequence': 7, 'distance_from_prev_km': 1.5, 'time_from_prev_mins': 6},
                    {'stop_id': 'S004', 'sequence': 8, 'distance_from_prev_km': 3.4, 'time_from_prev_mins': 11},
                ],
                'total_distance_km': 16.5,
                'estimated_duration_mins': 55,
                'base_fare': 30.0,
                'active': True
            },
            {
                'route_id': 'R004',
                'route_number': 'RT-04',
                'route_name': 'Airport - Central City Link (Ratna Park - Gaushala - Chabahil)',
                'stops': ['S001', 'S002', 'S003', 'S014', 'S013'],
                'stop_details': [
                    {'stop_id': 'S001', 'sequence': 1, 'distance_from_prev_km': 0.0, 'time_from_prev_mins': 0},
                    {'stop_id': 'S002', 'sequence': 2, 'distance_from_prev_km': 1.5, 'time_from_prev_mins': 6},
                    {'stop_id': 'S003', 'sequence': 3, 'distance_from_prev_km': 2.3, 'time_from_prev_mins': 9},
                    {'stop_id': 'S014', 'sequence': 4, 'distance_from_prev_km': 2.0, 'time_from_prev_mins': 7},
                    {'stop_id': 'S013', 'sequence': 5, 'distance_from_prev_km': 1.4, 'time_from_prev_mins': 5},
                ],
                'total_distance_km': 7.2,
                'estimated_duration_mins': 27,
                'base_fare': 20.0,
                'active': True
            },
            {
                'route_id': 'R005',
                'route_number': 'RT-05',
                'route_name': 'South-East Ring & Heritage Connector (Lagankhel - Koteshwor)',
                'stops': ['S005', 'S006', 'S015', 'S002', 'S003', 'S004'],
                'stop_details': [
                    {'stop_id': 'S005', 'sequence': 1, 'distance_from_prev_km': 0.0, 'time_from_prev_mins': 0},
                    {'stop_id': 'S006', 'sequence': 2, 'distance_from_prev_km': 1.4, 'time_from_prev_mins': 5},
                    {'stop_id': 'S015', 'sequence': 3, 'distance_from_prev_km': 2.1, 'time_from_prev_mins': 8},
                    {'stop_id': 'S002', 'sequence': 4, 'distance_from_prev_km': 0.9, 'time_from_prev_mins': 4},
                    {'stop_id': 'S003', 'sequence': 5, 'distance_from_prev_km': 2.3, 'time_from_prev_mins': 9},
                    {'stop_id': 'S004', 'sequence': 6, 'distance_from_prev_km': 2.0, 'time_from_prev_mins': 8},
                ],
                'total_distance_km': 8.7,
                'estimated_duration_mins': 34,
                'base_fare': 22.0,
                'active': True
            }
        ]
        for r in routes_data:
            route_repo.insert(r)

        self.stdout.write("4. Creating Drivers...")
        driver_repo = DriverRepository()
        drivers_data = [
            {'driver_id': 'D001', 'name': 'Ram Bahadur Thapa', 'license_number': 'DL-01-987651', 'phone': '+977-9841234501', 'experience_years': 8, 'status': 'Active', 'assigned_bus_id': 'B001'},
            {'driver_id': 'D002', 'name': 'Krishna Shrestha', 'license_number': 'DL-01-987652', 'phone': '+977-9841234502', 'experience_years': 6, 'status': 'Active', 'assigned_bus_id': 'B002'},
            {'driver_id': 'D003', 'name': 'Bikash Tamang', 'license_number': 'DL-01-987653', 'phone': '+977-9841234503', 'experience_years': 10, 'status': 'Active', 'assigned_bus_id': 'B003'},
            {'driver_id': 'D004', 'name': 'Dinesh Gurung', 'license_number': 'DL-01-987654', 'phone': '+977-9841234504', 'experience_years': 5, 'status': 'Active', 'assigned_bus_id': 'B004'},
            {'driver_id': 'D005', 'name': 'Sanjay Rai', 'license_number': 'DL-01-987655', 'phone': '+977-9841234505', 'experience_years': 7, 'status': 'Active', 'assigned_bus_id': 'B005'},
            {'driver_id': 'D006', 'name': 'Niroj Maharjan', 'license_number': 'DL-01-987656', 'phone': '+977-9841234506', 'experience_years': 4, 'status': 'Active', 'assigned_bus_id': 'B006'},
            {'driver_id': 'D007', 'name': 'Deepak KC', 'license_number': 'DL-01-987657', 'phone': '+977-9841234507', 'experience_years': 12, 'status': 'Active', 'assigned_bus_id': 'B007'},
            {'driver_id': 'D008', 'name': 'Santosh Silwal', 'license_number': 'DL-01-987658', 'phone': '+977-9841234508', 'experience_years': 9, 'status': 'Active', 'assigned_bus_id': 'B008'},
        ]
        for d in drivers_data:
            driver_repo.insert(d)

        self.stdout.write("5. Creating Bus Fleet...")
        bus_repo = BusRepository()
        buses_data = [
            {'bus_id': 'B001', 'bus_number': 'BA-2-KHA-101', 'registration_number': 'REG-101-2024', 'capacity': 45, 'model': 'Tata Starbus Ultra', 'bus_type': 'Standard', 'status': 'Available', 'assigned_driver_id': 'D001', 'assigned_route_id': 'R001'},
            {'bus_id': 'B002', 'bus_number': 'BA-2-KHA-102', 'registration_number': 'REG-102-2024', 'capacity': 45, 'model': 'Tata Starbus Ultra', 'bus_type': 'Standard', 'status': 'Available', 'assigned_driver_id': 'D002', 'assigned_route_id': 'R001'},
            {'bus_id': 'B003', 'bus_number': 'BA-2-KHA-103', 'registration_number': 'REG-103-2024', 'capacity': 55, 'model': 'Ashok Leyland Viking', 'bus_type': 'Express', 'status': 'Available', 'assigned_driver_id': 'D003', 'assigned_route_id': 'R003'},
            {'bus_id': 'B004', 'bus_number': 'BA-2-KHA-104', 'registration_number': 'REG-104-2024', 'capacity': 55, 'model': 'Ashok Leyland Viking', 'bus_type': 'Express', 'status': 'Available', 'assigned_driver_id': 'D004', 'assigned_route_id': 'R003'},
            {'bus_id': 'B005', 'bus_number': 'BA-2-KHA-105', 'registration_number': 'REG-105-2024', 'capacity': 40, 'model': 'BYD K9 Electric', 'bus_type': 'Electric', 'status': 'Available', 'assigned_driver_id': 'D005', 'assigned_route_id': 'R002'},
            {'bus_id': 'B006', 'bus_number': 'BA-2-KHA-106', 'registration_number': 'REG-106-2024', 'capacity': 40, 'model': 'BYD K9 Electric', 'bus_type': 'Electric', 'status': 'Available', 'assigned_driver_id': 'D006', 'assigned_route_id': 'R002'},
            {'bus_id': 'B007', 'bus_number': 'BA-2-KHA-107', 'registration_number': 'REG-107-2024', 'capacity': 30, 'model': 'Eicher Skyline Mini', 'bus_type': 'Mini', 'status': 'Available', 'assigned_driver_id': 'D007', 'assigned_route_id': 'R004'},
            {'bus_id': 'B008', 'bus_number': 'BA-2-KHA-108', 'registration_number': 'REG-108-2024', 'capacity': 30, 'model': 'Eicher Skyline Mini', 'bus_type': 'Mini', 'status': 'Available', 'assigned_driver_id': 'D008', 'assigned_route_id': 'R005'},
            {'bus_id': 'B009', 'bus_number': 'BA-2-KHA-109', 'registration_number': 'REG-109-2024', 'capacity': 50, 'model': 'Tata CityRide', 'bus_type': 'Standard', 'status': 'Available', 'assigned_driver_id': '', 'assigned_route_id': ''},
            {'bus_id': 'B010', 'bus_number': 'BA-2-KHA-110', 'registration_number': 'REG-110-2024', 'capacity': 50, 'model': 'Tata CityRide', 'bus_type': 'Standard', 'status': 'Available', 'assigned_driver_id': '', 'assigned_route_id': ''},
            {'bus_id': 'B011', 'bus_number': 'BA-2-KHA-111', 'registration_number': 'REG-111-2024', 'capacity': 45, 'model': 'BYD Electric Bus', 'bus_type': 'Electric', 'status': 'Available', 'assigned_driver_id': '', 'assigned_route_id': ''},
            {'bus_id': 'B012', 'bus_number': 'BA-2-KHA-112', 'registration_number': 'REG-112-2024', 'capacity': 35, 'model': 'Eicher CityBus', 'bus_type': 'Standard', 'status': 'Available', 'assigned_driver_id': '', 'assigned_route_id': ''},
        ]
        for b in buses_data:
            bus_repo.insert(b)

        self.stdout.write("6. Creating Passenger Demand Records (Peak & Off-Peak)...")
        demand_repo = DemandRepository()
        today = datetime.utcnow().strftime('%Y-%m-%d')
        demand_sample = [
            # Morning Peak (08:00-09:00)
            {'route_id': 'R001', 'stop_id': 'S008', 'date': today, 'time_period': '08:00-09:00', 'passenger_count': 185},
            {'route_id': 'R001', 'stop_id': 'S001', 'date': today, 'time_period': '08:00-09:00', 'passenger_count': 120},
            {'route_id': 'R002', 'stop_id': 'S010', 'date': today, 'time_period': '08:00-09:00', 'passenger_count': 140},
            {'route_id': 'R002', 'stop_id': 'S001', 'date': today, 'time_period': '08:00-09:00', 'passenger_count': 95},
            {'route_id': 'R003', 'stop_id': 'S008', 'date': today, 'time_period': '08:00-09:00', 'passenger_count': 260},
            {'route_id': 'R003', 'stop_id': 'S011', 'date': today, 'time_period': '08:00-09:00', 'passenger_count': 190},
            {'route_id': 'R004', 'stop_id': 'S001', 'date': today, 'time_period': '08:00-09:00', 'passenger_count': 75},
            {'route_id': 'R005', 'stop_id': 'S005', 'date': today, 'time_period': '08:00-09:00', 'passenger_count': 110},

            # Midday Off-Peak (12:00-13:00)
            {'route_id': 'R001', 'stop_id': 'S008', 'date': today, 'time_period': '12:00-13:00', 'passenger_count': 55},
            {'route_id': 'R002', 'stop_id': 'S010', 'date': today, 'time_period': '12:00-13:00', 'passenger_count': 45},
            {'route_id': 'R003', 'stop_id': 'S008', 'date': today, 'time_period': '12:00-13:00', 'passenger_count': 70},

            # Evening Peak (17:00-18:00)
            {'route_id': 'R001', 'stop_id': 'S004', 'date': today, 'time_period': '17:00-18:00', 'passenger_count': 210},
            {'route_id': 'R002', 'stop_id': 'S005', 'date': today, 'time_period': '17:00-18:00', 'passenger_count': 160},
            {'route_id': 'R003', 'stop_id': 'S004', 'date': today, 'time_period': '17:00-18:00', 'passenger_count': 280},
            {'route_id': 'R004', 'stop_id': 'S013', 'date': today, 'time_period': '17:00-18:00', 'passenger_count': 90},
            {'route_id': 'R005', 'stop_id': 'S004', 'date': today, 'time_period': '17:00-18:00', 'passenger_count': 130},
        ]
        demand_repo.batch_insert(demand_sample)

        self.stdout.write("7. Creating Timetable Schedules & Active Trips...")
        sched_repo = ScheduleRepository()
        trip_repo = TripRepository()

        schedules_sample = [
            {'schedule_id': 'SCH001', 'route_id': 'R001', 'bus_id': 'B001', 'driver_id': 'D001', 'departure_time': '07:30', 'arrival_time': '08:12', 'frequency_mins': 15, 'day_of_week': 'All Days', 'status': 'Active'},
            {'schedule_id': 'SCH002', 'route_id': 'R001', 'bus_id': 'B002', 'driver_id': 'D002', 'departure_time': '07:45', 'arrival_time': '08:27', 'frequency_mins': 15, 'day_of_week': 'All Days', 'status': 'Active'},
            {'schedule_id': 'SCH003', 'route_id': 'R002', 'bus_id': 'B005', 'driver_id': 'D005', 'departure_time': '07:30', 'arrival_time': '08:16', 'frequency_mins': 20, 'day_of_week': 'All Days', 'status': 'Active'},
            {'schedule_id': 'SCH004', 'route_id': 'R003', 'bus_id': 'B003', 'driver_id': 'D003', 'departure_time': '07:20', 'arrival_time': '08:15', 'frequency_mins': 15, 'day_of_week': 'All Days', 'status': 'Active'},
            {'schedule_id': 'SCH005', 'route_id': 'R003', 'bus_id': 'B004', 'driver_id': 'D004', 'departure_time': '07:35', 'arrival_time': '08:30', 'frequency_mins': 15, 'day_of_week': 'All Days', 'status': 'Active'},
        ]
        for s in schedules_sample:
            sched_repo.insert(s)

        trips_sample = [
            {'trip_id': 'TRP001', 'schedule_id': 'SCH001', 'route_id': 'R001', 'bus_id': 'B001', 'driver_id': 'D001', 'date': today, 'status': 'In Transit', 'scheduled_departure': '07:30', 'actual_departure': '07:32', 'current_stop_id': 'S001', 'delay_minutes': 2, 'notes': 'Moderate traffic at Maitighar'},
            {'trip_id': 'TRP002', 'schedule_id': 'SCH003', 'route_id': 'R002', 'bus_id': 'B005', 'driver_id': 'D005', 'date': today, 'status': 'Scheduled', 'scheduled_departure': '08:00', 'actual_departure': None, 'current_stop_id': 'S010', 'delay_minutes': 0, 'notes': 'Preparing for departure'},
            {'trip_id': 'TRP003', 'schedule_id': 'SCH004', 'route_id': 'R003', 'bus_id': 'B003', 'driver_id': 'D003', 'date': today, 'status': 'In Transit', 'scheduled_departure': '07:20', 'actual_departure': '07:20', 'current_stop_id': 'S011', 'delay_minutes': 0, 'notes': 'On schedule'},
        ]
        for t in trips_sample:
            trip_repo.insert(t)

        self.stdout.write(self.style.SUCCESS("MongoDB successfully populated with realistic transit network data!"))
