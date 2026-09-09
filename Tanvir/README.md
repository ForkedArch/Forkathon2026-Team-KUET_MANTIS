# KUET CampusShare // Borrow & Lend Location Log

**Forkathon: Freshers Hackathon 2026** — Team KUET_MANTIS  
**Component Author:** Tanvir  
**Deliverables:**
1. 📍 **The Location Engine** (Real map covering 500m radius of KUET).
2. 📝 **Item Log Setup** (Manual entry modal and backend item tracking).

---

## 📁 Folder Structure

```
Tanvir/
├── index.html                  # 🌟 MAIN FRONTEND (MapLibre + Real-World KUET Map)
├── app.py                      # Threaded Python HTTP Server & REST API
├── kuet_data/
│   └── kuet_landmarks.json     # Optional reference data
└── README.md
```

---

## 🚀 How to Run

1. Open your terminal in this folder and start the backend log server:
   ```bash
   python3 app.py 8000
   ```
2. Open your browser and navigate to:
   **[http://127.0.0.1:8000](http://127.0.0.1:8000)**

---

## 🛠️ Features & Workflow

This module provides the complete **KUET Campus Lending & Borrowing Map Interface**:

1. **Complete & Accurate KUET Campus Map**:
   - Centered at KUET (`22.9006° N, 89.5024° E`).
   - Visual boundary ring explicitly covering a **700m radius** centered on KUET.
   - Comprehensive landmarks: Academic complexes (CSE, EEE, ME, Civil), 7 Residential Halls (Amar Ekushey, Fazlul Haque, Lalan Shah, Khan Jahan Ali, Rashid, Rokeya, Bangabandhu), Central Library, Student Cafeteria, and Gates.
2. **Visual User & Demand Representation**:
   - Simulated realistic KUET student users (departments, batches, trust ratings 4.7 - 4.95 / 5.0, verified badges).
   - Distinct visual representations for "Willing to Lend" (emerald glow pins) vs. "Need to Borrow" (pulsing radar demand beacons).
   - Rich interactive cards on markers with user profile, specifications, condition, and exchange action buttons.
3. **Interactive Manual Item Addition & Pinpointing**:
   - "+ Add Item" modal with listing type switcher, category, condition, photo upload with live preview.
   - Interactive pinpoint mode converting campus map clicks to exact lat/lng coordinates with draggable pin confirmation.
   - Newly added items immediately appear on map and live sidebar feed without page reload.
4. **Automated Verification**:
   - Run the comprehensive automated verification suite:
     ```bash
     python3 verify_campus_map.py
     ```

