# Smart Public Bus Route and Schedule Optimization System

A web-based urban transit management and optimization platform built with **Python**, **Django**, **Django REST Framework**, **MongoDB**, **Leaflet (OpenStreetMap)**, **Chart.js**, and **Bootstrap 5**.

This project implements the system proposed in the academic software engineering proposal: combining record management of buses, drivers, routes, stops, and schedules with graph-theoretic shortest path routing and demand-responsive fleet scheduling algorithms.

---

## 🚌 System Overview & Objectives

In growing urban environments, public transit systems often suffer from:
- Suboptimal bus allocation leading to overcrowding on arterial lines during rush hours while low-demand routes run empty.
- High passenger waiting times due to irregular or static timetables.
- Inefficient journey planning for commuters navigating multi-route networks.

This system addresses these challenges through a centralized web application featuring:
1. **Weighted Graph Network Model**: Bus stops as nodes ($V$) and transit links as weighted directed edges ($E$).
2. **Algorithm 1 - Dijkstra's Shortest Path Algorithm**: Calculates the minimum-cost route between any two stops based on distance (km) or estimated travel time (minutes).
3. **Algorithm 2 - Demand-Based Service Frequency**: Estimates required trips, feasible service capacity, and headway intervals given passenger demand $D$, bus capacity $C$, fleet size $B$, and cycle time $T$.
4. **Algorithm 3 - Greedy Bus Allocation Heuristic**: Prioritizes routes by demand, matches vehicle capacities to minimize empty seat miles, and computes baseline vs. optimized comparison metrics.
5. **Algorithm 4 - Waiting-Time Estimation**: Computes average expected waiting time $W = H / 2$ based on service interval $H$.
6. **Multi-Role Portals**: Dedicated interfaces for **Passengers**, **Transport Operations Managers**, **Drivers**, and **System Administrators**.
7. **Interactive Visualizations**: Turn-by-turn route mapping with Leaflet & OpenStreetMap, plus analytical dashboards powered by Chart.js.

---

## 🛠️ Technology Stack

| Layer | Technology | Rationale |
|---|---|---|
| **Backend Framework** | Python 3.14 + Django 6.1.1 | Rapid web application development, clean MVC architecture, robust security. |
| **REST API** | Django REST Framework (DRF) 3.18.1 | High-performance JSON endpoints for mobile clients and SPA widgets. |
| **Primary Database** | MongoDB 8.x via PyMongo 4.18 | Native document storage, flexible nested route/stop schemas, indexed geospatial queries. |
| **Frontend Framework** | HTML5, Modern CSS3, Bootstrap 5.3, Bootstrap Icons | Fully responsive, accessible transit dashboard styling. |
| **Geospatial Mapping** | Leaflet.js 1.9 + OpenStreetMap | Interactive, zero-cost vector map rendering, custom markers, polyline routing. |
| **Data Analytics & Charts** | Chart.js 4.4 | Dynamic before/after comparison charts, demand distribution bar/donut charts. |

---

## 📐 High-Level Architecture & Database Model

### MongoDB Collections Schema

The system uses a dedicated Repository Data Access Layer (`bus_core/database/repositories.py`) for clean, decoupled document operations across 9 collections:

1. **`users`**: User profiles with hashed passwords (`make_password`), roles (`admin`, `manager`, `driver`, `passenger`).
2. **`buses`**: Fleet vehicles with `bus_number`, `capacity`, `model`, `bus_type`, `status` (`Available`, `In Service`, `Maintenance`), and assignments.
3. **`drivers`**: Personnel records with license credentials, contact info, duty status (`Active`, `On Leave`, `Off Duty`), and assigned vehicle.
4. **`bus_stops`**: Geographic stop nodes with `name`, `code`, `latitude`, `longitude`, `zone`, `facilities`, and `is_terminal`.
5. **`routes`**: Transit corridors with ordered list of stop IDs, segment distances, travel times, duration, and base fares.
6. **`schedules`**: Fixed departure timetables, headway frequencies, and assigned vehicle/driver IDs.
7. **`trips`**: Daily operational runs tracking actual departures, live status (`Scheduled`, `Departed`, `In Transit`, `Delayed`, `Completed`), delays, and driver notes.
8. **`demand_records`**: Passenger counts segmented by `route_id`, `stop_id`, `date`, and `time_period` (e.g., `08:00-09:00`).
9. **`optimization_results`**: Historical optimization outputs storing baseline vs. optimized KPIs, execution time, and route allocations.

---

## 🔬 Algorithms Implemented

### Algorithm 1: Dijkstra's Shortest Path Algorithm
- **Input**: Weighted Graph $G(V, E)$, source stop $s$, destination stop $t$, metric (distance or time).
- **Data Structure**: Binary Min-Heap Priority Queue via Python `heapq` and adjacency list.
- **Time Complexity**: $O((|V| + |E|) \log |V|)$.
- **Output**: Minimum cost, step-by-step stop itinerary, transit lines used, transfer count, estimated fare, and algorithm latency.

