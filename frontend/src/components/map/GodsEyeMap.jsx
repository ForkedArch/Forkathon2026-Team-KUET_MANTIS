import React, { useEffect, useRef, useState, useCallback } from 'react';
import './GodsEyeMap.css';
import { formatDept } from '../../utils/dept';

// KUET Campus Geographic Center [Longitude, Latitude]
export const KUET_CENTER = [89.5024, 22.9006];
export const CAMPUS_PERIMETER_RADIUS = 700; // 700 meters perimeter ring

/**
 * Generates GeoJSON Polygon for a circle of radius in meters.
 * Uses window.turf if available; otherwise falls back to exact spherical trigonometry.
 */
export function createCircleGeoJSON(centerLng, centerLat, radiusMeters, points = 64) {
  if (typeof window !== 'undefined' && window.turf && typeof window.turf.circle === 'function') {
    return window.turf.circle([centerLng, centerLat], radiusMeters, { steps: points, units: 'meters' });
  }

  const coords = [];
  const distance = (radiusMeters / 1000) / 6371; // Angular distance in radians
  const radLat = (centerLat * Math.PI) / 180;
  const radLng = (centerLng * Math.PI) / 180;

  for (let i = 0; i <= points; i++) {
    const bearing = (i * 360 / points) * (Math.PI / 180);
    const lat = Math.asin(
      Math.sin(radLat) * Math.cos(distance) +
      Math.cos(radLat) * Math.sin(distance) * Math.cos(bearing)
    );
    const lng = radLng + Math.atan2(
      Math.sin(bearing) * Math.sin(distance) * Math.cos(radLat),
      Math.cos(distance) - Math.sin(radLat) * Math.sin(lat)
    );
    coords.push([(lng * 180) / Math.PI, (lat * 180) / Math.PI]);
  }

  return {
    type: 'Feature',
    properties: { radius: radiusMeters },
    geometry: {
      type: 'Polygon',
      coordinates: [coords]
    }
  };
}

/**
 * GodsEyeMap - Interactive MapLibre GL Canvas for KUET CampusShare.
 */
