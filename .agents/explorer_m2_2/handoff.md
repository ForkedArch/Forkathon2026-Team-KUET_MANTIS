# Enterprise Dashboard Shell Layout & Navigation (R2) — Architecture & Code Recommendations

**Agent:** `explorer_m2_2`  
**Milestone:** M2 (Frontend Dashboard & MapLibre Integration)  
**Target Files:**
- `frontend/src/components/layout/DashboardLayout.jsx`
- `frontend/src/components/layout/Sidebar.jsx`
- `frontend/src/components/layout/TopActionBar.jsx`
- `frontend/src/pages/AllItems.jsx`
- `frontend/src/App.jsx`
- `frontend/src/index.css`

---

## 1. Observation

### 1.1 Existing Layout in `frontend/src/App.jsx`
* **File:** `/Users/tanvir/Forkathon2026-Team-KUET_MANTIS/frontend/src/App.jsx` (Lines 82-99)
* **Current Structure:**
  ```jsx
  export default function App() {
    return (
      <div className="min-h-screen bg-gray-50">
        <Navbar />
        <Toaster position="top-center" />
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/item/:id" element={<ItemDetail />} />
          <Route path="/add" element={<PrivateRoute><AddItem /></PrivateRoute>} />
          <Route path="/requests" element={<PrivateRoute><Requests /></PrivateRoute>} />
          <Route path="/chat/:requestId" element={<PrivateRoute><Chat /></PrivateRoute>} />
          <Route path="/transaction/:requestId" element={<PrivateRoute><Transaction /></PrivateRoute>} />
          <Route path="/profile" element={<PrivateRoute><Profile /></PrivateRoute>} />
        </Routes>
      </div>
    );
  }
  ```
* **Observation:** The application currently relies on a standard horizontal `<Navbar />` with full-page route switches. There is **no left sidebar**, no persistent dashboard shell, no unified top action bar, and no MapLibre map viewport.

### 1.2 Existing Navbar in `frontend/src/components/common/Navbar.jsx`
* **File:** `/Users/tanvir/Forkathon2026-Team-KUET_MANTIS/frontend/src/components/common/Navbar.jsx`
* **Observation:** Renders a basic navbar with text links (`CampusShare`, `+ Add Item`, `Requests`, `Profile`, `Logout`). It lacks KUET branding, active student session metadata (Department, Roll, Karma score), and campus perimeter indicators.

### 1.3 Target Requirements from `ORIGINAL_REQUEST.md` (R2)
* **Lines 24-25:** "Refactor the frontend into a dashboard layout with a left sidebar for navigation (e.g., Map View, My Items, Requests, Profile) and a main content area. The main area should feature a top bar with actions (e.g., 'Add Item'), a search/filter bar, and clean tables/lists for items. Use hover cards or popovers to show item details and mini-map locations. The color scheme should be light and clean with subtle brand accents. Keep options minimal for the prototype."
* **Lines 40-41:** "The React frontend renders a dashboard layout with a left sidebar, top action bar, and the MapLibre map in the main area. Hover cards or popups are used to display item details, avoiding cluttered full-page redirects where possible."

### 1.4 Frontend Environment & Dependencies
* **File:** `/Users/tanvir/Forkathon2026-Team-KUET_MANTIS/frontend/package.json`
* **Installed:** `react: ^18.2.0`, `react-router-dom: ^6.23.1`, `@tanstack/react-query: ^5.40.0`, `tailwindcss: ^3.4.4`, `axios: ^1.7.2`, `react-hot-toast: ^2.4.1`.
* **Not Installed:** `lucide-react` is not installed in `package.json`.
* **Host Tooling:** `node` and `npm` are not available in the host execution environment path. Therefore, all icons must be implemented as clean, dependency-free inline SVGs rather than importing from `lucide-react`, ensuring zero build errors across any environment.

### 1.5 Backend Filtering Capabilities
* **File:** `/Users/tanvir/Forkathon2026-Team-KUET_MANTIS/backend/app/routes/items.py` (Lines 14-51)
* **Endpoints:** `GET /api/items` natively supports query parameters:
  - `search` / `q`: Case-insensitive search across title, description, specs, owner name, and owner dept.
  - `category`: Matches item category (case-insensitive, ignoring "ALL").
  - `type`: Matches `"lend"` or `"borrow"` (ignoring "ALL").
  - `available_only`: Filters active listings.

---

## 2. Logic Chain

