/**
 * Leaflet & OpenStreetMap Transit Mapping Utilities
 */

const TransitMap = {
    // Default center Kathmandu Valley
    DEFAULT_CENTER: [27.7058, 85.3157],
    DEFAULT_ZOOM: 13,

    initMap: function(elementId, center = null, zoom = null) {
        const c = center || this.DEFAULT_CENTER;
        const z = zoom || this.DEFAULT_ZOOM;
        const map = L.map(elementId).setView(c, z);

        const transitTiles = L.tileLayer('https://tile.openstreetmap.de/{z}/{x}/{y}.png', {
            maxZoom: 18,
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        });

        transitTiles.addTo(map);

        return map;
    },

    renderStops: function(map, stops) {
        if (!stops || stops.length === 0) return;

        const bounds = [];
        stops.forEach(stop => {
            if (stop.latitude && stop.longitude) {
                const latLng = [parseFloat(stop.latitude), parseFloat(stop.longitude)];
                bounds.push(latLng);

                const icon = L.divIcon({
                    className: 'stop-pin',
                    html: `<div style="background-color: ${stop.is_terminal ? '#ef4444' : '#2563eb'}; width: 14px; height: 14px; border-radius: 50%; border: 2.5px solid white; box-shadow: 0 2px 4px rgba(0,0,0,0.3);"></div>`,
                    iconSize: [14, 14],
                    iconAnchor: [7, 7]
                });

                const marker = L.marker(latLng, { icon: icon }).addTo(map);
                const facilitiesHtml = stop.facilities ? stop.facilities.map(f => `<span class="badge bg-light text-dark border me-1">${f}</span>`).join('') : '';

                marker.bindPopup(`
                    <div style="font-family: inherit;">
                        <h6 style="margin-bottom: 4px; font-weight: 700; color: #1e293b;">${stop.name}</h6>
                        <p style="margin-bottom: 6px; font-size: 0.8rem; color: #64748b;">
                            <strong>Code:</strong> ${stop.code || stop.stop_id} | <strong>Zone:</strong> ${stop.zone || 'General'}
                        </p>
                        ${stop.is_terminal ? '<span class="badge bg-danger mb-2">Major Terminal Hub</span><br>' : ''}
                        ${facilitiesHtml}
                    </div>
                `);
            }
        });

        if (bounds.length > 0) {
            map.fitBounds(bounds, { padding: [30, 30] });
        }
    },

    createLiveBusLayer: function(map) {
        const layer = L.layerGroup().addTo(map);
        const markers = new Map();
        const escapeHtml = value => String(value ?? '').replace(/[&<>"']/g, character => ({
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#39;'
        })[character]);

        return {
            update: function(buses) {
                const visibleTrips = new Set();
                (buses || []).forEach(bus => {
                    if (
                        bus.latitude == null
                        || bus.longitude == null
                        || !Number.isFinite(Number(bus.latitude))
                        || !Number.isFinite(Number(bus.longitude))
                    ) {
                        return;
                    }
                    visibleTrips.add(bus.trip_id);
                    const position = [Number(bus.latitude), Number(bus.longitude)];
                    const nextStop = bus.stop_arrivals && bus.stop_arrivals[0];
                    const popup = `
                        <strong>${escapeHtml(bus.bus_number)} · ${escapeHtml(bus.route_number)}</strong><br>
                        <small>${escapeHtml(bus.route_name || '')}</small>
                        ${nextStop ? `<br><span>Next: ${escapeHtml(nextStop.name)} · ~${escapeHtml(nextStop.eta_minutes)} min</span>` : ''}
                        <br><small>GPS updated ${escapeHtml(bus.updated_at || 'recently')}</small>
                    `;

                    let marker = markers.get(bus.trip_id);
                    if (marker) {
                        marker.setLatLng(position);
                        marker.setPopupContent(popup);
                    } else {
                        const icon = L.divIcon({
                            className: 'live-bus-marker',
                            html: '<div style="width:34px;height:34px;border-radius:50%;background:#0f172a;border:3px solid #fff;box-shadow:0 2px 8px #0005;color:#fff;display:flex;align-items:center;justify-content:center;font-size:16px"><i class="bi bi-bus-front-fill"></i></div>',
                            iconSize: [34, 34],
                            iconAnchor: [17, 17]
                        });
                        marker = L.marker(position, { icon: icon }).bindPopup(popup).addTo(layer);
                        markers.set(bus.trip_id, marker);
                    }
                });

                markers.forEach((marker, tripId) => {
                    if (!visibleTrips.has(tripId)) {
                        layer.removeLayer(marker);
                        markers.delete(tripId);
                    }
                });
            }
        };
    },

    renderPath: function(map, pathDetails) {
        if (!pathDetails || pathDetails.length === 0) return;

        const latLngs = [];
        const bounds = [];

        pathDetails.forEach((step, idx) => {
            const latLng = [step.latitude, step.longitude];
            latLngs.push(latLng);
            bounds.push(latLng);

            let pinColor = '#2563eb';
            let label = `${idx + 1}. ${step.name}`;

            if (idx === 0) {
                pinColor = '#10b981'; // Green for Start
            } else if (idx === pathDetails.length - 1) {
                pinColor = '#ef4444'; // Red for Destination
            }

            const icon = L.divIcon({
                className: 'path-marker',
                html: `<div style="background-color: ${pinColor}; color: white; border-radius: 50%; width: 24px; height: 24px; display: flex; align-items: center; justify-content: center; font-size: 11px; font-weight: bold; border: 2px solid white; box-shadow: 0 2px 6px rgba(0,0,0,0.3);">${idx + 1}</div>`,
                iconSize: [24, 24],
                iconAnchor: [12, 12]
            });

            const marker = L.marker(latLng, { icon: icon }).addTo(map);
            marker.bindPopup(`
                <div style="font-family: inherit;">
                    <strong style="color: ${pinColor};">${idx === 0 ? 'START: ' : (idx === pathDetails.length - 1 ? 'DESTINATION: ' : '')}${step.name}</strong><br>
                    <small>Cumulative Dist: ${step.cumulative_dist_km} km | Time: ${step.cumulative_time_mins} min</small><br>
                    ${step.route_number ? `<span class="badge bg-primary mt-1">Bus Line: ${step.route_number}</span>` : ''}
                </div>
            `);
        });

        // Draw polyline connecting stops
        const polyline = L.polyline(latLngs, {
            color: '#10b981',
            weight: 5,
            opacity: 0.85,
            dashArray: '1, 8',
            lineJoin: 'round'
        }).addTo(map);

        // Solid underline for glow effect
        L.polyline(latLngs, {
            color: '#2563eb',
            weight: 3,
            opacity: 0.9,
            lineJoin: 'round'
        }).addTo(map);

        map.fitBounds(bounds, { padding: [40, 40] });
    }
};
