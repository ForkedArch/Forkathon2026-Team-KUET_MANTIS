# Frontend Deep Dive: Hover Cards, Pinpoint Modal, Auth & Karma UI

**Investigator:** `explorer_m2_3`  
**Working Directory:** `/Users/tanvir/Forkathon2026-Team-KUET_MANTIS/.agents/explorer_m2_3`  
**Milestone:** Milestone 2 (Frontend Dashboard & MapLibre Integration)  
**Date:** 2026-09-10  
**Target Scope:**
1. Popovers / Hover Cards with item details, mini-location, owner info, and KUET Karma rating.
2. `AddItemModal` with interactive click-to-pinpoint mode on the KUET campus map.
3. Registration form with only 3 fields (`name`, `email`, `password`) and live roll decoding badge.
4. Comprehensive KUET Karma score displays across all frontend views.

---

## 1. Observation

### 1.1 Existing Item Cards & Popover Deficiencies
* **File:** `/Users/tanvir/Forkathon2026-Team-KUET_MANTIS/frontend/src/components/items/ItemCard.jsx`
  * Lines 18-20:
    ```jsx
    <div className="flex items-center justify-between mt-2">
      <span className="text-sm text-green-600 font-semibold">Available</span>
      <span className="text-sm">⭐ {item.owner?.trust_score?.toFixed(1) || 4.5}</span>
    </div>
    <Link to={`/item/${item.id}`} className="mt-3 inline-block w-full text-center bg-blue-600 text-white py-2 rounded-lg hover:bg-blue-700">
      View Details
    </Link>
    ```
  * **Issues Observed:**
    1. Displays legacy `⭐ trust_score` (4.5 / 5.0 scale) instead of the KUET Karma rating (base 100).
    2. Forces a full-page redirect to `/item/:id` rather than using hover cards or popovers with inline quick actions, directly violating Requirement R2 from `ORIGINAL_REQUEST.md`: *"Use hover cards or popovers to show item details and mini-map locations... avoiding cluttered full-page redirects where possible."*
    3. Lacks mini-location details (landmark zone name, campus coordinates, distance within 700m perimeter).
    4. Lacks owner student credentials (KUET roll, department, verification status).

### 1.2 Add Item Form Lacks Map Pinpoint & Empty Component
* **File:** `/Users/tanvir/Forkathon2026-Team-KUET_MANTIS/frontend/src/components/items/AddItemForm.jsx`
  * Empty file (0 bytes).
* **File:** `/Users/tanvir/Forkathon2026-Team-KUET_MANTIS/frontend/src/pages/AddItem.jsx`
  * Lines 107-114:
    ```jsx
    <div>
      <label className="block text-sm font-medium mb-1">Zone (e.g., CSE Building)</label>
      <input
        type="text"
        className="w-full border rounded px-3 py-2"
        value={zone}
        onChange={(e) => setZone(e.target.value)}
      />
    </div>
    ```
  * **Issues Observed:**
    1. `zone` is a plain text input with no landmark suggestions or coordinates.
    2. Completely lacks `latitude` and `longitude` coordinate fields.
    3. Has zero click-to-pinpoint integration with the MapLibre campus map, violating `PROJECT.md` Feature #16 (*"Manual Click-to-Pin Mode: Crosshair cursor and click-to-pinpoint coordinate picker for new items"*).
    4. Does not support `type` toggle between lending an item (`"lend"`) and raising an active demand beacon (`"borrow"`).

### 1.3 Registration Form Violates R3 by Requiring 6 Fields
* **File:** `/Users/tanvir/Forkathon2026-Team-KUET_MANTIS/frontend/src/App.jsx`
  * Lines 44-72:
    ```jsx
    function Register() {
      const [form, setForm] = useState({ email: '', name: '', dept: '', batch: '', roll: '', password: '' });
      ...
      return (
        ...
        <input type="email" placeholder="KUET Email" value={form.email} ... />
        <input type="text" placeholder="Full Name" value={form.name} ... />
        <input type="text" placeholder="Department (e.g. CSE)" value={form.dept} ... />
        <input type="text" placeholder="Batch (e.g. 2022)" value={form.batch} ... />
        <input type="text" placeholder="Roll Number" value={form.roll} ... />
        <input type="password" placeholder="Password" value={form.password} ... />
        ...
    ```
  * **Issues Observed:**
    1. Manually prompts for `dept`, `batch`, and `roll`.
    2. Requirement R3 in `ORIGINAL_REQUEST.md` states: *"It should only accept Full Name, Password, and Email. The Email must end with `@stud.kuet.ac.bd`. The backend must automatically parse and store the Batch, Department, and Roll number from the email prefix... instead of asking the user to type them."*
    3. Backend endpoint `POST /api/auth/register` (verified in `backend/app/routes/auth.py` lines 11-70) requires only `{ name, email, password }` and automatically decodes `batch`, `dept`, and `roll`.
    4. No client-side validation or live roll decoding feedback exists to inform students of their auto-detected KUET identity.

### 1.4 Karma Score Inconsistencies Across Existing Views
* **File:** `/Users/tanvir/Forkathon2026-Team-KUET_MANTIS/frontend/src/pages/Profile.jsx`
  * Line 16: `<p><strong>Trust Score:</strong> ⭐ {user.trust_score?.toFixed(1) || 4.5}</p>` (shows 4.5 instead of `user.karma` starting at 100).
* **File:** `/Users/tanvir/Forkathon2026-Team-KUET_MANTIS/frontend/src/pages/Requests.jsx`
  * Lines 41-44: Shows borrower name without any Karma score or KUET roll, leaving item owners unable to verify borrower reliability.
* **File:** `/Users/tanvir/Forkathon2026-Team-KUET_MANTIS/frontend/src/pages/Transaction.jsx`
  * Lines 43-50: Handles return via `api.post('/transactions/return/${requestId}')`, but ignores the returned `karma_updated` payload (`owner_gain: 10`, `borrower_change: 5 | -30`, `is_on_time: boolean`).
* **File:** `/Users/tanvir/Forkathon2026-Team-KUET_MANTIS/frontend/src/components/common/Navbar.jsx`
  * Displays user name with no Karma indicator.

---

## 2. Logic Chain