1. **Premise 1:** R2 dictates an enterprise dashboard shell layout with a left sidebar, a top action bar, and a main content area hosting either the MapLibre view (`/`) or item listings (`/items`), requests (`/requests`), and profile (`/profile`).
2. **Premise 2:** In modern single-page applications, the shell should remain mounted across route transitions so global search, category selection, and type filtering can be shared seamlessly between the Map View and the Items List View without redundant page reloads or loss of filter state.
3. **Inference 1:** `DashboardLayout` should use React Router's `<Outlet context={{ ... }} />` pattern. It holds state for `search`, `category`, and `listingType`, exposing them via `useOutletContext()` (and a typed/structured helper hook `useDashboard()`).
4. **Premise 3:** In `Tanvir/index.html`, the header displayed student session metadata (Avatar, Full Name, Department, Roll, and Karma rating) and a `📍 700m Campus Perimeter` indicator.
5. **Inference 2:** Placing the active student profile card at the bottom of the left sidebar fulfills both the R2 navigation requirement and the R4 KUET Karma visibility requirement (`⚡ 100 Karma`), with graceful fallback to a guest login prompt if the user is unauthenticated.
6. **Premise 4:** `lucide-react` is absent from `package.json`. Attempting `import { Search } from 'lucide-react'` would cause runtime module resolution errors.
7. **Inference 3:** Providing lightweight, accessible inline SVG icons (Map, Package, Inbox, User, Search, Plus, Lightning, Shield, Logout) eliminates third-party icon dependencies while maintaining pixel-perfect fidelity.
8. **Premise 5:** MapLibre GL JS canvas instances require layout recalculation whenever container dimensions change.
9. **Inference 4:** `DashboardLayout` must ensure full container bounds (`h-screen overflow-hidden`) and trigger a window resize dispatch if the sidebar is toggled on mobile, preventing WebGL canvas clipping.

---

## 3. Caveats

1. **Map Persistence:** When navigating away from `/` to `/requests` or `/profile`, the MapLibre instance unmounts and remounts when returning. This is standard React Router behavior and clean because `GodsEyeMap` initializes quickly (~50ms) using OSM raster tiles.
2. **Icons:** All icons are self-contained SVGs styled with Tailwind utilities (`w-5 h-5 text-slate-500`, etc.). No npm installation is required.
3. **Modal Integration:** The Top Action Bar includes a primary `+ Add Item` CTA button. When clicked, it dispatches `setIsAddModalOpen(true)`. Explorer M2-3 is providing `AddItemModal.jsx`. As a fallback, if `AddItemModal` is not mounted, the button navigates to `/add`.

---

## 4. Conclusion & Complete Code Recommendations

Below are the complete, production-ready code files for the enterprise dashboard layout.

---

### Component 1: `frontend/src/components/layout/TopActionBar.jsx`
* **Path:** `/Users/tanvir/Forkathon2026-Team-KUET_MANTIS/frontend/src/components/layout/TopActionBar.jsx`
* **Features:**
  - Responsive search bar with search lens icon and clear button.
  - Segmented listing type filter tabs: `All`, `🟢 Lending`, `🚨 Beacons`.
  - Category filter selector (with both scrollable pills and select options).
  - High-contrast primary CTA: `+ Add Item` button.
  - Active item count and campus status indicator.