export default function GodsEyeMap({
  items = [],
  selectedItemId = null,
  isPinMode = false,
  pinpointCoords = null,
  onSelectLocation = null,
  onCancelPinMode = null,
  onSelectItem = null,
  onRequestBorrow = null,
  activeTypeFilter = 'ALL',
  activeCategoryFilter = 'ALL',
  searchQuery = '',
  className = ''
}) {
  const mapContainerRef = useRef(null);
  const mapInstanceRef = useRef(null);
  const markersRef = useRef([]);
  const tempPinMarkerRef = useRef(null);

  // HUD layer states
  const [showPerimeterRing, setShowPerimeterRing] = useState(true);
  const [showBeacons, setShowBeacons] = useState(true);
  const [mapLoaded, setMapLoaded] = useState(false);

  // Keep references to latest callbacks for DOM event handlers
  const onSelectLocationRef = useRef(onSelectLocation);
  const onSelectItemRef = useRef(onSelectItem);
  const onRequestBorrowRef = useRef(onRequestBorrow);
  const itemsRef = useRef(items);

  useEffect(() => {
    onSelectLocationRef.current = onSelectLocation;
    onSelectItemRef.current = onSelectItem;
    onRequestBorrowRef.current = onRequestBorrow;
    itemsRef.current = items;
  }, [onSelectLocation, onSelectItem, onRequestBorrow, items]);

  // 1. Initialize MapLibre GL Instance
  useEffect(() => {
    if (!mapContainerRef.current) return;
    if (mapInstanceRef.current) return; // Prevent double initialization

    const initMap = () => {
      const maplibregl = typeof window !== 'undefined' ? window.maplibregl : null;
      if (!maplibregl || !mapContainerRef.current) return false;

      // OpenStreetMap Free Raster Style
      const osmStyle = {
        version: 8,
        sources: {
          'osm-tiles': {
            type: 'raster',
            tiles: ['https://tile.openstreetmap.org/{z}/{x}/{y}.png'],
            tileSize: 256,
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors | KUET Campus Map'
          }
        },
        layers: [
          {
            id: 'osm-tiles-layer',
            type: 'raster',
            source: 'osm-tiles',
            minzoom: 0,
            maxzoom: 19
          }
        ]
      };

      const map = new maplibregl.Map({
        container: mapContainerRef.current,
        style: osmStyle,
        center: KUET_CENTER,
        zoom: 16.2,
        pitch: 0,
        bearing: 0
      });

      // Add navigation & scale controls
      map.addControl(new maplibregl.NavigationControl({ visualizePitch: true }), 'top-right');
      map.addControl(new maplibregl.ScaleControl({ unit: 'metric' }), 'bottom-left');

      map.on('load', () => {
        // Draw Visual 700m Perimeter Circle
        const circleGeoJSON = createCircleGeoJSON(KUET_CENTER[0], KUET_CENTER[1], CAMPUS_PERIMETER_RADIUS);

        map.addSource('campus-perimeter-700m', {
          type: 'geojson',
          data: circleGeoJSON
        });

        // 1. Fill layer
        map.addLayer({
          id: 'perimeter-fill',
          type: 'fill',
          source: 'campus-perimeter-700m',
          paint: {
            'fill-color': '#2563eb',
            'fill-opacity': 0.05
          }
        });

        // 2. Dash line
        map.addLayer({
          id: 'perimeter-line',
          type: 'line',
          source: 'campus-perimeter-700m',
          paint: {
            'line-color': '#2563eb',
            'line-width': 2.5,
            'line-dasharray': [3, 2]
          }
        });

        // 3. Halo line
        map.addLayer({
          id: 'perimeter-halo',
          type: 'line',
          source: 'campus-perimeter-700m',
          paint: {
            'line-color': '#3b82f6',
            'line-width': 6,
            'line-opacity': 0.2
          }
        });

        setMapLoaded(true);
      });

      mapInstanceRef.current = map;
      return true;
    };

    if (!initMap()) {
      const interval = setInterval(() => {
        if (initMap()) clearInterval(interval);
      }, 100);
      return () => clearInterval(interval);
    }

    return () => {
      if (mapInstanceRef.current) {
        mapInstanceRef.current.remove();
        mapInstanceRef.current = null;
      }
    };
  }, []);

  // 2. Toggle 700m Perimeter Ring Visibility
  useEffect(() => {
    const map = mapInstanceRef.current;
    if (!map || !mapLoaded) return;

    const visibility = showPerimeterRing ? 'visible' : 'none';
    ['perimeter-fill', 'perimeter-line', 'perimeter-halo'].forEach(layerId => {
      if (map.getLayer(layerId)) {
        map.setLayoutProperty(layerId, 'visibility', visibility);
      }
    });
  }, [showPerimeterRing, mapLoaded]);

  // 3. Render Custom Item Markers (Emerald Lend Pins & Red Pulsing Beacons)
  const renderMarkers = useCallback(() => {
    const map = mapInstanceRef.current;
    const maplibregl = typeof window !== 'undefined' ? window.maplibregl : null;
    if (!map || !mapLoaded || !maplibregl) return;

    // Clear existing markers
    markersRef.current.forEach(m => m.marker.remove());
    markersRef.current = [];

    // Filter items according to active filters & search query
    const filtered = items.filter(item => {
      // Type filter
      if (activeTypeFilter !== 'ALL' && item.type !== activeTypeFilter) return false;

      // Category filter
      if (activeCategoryFilter !== 'ALL' && item.category !== activeCategoryFilter) return false;

      // Search query
      if (searchQuery && searchQuery.trim() !== '') {
        const q = searchQuery.toLowerCase();
        const matchTitle = (item.title || '').toLowerCase().includes(q);
        const matchSpecs = (item.specs || item.description || '').toLowerCase().includes(q);
        const matchLender = (item.lender_name || item.owner?.name || '').toLowerCase().includes(q);
        const matchDept = (item.dept || item.owner?.dept || '').toLowerCase().includes(q);
        const matchCat = (item.category || '').toLowerCase().includes(q);
        if (!matchTitle && !matchSpecs && !matchLender && !matchDept && !matchCat) return false;
      }

      return true;
    });

    filtered.forEach(item => {
      const lng = item.lng ?? item.longitude;
      const lat = item.lat ?? item.latitude;
      if (lng == null || lat == null) return;

      const isBeacon = item.type === 'borrow' || item.status === 'beacon';

      // Respect beacon visibility toggle
      if (isBeacon && !showBeacons) return;

      // Create Custom Pin Element with isolated outer wrapper
      const el = document.createElement('div');
      el.className = 'marker-pin-outer';
      el.setAttribute('data-item-id', item.id);

      const inner = document.createElement('div');
      inner.className = `marker-pin ${isBeacon ? 'marker-beacon' : 'marker-lend'}`;

      if (isBeacon) {
        inner.innerHTML = `
          <div class="beacon-pulse"></div>
          <div class="beacon-pulse-inner"></div>
          <span>⚡</span>
        `;
      } else {
        let icon = '📦';
        const cat = (item.category || '').toLowerCase();
        if (cat.includes('calc')) icon = '🧮';
        else if (cat.includes('elect') || cat.includes('charg') || cat.includes('power')) icon = '🔌';
        else if (cat.includes('lab')) icon = '🔬';
        else if (cat.includes('cable') || cat.includes('adapt')) icon = '🔗';
        else if (cat.includes('book') || cat.includes('note')) icon = '📖';
        else if (cat.includes('station') || cat.includes('draw')) icon = '📐';
        inner.innerHTML = `<span>${icon}</span>`;
      }
      el.appendChild(inner);

      // Build Rich Interactive Popup
      const ownerName = item.owner?.name || item.lender_name || 'KUET Student';
      const initials = ownerName
        .split(' ')
        .filter(Boolean)
        .slice(0, 2)
        .map(n => n[0])
        .join('')
        .toUpperCase() || 'KU';

      const defaultImage = isBeacon
        ? 'https://images.unsplash.com/photo-1616469829941-c7200edec809?w=400'
        : 'https://images.unsplash.com/photo-1583863788434-e58a36330cf0?w=400';

      const imgSrc = (item.image_url || item.image) && (item.image_url || item.image).trim() !== ''
        ? (item.image_url?.startsWith('http') ? item.image_url : (item.image || defaultImage))
        : defaultImage;

      const karmaScore = item.owner?.karma ?? item.karma ?? (item.trust_rating ? (item.trust_rating * 20).toFixed(0) : 100);
      const studentRoll = item.owner?.roll || item.roll || 'Verified';
      const studentDept = formatDept(item.owner?.dept || item.dept) || 'KUET';
      const totalExchanges = (item.owner?.total_lends || 0) + (item.owner?.total_borrows || 0) || item.total_exchanges || 12;

      const statusBadge = isBeacon
        ? '<span class="popup-status-badge status-badge-beacon">🚨 Active Demand Beacon</span>'
        : '<span class="popup-status-badge status-badge-lend">🟢 Available to Borrow</span>';

      const actionBtnText = isBeacon ? '⚡ Offer to Lend This Item' : '🤝 Request to Borrow';

      const popupNode = document.createElement('div');
      popupNode.className = 'popup-card';
      popupNode.innerHTML = `
        <div class="popup-img-wrap">
          <img class="popup-img" src="${imgSrc}" alt="${item.title}" onerror="this.src='${defaultImage}';" />
          ${statusBadge}
        </div>
        <div class="popup-body">
          <div style="display:flex; justify-content:space-between; align-items:center;">
            <span style="font-size:0.72rem; font-weight:700; color:var(--primary, #2563eb); text-transform:uppercase;">${item.category || 'General'}</span>
            <span style="font-size:0.72rem; background:#f1f5f9; padding:2px 8px; border-radius:10px; font-weight:600; color:#475569;">${item.condition || 'Good'}</span>
          </div>
          <div class="popup-title">${item.title}</div>
          <div class="popup-specs">${item.specs || item.description || 'No specific notes provided.'}</div>
          
          <div class="popup-user-section">
            <div class="popup-user-detail">
              <div class="popup-avatar">${initials}</div>
              <div class="popup-user-text">
                <span class="popup-user-name">${ownerName}</span>
                <span class="popup-user-sub">${studentDept} • Roll ${studentRoll}</span>
              </div>
            </div>
            <div class="popup-trust-box">
              <div class="popup-trust-score">⚡ ${karmaScore} Karma</div>
              <div class="popup-trust-label">${totalExchanges} Exchanges</div>
            </div>
          </div>

          <div class="popup-actions">
            <button class="btn-popup-primary ${isBeacon ? 'btn-beacon-action' : ''}" data-action="request">
              ${actionBtnText}
            </button>
          </div>
        </div>
      `;

      // Attach button event listener
      const actionBtn = popupNode.querySelector('[data-action="request"]');
      if (actionBtn) {
        actionBtn.addEventListener('click', () => {
          if (onRequestBorrowRef.current) {
            onRequestBorrowRef.current(item);
          } else if (window.__campusShareActions?.onRequestBorrow) {
            window.__campusShareActions.onRequestBorrow(item);
          }
        });
      }

      const popup = new maplibregl.Popup({ offset: 25, closeButton: true }).setDOMContent(popupNode);

      el.addEventListener('click', () => {
        if (onSelectItemRef.current) {
          onSelectItemRef.current(item);
        }
      });

      const marker = new maplibregl.Marker({ element: el, anchor: 'center' })
        .setLngLat([lng, lat])
        .setPopup(popup)
        .addTo(map);

      markersRef.current.push({ id: item.id, marker });
    });
  }, [items, activeTypeFilter, activeCategoryFilter, searchQuery, showBeacons, mapLoaded]);

  useEffect(() => {
    renderMarkers();
  }, [renderMarkers]);

  // 4. Fly to selected item when selectedItemId prop updates
  useEffect(() => {
    if (!selectedItemId || !mapInstanceRef.current) return;
    const item = items.find(i => String(i.id) === String(selectedItemId));
    if (!item) return;

    const lng = item.lng ?? item.longitude;
    const lat = item.lat ?? item.latitude;
    if (lng == null || lat == null) return;

    mapInstanceRef.current.flyTo({
      center: [lng, lat],
      zoom: 17.5,
      pitch: 35,
      essential: true
    });

    const markerObj = markersRef.current.find(m => String(m.id) === String(selectedItemId));
    if (markerObj && markerObj.marker) {
      markerObj.marker.togglePopup();
    }
  }, [selectedItemId, items]);

  // Helper to build pixel-accurate needle pin element
  const createPinpointElement = () => {
    const el = document.createElement('div');
    el.className = 'custom-pinpoint-container';
    el.innerHTML = `
      <div class="custom-pinpoint-wrapper">
        <svg class="custom-pinpoint-svg" width="34" height="46" viewBox="0 0 34 46" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M17 0C7.611 0 0 7.611 0 17C0 29.75 17 46 17 46C17 46 34 29.75 34 17C34 7.611 26.389 0 17 0Z" fill="#2563EB"/>
          <path d="M17 2C8.716 2 2 8.716 2 17C2 28.2 17 43.5 17 43.5C17 43.5 32 28.2 32 17C32 8.716 25.284 2 17 2Z" fill="#1D4ED8"/>
          <circle cx="17" cy="17" r="8" fill="white"/>
          <circle cx="17" cy="17" r="4.5" fill="#2563EB"/>
        </svg>
        <div class="custom-pinpoint-pulse"></div>
        <div class="custom-pinpoint-shadow"></div>
      </div>
    `;
    return el;
  };

  // 5. Click-to-Pinpoint Mode Handler
  useEffect(() => {
    const map = mapInstanceRef.current;
    const maplibregl = typeof window !== 'undefined' ? window.maplibregl : null;
    if (!map || !mapLoaded || !maplibregl) return;

    const handleMapClick = (e) => {
      if (!isPinMode) return;

      const { lng, lat } = e.lngLat;

      // Drop/update temporary draggable confirmation pin with exact bottom needle alignment
      if (tempPinMarkerRef.current) {
        tempPinMarkerRef.current.remove();
      }

      const el = createPinpointElement();

      const tempMarker = new maplibregl.Marker({ element: el, draggable: true, anchor: 'bottom' })
        .setLngLat([lng, lat])
        .addTo(map);

      tempMarker.on('dragend', () => {
        const pt = tempMarker.getLngLat();
        if (onSelectLocationRef.current) {
          onSelectLocationRef.current({ lat: pt.lat, lng: pt.lng });
        }
      });

      tempPinMarkerRef.current = tempMarker;

      if (onSelectLocationRef.current) {
        onSelectLocationRef.current({ lat, lng });
      }
    };

    map.on('click', handleMapClick);

    return () => {
      map.off('click', handleMapClick);
    };
  }, [isPinMode, mapLoaded]);

  // Synchronize pin position if pinpointCoords is provided
  useEffect(() => {
    const map = mapInstanceRef.current;
    const maplibregl = typeof window !== 'undefined' ? window.maplibregl : null;
    if (!map || !mapLoaded || !maplibregl) return;

    if (pinpointCoords && pinpointCoords.lat != null && pinpointCoords.lng != null) {
      if (tempPinMarkerRef.current) {
        tempPinMarkerRef.current.setLngLat([pinpointCoords.lng, pinpointCoords.lat]);
      } else {
        const el = createPinpointElement();
        const m = new maplibregl.Marker({ element: el, draggable: isPinMode, anchor: 'bottom' })
          .setLngLat([pinpointCoords.lng, pinpointCoords.lat])
          .addTo(map);

        m.on('dragend', () => {
          const pt = m.getLngLat();
          if (onSelectLocationRef.current) {
            onSelectLocationRef.current({ lat: pt.lat, lng: pt.lng });
          }
        });

        tempPinMarkerRef.current = m;
      }
    } else if (!isPinMode && tempPinMarkerRef.current) {
      tempPinMarkerRef.current.remove();
      tempPinMarkerRef.current = null;
    }
  }, [pinpointCoords, isPinMode, mapLoaded]);

  // 6. HUD Actions
  const handleRecenter = () => {
    if (!mapInstanceRef.current) return;
    mapInstanceRef.current.flyTo({
      center: KUET_CENTER,
      zoom: 16.2,
      pitch: 0,
      bearing: 0,
      essential: true
    });
  };

  return (
    <div className={`relative w-full h-full overflow-hidden ${isPinMode ? 'pin-mode' : ''} ${className}`}>
      {/* MapLibre DOM Canvas */}
      <div id="map" ref={mapContainerRef} className="w-full h-full" />

      {/* Pinpoint Guidance Top Banner */}
      {isPinMode && (
        <div id="pin-banner" className="pin-banner">
          <span>📍 Click anywhere on KUET campus map to drop item exchange location</span>
          <button
            id="btn-cancel-pin"
            type="button"
            className="btn-cancel-pin"
            onClick={onCancelPinMode}
          >
            ✕ Cancel
          </button>
        </div>
      )}

      {/* Map HUD Floating Controls - Docked Bottom-Right */}
      <div className="map-hud">
        <div className="hud-card">
          <span className="hud-label">Layers</span>
          <div className="hud-layer-toggle">
            <button
              id="toggle-ring-btn"
              type="button"
              className={`layer-btn ${showPerimeterRing ? 'active' : ''}`}
              onClick={() => setShowPerimeterRing(prev => !prev)}
              title="Toggle 700m Campus Perimeter Ring"
            >
              ⭕ 700m Ring
            </button>
            <button
              id="toggle-beacons-btn"
              type="button"
              className={`layer-btn ${showBeacons ? 'active' : ''}`}
              onClick={() => setShowBeacons(prev => !prev)}
              title="Toggle Borrow Demand Beacons"
            >
              🚨 Beacons
            </button>
            <button
              id="recenter-kuet-btn"
              type="button"
              className="layer-btn"
              onClick={handleRecenter}
              title="Recenter to KUET Campus"
            >
              🎯 Recenter
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
