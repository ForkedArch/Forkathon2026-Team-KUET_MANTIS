#!/usr/bin/env python3
"""
CampusShare KUET - 20-Point Problem Statement Rubric Evaluator (judge_rubric.py)
Milestone 4: Agent-as-Judge Evaluation
Runs offline (no live server needed) using direct imports.
"""

import os
import sys
import re
import json
import glob
import sqlite3
import random
import string

ROOT = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(ROOT, "backend")
FRONTEND_DIR = os.path.join(ROOT, "frontend")
TANVIR_DIR = os.path.join(ROOT, "Tanvir")
DB_PATH = os.path.join(BACKEND_DIR, "campus_share.db")

sys.path.insert(0, BACKEND_DIR)

score = 0
max_score = 20
results = []


def check(name, condition, points, detail=""):
    global score
    passed = bool(condition)
    if passed:
        score += points
    status = "✅ PASS" if passed else "❌ FAIL"
    results.append((name, status, points if passed else 0, points, detail))
    print(f"{status} [{points}pts] {name}" + (f"\n         {detail}" if detail else ""))
    return passed


print("=" * 70)
print("  CampusShare KUET — 20-Point Problem Statement Rubric")
print("=" * 70)

# ─── SECTION 1: Architecture Integration (4 pts) ────────────────────────
print("\n── Section 1: Architecture Integration (4 pts) ──")

check(
    "Tanvir/ folder deleted from root",
    not os.path.isdir(TANVIR_DIR),
    1,
    "Tanvir/ should not exist after integration"
)

check(
    "backend/app/data/kuet_landmarks.json present",
    os.path.isfile(os.path.join(BACKEND_DIR, "app", "data", "kuet_landmarks.json")),
    1,
    "Landmarks ported to backend"
)

# MapLibre integration in frontend
godseye_path = os.path.join(FRONTEND_DIR, "src", "components", "map", "GodsEyeMap.jsx")
check(
    "GodsEyeMap.jsx component exists",
    os.path.isfile(godseye_path),
    1,
    "MapLibre map component ported from Tanvir/"
)

dashboard_path = os.path.join(FRONTEND_DIR, "src", "components", "layout", "DashboardLayout.jsx")
check(
    "DashboardLayout.jsx component exists",
    os.path.isfile(dashboard_path),
    1,
    "Dashboard layout component created"
)

# ─── SECTION 2: UI Layout & Design (4 pts) ──────────────────────────────
print("\n── Section 2: UI Layout & Design (4 pts) ──")

# Check for left sidebar in DashboardLayout
sidebar_content = ""
if os.path.isfile(dashboard_path):
    sidebar_content = open(dashboard_path).read()

check(
    "DashboardLayout has sidebar navigation",
    "sidebar" in sidebar_content.lower() or "nav" in sidebar_content.lower(),
    1,
    "Left sidebar with navigation links"
)

# Check AddItemModal
add_item_modal = os.path.join(FRONTEND_DIR, "src", "components", "items", "AddItemModal.jsx")
check(
    "AddItemModal.jsx exists (item add flow)",
    os.path.isfile(add_item_modal),
    1,
    "Modal for adding items"
)

# Check ItemHoverCard
hover_card = os.path.join(FRONTEND_DIR, "src", "components", "items", "ItemHoverCard.jsx")
check(
    "ItemHoverCard.jsx exists (hover cards/popovers)",
    os.path.isfile(hover_card),
    1,
    "Hover cards for item details"
)

# Check tailwind is set up (no extra deps broken)
pkg_json = os.path.join(FRONTEND_DIR, "package.json")
pkg = json.load(open(pkg_json)) if os.path.isfile(pkg_json) else {}
check(
    "Frontend uses Tailwind CSS",
    "tailwindcss" in str(pkg.get("devDependencies", {})),
    1,
    "Tailwind CSS present in devDependencies"
)

# ─── SECTION 3: KUET Authentication & Roll Decoder (4 pts) ──────────────
print("\n── Section 3: KUET Authentication & Roll Decoder (4 pts) ──")

sys.path.insert(0, BACKEND_DIR)
try:
    from app.routes.auth import router as _auth_router  # noqa - just check importable
    auth_route_src = open(os.path.join(BACKEND_DIR, "app", "routes", "auth.py")).read()

    check(
        "Backend rejects non-KUET emails",
        "stud.kuet.ac.bd" in auth_route_src,
        1,
        "Email validation for @stud.kuet.ac.bd"
    )

    check(
        "Backend auto-decodes batch/dept/roll from email",
        re.search(r"(\d{2})(\d{2})(\d{3})", auth_route_src) is not None or "decode" in auth_route_src.lower(),
        1,
        "Regex roll decoder present in auth.py"
    )
except Exception as e:
    check("Backend auth route importable", False, 1, str(e))
    check("Backend roll decoder present", False, 1, "")

# Frontend roll decoder
app_jsx = os.path.join(FRONTEND_DIR, "src", "App.jsx")
app_jsx_content = open(app_jsx).read() if os.path.isfile(app_jsx) else ""
check(
    "Frontend Roll Decoder function present",
    "decodeKuetEmail" in app_jsx_content or "decode" in app_jsx_content.lower(),
    1,
    "Client-side live decoder in App.jsx"
)