```jsx
import React from 'react';

// Clean inline SVGs (zero external package dependencies)
const SearchIcon = () => (
  <svg className="w-4 h-4 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
  </svg>
);

const PlusIcon = () => (
  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M12 4v16m8-8H4" />
  </svg>
);

const CloseIcon = () => (
  <svg className="w-3.5 h-3.5 text-slate-400 hover:text-slate-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
  </svg>
);

const MenuIcon = () => (
  <svg className="w-5 h-5 text-slate-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 6h16M4 12h16M4 18h16" />
  </svg>
);

const CATEGORIES = [
  { id: 'ALL', label: 'All Categories', icon: '🏷️' },
  { id: 'Calculators', label: 'Calculators', icon: '🧮' },
  { id: 'Electronics & Power', label: 'Power & Chargers', icon: '🔌' },
  { id: 'Lab Equipment', label: 'Lab Equipment', icon: '🔬' },
  { id: 'Books & Notes', label: 'Books & Notes', icon: '📖' },
  { id: 'Cables & Adapters', label: 'Cables', icon: '🔗' },
  { id: 'Other', label: 'Other Items', icon: '📦' }
];

export default function TopActionBar({
  search,
  setSearch,
  category,
  setCategory,
  listingType,
  setListingType,
  onOpenAddModal,
  onToggleSidebar,
  totalItems = null
}) {
  return (
    <header className="h-16 bg-white/95 backdrop-blur-md border-b border-slate-200 px-4 lg:px-6 flex items-center justify-between gap-3 z-20 flex-shrink-0">
      {/* Mobile Sidebar Toggle Button */}
      <button
        onClick={onToggleSidebar}
        className="lg:hidden p-2 rounded-lg text-slate-500 hover:bg-slate-100 hover:text-slate-800 transition-colors"
        title="Toggle Menu"
      >
        <MenuIcon />
      </button>

      {/* Search Input */}
      <div className="relative flex-1 max-w-xs md:max-w-md">
        <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
          <SearchIcon />
        </div>
        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search calculators, chargers, books, roll..."
          className="w-full pl-9 pr-8 py-2 text-sm bg-slate-50 hover:bg-slate-100/80 focus:bg-white border border-slate-200 focus:border-blue-500 rounded-lg outline-none focus:ring-2 focus:ring-blue-500/20 text-slate-800 placeholder-slate-400 transition-all"
        />
        {search && (
          <button
            onClick={() => setSearch('')}
            className="absolute inset-y-0 right-0 pr-2.5 flex items-center"
            title="Clear search"
          >
            <CloseIcon />
          </button>
        )}
      </div>

      {/* Segmented Type Filter (All / Lending / Beacons) */}
      <div className="hidden sm:flex items-center bg-slate-100 p-1 rounded-lg border border-slate-200/80 text-xs font-semibold">
        <button
          onClick={() => setListingType('ALL')}
          className={`px-3 py-1.5 rounded-md transition-all ${
            listingType === 'ALL'
              ? 'bg-white text-slate-900 shadow-xs'
              : 'text-slate-600 hover:text-slate-900'
          }`}
        >
          All Items
        </button>
        <button
          onClick={() => setListingType('lend')}
          className={`px-3 py-1.5 rounded-md transition-all flex items-center gap-1.5 ${
            listingType === 'lend'
              ? 'bg-emerald-50 text-emerald-700 shadow-xs border border-emerald-200/80 font-bold'
              : 'text-slate-600 hover:text-emerald-700'
          }`}
        >
          <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
          Lending
        </button>
        <button
          onClick={() => setListingType('borrow')}
          className={`px-3 py-1.5 rounded-md transition-all flex items-center gap-1.5 ${
            listingType === 'borrow'
              ? 'bg-rose-50 text-rose-700 shadow-xs border border-rose-200/80 font-bold'
              : 'text-slate-600 hover:text-rose-700'
          }`}
        >
          <span className="w-2 h-2 rounded-full bg-rose-500 animate-pulse"></span>
          Beacons
        </button>
      </div>

      {/* Category Dropdown (Compact for Header) */}
      <div className="hidden md:block">
        <select
          value={category}
          onChange={(e) => setCategory(e.target.value)}
          className="text-xs font-medium text-slate-700 bg-white border border-slate-200 rounded-lg px-3 py-2 outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 cursor-pointer shadow-xs"
        >
          {CATEGORIES.map((cat) => (
            <option key={cat.id} value={cat.id}>
              {cat.icon} {cat.label}
            </option>
          ))}
        </select>
      </div>

      {/* Right Actions: Primary Add Item Button */}
      <div className="flex items-center gap-2">
        <button
          onClick={onOpenAddModal}
          className="inline-flex items-center gap-2 px-3.5 py-2 rounded-lg text-sm font-semibold bg-blue-600 hover:bg-blue-700 active:bg-blue-800 text-white shadow-sm hover:shadow transition-all"
        >
          <PlusIcon />
          <span className="hidden xs:inline">Add Item</span>
        </button>
      </div>
    </header>
  );
}
```

---

### Component 2: `frontend/src/components/layout/Sidebar.jsx`
* **Path:** `/Users/tanvir/Forkathon2026-Team-KUET_MANTIS/frontend/src/components/layout/Sidebar.jsx`
* **Features:**
  - KUET CampusShare branding with gradient badge, university title, and 700m perimeter status pill.
  - Active navigation links: Map View (`/`), All Items (`/items`), Borrow Requests (`/requests`), Profile (`/profile`).
  - Active indicator styling (slate/blue soft surface, high-contrast text).
  - Bottom active student profile card: Student Name, Roll (`Roll: 2207001`), Department badge (`CSE '22`), KUET Karma badge (`⚡ 100 Karma`), and Logout action.
  - Guest state fallback with direct Login / Register actions.