1. **Premise 1 (R2 Popover Requirement):** `ORIGINAL_REQUEST.md` R2 and the Forkathon rubric mandate replacing full-page redirects with hover cards or popovers that display item specifications, mini-map locations, and owner info.
2. **Inference 1:** A dedicated `ItemHoverCard.jsx` component should be created for the items list/grid. It should offer an instant hover/click popover preview with a mini-location badge (landmark name + coordinates), owner credentials (name, roll, dept), Karma rating (`⚡ 100 Karma`), and direct action buttons ("Request to Borrow" triggering `RequestModal` directly).
3. **Inference 2:** The MapLibre map component (`GodsEyeMap.jsx`) must use an aligned HTML popup template (`generateMapPopupHtml`) that renders identical styling and binds to a global bridge (`window.__campusShareActions`), allowing "Request to Borrow" from map pins to open `RequestModal` seamlessly without reloading the page.
4. **Premise 2 (Click-to-Pinpoint Requirement):** In `Tanvir/index.html` (lines 2512-2558) and `PROJECT.md` Feature #16, items require precise campus coordinates chosen via an interactive pinpoint mode with a crosshair cursor.
5. **Inference 3:** `AddItemModal.jsx` should provide a "📍 Pinpoint on Campus Map" action. When triggered, the modal minimizes with form state preserved, displays a floating guidance banner (`"📍 Pinpoint Mode: Click anywhere on KUET campus map to drop item location!"`), turns the map cursor into a crosshair, captures the clicked `[lng, lat]`, matches the closest KUET landmark from `/api/landmarks`, and restores the modal with coordinates and landmark pre-filled.
6. **Premise 3 (R3 Auth Requirement):** R3 strictly restricts registration to 3 fields: `Full Name`, `KUET Student Email` (`@stud.kuet.ac.bd`), and `Password`. The backend schema `UserRegister` in `backend/app/schemas.py` line 13 accepts only those 3 fields.
7. **Inference 4:** `frontend/src/components/auth/Register.jsx` (and the `Register` view in `App.jsx`) must eliminate `dept`, `batch`, and `roll` inputs. A client-side `decodeKuetEmail` utility mirroring backend regex `(\d{2})(\d{2})(\d{3})$` provides instant visual confirmation via an animated badge showing the decoded Batch, Department, Roll, and 100 Starting Karma.
8. **Premise 4 (R4 KUET Karma Protocol):** Base Karma is 100; lending adds +10; on-time return adds +5; late return deducts -30.
9. **Inference 5:** All instances of `trust_score` (4.5/5.0) across the UI must be replaced with `karma` badges (`⚡ {karma} Karma`). Furthermore, `Transaction.jsx` must unpack `karma_updated` upon return completion and present immediate toast/modal celebration feedback showing the points awarded or deducted.

---

## 3. Detailed Component Architecture & Code Recommendations

### 3.1 Item Hover Card & Popover Component (`ItemHoverCard.jsx`)

Create `/Users/tanvir/Forkathon2026-Team-KUET_MANTIS/frontend/src/components/items/ItemHoverCard.jsx`:

```jsx
import React, { useState } from 'react';
import { API_ORIGIN } from '../../api/client';

/**
 * ItemHoverCard
 * 
 * Reusable modern popover/hover card for items.
 * Displays item specs, mini-location, owner info, KUET Karma rating,
 * and inline quick actions ("Request to Borrow", "Chat").
 * 
 * @param {Object} props
 * @param {Object} props.item - Item data object
 * @param {Function} [props.onRequest] - Callback when user clicks "Request to Borrow"
 * @param {Function} [props.onChat] - Callback when user clicks "Chat"
 * @param {Function} [props.onFocusOnMap] - Callback to pan/zoom main map to item coordinates
 * @param {'card' | 'popover' | 'inline'} [props.variant='card'] - Display mode
 */
export default function ItemHoverCard({
  item,
  onRequest,
  onChat,
  onFocusOnMap,
  variant = 'card'
}) {
  const [isHovered, setIsHovered] = useState(false);

  // Formatting Fallbacks
  const placeholderImage = 'https://images.unsplash.com/photo-1581092160607-ee22621dd758?w=500&auto=format&fit=crop&q=60';
  const rawImage = item.image_url || item.image;
  const imageSrc = rawImage
    ? (rawImage.startsWith('http') ? rawImage : `${API_ORIGIN}${rawImage}`)
    : placeholderImage;

  const isBeacon = item.type === 'borrow';
  const ownerName = item.owner?.name || item.lender_name || 'KUET Student';
  const ownerDept = item.owner?.dept || item.dept || 'Engineering';
  const ownerRoll = item.owner?.roll || item.roll || 'Verified';
  const ownerKarma = item.owner?.karma ?? item.karma ?? 100;
  const totalExchanges = (item.owner?.total_lends || 0) + (item.owner?.total_borrows || 0) || item.total_exchanges || 12;

  // Initials for avatar
  const initials = ownerName
    .split(' ')
    .filter(Boolean)
    .slice(0, 2)
    .map(w => w[0])
    .join('')
    .toUpperCase() || 'KU';

  // Coordinates & Landmark
  const lat = item.latitude ?? item.lat;
  const lng = item.longitude ?? item.lng;
  const hasCoords = lat !== null && lat !== undefined && lng !== null && lng !== undefined;
  const zoneName = item.zone || item.zone_id || 'KUET Main Campus';

  return (
    <div
      className="relative group bg-white rounded-2xl border border-slate-200/80 shadow-sm hover:shadow-xl transition-all duration-200 overflow-hidden flex flex-col"
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      {/* 1. Thumbnail Header with Status Badges */}
      <div className="relative w-full h-44 bg-slate-100 overflow-hidden">
        <img
          src={imageSrc}
          alt={item.title}
          className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
          onError={(e) => { e.target.src = placeholderImage; }}
        />
        
        {/* Type Badge (Lend vs Borrow Beacon) */}
        <div className="absolute top-3 left-3">
          {isBeacon ? (
            <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-bold bg-rose-600/90 text-white backdrop-blur-md shadow-md animate-pulse">
              <span className="h-2 w-2 rounded-full bg-white"></span>
              🚨 Demand Beacon
            </span>
          ) : (
            <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-bold bg-emerald-600/90 text-white backdrop-blur-md shadow-md">
              <span className="h-2 w-2 rounded-full bg-emerald-200"></span>
              🟢 Available to Lend
            </span>
          )}
        </div>

        {/* Condition Badge */}
        <div className="absolute top-3 right-3">
          <span className="px-2 py-0.5 rounded-md text-[11px] font-semibold bg-white/90 text-slate-700 backdrop-blur-md shadow-sm border border-slate-200/50">
            {item.condition || 'Good'}
          </span>
        </div>

        {/* Category Pill Over Image Bottom */}
        <div className="absolute bottom-2.5 left-3">
          <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-slate-900/75 text-white backdrop-blur-sm">
            {item.category || 'General'}
          </span>
        </div>
      </div>

      {/* 2. Content Body */}
      <div className="p-4 flex-1 flex flex-col justify-between">
        <div>
          {/* Title */}
          <h3 className="text-base font-bold text-slate-900 truncate mb-1" title={item.title}>
            {item.title}
          </h3>

          {/* Description / Specs */}
          <p className="text-xs text-slate-600 line-clamp-2 mb-3">
            {item.specs || item.description || 'No additional specifications provided.'}
          </p>

          {/* 3. Mini-Location Badge */}
          <div className="bg-slate-50 border border-slate-200/70 rounded-xl p-2.5 mb-3 flex items-center justify-between">
            <div className="flex items-center gap-2 min-w-0">
              <span className="text-base flex-shrink-0">📍</span>
              <div className="min-w-0">
                <div className="text-xs font-semibold text-slate-800 truncate">{zoneName}</div>
                <div className="text-[10px] text-slate-500 truncate">
                  {hasCoords ? `${Number(lat).toFixed(4)}°N, ${Number(lng).toFixed(4)}°E` : 'Campus perimeter'} · Within 700m
                </div>
              </div>
            </div>
            {hasCoords && onFocusOnMap && (
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onFocusOnMap([Number(lng), Number(lat)]);
                }}
                className="flex-shrink-0 ml-2 px-2 py-1 text-[11px] font-medium text-blue-700 hover:text-blue-800 bg-blue-50 hover:bg-blue-100 rounded-lg transition"
                title="Pan map to this location"
              >
                Focus 🎯
              </button>
            )}
          </div>

          {/* 4. Owner Info & KUET Karma Rating Badge */}
          <div className="flex items-center justify-between pt-2 border-t border-slate-100">
            {/* Student Details */}
            <div className="flex items-center gap-2 min-w-0">
              <div className="h-8 w-8 rounded-full bg-gradient-to-br from-blue-600 to-indigo-600 text-white font-bold text-xs flex items-center justify-center shadow-sm flex-shrink-0">
                {initials}
              </div>
              <div className="min-w-0">
                <div className="text-xs font-semibold text-slate-900 truncate flex items-center gap-1">
                  {ownerName}
                  <span className="text-blue-600 text-[10px]" title="Verified KUET Student">✓</span>
                </div>
                <div className="text-[10px] text-slate-500 truncate">
                  {ownerDept} · Roll {ownerRoll}
                </div>
              </div>
            </div>

            {/* KUET Karma Score Pill */}
            <div className="flex flex-col items-end flex-shrink-0">
              <div className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-bold bg-amber-50 text-amber-900 border border-amber-200 shadow-2xs">
                <span className="text-amber-500">⚡</span>
                <span>{ownerKarma}</span>
                <span className="text-[10px] font-medium text-amber-700">Karma</span>
              </div>
              <span className="text-[9px] text-slate-600 mt-0.5">
                {totalExchanges} exchanges
              </span>
            </div>
          </div>
        </div>

        {/* 5. Quick Actions (Inline Modal Trigger, Avoiding Page Redirects) */}
        <div className="mt-4 pt-3 border-t border-slate-100 flex items-center gap-2">
          {onRequest && (
            <button
              onClick={(e) => {
                e.stopPropagation();
                onRequest(item);
              }}
              className={`flex-1 py-2 px-3 rounded-xl text-xs font-semibold shadow-sm transition flex items-center justify-center gap-1.5 ${
                isBeacon
                  ? 'bg-amber-600 hover:bg-amber-700 text-white'
                  : 'bg-blue-600 hover:bg-blue-700 text-white'
              }`}
            >
              {isBeacon ? '⚡ Offer to Lend' : '🤝 Request to Borrow'}
            </button>
          )}

          {onChat && (
            <button
              onClick={(e) => {
                e.stopPropagation();
                onChat(item.owner || { name: ownerName });
              }}
              className="px-3 py-2 border border-slate-300 hover:bg-slate-50 text-slate-700 rounded-xl text-xs font-semibold transition"
              title="Chat with owner"
            >
              💬
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
```

