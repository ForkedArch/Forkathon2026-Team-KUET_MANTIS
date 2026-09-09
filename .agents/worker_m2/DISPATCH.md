## 2026-09-10T04:22:42+06:00
You are worker_m2.
Your working directory is: /Users/tanvir/Forkathon2026-Team-KUET_MANTIS/.agents/worker_m2
Your dispatch file is: /Users/tanvir/Forkathon2026-Team-KUET_MANTIS/.agents/worker_m2/DISPATCH.md
MANDATORY: Read /Users/tanvir/Forkathon2026-Team-KUET_MANTIS/ORIGINAL_REQUEST.md before starting work.
Read /Users/tanvir/Forkathon2026-Team-KUET_MANTIS/PROJECT.md.
Read Explorer handoffs:
- /Users/tanvir/Forkathon2026-Team-KUET_MANTIS/.agents/explorer_m2_1/handoff.md
- /Users/tanvir/Forkathon2026-Team-KUET_MANTIS/.agents/explorer_m2_2/handoff.md
- /Users/tanvir/Forkathon2026-Team-KUET_MANTIS/.agents/explorer_m2_3/handoff.md

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Your task:
Implement Milestone 2 (Frontend Dashboard & MapLibre Integration):
1. In frontend/index.html: load MapLibre GL JS v3.6.2 and CSS via CDN tags, Turf.js v6, and Google Fonts.
2. Implement frontend/src/components/layout/Sidebar.jsx (Left sidebar, KUET branding, navigation, student Karma card ⚡ 100 Karma, logout).
3. Implement frontend/src/components/layout/TopActionBar.jsx (Search input, category dropdown, type toggle All/Lending/Beacons, + Add Item button).
4. Implement frontend/src/components/layout/DashboardLayout.jsx (Container coordinating Sidebar, TopActionBar, Outlet, context).
5. Implement frontend/src/components/map/GodsEyeMap.jsx and GodsEyeMap.css (MapLibre canvas, center [89.5024, 22.9006], zoom 16.2, OSM raster tiles, 700m perimeter circle, emerald lend pins, red radar pulsing beacons, click-to-pinpoint mode, HUD controls).
6. Implement frontend/src/components/items/ItemHoverCard.jsx (Popovers showing specs, mini-location, owner karma).
7. Implement frontend/src/components/items/AddItemModal.jsx (Listing type switcher, click-to-pinpoint mode).
8. Implement frontend/src/pages/Home.jsx (Mounts GodsEyeMap and dashboard integration).
9. Implement frontend/src/pages/AllItems.jsx (Clean enterprise cards/table view).
10. Update frontend/src/App.jsx (Wrap routes in DashboardLayout; update Register to accept only Name, Email, Password with live roll decoder badge).
11. Update Profile.jsx, Transaction.jsx, Requests.jsx with Karma displays.
12. Verify frontend JSX syntax and verify against Tanvir/verify_campus_map.py.

Write handoff report to:
/Users/tanvir/Forkathon2026-Team-KUET_MANTIS/.agents/worker_m2/handoff.md
Send a completion message when finished.