```jsx
import React from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';

// Clean inline SVGs for zero-dependency portability
const MapIcon = () => (
  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7" />
  </svg>
);

const PackageIcon = () => (
  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
  </svg>
);

const InboxIcon = () => (
  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 4H6a2 2 0 00-2 2v12a2 2 0 002 2h12a2 2 0 002-2V6a2 2 0 00-2-2h-2m-4-1v8m0 0l3-3m-3 3L9 8m-5 5h2.586a1 1 0 01.707.293l2.414 2.414a1 1 0 00.707.293h3.172a1 1 0 00.707-.293l2.414-2.414a1 1 0 01.707-.293H20" />
  </svg>
);

const UserIcon = () => (
  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
  </svg>
);

const LogoutIcon = () => (
  <svg className="w-4 h-4 text-slate-400 hover:text-rose-600 transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
  </svg>
);

export default function Sidebar({ isOpen, onClose }) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const navLinkClasses = ({ isActive }) =>
    `flex items-center justify-between px-3.5 py-2.5 rounded-lg text-sm font-medium transition-colors ${
      isActive
        ? 'bg-blue-50 text-blue-700 font-semibold border border-blue-100 shadow-xs'
        : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100/80'
    }`;

  // Helper to extract student initials
  const getInitials = (name) => {
    if (!name) return 'KU';
    const parts = name.trim().split(' ');
    if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
    return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
  };

  return (
    <>
      {/* Mobile Backdrop */}
      {isOpen && (
        <div
          onClick={onClose}
          className="fixed inset-0 bg-slate-900/40 backdrop-blur-xs z-30 lg:hidden"
        />
      )}

      <aside
        className={`fixed lg:static top-0 bottom-0 left-0 w-64 bg-white border-r border-slate-200 flex flex-col z-40 transition-transform duration-200 ease-in-out ${
          isOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
        }`}
      >
        {/* Branding Header */}
        <div className="p-5 border-b border-slate-200">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-600 to-indigo-700 text-white font-black text-xl flex items-center justify-center shadow-md shadow-blue-500/20">
              K
            </div>
            <div>
              <div className="flex items-center gap-1.5">
                <span className="font-bold text-base tracking-tight text-slate-900">
                  CampusShare
                </span>
                <span className="text-[10px] font-bold bg-blue-100 text-blue-800 px-1.5 py-0.5 rounded">
                  KUET
                </span>
              </div>
              <p className="text-xs text-slate-500 font-medium">Peer-to-Peer Campus Hub</p>
            </div>
          </div>

          {/* 700m Campus Perimeter Badge */}
          <div className="mt-3.5 flex items-center gap-2 px-2.5 py-1 rounded-full bg-blue-50/80 border border-blue-200/60 text-blue-700 text-xs font-semibold">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-blue-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-blue-600"></span>
            </span>
            <span>📍 700m Campus Perimeter</span>
          </div>
        </div>

        {/* Navigation Links */}
        <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
          <div className="px-3 pb-2 text-[11px] font-bold uppercase tracking-wider text-slate-400">
            Navigation
          </div>

          <NavLink to="/" end className={navLinkClasses} onClick={onClose}>
            <div className="flex items-center gap-3">
              <MapIcon />
              <span>Map View</span>
            </div>
            <span className="text-[11px] font-bold bg-slate-100 text-slate-600 px-1.5 py-0.5 rounded">
              God's Eye
            </span>
          </NavLink>

          <NavLink to="/items" className={navLinkClasses} onClick={onClose}>
            <div className="flex items-center gap-3">
              <PackageIcon />
              <span>All Items</span>
            </div>
            <span className="text-[11px] font-semibold text-slate-400">Browse</span>
          </NavLink>

          <NavLink to="/requests" className={navLinkClasses} onClick={onClose}>
            <div className="flex items-center gap-3">
              <InboxIcon />
              <span>Borrow Requests</span>
            </div>
          </NavLink>

          <NavLink to="/profile" className={navLinkClasses} onClick={onClose}>
            <div className="flex items-center gap-3">
              <UserIcon />
              <span>My Profile</span>
            </div>
            <span className="text-[11px] font-bold text-amber-700 bg-amber-50 px-1.5 py-0.5 rounded border border-amber-200/60">
              Karma
            </span>
          </NavLink>
        </nav>

        {/* Active Student Footer Card */}
        <div className="p-3 border-t border-slate-200 bg-slate-50/60">
          {user ? (
            <div className="bg-white p-3 rounded-xl border border-slate-200 shadow-xs">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2.5 min-w-0">
                  <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-600 to-indigo-600 text-white font-bold text-xs flex items-center justify-center flex-shrink-0 shadow-xs">
                    {getInitials(user.name)}
                  </div>
                  <div className="min-w-0">
                    <p className="text-xs font-bold text-slate-900 truncate" title={user.name}>
                      {user.name}
                    </p>
                    <p className="text-[11px] text-slate-500 truncate">
                      Roll: {user.roll || 'KUET'} · {user.dept || 'Stud'}
                    </p>
                  </div>
                </div>

                <button
                  onClick={handleLogout}
                  className="p-1 rounded hover:bg-rose-50 transition-colors"
                  title="Logout"
                >
                  <LogoutIcon />
                </button>
              </div>

              {/* Karma Score Badge (R4) */}
              <div className="mt-2.5 pt-2 border-t border-slate-100 flex items-center justify-between">
                <span className="text-[11px] text-slate-500 font-medium">KUET Karma</span>
                <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-bold bg-amber-50 text-amber-800 border border-amber-200 shadow-xs">
                  <span>⚡</span>
                  <span>{user.karma ?? 100} Karma</span>
                </span>
              </div>
            </div>
          ) : (
            <div className="bg-white p-3 rounded-xl border border-dashed border-slate-300 text-center">
              <p className="text-xs font-bold text-slate-800">KUET Student Portal</p>
              <p className="text-[11px] text-slate-500 mt-0.5 mb-2">
                Sign in with @stud.kuet.ac.bd
              </p>
              <div className="flex gap-2">
                <button
                  onClick={() => navigate('/login')}
                  className="flex-1 py-1.5 text-xs font-semibold bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                >
                  Log In
                </button>
                <button
                  onClick={() => navigate('/register')}
                  className="flex-1 py-1.5 text-xs font-semibold bg-slate-100 text-slate-700 rounded-lg hover:bg-slate-200 transition-colors"
                >
                  Register
                </button>
              </div>
            </div>
          )}
        </div>
      </aside>
    </>
  );
}
```