### Algorithm 2: Demand-Based Service Frequency
- **Input**: Passenger demand $D$, bus capacity $C$, available buses $B$, round-trip time $T$, planning period $P$ (e.g. 60 min).
- **Formulation**:
  $$\text{Required Trips} = \left\lceil \frac{D}{C} \right\rceil$$
  $$\text{Feasible Trips} = \min\left(\text{Required Trips}, \left\lfloor \frac{P}{T + T_{\text{turnaround}}} \cdot B \right\rfloor\right)$$
  $$\text{Service Interval } H = \frac{P}{\text{Feasible Trips}}$$
  $$\text{Unmet Demand} = \max(0, D - (\text{Feasible Trips} \cdot C))$$

### Algorithm 3: Greedy Bus Allocation Heuristic
- **Procedure**:
  1. Sort routes descending by passenger demand $D$.
  2. Reserve minimum fleet service for active routes.
  3. Iteratively match remaining unassigned buses to routes with the greatest capacity deficits, selecting vehicles whose capacity minimizes wasted seats.
  4. Compare results side-by-side with **Baseline Uniform Allocation** to quantify percentage improvements in waiting time and bus utilization.

### Algorithm 4: Waiting-Time Estimation
- **Formulation**: Average passenger waiting time assuming random uniform arrivals:
  $$W_{\text{avg}} = \frac{H}{2}$$

---

## 👥 User Roles & Portals

| Role | Default Credentials | Accessible Modules & Permissions |
|---|---|---|
| **Passenger** (Public) | `passenger1` / `passenger123` | Public transit portal, Dijkstra shortest route finder with Leaflet map, route timetables, stop directory. |
| **Transport Manager** | `manager` / `manager123` | Passenger demand records, simulation data generator, Schedule Optimizer runner, before/after comparative analytical reports, timetable schedule management. |
| **Driver** | `driver1` / `driver123` | Driver portal, assigned vehicle details, duty schedule, live trip status updater (`In Transit`, `Delayed`, `Completed`), delay logging. |
| **Administrator** | `admin` / `admin123` | Master admin dashboard, full CRUD operations on Buses, Drivers, Bus Stops, Routes, and User role management. |

> **Note**: The login screen (`/login/`) includes convenient **One-Click Demo Role Buttons** to quickly test any role during demonstrations!

---

## 🚀 Setup & Installation Instructions

### Prerequisites
- **Python**: Version 3.10+ (tested on Python 3.14)
- **MongoDB**: Community Server running locally on `localhost:27017` (or MongoDB Atlas URI)

### Step 1: Clone & Navigate to Project Directory
```powershell
cd "c:\Users\supre\OneDrive\Desktop\6th sem project"
```

### Step 2: Install Python Dependencies
```powershell
pip install -r requirements.txt
```

### Step 3: Run Database Migrations
Creates Django internal session tables:
```powershell
python manage.py migrate
```

### Step 4: Seed MongoDB with Realistic Transit Network Data
Populates Kathmandu transit stops (Ratna Park, Kalanki, Koteshwor, Lagankhel, Maharajgunj, etc.), routes, fleet buses, drivers, schedules, and peak demand records:
```powershell
python manage.py seed_data
```

### Step 5: Start the Development Server
```powershell
python manage.py runserver 127.0.0.1:8000
```
Open your browser and navigate to: **`http://127.0.0.1:8000/`**

---

## 🧪 Automated Testing & Verification

The project includes unit and integration tests covering:
- Dijkstra direct, multi-hop, time vs. distance, unreachable nodes, and fare calculations.
- Demand scheduling edge cases (zero demand, fleet deficits, invalid parameters).
- Greedy bus allocation versus baseline uniform allocation.
- Waiting time formulations.
- REST API responses and Django view integration.

To run the complete test suite:
```powershell
python manage.py test bus_core.tests
```

---

## 📡 REST API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/stops/` | Retrieves all bus stops with geographic coordinates and facilities. |
| `GET` | `/api/routes/` | Lists active bus routes with ordered stop sequences. |
| `GET` | `/api/buses/` | Returns fleet vehicle inventory and availability status. |
| `GET` | `/api/shortest-path/?source=S001&destination=S004&metric=distance` | Computes Dijkstra shortest path with full itinerary and latency. |
| `GET` | `/api/demand/?aggregate=true` | Returns aggregate passenger counts grouped by route. |
| `POST` | `/api/demand/` | Ingests a new passenger demand record. |
| `POST` | `/api/optimize/` | Triggers fleet schedule optimization and returns baseline vs. optimized metrics. |
| `GET` | `/api/optimization-results/` | Retrieves historical optimization runs. |
| `PATCH` | `/api/trips/<trip_id>/status/` | Updates real-time trip status, delays, and driver notes. |

---

## 📊 Academic Evaluation Metrics

Quantitative comparisons between baseline uniform schedules and the optimized schedules:
1. **Average Passenger Waiting Time (mins)**: Measured reduction across peak hours.
2. **Bus Fleet Seat Utilization (%)**: Measured improvement in seat occupancy factor.
3. **Unmet Passenger Demand**: Reduction in passengers left unserved during rush hours.
4. **Computational Latency (ms)**: Dijkstra and Greedy allocation execution time measured using high-resolution timers.

---

## 📄 License
Academic Prototype &copy; 2026. Developed for academic submission and transit engineering research.