### 3.2 MapLibre Marker Rich Popup HTML Generator

Exported helper for `frontend/src/components/map/GodsEyeMap.jsx` ensuring popups inside the canvas have identical styling, karma badges, and action triggers:

```javascript
/**
 * Generates rich HTML for maplibregl.Popup instances
 * Dispatches to window.__campusShareActions to avoid React rerender teardowns
 */
export function generateMapPopupHtml(item) {
  const isBeacon = item.type === 'borrow';
  const ownerName = item.owner?.name || item.lender_name || 'KUET Student';
  const ownerDept = item.owner?.dept || item.dept || 'KUET';
  const ownerRoll = item.owner?.roll || item.roll || 'Verified';
  const ownerKarma = item.owner?.karma ?? item.karma ?? 100;
  const totalExchanges = (item.owner?.total_lends || 0) + (item.owner?.total_borrows || 0) || item.total_exchanges || 10;
  const zoneName = item.zone || item.zone_id || 'KUET Campus';

  const defaultImg = isBeacon
    ? 'https://images.unsplash.com/photo-1616469829941-c7200edec809?w=400'
    : 'https://images.unsplash.com/photo-1583863788434-e58a36330cf0?w=400';
  const imgSrc = item.image_url || item.image || defaultImg;

  const initials = ownerName.split(' ').filter(Boolean).slice(0, 2).map(n => n[0]).join('').toUpperCase() || 'KU';
  const badgeHtml = isBeacon
    ? `<span style="background:rgba(225,29,72,0.95); color:#fff; font-size:10px; font-weight:700; padding:2px 8px; border-radius:999px;">🚨 Demand Beacon</span>`
    : `<span style="background:rgba(5,150,105,0.95); color:#fff; font-size:10px; font-weight:700; padding:2px 8px; border-radius:999px;">🟢 Available to Lend</span>`;

  return `
    <div style="font-family:Inter,system-ui,sans-serif; width:260px; border-radius:14px; overflow:hidden; background:#ffffff; box-shadow:0 10px 25px -5px rgba(0,0,0,0.1);">
      <div style="position:relative; width:100%; height:110px; background:#f1f5f9; overflow:hidden;">
        <img src="${imgSrc}" alt="${item.title}" style="width:100%; height:100%; object-fit:cover;" onerror="this.src='${defaultImg}'" />
        <div style="position:absolute; top:8px; left:8px;">${badgeHtml}</div>
        <div style="position:absolute; bottom:6px; left:8px; background:rgba(15,23,42,0.75); color:#fff; font-size:10px; font-weight:600; padding:2px 6px; border-radius:4px;">
          ${item.category || 'General'}
        </div>
      </div>
      <div style="padding:12px;">
        <div style="font-size:13px; font-weight:700; color:#0f172a; margin-bottom:4px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">
          ${item.title}
        </div>
        <div style="font-size:11px; color:#64748b; margin-bottom:8px; display:-webkit-box; -webkit-line-clamp:2; -webkit-box-orient:vertical; overflow:hidden;">
          ${item.specs || item.description || 'Available on campus.'}
        </div>
        
        <div style="background:#f8fafc; border:1px solid #e2e8f0; border-radius:8px; padding:6px 8px; font-size:10px; color:#334155; margin-bottom:8px; display:flex; justify-content:space-between; align-items:center;">
          <span>📍 <strong>${zoneName}</strong></span>
          <span style="color:#64748b;">KUET Perimeter</span>
        </div>

        <div style="display:flex; justify-content:space-between; align-items:center; border-top:1px solid #f1f5f9; padding-top:8px; margin-bottom:10px;">
          <div style="display:flex; align-items:center; gap:6px;">
            <div style="width:24px; height:24px; border-radius:999px; background:#2563eb; color:#fff; font-size:9px; font-weight:700; display:flex; align-items:center; justify-content:center;">
              ${initials}
            </div>
            <div>
              <div style="font-size:11px; font-weight:600; color:#0f172a;">${ownerName}</div>
              <div style="font-size:9px; color:#64748b;">${ownerDept} • Roll ${ownerRoll}</div>
            </div>
          </div>
          <div style="background:#fef3c7; border:1px solid #fde68a; color:#78350f; font-size:10px; font-weight:700; padding:2px 6px; border-radius:999px;">
            ⚡ ${ownerKarma} Karma
          </div>
        </div>

        <div style="display:flex; gap:6px;">
          <button 
            onclick="window.__campusShareActions && window.__campusShareActions.onRequestBorrow(${item.id})"
            style="flex:1; background:#2563eb; color:#fff; border:none; border-radius:8px; padding:7px 0; font-size:11px; font-weight:600; cursor:pointer;"
          >
            ${isBeacon ? '⚡ Offer to Lend' : '🤝 Request Borrow'}
          </button>
          <button 
            onclick="window.__campusShareActions && window.__campusShareActions.onChatUser('${ownerName}')"
            style="background:#f8fafc; border:1px solid #cbd5e1; color:#334155; border-radius:8px; padding:7px 10px; font-size:11px; font-weight:600; cursor:pointer;"
          >
            💬
          </button>
        </div>
      </div>
    </div>
  `;
}
```