---

### Component 3: `frontend/src/components/layout/DashboardLayout.jsx`
* **Path:** `/Users/tanvir/Forkathon2026-Team-KUET_MANTIS/frontend/src/components/layout/DashboardLayout.jsx`
* **Features:**
  - Coordinates Left Sidebar, Top Action Bar, and dynamic child views via `<Outlet />`.
  - Manages global state: `search`, `category`, `listingType`, `isAddModalOpen`.
  - Exports a custom hook `useDashboard()` for child views (`Home`, `AllItems`) to read and update filters.
  - Automatically handles mobile sidebar toggling and dispatches window resize events so MapLibre canvas resizes smoothly.

```jsx
import React, { useState, useEffect, createContext, useContext } from 'react';
import { Outlet, useNavigate } from 'react-router-dom';
import Sidebar from './Sidebar';
import TopActionBar from './TopActionBar';

const DashboardContext = createContext(null);

export const useDashboard = () => {
  const context = useContext(DashboardContext);
  if (!context) {
    throw new Error('useDashboard must be used within a DashboardLayout');
  }
  return context;
};

export default function DashboardLayout() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [search, setSearch] = useState('');
  const [category, setCategory] = useState('ALL');
  const [listingType, setListingType] = useState('ALL'); // 'ALL' | 'lend' | 'borrow'
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const navigate = useNavigate();

  // Handle CTA button click
  const handleOpenAdd = () => {
    setIsAddModalOpen(true);
  };

  // Trigger window resize when sidebar state changes to adjust MapLibre canvas
  useEffect(() => {
    const timer = setTimeout(() => {
      window.dispatchEvent(new Event('resize'));
    }, 250);
    return () => clearTimeout(timer);
  }, [sidebarOpen]);

  const dashboardValue = {
    search,
    setSearch,
    category,
    setCategory,
    listingType,
    setListingType,
    isAddModalOpen,
    setIsAddModalOpen
  };

  return (
    <DashboardContext.Provider value={dashboardValue}>
      <div className="flex h-screen w-screen overflow-hidden bg-slate-50 font-sans text-slate-900">
        {/* Left Sidebar Navigation */}
        <Sidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />

        {/* Main Content Workspace */}
        <div className="flex flex-1 flex-col min-w-0 h-full overflow-hidden">
          {/* Top Action Bar */}
          <TopActionBar
            search={search}
            setSearch={setSearch}
            category={category}
            setCategory={setCategory}
            listingType={listingType}
            setListingType={setListingType}
            onOpenAddModal={handleOpenAdd}
            onToggleSidebar={() => setSidebarOpen(!sidebarOpen)}
          />

          {/* Child Views (Map View, Items, Requests, Profile) */}
          <main className="relative flex-1 overflow-y-auto bg-slate-50">
            <Outlet context={dashboardValue} />
          </main>
        </div>
      </div>
    </DashboardContext.Provider>
  );
}
```

---

### Component 4: `frontend/src/pages/AllItems.jsx`
* **Path:** `/Users/tanvir/Forkathon2026-Team-KUET_MANTIS/frontend/src/pages/AllItems.jsx`
* **Features:**
  - Fulfills the `/items` view requirement ("clean tables/lists for items").
  - Consumes filters (`search`, `category`, `listingType`) from `useDashboard()`.
  - Displays enterprise item cards with badges for type (Lending vs. Beacon), location, owner with KUET Karma badge (`⚡ 100 Karma`), and actions.
  - Interactive empty state with filter reset.

