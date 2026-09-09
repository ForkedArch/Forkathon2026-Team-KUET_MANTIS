import os, re, json

results = []

def record(test_name, passed, detail=''):
    results.append((test_name, passed, detail))
    status = '[PASS]' if passed else '[FAIL]'
    print(f'{status} {test_name}: {detail}')

# 1. MapLibre GL CDN & Styles in frontend/index.html
html = open('frontend/index.html').read()
record('MapLibre GL CSS CDN loaded in frontend/index.html', 'maplibre-gl.css' in html)
record('MapLibre GL JS CDN loaded in frontend/index.html', 'maplibre-gl.js' in html)
record('Turf.js CDN loaded in frontend/index.html', 'turf.min.js' in html)

# 2. GodsEyeMap.jsx Authenticity
map_jsx = open('frontend/src/components/map/GodsEyeMap.jsx').read()
record('GodsEyeMap initializes maplibregl.Map', 'new maplibregl.Map' in map_jsx)
record('GodsEyeMap uses OSM raster tiles', 'osm-tiles' in map_jsx and 'tile.openstreetmap.org' in map_jsx)
record('GodsEyeMap centers at KUET [89.5024, 22.9006]', '89.5024' in map_jsx and '22.9006' in map_jsx)
record('GodsEyeMap defines 700m perimeter radius', 'CAMPUS_PERIMETER_RADIUS = 700' in map_jsx)
record('GodsEyeMap includes spherical trig circle fallback', 'Math.asin' in map_jsx and 'Math.sin(radLat)' in map_jsx)
record('GodsEyeMap renders dual markers (.marker-lend & .marker-beacon)', 'marker-lend' in map_jsx and 'marker-beacon' in map_jsx)
record('GodsEyeMap implements interactive click-to-pinpoint listener', "map.on('click'" in map_jsx)
record('GodsEyeMap supports camera flyTo navigation', 'mapInstanceRef.current.flyTo' in map_jsx)
record('GodsEyeMap HUD contains 700m ring toggle', 'toggle-ring-btn' in map_jsx)
record('GodsEyeMap HUD contains beacons toggle', 'toggle-beacons-btn' in map_jsx)
record('GodsEyeMap HUD contains recenter button', 'recenter-kuet-btn' in map_jsx)

# 3. AddItemModal.jsx Authenticity
modal_jsx = open('frontend/src/components/items/AddItemModal.jsx').read()
record('AddItemModal has #add-item-modal ID', 'id="add-item-modal"' in modal_jsx)
record('AddItemModal has #proceed-pin-btn', 'id="proceed-pin-btn"' in modal_jsx)
record('AddItemModal has #direct-submit-btn', 'id="direct-submit-btn"' in modal_jsx)
record('AddItemModal submits to /items API', "api.post('/items'" in modal_jsx)
record('AddItemModal supports multipart/form-data upload', 'multipart/form-data' in modal_jsx)
record('AddItemModal nearest landmark detection algorithm', 'findNearestLandmark' in modal_jsx)

# 4. Roll Decoder & Minimal Form in App.jsx
app_jsx = open('frontend/src/App.jsx').read()
record('App.jsx has decodeKuetEmail function', 'export function decodeKuetEmail' in app_jsx)
record('Roll decoder validates @stud.kuet.ac.bd suffix', "endsWith('@stud.kuet.ac.bd')" in app_jsx)
record('Roll decoder uses dynamic regex (\\d{2})(\\d{2})(\\d{3})$', r'(\d{2})(\d{2})(\d{3})$' in app_jsx)
reg_match = re.search(r'api\.post\([\'\"]/auth/register[\'\"],\s*\{([^}]+)\}\)', app_jsx)
reg_fields = set([line.strip().split(':')[0].strip() for line in reg_match.group(1).split(',') if line.strip()])
record('Register form strictly submits 3 fields (name, email, password)', reg_fields == {'name', 'email', 'password'})
record('App.jsx displays 100 Base Karma on registration', '100 Base Karma' in app_jsx)

# 5. KUET Karma Protocol integration across views
profile_jsx = open('frontend/src/pages/Profile.jsx').read()
record('Profile.jsx displays KUET Karma Protocol Score', 'KUET Karma Protocol Score' in profile_jsx)
record('Profile.jsx reads user.karma dynamically', 'user.karma ?? 100' in profile_jsx)
record('Profile.jsx displays +10 lend, +5 on-time, -30 late rules', '+10' in profile_jsx and '+5' in profile_jsx and '-30' in profile_jsx)

tx_jsx = open('frontend/src/pages/Transaction.jsx').read()
record('Transaction.jsx displays karma feedback from return API', 'res.data?.karma_updated' in tx_jsx)
record('Transaction.jsx celebrates on-time return with +karma', 'borrower_change' in tx_jsx and 'owner_gain' in tx_jsx)
record('Transaction.jsx handles late return penalty', 'Late return!' in tx_jsx)

sidebar_jsx = open('frontend/src/components/layout/Sidebar.jsx').read()
record('Sidebar.jsx displays 700m Campus Perimeter badge', '700m Campus Perimeter' in sidebar_jsx)
record('Sidebar.jsx displays active user karma badge', 'user.karma ?? 100' in sidebar_jsx)
record('Sidebar.jsx navigates to Map View, All Items, Requests, Profile', 'Map View' in sidebar_jsx and 'All Items' in sidebar_jsx and 'Borrow Requests' in sidebar_jsx and 'My Profile' in sidebar_jsx)

# 6. Overall Pass rate
passed_count = sum(1 for _, p, _ in results if p)
failed_count = sum(1 for _, p, _ in results if not p)
print('=' * 60)
print(f'TOTAL FORENSIC CHECKS: {len(results)}, PASSED: {passed_count}, FAILED: {failed_count}')
assert failed_count == 0, f'{failed_count} checks failed!'