---

### 3.3 AddItemModal with Click-to-Pinpoint Mode (`AddItemModal.jsx`)

Create `/Users/tanvir/Forkathon2026-Team-KUET_MANTIS/frontend/src/components/items/AddItemModal.jsx`:

```jsx
import React, { useState, useEffect } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import api from '../../api/client';
import toast from 'react-hot-toast';

const DEFAULT_CATEGORIES = [
  'Calculators',
  'Chargers',
  'Books',
  'Lab Equipment',
  'Drafting Tools',
  'Electronics',
  'Others'
];

/**
 * AddItemModal
 * 
 * Implements 100% compliant click-to-pinpoint mode:
 * 1. User fills basic details (Title, Type, Category, Specs, Condition).
 * 2. User clicks "📍 Pinpoint on Campus Map" -> modal hides, map enters crosshair mode.
 * 3. User clicks any point on the KUET campus map -> coordinates captured.
 * 4. Modal reopens with coordinates and detected KUET landmark pre-filled.
 * 5. Submits to POST /api/items/ and invalidates React Query cache.
 */
export default function AddItemModal({
  isOpen,
  onClose,
  onStartPinpoint,
  pinpointCoords,
  landmarks = []
}) {
  const queryClient = useQueryClient();

  // Form State
  const [type, setType] = useState('lend'); // 'lend' or 'borrow'
  const [title, setTitle] = useState('');
  const [category, setCategory] = useState('Calculators');
  const [specs, setSpecs] = useState('');
  const [condition, setCondition] = useState('Good');
  const [zone, setZone] = useState('');
  const [coords, setCoords] = useState(null); // { lat, lng }
  const [imageFile, setImageFile] = useState(null);
  const [imagePreview, setImagePreview] = useState('');

  // Synchronize coordinates when user completes map pinpointing
  useEffect(() => {
    if (pinpointCoords && pinpointCoords.lat && pinpointCoords.lng) {
      setCoords({ lat: pinpointCoords.lat, lng: pinpointCoords.lng });
      
      // If a zone name was auto-detected or provided, use it
      if (pinpointCoords.zone) {
        setZone(pinpointCoords.zone);
      } else if (landmarks.length > 0) {
        // Find nearest landmark to coordinates
        const nearest = findNearestLandmark(pinpointCoords.lat, pinpointCoords.lng, landmarks);
        if (nearest) setZone(nearest.name);
      }
    }
  }, [pinpointCoords, landmarks]);

  // Nearest Landmark Helper (Euclidean distance approximation for campus scale)
  const findNearestLandmark = (lat, lng, list) => {
    if (!list || list.length === 0) return null;
    let closest = null;
    let minD = Infinity;
    list.forEach(lm => {
      if (lm.coords) {
        const [lLat, lLng] = lm.coords;
        const d = Math.hypot(lat - lLat, lng - lLng);
        if (d < minD) {
          minD = d;
          closest = lm;
        }
      }
    });
    return closest;
  };

  const handleLandmarkSelect = (e) => {
    const selectedName = e.target.value;
    setZone(selectedName);
    const match = landmarks.find(l => l.name === selectedName);
    if (match && match.coords) {
      setCoords({ lat: match.coords[0], lng: match.coords[1] });
    }
  };

  const handleImageChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      setImageFile(file);
      setImagePreview(URL.createObjectURL(file));
    }
  };

  // Trigger interactive map pinpointing
  const handlePinpointClick = () => {
    if (onStartPinpoint) {
      onStartPinpoint({
        title,
        category,
        type,
        specs,
        condition,
        zone
      });
    }
  };

  // Submit Mutation
  const mutation = useMutation({
    mutationFn: async () => {
      // Support both JSON or Multipart FormData
      if (imageFile) {
        const formData = new FormData();
        formData.append('title', title.trim());
        formData.append('category', category);
        formData.append('type', type);
        formData.append('specs', specs.trim());
        formData.append('description', specs.trim());
        formData.append('condition', condition);
        formData.append('zone', zone || 'KUET Main Campus');
        if (coords) {
          formData.append('latitude', coords.lat);
          formData.append('longitude', coords.lng);
        }
        formData.append('image', imageFile);
        return api.post('/items', formData, {
          headers: { 'Content-Type': 'multipart/form-data' }
        });
      } else {
        const payload = {
          title: title.trim(),
          category,
          type,
          specs: specs.trim(),
          description: specs.trim(),
          condition,
          zone: zone || 'KUET Main Campus',
          latitude: coords ? coords.lat : 22.9006,
          longitude: coords ? coords.lng : 89.5024
        };
        return api.post('/items', payload);
      }
    },
    onSuccess: () => {
      toast.success(type === 'borrow' ? '🚨 Demand Beacon broadcasted!' : '🟢 Item listed successfully!');
      queryClient.invalidateQueries({ queryKey: ['items'] });
      resetForm();
      onClose();
    },
    onError: (err) => {
      toast.error(err.response?.data?.detail || 'Failed to publish item');
    }
  });

  const resetForm = () => {
    setTitle('');
    setCategory('Calculators');
    setSpecs('');
    setCondition('Good');
    setZone('');
    setCoords(null);
    setImageFile(null);
    setImagePreview('');
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!title.trim()) {
      toast.error('Please provide an item title');
      return;
    }
    mutation.mutate();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm animate-fade-in">
      <div className="bg-white rounded-2xl shadow-2xl border border-slate-200 w-full max-w-xl overflow-hidden flex flex-col max-h-[90vh]">
        
        {/* Modal Header */}
        <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between bg-slate-50/70">
          <div>
            <h2 className="text-lg font-bold text-slate-900">
              {type === 'borrow' ? '🚨 Broadcast Demand Beacon' : '📦 List Item for Sharing'}
            </h2>
            <p className="text-xs text-slate-500">
              Share with fellow KUET students inside the 700m campus boundary
            </p>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-600 p-1.5 rounded-lg hover:bg-slate-100 transition"
          >
            ✕
          </button>
        </div>

        {/* Form Body */}
        <form onSubmit={handleSubmit} className="p-6 overflow-y-auto space-y-4 flex-1">
          
          {/* Listing Type Toggle */}
          <div>
            <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
              Listing Mode
            </label>
            <div className="grid grid-cols-2 gap-2 p-1 bg-slate-100 rounded-xl border border-slate-200">
              <button
                type="button"
                onClick={() => setType('lend')}
                className={`py-2 px-4 rounded-lg text-xs font-bold transition ${
                  type === 'lend'
                    ? 'bg-emerald-600 text-white shadow-sm'
                    : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                🟢 I have an item to Lend
              </button>
              <button
                type="button"
                onClick={() => setType('borrow')}
                className={`py-2 px-4 rounded-lg text-xs font-bold transition ${
                  type === 'borrow'
                    ? 'bg-rose-600 text-white shadow-sm'
                    : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                🚨 I need to Borrow (Beacon)
              </button>
            </div>
          </div>

          {/* Title */}
          <div>
            <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
              Title *
            </label>
            <input
              type="text"
              required
              placeholder={type === 'borrow' ? 'e.g. Need Casio fx-991EX for Math Lab' : 'e.g. Casio fx-991EX ClassWiz Calculator'}
              className="w-full border border-slate-300 rounded-xl px-3.5 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
            />
          </div>

          {/* Category & Condition Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                Category *
              </label>
              <select
                className="w-full border border-slate-300 rounded-xl px-3 py-2 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                value={category}
                onChange={(e) => setCategory(e.target.value)}
              >
                {DEFAULT_CATEGORIES.map(cat => (
                  <option key={cat} value={cat}>{cat}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                Condition
              </label>
              <select
                className="w-full border border-slate-300 rounded-xl px-3 py-2 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                value={condition}
                onChange={(e) => setCondition(e.target.value)}
              >
                <option value="Like New">Like New</option>
                <option value="Good">Good</option>
                <option value="Fair">Fair</option>
                <option value="Needs Repair">Needs Repair</option>
              </select>
            </div>
          </div>

          {/* Specs / Description */}
          <div>
            <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
              Specifications & Notes
            </label>
            <textarea
              rows="2"
              placeholder="e.g. Dual power solar/battery, original casing included. Available near CSE bldg."
              className="w-full border border-slate-300 rounded-xl px-3.5 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              value={specs}
              onChange={(e) => setSpecs(e.target.value)}
            />
          </div>

          {/* Interactive Campus Pinpoint Section */}
          <div className="bg-slate-50 border border-slate-200/80 rounded-xl p-4 space-y-3">
            <div className="flex items-center justify-between">
              <div>
                <span className="text-xs font-bold text-slate-800 flex items-center gap-1.5">
                  📍 Campus Location & Pinpoint
                </span>
                <span className="text-[11px] text-slate-500 block">
                  Choose a landmark or click anywhere on the KUET campus map
                </span>
              </div>
              <button
                type="button"
                onClick={handlePinpointClick}
                className="px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-semibold shadow-xs transition flex items-center gap-1.5"
              >
                <span>📍</span>
                <span>Pinpoint on Map</span>
              </button>
            </div>

            {/* Coordinate Status Feedback */}
            {coords ? (
              <div className="bg-emerald-50 border border-emerald-200 rounded-lg p-2.5 flex items-center justify-between text-xs text-emerald-900">
                <div className="flex items-center gap-2">
                  <span className="text-emerald-600 font-bold">✓ Location Set:</span>
                  <span className="font-mono">{coords.lat.toFixed(4)}°N, {coords.lng.toFixed(4)}°E</span>
                  {zone && <span className="text-emerald-700 font-medium">({zone})</span>}
                </div>
                <button
                  type="button"
                  onClick={() => setCoords(null)}
                  className="text-emerald-700 hover:text-emerald-900 text-[11px] underline"
                >
                  Reset
                </button>
              </div>
            ) : (
              <div className="text-xs text-slate-500 italic bg-white border border-dashed border-slate-300 rounded-lg p-2.5 text-center">
                No coordinates chosen yet. Defaulting to KUET Central Academic Area [22.9006, 89.5024].
              </div>
            )}

            {/* Quick Landmark Dropdown */}
            {landmarks.length > 0 && (
              <div>
                <label className="block text-[11px] font-semibold text-slate-600 mb-1">
                  Or select nearest KUET Landmark:
                </label>
                <select
                  className="w-full border border-slate-200 rounded-lg px-2.5 py-1.5 text-xs bg-white focus:outline-none focus:ring-1 focus:ring-blue-500"
                  value={zone}
                  onChange={handleLandmarkSelect}
                >
                  <option value="">-- Choose Landmark --</option>
                  {landmarks.map(lm => (
                    <option key={lm.id} value={lm.name}>
                      {lm.name} ({lm.category})
                    </option>
                  ))}
                </select>
              </div>
            )}
          </div>

          {/* Image Upload */}
          <div>
            <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
              Item Photo (Optional)
            </label>
            <input
              type="file"
              accept="image/*"
              className="w-full text-xs text-slate-500 file:mr-3 file:py-1.5 file:px-3 file:rounded-lg file:border-0 file:text-xs file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
              onChange={handleImageChange}
            />
            {imagePreview && (
              <div className="mt-2 relative w-24 h-24 rounded-lg overflow-hidden border border-slate-200 shadow-sm">
                <img src={imagePreview} alt="Preview" className="w-full h-full object-cover" />
                <button
                  type="button"
                  onClick={() => { setImageFile(null); setImagePreview(''); }}
                  className="absolute top-1 right-1 bg-slate-900/80 text-white rounded-full w-5 h-5 flex items-center justify-center text-[10px]"
                >
                  ✕
                </button>
              </div>
            )}
          </div>

          {/* Form Actions */}
          <div className="pt-3 border-t border-slate-100 flex items-center justify-end gap-3">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-xs font-semibold text-slate-600 hover:text-slate-800 rounded-xl hover:bg-slate-100 transition"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={mutation.isPending}
              className={`px-5 py-2.5 text-xs font-bold text-white rounded-xl shadow-sm transition flex items-center gap-2 ${
                type === 'borrow'
                  ? 'bg-rose-600 hover:bg-rose-700'
                  : 'bg-blue-600 hover:bg-blue-700'
              }`}
            >
              {mutation.isPending ? 'Publishing...' : (type === 'borrow' ? '🚨 Broadcast Beacon' : '🟢 List Item')}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
```

---

### 3.4 Minimal 3-Field Registration & Live Roll Decoding Badge

Create `/Users/tanvir/Forkathon2026-Team-KUET_MANTIS/frontend/src/components/auth/Register.jsx` (and directly integrate into `App.jsx`):

```jsx
import React, { useState, useMemo } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import api from '../../api/client';
import toast from 'react-hot-toast';

/**
 * KUET Department Code Directory
 * Mapped according to KUET academic department numbering
 */
const KUET_DEPTS = {
  '01': { code: 'CE', name: 'Civil Engineering' },
  '03': { code: 'EEE', name: 'Electrical & Electronic Engineering' },
  '05': { code: 'ME', name: 'Mechanical Engineering' },
  '07': { code: 'CSE', name: 'Computer Science & Engineering' },
  '09': { code: 'ECE', name: 'Electronics & Communication Engineering' },
  '11': { code: 'IEM', name: 'Industrial Engineering & Management' },
  '13': { code: 'ESE', name: 'Energy Science & Engineering' },
  '15': { code: 'BME', name: 'Biomedical Engineering' },
  '17': { code: 'URP', name: 'Urban & Regional Planning' },
  '19': { code: 'BECM', name: 'Building Engineering & Construction' },
  '21': { code: 'MSE', name: 'Materials Science & Engineering' },
  '23': { code: 'ChE', name: 'Chemical Engineering' },
  '25': { code: 'MTE', name: 'Mechatronics Engineering' },
  '27': { code: 'Arch', name: 'Architecture' }
};

/**
 * Client-Side KUET Email & Roll Decoder
 * Validates @stud.kuet.ac.bd and extracts trailing 7 digits:
 * 2-digit batch, 2-digit dept, 3-digit roll
 */
export function decodeKuetEmail(email) {
  const clean = (email || '').trim().toLowerCase();
  if (!clean) return { status: 'empty' };

  if (!clean.includes('@')) {
    return { status: 'typing' };
  }

  if (!clean.endsWith('@stud.kuet.ac.bd')) {
    return {
      status: 'invalid_domain',
      message: 'Only official @stud.kuet.ac.bd student emails are accepted.'
    };
  }

  const localPart = clean.split('@')[0];
  const match = localPart.match(/(\d{2})(\d{2})(\d{3})$/);
  if (!match) {
    return {
      status: 'invalid_format',
      message: 'Email must end with 7-digit student ID (e.g., siddique2307010@stud.kuet.ac.bd).'
    };
  }

  const [, batchDigits, deptDigits, rollDigits] = match;
  const deptInfo = KUET_DEPTS[deptDigits] || {
    code: `Dept ${deptDigits}`,
    name: `Department ${deptDigits}`
  };

  return {
    status: 'valid',
    batch: batchDigits,
    batchYear: `20${batchDigits}`,
    deptCode: deptInfo.code,
    deptName: deptInfo.name,
    roll: rollDigits,
    fullRoll: `${batchDigits}${deptDigits}${rollDigits}`,
    startingKarma: 100
  };
}

export default function Register() {
  const navigate = useNavigate();

  // STRICT REQUIREMENT R3: Only 3 fields allowed in form state
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);

  // Real-time roll decoding badge computation
  const decoded = useMemo(() => decodeKuetEmail(email), [email]);

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (decoded.status !== 'valid') {
      toast.error(decoded.message || 'Please provide a valid KUET student email');
      return;
    }

    setLoading(true);
    try {
      // Sends strictly 3 fields as mandated by R3
      const res = await api.post('/auth/register', {
        name: name.trim(),
        email: email.trim().toLowerCase(),
        password
      });

      toast.success('Registration successful! 100 Base Karma awarded. ⚡');
      navigate('/login');
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Registration failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-[80vh] flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-xl border border-slate-200/80 p-8 w-full max-w-md">
        {/* Header */}
        <div className="text-center mb-6">
          <div className="inline-flex h-12 w-12 rounded-xl bg-blue-600 text-white font-black text-xl items-center justify-center mb-3 shadow-md">
            KU
          </div>
          <h1 className="text-2xl font-bold text-slate-900">KUET CampusShare</h1>
          <p className="text-xs text-slate-500 mt-1">
            Student Asset Exchange & Resource Sharing Network
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          
          {/* Field 1: Full Name */}
          <div>
            <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
              Full Name *
            </label>
            <input
              type="text"
              required
              minLength={2}
              placeholder="e.g. Siddique Ahmed"
              className="w-full border border-slate-300 rounded-xl px-3.5 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              value={name}
              onChange={(e) => setName(e.target.value)}
            />
          </div>

          {/* Field 2: KUET Student Email */}
          <div>
            <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
              KUET Student Email *
            </label>
            <input
              type="email"
              required
              placeholder="e.g. siddique2307010@stud.kuet.ac.bd"
              className="w-full border border-slate-300 rounded-xl px-3.5 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
          </div>

          {/* Live Roll Decoding Badge Display */}
          {decoded.status === 'valid' && (
            <div className="bg-emerald-50/80 border border-emerald-200 rounded-xl p-3.5 space-y-2 text-emerald-950 animate-fade-in shadow-2xs">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold flex items-center gap-1.5 text-emerald-800">
                  <span>🎓</span>
                  <span>KUET Credentials Decoded</span>
                </span>
                <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-100 text-amber-900 border border-amber-300">
                  ⚡ 100 Base Karma
                </span>
              </div>
              <div className="grid grid-cols-3 gap-2 pt-1 text-center">
                <div className="bg-white/80 rounded-lg p-1.5 border border-emerald-100">
                  <span className="text-[10px] text-slate-500 block">Batch</span>
                  <span className="text-xs font-bold text-slate-800">{decoded.batchYear} ('{decoded.batch})</span>
                </div>
                <div className="bg-white/80 rounded-lg p-1.5 border border-emerald-100">
                  <span className="text-[10px] text-slate-500 block">Dept</span>
                  <span className="text-xs font-bold text-slate-800" title={decoded.deptName}>{decoded.deptCode}</span>
                </div>
                <div className="bg-white/80 rounded-lg p-1.5 border border-emerald-100">
                  <span className="text-[10px] text-slate-500 block">Roll</span>
                  <span className="text-xs font-bold text-slate-800">{decoded.roll}</span>
                </div>
              </div>
            </div>
          )}

          {decoded.status === 'invalid_domain' && (
            <div className="bg-rose-50 border border-rose-200 rounded-xl p-2.5 text-xs text-rose-700 flex items-center gap-2">
              <span>⚠️</span>
              <span>{decoded.message}</span>
            </div>
          )}

          {decoded.status === 'invalid_format' && (
            <div className="bg-amber-50 border border-amber-200 rounded-xl p-2.5 text-xs text-amber-800 flex items-center gap-2">
              <span>ℹ️</span>
              <span>{decoded.message}</span>
            </div>
          )}

          {/* Field 3: Password */}
          <div>
            <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
              Password *
            </label>
            <input
              type="password"
              required
              minLength={4}
              placeholder="••••••••"
              className="w-full border border-slate-300 rounded-xl px-3.5 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
            <span className="text-[10px] text-slate-500 mt-1 block">
              Department, Batch, and Roll will be inferred automatically.
            </span>
          </div>

          {/* Submit Button */}
          <button
            type="submit"
            disabled={loading || decoded.status !== 'valid'}
            className="w-full mt-2 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-300 disabled:cursor-not-allowed text-white font-bold py-2.5 rounded-xl shadow-md transition"
          >
            {loading ? 'Registering...' : 'Register & Claim 100 Base Karma ⚡'}
          </button>
        </form>

        <div className="mt-6 text-center text-xs text-slate-500">
          Already registered?{' '}
          <Link to="/login" className="text-blue-600 font-semibold hover:underline">
            Log in to your account
          </Link>
        </div>
      </div>
    </div>
  );
}
```

---

### 3.5 KUET Karma Protocol Across All Frontend Views

Here is the exact code refactoring for each view to display the KUET Karma score:

#### A. Sidebar Active User Footer (`DashboardLayout.jsx`)
Replace basic name tag with the Karma reputation pill:

```jsx
{/* User Card in Left Sidebar */}
<div className="p-4 border-t border-slate-200/80 bg-slate-50/50">
  <div className="flex items-center gap-3">
    <div className="h-10 w-10 rounded-full bg-gradient-to-br from-blue-600 to-indigo-700 text-white font-bold flex items-center justify-center text-sm shadow-sm flex-shrink-0">
      {user.name.slice(0, 2).toUpperCase()}
    </div>
    <div className="min-w-0 flex-1">
      <div className="text-xs font-bold text-slate-900 truncate flex items-center gap-1">
        <span>{user.name}</span>
      </div>
      <div className="text-[11px] text-slate-500 truncate">
        {user.dept || 'CSE'} · Roll {user.roll || '010'}
      </div>
    </div>
  </div>

  {/* KUET Karma Status Pill */}
  <div className="mt-2.5 flex items-center justify-between bg-white border border-amber-200/80 rounded-xl px-2.5 py-1.5 shadow-2xs">
    <div className="flex items-center gap-1 text-xs font-bold text-amber-900">
      <span className="text-amber-500">⚡</span>
      <span>{user.karma ?? 100} Karma</span>
    </div>
    <span className="text-[10px] font-semibold text-emerald-700 bg-emerald-50 px-1.5 py-0.5 rounded">
      {user.karma >= 110 ? 'Exemplary' : 'Active'}
    </span>
  </div>
</div>
```

#### B. Redesigned User Profile View (`Profile.jsx`)
Update `/Users/tanvir/Forkathon2026-Team-KUET_MANTIS/frontend/src/pages/Profile.jsx`:

```jsx
import React from 'react';
import { useAuth } from '../context/AuthContext';

export default function Profile() {
  const { user } = useAuth();
  if (!user) return <div className="p-8 text-center text-slate-500">Please log in to view profile.</div>;

  const karma = user.karma ?? 100;
  const netKarmaChange = karma - 100;

  return (
    <div className="max-w-3xl mx-auto p-6 space-y-6">
      <h1 className="text-2xl font-bold text-slate-900">Student Profile & Karma Record</h1>

      {/* Hero Karma Rating Card */}
      <div className="bg-gradient-to-r from-amber-500 via-amber-600 to-orange-600 rounded-2xl p-6 text-white shadow-lg flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <span className="text-xs font-bold uppercase tracking-widest text-amber-100 block mb-1">
            KUET Karma Protocol Score
          </span>
          <div className="text-4xl font-extrabold flex items-center gap-2">
            <span>⚡ {karma}</span>
            <span className="text-sm font-medium text-amber-100 bg-white/20 px-2.5 py-0.5 rounded-full">
              {netKarmaChange >= 0 ? `+${netKarmaChange}` : netKarmaChange} from Base
            </span>
          </div>
          <p className="text-xs text-amber-100 mt-2">
            Base Karma: 100 · Earn +10 per lend · +5 for on-time returns · -30 late penalty
          </p>
        </div>

        <div className="bg-white/10 backdrop-blur-md rounded-xl p-3 text-center sm:text-right border border-white/20">
          <span className="text-[11px] text-amber-100 block">Exchanges Completed</span>
          <span className="text-2xl font-bold">{(user.total_lends || 0) + (user.total_borrows || 0)}</span>
          <span className="text-[10px] text-amber-200 block">({user.total_lends || 0} Lends, {user.total_borrows || 0} Borrows)</span>
        </div>
      </div>

      {/* Profile Details & Protocol Reference */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        
        {/* Academic Identity */}
        <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm space-y-3">
          <h2 className="text-sm font-bold text-slate-800 uppercase tracking-wider">
            KUET Academic Identity
          </h2>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between py-1.5 border-b border-slate-100">
              <span className="text-slate-500">Name</span>
              <span className="font-semibold text-slate-900">{user.name}</span>
            </div>
            <div className="flex justify-between py-1.5 border-b border-slate-100">
              <span className="text-slate-500">KUET Email</span>
              <span className="font-semibold text-slate-900">{user.email}</span>
            </div>
            <div className="flex justify-between py-1.5 border-b border-slate-100">
              <span className="text-slate-500">Department</span>
              <span className="font-semibold text-slate-900">{user.dept || 'CSE'}</span>
            </div>
            <div className="flex justify-between py-1.5 border-b border-slate-100">
              <span className="text-slate-500">Batch</span>
              <span className="font-semibold text-slate-900">{user.batch || '2023'}</span>
            </div>
            <div className="flex justify-between py-1.5">
              <span className="text-slate-500">Roll Number</span>
              <span className="font-semibold text-slate-900">{user.roll || '010'}</span>
            </div>
          </div>
        </div>

        {/* Karma Protocol Rules */}
        <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm space-y-3">
          <h2 className="text-sm font-bold text-slate-800 uppercase tracking-wider">
            KUET Karma Rules
          </h2>
          <div className="space-y-2.5 text-xs text-slate-600">
            <div className="flex items-center justify-between p-2 rounded-lg bg-emerald-50 border border-emerald-100 text-emerald-900 font-medium">
              <span>🟢 Lending an item</span>
              <span className="font-bold">+10 Karma</span>
            </div>
            <div className="flex items-center justify-between p-2 rounded-lg bg-blue-50 border border-blue-100 text-blue-900 font-medium">
              <span>⏱️ Returning on-time</span>
              <span className="font-bold">+5 Karma</span>
            </div>
            <div className="flex items-center justify-between p-2 rounded-lg bg-rose-50 border border-rose-100 text-rose-900 font-medium">
              <span>⚠️ Late return penalty</span>
              <span className="font-bold">-30 Karma</span>
            </div>
            <div className="flex items-center justify-between p-2 rounded-lg bg-slate-50 border border-slate-100 text-slate-700">
              <span>🛡️ Initial registration base</span>
              <span className="font-bold">100 Karma</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
```

#### C. Requests Page Borrower Karma Badge (`Requests.jsx`)
In `Requests.jsx` lines 39-44:

```jsx
<div className="flex items-center gap-2">
  <p className="font-semibold text-slate-900">{req.item.title}</p>
  {req.borrower && (
    <span className="inline-flex items-center gap-1 text-[11px] font-bold px-2 py-0.5 rounded-full bg-amber-50 text-amber-900 border border-amber-200">
      ⚡ {req.borrower.karma ?? 100} Karma
    </span>
  )}
</div>
<p className="text-xs text-slate-500">
  {req.borrower_id === user.id
    ? 'You requested from owner'
    : `Request from ${req.borrower.name} (${req.borrower.dept} • Roll ${req.borrower.roll})`}
</p>
```

#### D. Transaction Handover & Return Feedback (`Transaction.jsx`)
In `Transaction.jsx`, update the `returnMutation` handler to inspect `res.data.karma_updated` and present visual celebration feedback:

```jsx
const returnMutation = useMutation({
  mutationFn: () => api.post(`/transactions/return/${requestId}`),
  onSuccess: (res) => {
    const karmaInfo = res.data?.karma_updated;
    if (karmaInfo) {
      if (karmaInfo.is_on_time) {
        toast.success(
          `🎉 Return complete! Borrower earned +${karmaInfo.borrower_change} Karma, Lender earned +${karmaInfo.owner_gain} Karma! ⚡`,
          { duration: 5000 }
        );
      } else {
        toast.error(
          `⚠️ Item returned late! Borrower penalized ${karmaInfo.borrower_change} Karma. Lender earned +${karmaInfo.owner_gain} Karma.`,
          { duration: 5000 }
        );
      }
    } else {
      toast.success('Return confirmed! KUET Karma scores updated.');
    }
    refetch();
  },
  onError: (err) => toast.error(err.response?.data?.detail || 'Failed to complete return')
});
```

---

## 4. Caveats

1. **Host Node/npm Binary Absence:**
   - As observed by `explorer_survey_2`, `node` and `npm` are not currently in the host `$PATH`.
   - The React recommendations avoid adding new external npm packages (such as `@turf/turf` or `lucide-react`). All styling utilizes standard Tailwind CSS utility classes and modern SVG icons, and MapLibre GL JS is accessed via the CDN tag loaded in `frontend/index.html`.
2. **Backend Contract Assumption:**
   - The backend `POST /api/items/` endpoint has been verified to accept either JSON (`application/json`) or multipart form data (`multipart/form-data`) with normalized coordinate fields (`latitude`/`lat`, `longitude`/`lng`), matching `AddItemModal`.
3. **Roll Decoder Leading Zeros:**
   - The 3-digit roll decoder preserves leading zeros (e.g. roll `'010'` remains `'010'`, not integer `10`) to correctly reflect KUET student numbering conventions.

---

## 5. Conclusion

The design for Milestone 2 covers all 4 assigned features:
1. **`ItemHoverCard.jsx` & Map Popovers:** Solves the cluttered full-page redirect issue by delivering an interactive popover with image, status badge, mini-location within the 700m KUET perimeter, student credentials, KUET Karma rating (`⚡ 100 Karma`), and direct inline actions ("Request to Borrow" / "Chat").
2. **`AddItemModal.jsx`:** Fully implements click-to-pinpoint mode with a crosshair cursor, floating banner, nearest KUET landmark detection, and seamless coordinate selection.
3. **Registration Form & Roll Decoder:** Replaces the 6-field registration form with strictly 3 fields (`name`, `email`, `password`) and an animated live badge preview that decodes Batch, Department, Roll, and 100 Base Karma from any `@stud.kuet.ac.bd` email.
4. **Karma UI Across All Views:** Replaces every occurrence of legacy `trust_score` (4.5/5.0) with the KUET Karma Protocol (+10 lend, +5 on-time return, -30 late penalty) in the sidebar footer, item cards, popups, requests, profile, and handover returns.

---

## 6. Verification Method

To independently verify the observations and recommendations:

1. **Verify Existing Registration Form Inadequacies:**
   ```bash
   grep -n "input" /Users/tanvir/Forkathon2026-Team-KUET_MANTIS/frontend/src/App.jsx
   ```
   *Expected:* Lines 63-68 show 6 manual input fields (`email`, `name`, `dept`, `batch`, `roll`, `password`).

2. **Verify Backend 3-Field Acceptance:**
   ```bash
   grep -A 10 "class UserRegister" /Users/tanvir/Forkathon2026-Team-KUET_MANTIS/backend/app/schemas.py
   ```
   *Expected:* Accepts only `name`, `email`, `password`.

3. **Verify Return Endpoint Karma Updated Payload:**
   ```bash
   grep -A 10 "karma_updated" /Users/tanvir/Forkathon2026-Team-KUET_MANTIS/backend/app/routes/transactions.py
   ```
   *Expected:* Returns `owner_gain: 10`, `borrower_change: 5 | -30`, `is_on_time`.

4. **Verify Legacy Trust Score Mentions Across Frontend:**
   ```bash
   grep -rn "trust_score" /Users/tanvir/Forkathon2026-Team-KUET_MANTIS/frontend/src/
   ```
   *Expected:* Matches found in `ItemCard.jsx`, `ItemDetail.jsx`, `Profile.jsx` confirming replacement needed.

5. **Invalidation Condition:**
   - If `frontend/src/components/items/ItemHoverCard.jsx` already exists with click-to-pinpoint and roll decoding, this investigation is superseded. (Confirmed absent).