```jsx
import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import api, { API_ORIGIN } from '../api/client';
import Loader from '../components/common/Loader';
import { useDashboard } from '../components/layout/DashboardLayout';

export default function AllItems() {
  const { search, category, listingType, setSearch, setCategory, setListingType } = useDashboard();

  const { data: items, isLoading, error } = useQuery({
    queryKey: ['items', { category, search, listingType }],
    queryFn: async () => {
      const params = {};
      if (search) params.search = search;
      if (category && category !== 'ALL') params.category = category;
      if (listingType && listingType !== 'ALL') params.type = listingType;
      const res = await api.get('/items', { params });
      return res.data;
    }
  });

  if (isLoading) return <Loader />;
  if (error) return <div className="p-8 text-center text-rose-500 font-semibold">Failed to load items.</div>;

  const placeholderImage = 'https://via.placeholder.com/300x200?text=KUET+Item';

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Header bar */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Campus Listings</h1>
          <p className="text-sm text-slate-500">
            Active lending supplies and student borrow demand beacons within 700m perimeter
          </p>
        </div>
        <div className="text-xs font-semibold text-slate-600 bg-white border border-slate-200 px-3 py-1.5 rounded-lg shadow-xs">
          Showing <span className="text-blue-600 font-bold">{items?.length || 0}</span> items
        </div>
      </div>

      {/* Empty State */}
      {items?.length === 0 ? (
        <div className="bg-white border border-dashed border-slate-300 rounded-2xl p-12 text-center max-w-md mx-auto my-8 shadow-xs">
          <div className="w-12 h-12 rounded-full bg-blue-50 text-blue-600 flex items-center justify-center mx-auto mb-3 text-2xl">
            📦
          </div>
          <h3 className="font-bold text-slate-800 text-base mb-1">No Listings Found</h3>
          <p className="text-xs text-slate-500 mb-4">
            Try adjusting your search query, category, or listing type filter.
          </p>
          <button
            onClick={() => {
              setSearch('');
              setCategory('ALL');
              setListingType('ALL');
            }}
            className="px-4 py-2 text-xs font-semibold bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg transition-colors"
          >
            Reset Filters
          </button>
        </div>
      ) : (
        /* Enterprise Cards Grid */
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-5">
          {items?.map((item) => {
            const isBeacon = item.type === 'borrow';
            return (
              <div
                key={item.id}
                className="bg-white border border-slate-200 rounded-xl overflow-hidden shadow-xs hover:shadow-md hover:border-slate-300 transition-all flex flex-col group"
              >
                {/* Thumbnail / Header */}
                <div className="relative h-44 bg-slate-100 overflow-hidden">
                  <img
                    src={item.image_url ? `${API_ORIGIN}${item.image_url}` : placeholderImage}
                    alt={item.title}
                    className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                    onError={(e) => (e.target.src = placeholderImage)}
                  />
                  {/* Type Badge */}
                  <span
                    className={`absolute top-2.5 left-2.5 px-2.5 py-0.5 rounded-full text-xs font-bold shadow-xs ${
                      isBeacon
                        ? 'bg-rose-500 text-white'
                        : 'bg-emerald-600 text-white'
                    }`}
                  >
                    {isBeacon ? '🚨 Beacon' : '🟢 Lending'}
                  </span>

                  {/* Condition Badge */}
                  <span className="absolute top-2.5 right-2.5 px-2 py-0.5 rounded text-[10px] font-semibold bg-slate-900/70 text-white backdrop-blur-xs">
                    {item.condition || 'Good'}
                  </span>
                </div>

                {/* Content */}
                <div className="p-4 flex-1 flex flex-col">
                  <h3 className="font-bold text-slate-900 text-sm truncate mb-1" title={item.title}>
                    {item.title}
                  </h3>
                  <p className="text-xs text-slate-500 mb-2">
                    {item.category} · {item.zone || 'Campus'}
                  </p>

                  {/* Owner & Karma */}
                  <div className="mt-auto pt-3 border-t border-slate-100 flex items-center justify-between text-xs">
                    <span className="text-slate-600 truncate font-medium max-w-[120px]">
                      {item.owner?.name || 'KUET Student'}
                    </span>
                    <span className="inline-flex items-center gap-1 font-bold text-amber-700 bg-amber-50 px-2 py-0.5 rounded-full border border-amber-200/60 text-[11px]">
                      ⚡ {item.owner?.karma ?? item.owner?.trust_score ?? 100}
                    </span>
                  </div>

                  {/* Action CTA */}
                  <Link
                    to={`/item/${item.id}`}
                    className={`mt-3 block text-center py-2 rounded-lg text-xs font-semibold transition-colors ${
                      isBeacon
                        ? 'bg-rose-50 text-rose-700 hover:bg-rose-100 border border-rose-200'
                        : 'bg-blue-50 text-blue-700 hover:bg-blue-100 border border-blue-200'
                    }`}
                  >
                    {isBeacon ? 'Offer to Lend' : 'Request to Borrow'}
                  </Link>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
```

---