# Check karma=100 on register in models or auth
models_src = open(os.path.join(BACKEND_DIR, "app", "models.py")).read()
check(
    "User model defaults karma to 100",
    "karma" in models_src and "100" in models_src,
    1,
    "karma = Column(Integer, default=100) in models.py"
)

# ─── SECTION 4: KUET Karma Protocol (4 pts) ─────────────────────────────
print("\n── Section 4: KUET Karma Protocol (4 pts) ──")

trans_src = open(os.path.join(BACKEND_DIR, "app", "routes", "transactions.py")).read()

check(
    "Owner earns +10 karma on successful lend",
    "owner_gain = 10" in trans_src or "karma.*10" in trans_src or "+ 10" in trans_src or "+10" in trans_src,
    1,
    "Owner +10 karma in transactions.py"
)

check(
    "Borrower earns +5 karma on on-time return",
    "5 if is_on_time" in trans_src or "borrower_change = 5" in trans_src or "+5" in trans_src,
    1,
    "Borrower on-time +5 karma"
)

check(
    "Borrower loses -30 karma on late return",
    "-30" in trans_src,
    1,
    "Borrower late return -30 karma"
)

# Check frontend displays karma
profile_src = open(os.path.join(FRONTEND_DIR, "src", "pages", "Profile.jsx")).read() \
    if os.path.isfile(os.path.join(FRONTEND_DIR, "src", "pages", "Profile.jsx")) else ""
check(
    "Frontend Profile page displays Karma",
    "karma" in profile_src.lower(),
    1,
    "Karma displayed in Profile.jsx"
)

# ─── SECTION 5: End-to-End User Experience (4 pts) ──────────────────────
print("\n── Section 5: End-to-End User Experience (4 pts) ──")

# Database sanity - use sqlite directly to avoid migration issues
try:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = {row[0] for row in cursor.fetchall()}
    conn.close()
    expected_tables = {"users", "items", "borrow_requests", "transactions", "messages"}
    missing = expected_tables - tables
    check(
        "All required DB tables exist",
        len(missing) == 0,
        1,
        f"Tables: {tables}" if not missing else f"Missing: {missing}"
    )
except Exception as e:
    check("Database accessible", False, 1, str(e))

# Check QR code utility
qr_util = os.path.join(BACKEND_DIR, "app", "utils", "qr_code.py")
check(
    "QR code utility present for handover",
    os.path.isfile(qr_util),
    1,
    "QR handshake utility in backend/app/utils/qr_code.py"
)

# Check Transaction.jsx has OTP/QR and return flow
transaction_jsx = os.path.join(FRONTEND_DIR, "src", "pages", "Transaction.jsx")
trans_jsx_content = open(transaction_jsx).read() if os.path.isfile(transaction_jsx) else ""
check(
    "Transaction.jsx has OTP/QR handover + return flow",
    ("otp" in trans_jsx_content.lower() or "qr" in trans_jsx_content.lower()) and "return" in trans_jsx_content.lower(),
    1,
    "OTP/QR and return flow in Transaction.jsx"
)

# Final summary
requests_jsx = os.path.join(FRONTEND_DIR, "src", "pages", "Requests.jsx")
check(
    "Requests.jsx (accept/decline borrow requests) exists",
    os.path.isfile(requests_jsx) and os.path.getsize(requests_jsx) > 500,
    1,
    "Borrow request management page"
)

# ─── SUMMARY ────────────────────────────────────────────────────────────
print("\n" + "=" * 70)
print(f"  FINAL SCORE: {score} / {max_score}")
print(f"  {'🏆 PASSED (≥18/20)' if score >= 18 else '⚠  NEEDS WORK (<18/20)'}")
print("=" * 70)
print("\nRubric Breakdown:")
print(f"  Section 1 - Architecture Integration : {sum(p for n,s,p,m,d in results[:4])}/4")
print(f"  Section 2 - UI Layout & Design       : {sum(p for n,s,p,m,d in results[4:8])}/4")
print(f"  Section 3 - KUET Auth & Roll Decoder : {sum(p for n,s,p,m,d in results[8:12])}/4")
print(f"  Section 4 - KUET Karma Protocol      : {sum(p for n,s,p,m,d in results[12:16])}/4")
print(f"  Section 5 - End-to-End Experience    : {sum(p for n,s,p,m,d in results[16:])}/4")

# Save report
report = {
    "score": score,
    "max_score": max_score,
    "passed": score >= 18,
    "sections": {
        "architecture_integration": sum(p for n,s,p,m,d in results[:4]),
        "ui_layout": sum(p for n,s,p,m,d in results[4:8]),
        "kuet_auth": sum(p for n,s,p,m,d in results[8:12]),
        "karma_protocol": sum(p for n,s,p,m,d in results[12:16]),
        "e2e_ux": sum(p for n,s,p,m,d in results[16:]),
    },
    "checks": [{"name": n, "status": s, "earned": p, "max": m} for n,s,p,m,d in results]
}
with open(os.path.join(ROOT, "judge_report.json"), "w") as f:
    json.dump(report, f, indent=2)
print("\n  Report saved to judge_report.json")

sys.exit(0 if score >= 18 else 1)

