<img src="https://i.ibb.co.com/7NrtB6Vv/image.png" alt="Forkathon 2026 Banner" />

# Forkathon 2026: [CampusShare KUET] by [KUET_MANTIS]

> Built for ForkedArch Freshers Hackathon 2026  
> 🌐 **Live Production Application:** [https://forkathon2026-team-kuet-mantis-3.onrender.com](https://forkathon2026-team-kuet-mantis-3.onrender.com)  
> ⚡ **Live API Documentation:** [https://forkathon2026-team-kuet-mantis-2.onrender.com/docs](https://forkathon2026-team-kuet-mantis-2.onrender.com/docs)

[![Live Demo](https://img.shields.io/badge/Render-Live%20Demo-brightgreen?logo=render)](https://forkathon2026-team-kuet-mantis-3.onrender.com)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)](https://python.org)
[![React](https://img.shields.io/badge/React-18-61DAFB?logo=react&logoColor=black)](https://react.dev)
[![Vite](https://img.shields.io/badge/Vite-5.4-646CFF?logo=vite&logoColor=white)](https://vitejs.dev)
[![TailwindCSS](https://img.shields.io/badge/TailwindCSS-3.4-38B2AC?logo=tailwind-css&logoColor=white)](https://tailwindcss.com)
[![Neon Database](https://img.shields.io/badge/PostgreSQL-Neon%20Serverless-00E599?logo=postgresql&logoColor=white)](https://neon.tech)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](./LICENSE)

---

## 🎥 Video Presentation & Demonstration

> 📺 **Official Project Presentation Video:**  
> ### [▶️ Click to Watch Our Video Presentation on YouTube / Google Drive](https://youtu.be/eO9GICwQhOo)
>
> *(Note for Evaluators: Click the link above to watch our team walkthrough demonstrating problem validation, God's Eye Map discovery, instant Messages, and the OTP-verified borrow/return lifecycle).*


## 👥 Team :

| Name | Roll | Department | GitHub |
| :--- | :--- | :--- | :--- |
| **Anupoma Sharmin Anonya** | 2K2507009 | CSE | [@anonya25-1](https://github.com/anonya25-1) |
| **Mugdha Sarkar Anik** | 2K2507030 | CSE | [@mugdha-sarkar81](https://github.com/mugdha-sarkar81) |
| **Tanvir Siddique** | 2K2507028 | CSE | [@siddiquetanvir](https://github.com/siddiquetanvir) |

---

## ❓ Problem

### Problem Statement :

> #### **The Borrowed Charger**
>
> It starts with a simple question:  
> *"Does anyone have a charger?"*  
>
> Someone has one. Someone else has a calculator. Another student has an HDMI cable. Someone has a lab component sitting unused in their bag.  
>
> The problem is that nobody knows who has what.  
>
> So people buy things they only need once, while perfectly useful items sit unused a few rooms away.  
>
> Maybe create a simple system that helps students lend, borrow, and find useful items within their community.  
>
> **Users could:**  
> - Add items they are willing to lend.  
> - Search for an item they need.  
> - Request to borrow an item.  
> - See whether an item is currently available.  
> - Keep track of borrowed and returned items.  
>
> Items could be anything from calculators and books to chargers, cables, lab equipment, or sports gear.  
>
> **Brainstorming twist:** *How can you make borrowing something from another student feel simple, safe, and organized?*

---

### 🤔 [KUET_MANTIS]'s Understanding :

#### **The Main Issue:**
Across university campuses—and particularly in an intensive technical environment like KUET—students frequently encounter urgent, high-stakes supply shortages. Whether it is an approved scientific calculator an hour before a semester exam, a 65W USB-C charger when a battery is critically dying in the Central Computer Centre, an HDMI dongle for a project presentation, or expensive civil drafting drafters and mechanical tools needed for only a single sessional. 

Because students have no structured way to discover who owns what nearby, they are forced to either buy expensive single-use equipment or spam large Messenger/WhatsApp batch groups where urgent cries for help get lost in noise. Meanwhile, perfectly working items sit dormant inside dormitory rooms just 50 meters away.

#### **Experience:**
As 1st-year CSE students residing and studying at KUET, our team (Tanvir, Anik, and Anupoma) has directly experienced this frustration:
- **Tanvir** was once working on a critical sessional project at the Central Library when his laptop charger failed, leaving him scrambling across halls without knowing anyone in nearby rooms who had a compatible Type-C power brick.
- **Anik** had to spend hundreds of takas to purchase specialized drafting tools for engineering drawing that were used for only two laboratory sessions and never touched again.
- **Anupoma** witnessed multiple batchmates panic before midterm exams because their calculators ran out of battery or were missing the required matrix-solving functions approved by examiners.

#### **Our Main Goal:**
Our objective is to transform the KUET campus into a zero-waste, high-trust sharing community. **CampusShare KUET** provides an intuitive, real-time peer-to-peer sharing ecosystem that connects student demand with idle campus resources. By integrating verified academic student credentials, geospatial campus mapping ("God's Eye Map"), direct 1:1 coordination, and a self-governing Karma Protocol with cryptographic OTP verification, we solve the core challenge: **making borrowing feel simple, safe, and organized.**

---

## 💡 Key Features :

### 🙋‍♂️ For Borrowers :
- **God's Eye Campus Map:** Explore items across the entire 700m KUET campus perimeter using an interactive MapLibre GL radar map.
- **Demand Beacons (Urgent Broadcasts):** Can't find an available item? Drop a glowing red "Demand Beacon" on the campus map to alert students nearby about what you need immediately.
- **Instant 1:1 Campus Chat:** Initiate communication immediately upon submitting a request (even before owner approval) to establish familiarity, agree on meetup points, or ask questions.
- **Granular Search & Filters:** Search items instantly by keyword, technical specification, department, or categories (Calculators, Chargers, Lab Tools, Books, Cables).
- **Cryptographic OTP Handover:** Zero awkward disputes—verify handovers securely using a dynamic 4-digit OTP or scannable QR code.

### 🤝 For Lenders :
- **Rapid Listing with Pinpoint Mode:** Publish an item in under 30 seconds with photos, specifications, and a precise map drop-pin on campus landmarks (Rokeya Hall, Central Library, ME Building, etc.).
- **Automated Collision Protection:** Accepting a borrow request automatically reserves the item and notifies or declines conflicting pending requests.
- **Reputation & Karma Growth:** Earn **+10 KUET Karma** for every successful lending exchange, increasing your public trust score on campus.
- **Live Inventory Tracking:** Monitor active borrows, handover confirmations, and return deadlines from a clean dashboard.

### 🛡️ Campus Trust & Safety (The Twist) :
- **Strict KUET Email Decoupling:** Registration is exclusively restricted to official `@stud.kuet.ac.bd` emails. The system auto-decodes Batch, Department, and Roll Number (`BB DD RRR`), eliminating fake accounts and impersonation.
- **Self-Regulating Karma Protocol:**
  - **100 Base Karma:** Seeded to every verified KUET student upon registration.
  - **+10 Karma:** Awarded to lenders for completing an exchange.
  - **+5 Karma:** Awarded to borrowers for on-time item returns.
  - **-30 Karma Penalty:** Automatically applied for unreturned or late items.
- **Physical Proof of Handover:** Transactions do not activate until the borrower physically inspects the item and provides the private OTP to the owner.

### ⚙️ Under the Hood :
- **Frontend:** React 18, Vite, Tailwind CSS, MapLibre GL JS, Turf.js, TanStack React Query.
- **Backend:** FastAPI (Python 3.10), SQLAlchemy ORM, Pydantic V2 schemas, Bcrypt password hashing, PyJWT authentication.
- **Database:** Serverless PostgreSQL via **Neon Database** with connection pooling and automated migration scripts.
- **Infrastructure:** Frontend deployed on **Render Static Site CDN**; API hosted on **Render Web Services** with universal CORS support.

---

## 🏗️ Architecture :

### 🏛️ CampusShare KUET — Architecture :

CampusShare KUET is built with a decoupled client-server architecture designed for high availability, zero latency geospatial rendering, and strict campus-level authentication.

#### 1. System Overview :

```text
               ┌─────────────────────────────────────────────────────────┐
               │                 KUET Student Browser                    │
               │   (React 18 + Tailwind CSS + MapLibre GL + React Query) │
               └────────────────────────────┬────────────────────────────┘
                                            │
                                            │ HTTPS / REST (JSON + Multipart)
                                            │ Bearer JWT Auth
                                            ▼
               ┌─────────────────────────────────────────────────────────┐
               │                   FastAPI Backend Server                │
               │              (Render Cloud Platform, Python)            │
               ├─────────────────────────────────────────────────────────┤
               │  • /api/auth       - KUET Email Decoder & JWT Provider   │
               │  • /api/items      - Campus Inventory & Geo-Coordinates  │
               │  • /api/requests   - Borrow Workflow & Lifecycle Engine │
               │  • /api/chat       - 1:1 Direct Messaging & Threads     │
               │  • /api/transact   - OTP / QR Handover Verification      │
               │  • /api/landmarks  - KUET Campus Geographic Anchors      │
               └──────────────┬───────────────────────────┬──────────────┘
                              │                           │
                              ▼                           ▼
               ┌───────────────────────────┐ ┌───────────────────────────┐
               │    Neon PostgreSQL DB     │ │    Local Upload Storage   │
               │ (Users, Items, Requests,  │ │   (Item Inspection Photos │
               │  Messages, Transactions)  │ │      & Campus Media)      │
               └───────────────────────────┘ └───────────────────────────┘
```

---

#### 2. Borrowing & Handover State Machine :

```text
[ Borrower creates Request ]
             │
             ▼
      ( Status: PENDING ) ───► [ 1:1 Chat active for negotiation & familiarity ]
             │
      ┌──────┴──────┐
      ▼             ▼
[ DECLINED ]   [ ACCEPTED ]
                    │
                    ▼
         [ Owner starts Handover ]
                    │
                    ▼ Generates 4-digit OTP & QR Code
         [ In-Person Physical Check ]
                    │
                    ▼ Borrower provides OTP to Owner
         ( Status: BORROWED )
                    │
                    ▼ Borrower returns item
         ( Status: COMPLETED )
                    │
                    ├─► Lender awarded +10 KUET Karma ⚡
                    └─► Borrower awarded +5 KUET Karma ⚡
```

---

#### 3. Data Model (Entity Relationship) :

```text
 ┌────────────────────────┐             ┌────────────────────────┐
 │         USERS          │ 1         * │         ITEMS          │
 ├────────────────────────┼─────────────┼────────────────────────┤
 │ id (PK)                │   owns      │ id (PK)                │
 │ email (UNIQUE)         │             │ owner_id (FK -> Users) │
 │ name                   │             │ title                  │
 │ dept, batch, roll      │             │ type (lend / borrow)   │
 │ hashed_password        │             │ category               │
 │ karma (Default: 100)   │             │ lat, lng, zone_id      │
 │ trust_score            │             │ status (avail/borrowed)│
 └───────────┬────────────┘             └───────────┬────────────┘
             │ 1                                    │ 1
             │                                      │
             │ creates / receives                   │ relates to
             ▼ *                                    ▼ *
 ┌────────────────────────┐             ┌────────────────────────┐
 │    BORROW_REQUESTS     │ 1         1 │      TRANSACTIONS      │
 ├────────────────────────┼─────────────┼────────────────────────┤
 │ id (PK)                │   spawns    │ id (PK)                │
 │ item_id (FK -> Items)  │             │ request_id (FK)        │
 │ borrower_id (FK->Users)│             │ otp (4-digit code)     │
 │ owner_id (FK -> Users) │             │ qr_code                │
 │ duration_hours         │             │ status                 │
 │ status (pending/etc.)  │             │ created_at             │
 └───────────┬────────────┘             └────────────────────────┘
             │ 1
             │ references
             ▼ *
 ┌────────────────────────┐             ┌────────────────────────┐
 │        MESSAGES        │             │     NOTIFICATIONS      │
 ├────────────────────────┤             ├────────────────────────┤
 │ id (PK)                │             │ id (PK)                │
 │ sender_id (FK->Users)  │             │ user_id (FK -> Users)  │
 │ recipient_id (FK->Users│             │ title, message, link   │
 │ request_id (FK, opt)   │             │ is_read (Boolean)      │
 │ content, created_at    │             │ created_at             │
 └────────────────────────┘             └────────────────────────┘
```

---

## 🏆 Hackathon Judging Criteria Alignment :

| Evaluation Pillar | How CampusShare KUET Solves It |
| :--- | :--- |
| **Problem Solving & Relevance** | Directly targets *"The Borrowed Charger"* statement. Solves immediate supply panics (calculators before exams, chargers in labs, drafting tools in sessional) that KUET students face daily. |
| **The Brainstorming Twist** | Solves safety and trust through a 3-pillar protocol: (1) Verified `@stud.kuet.ac.bd` domain gate with auto-decoded Roll/Batch, (2) Self-regulating KUET Karma Protocol (+10 lend, +5 on-time, -30 penalty), and (3) Dynamic 4-digit OTP/QR physical handover verification. |
| **Technical Excellence** | Modern decoupled fullstack architecture: Python FastAPI backend with Pydantic V2 validation, Serverless Neon PostgreSQL database with ACID transactions, and React 18 with MapLibre GL geospatial radar. |
| **User Experience & Polish** | Instant Messages coordination on requests, God's Eye 700m interactive perimeter map with click-to-pin, responsive mobile layout, and zero-setup student onboarding. |
| **Working Production Deployment** | 100% deployed and fully operational: static frontend on Render CDN connected to Render backend and cloud-hosted Neon PostgreSQL. |

---
### Folder Structure

```text
.
├── backend/
│   ├── app/
│   │   ├── data/
│   │   │   └── kuet_landmarks.json
│   │   ├── routes/
│   │   │   ├── auth.py
│   │   │   ├── borrow_requests.py
│   │   │   ├── chat.py
│   │   │   ├── items.py
│   │   │   ├── landmarks.py
│   │   │   ├── notifications.py
│   │   │   ├── reviews.py
│   │   │   └── transactions.py
│   │   ├── utils/
│   │   │   ├── file_upload.py
│   │   │   └── qr_code.py
│   │   ├── auth.py
│   │   ├── database.py
│   │   ├── main.py
│   │   ├── models.py
│   │   ├── schemas.py
│   │   └── seed.py
│   ├── uploads/
│   │   └── .gitkeep
│   ├── .env.example
│   ├── .env.production.example
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── public/
│   │   ├── _redirects
│   │   └── logo.svg
│   ├── src/
│   │   ├── api/
│   │   │   └── client.js
│   │   ├── components/
│   │   │   ├── common/
│   │   │   │   ├── Loader.jsx
│   │   │   │   └── Logo.jsx
│   │   │   ├── items/
│   │   │   │   ├── AddItemModal.jsx
│   │   │   │   ├── ItemCard.jsx
│   │   │   │   └── ItemHoverCard.jsx
│   │   │   ├── layout/
│   │   │   │   ├── DashboardLayout.jsx
│   │   │   │   ├── Sidebar.jsx
│   │   │   │   └── TopActionBar.jsx
│   │   │   ├── map/
│   │   │   │   ├── GodsEyeMap.css
│   │   │   │   ├── GodsEyeMap.jsx
│   │   │   │   └── index.js
│   │   │   └── requests/
│   │   │       └── RequestModal.jsx
│   │   ├── context/
│   │   │   └── AuthContext.jsx
│   │   ├── pages/
│   │   │   ├── AddItem.jsx
│   │   │   ├── AllItems.jsx
│   │   │   ├── Chat.jsx
│   │   │   ├── Home.jsx
│   │   │   ├── ItemDetail.jsx
│   │   │   └── Profile.jsx
│   │   ├── utils/
│   │   ├── App.jsx
│   │   ├── index.css
│   │   └── main.jsx
│   ├── .env.example
│   ├── .env.production.example
│   ├── Dockerfile
│   ├── index.html
│   ├── nginx.conf
│   ├── package.json
│   └── postcss.config.js
├── .gitignore
├── docker-compose.yml
├── LICENSE
├── package.json
├── README.md
├── render.yaml
└── vercel.json




## 🚀 Local Setup & Installation :

### Prerequisites :
- **Python 3.10+**
- **Node.js 18+ & npm**
- **Git**

### 1. Clone the Repository :
```bash
git clone https://github.com/ForkedArch/Forkathon2026-Team-KUET_MANTIS.git
cd Forkathon2026-Team-KUET_MANTIS
```

### 2. Backend Setup (FastAPI) :
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env

# Run FastAPI Development Server
uvicorn app.main:app --reload --port 8000
```
- API Docs: `http://localhost:8000/docs`
- Health Endpoint: `http://localhost:8000/health`

### 3. Frontend Setup (React + Vite) :
```bash
# In another terminal window:
cd frontend
npm install
cp .env.example .env

# Start Vite Development Server
npm run dev
```
- Application: `http://localhost:5173`

---

## 🌐 Production Deployments :

- **Live Frontend App:** [https://forkathon2026-team-kuet-mantis-3.onrender.com](https://forkathon2026-team-kuet-mantis-3.onrender.com)
- **Live Backend API:** [https://forkathon2026-team-kuet-mantis-2.onrender.com](https://forkathon2026-team-kuet-mantis-2.onrender.com)
- **API Health Check:** [https://forkathon2026-team-kuet-mantis-2.onrender.com/health](https://forkathon2026-team-kuet-mantis-2.onrender.com/health)

---

## 📜 License :
This project is open-sourced under the [MIT License](./LICENSE).

---

<div align="center">
  <b>Forkathon: Freshers Hackathon 2026 presented by ForkedArch powered by XtendArena</b>
</div>