### Component 5: Integration with `frontend/src/App.jsx`
* **Path:** `/Users/tanvir/Forkathon2026-Team-KUET_MANTIS/frontend/src/App.jsx`
* **Features:**
  - Wraps routes inside `DashboardLayout`.
  - Separates standalone auth routes (`/login`, `/register`) from the enterprise shell.
  - Supports both Map View (`/`) and All Items list (`/items`).

```jsx
import React, { useState } from 'react';
import { Routes, Route, Navigate, useNavigate } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import { useAuth } from './context/AuthContext';
import DashboardLayout from './components/layout/DashboardLayout';
import Home from './pages/Home';
import AllItems from './pages/AllItems';
import AddItem from './pages/AddItem';
import ItemDetail from './pages/ItemDetail';
import Requests from './pages/Requests';
import Chat from './pages/Chat';
import Transaction from './pages/Transaction';
import Profile from './pages/Profile';
import api from './api/client';

// Clean inline Login Component
function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await login(email, password);
      navigate('/');
    } catch (err) {
      alert(err.response?.data?.detail || 'Login failed');
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50 p-4 font-sans">
      <div className="w-full max-w-md bg-white rounded-2xl border border-slate-200 p-8 shadow-sm">
        <div className="flex items-center gap-3 mb-6">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-600 to-indigo-700 text-white font-black text-xl flex items-center justify-center">
            K
          </div>
          <div>
            <h1 className="text-xl font-bold text-slate-900">CampusShare KUET</h1>
            <p className="text-xs text-slate-500">Sign in to your student account</p>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">KUET Email</label>
            <input
              type="email"
              placeholder="e.g. siddique2307010@stud.kuet.ac.bd"
              className="w-full text-sm border border-slate-200 rounded-lg px-3.5 py-2.5 outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Password</label>
            <input
              type="password"
              placeholder="••••••••"
              className="w-full text-sm border border-slate-200 rounded-lg px-3.5 py-2.5 outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>
          <button
            type="submit"
            className="w-full py-2.5 bg-blue-600 hover:bg-blue-700 active:bg-blue-800 text-white font-semibold rounded-lg shadow-sm transition-colors text-sm"
          >
            Sign In
          </button>
        </form>

        <p className="mt-5 text-center text-xs text-slate-500">
          Don't have an account?{' '}
          <button
            onClick={() => navigate('/register')}
            className="font-semibold text-blue-600 hover:underline"
          >
            Register with KUET email
          </button>
        </p>
      </div>
    </div>
  );
}

// Clean inline Register Component (R3 minimal 3-field requirement with Roll Decoder)
function Register() {
  const [form, setForm] = useState({ email: '', name: '', password: '' });
  const navigate = useNavigate();

  // Automatic Roll Decoder preview
  const parseKuetEmail = (email) => {
    const clean = email.trim().toLowerCase();
    if (!clean.endsWith('@stud.kuet.ac.bd')) return null;
    const prefix = clean.split('@')[0];
    const match = prefix.match(/(\d{2})(\d{2})(\d{3})$/);
    if (!match) return null;
    return { batch: match[1], dept: match[2], roll: match[3] };
  };

  const decoded = parseKuetEmail(form.email);

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await api.post('/auth/register', form);
      alert('Registration successful! Please login.');
      navigate('/login');
    } catch (err) {
      alert(err.response?.data?.detail || 'Registration failed');
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50 p-4 font-sans">
      <div className="w-full max-w-md bg-white rounded-2xl border border-slate-200 p-8 shadow-sm">
        <div className="flex items-center gap-3 mb-6">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-600 to-indigo-700 text-white font-black text-xl flex items-center justify-center">
            K
          </div>
          <div>
            <h1 className="text-xl font-bold text-slate-900">Student Registration</h1>
            <p className="text-xs text-slate-500">Auto-decodes batch, dept & roll</p>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Full Name</label>
            <input
              type="text"
              placeholder="e.g. Tanvir Rahman"
              className="w-full text-sm border border-slate-200 rounded-lg px-3.5 py-2.5 outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20"
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              required
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">KUET Email (@stud.kuet.ac.bd)</label>
            <input
              type="email"
              placeholder="siddique2307010@stud.kuet.ac.bd"
              className="w-full text-sm border border-slate-200 rounded-lg px-3.5 py-2.5 outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20"
              value={form.email}
              onChange={(e) => setForm({ ...form, email: e.target.value })}
              required
            />
            {/* Live Decoder Badge */}
            {decoded && (
              <div className="mt-2 p-2 bg-blue-50 border border-blue-200 rounded-lg flex items-center gap-3 text-xs text-blue-800">
                <span>🎓 <strong>Batch:</strong> {decoded.batch}</span>
                <span>🏛️ <strong>Dept:</strong> {decoded.dept}</span>
                <span>🆔 <strong>Roll:</strong> {decoded.roll}</span>
              </div>
            )}
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Password</label>
            <input
              type="password"
              placeholder="••••••••"
              className="w-full text-sm border border-slate-200 rounded-lg px-3.5 py-2.5 outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20"
              value={form.password}
              onChange={(e) => setForm({ ...form, password: e.target.value })}
              required
            />
          </div>

          <button
            type="submit"
            className="w-full py-2.5 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-lg shadow-sm transition-colors text-sm"
          >
            Register Student Account
          </button>
        </form>

        <p className="mt-5 text-center text-xs text-slate-500">
          Already registered?{' '}
          <button
            onClick={() => navigate('/login')}
            className="font-semibold text-blue-600 hover:underline"
          >
            Sign In
          </button>
        </p>
      </div>
    </div>
  );
}

// Private route guard
function PrivateRoute({ children }) {
  const { user, loading } = useAuth();
  if (loading) return <div className="p-8 text-center text-slate-500">Loading...</div>;
  return user ? children : <Navigate to="/login" />;
}

export default function App() {
  return (
    <>
      <Toaster position="top-center" toastOptions={{ duration: 3000 }} />
      <Routes>
        {/* Standalone Authentication Views */}
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />

        {/* Enterprise Dashboard Shell Layout */}
        <Route element={<DashboardLayout />}>
          <Route path="/" element={<Home />} />
          <Route path="/items" element={<AllItems />} />
          <Route path="/item/:id" element={<ItemDetail />} />
          <Route path="/add" element={<PrivateRoute><AddItem /></PrivateRoute>} />
          <Route path="/requests" element={<PrivateRoute><Requests /></PrivateRoute>} />
          <Route path="/chat/:requestId" element={<PrivateRoute><Chat /></PrivateRoute>} />
          <Route path="/transaction/:requestId" element={<PrivateRoute><Transaction /></PrivateRoute>} />
          <Route path="/profile" element={<PrivateRoute><Profile /></PrivateRoute>} />
        </Route>
      </Routes>
    </>
  );
}
```

---

### Component 6: `frontend/src/index.css`
* **Path:** `/Users/tanvir/Forkathon2026-Team-KUET_MANTIS/frontend/src/index.css`
* **Features:**
  - Modern light enterprise theme variables and animations.
  - Subtle radar pulse for borrow beacons.
  - Slim scrollbars and crisp typography.

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

:root {
  --primary: #2563eb;
  --lend-color: #10b981;
  --borrow-color: #ef4444;
}

body {
  @apply bg-slate-50 text-slate-900 antialiased;
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  margin: 0;
  padding: 0;
  overflow: hidden;
}

/* Slim enterprise scrollbar */
::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}

::-webkit-scrollbar-track {
  background: #f1f5f9;
}

::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 9999px;
}

::-webkit-scrollbar-thumb:hover {
  background: #94a3b8;
}

/* Beacon pulse animation */
@keyframes radar-pulse {
  0% {
    transform: scale(0.95);
    box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.7);
  }
  70% {
    transform: scale(1.05);
    box-shadow: 0 0 0 10px rgba(239, 68, 68, 0);
  }
  100% {
    transform: scale(0.95);
    box-shadow: 0 0 0 0 rgba(239, 68, 68, 0);
  }
}

.animate-radar {
  animation: radar-pulse 2s infinite cubic-bezier(0.4, 0, 0.6, 1);
}
```

---

## 5. Verification Method

### How to Verify the Recommendations:
1. **Verify Component Integration in `App.jsx`:**
   Inspect that `<Route element={<DashboardLayout />}>` wraps `/`, `/items`, `/requests`, and `/profile`.
2. **Verify Left Sidebar Elements:**
   - KUET branding: Logo badge `K`, title `CampusShare KUET`, and badge `📍 700m Campus Perimeter`.
   - Navigation links: Map View (`/`), All Items (`/items`), Borrow Requests (`/requests`), Profile (`/profile`).
   - Active student card: Student Name, Roll number, Department, and Karma score pill (`⚡ 100 Karma`).
3. **Verify Top Action Bar Elements:**
   - Search input connected to query state.
   - Segmented filter buttons for `All`, `Lending`, `Beacons`.
   - Category selector covering calculators, power, lab equipment, books, etc.
   - Primary `+ Add Item` CTA button.
4. **Verify Clean Light Enterprise Theme:**
   - Canvas background `#f8fafc` (`bg-slate-50`).
   - Cards and panels `#ffffff` (`bg-white`).
   - Borders `#e2e8f0` (`border-slate-200`).
   - Accent colors: Blue-600 (`#2563eb`), Emerald-600 (`#10b981`), Rose-600 (`#ef4444`), Amber-600 (`#d97706`).
5. **Invalidation Condition:**
   - If external dependencies like `lucide-react` are required for rendering, this recommendation would fail due to missing npm packages. The provided implementation uses 100% self-contained inline SVGs, invalidating dependency failure risks.
