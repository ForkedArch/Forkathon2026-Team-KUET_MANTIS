# CampusShare KUET — Production Deployment Guide

This guide provides step-by-step instructions for deploying the **CampusShare KUET** backend and website into production.

---

## Architecture Overview

* **Backend:** FastAPI (Python 3.10) with SQLite database and persistent uploads storage.
* **Frontend:** React 18 SPA (Vite + Tailwind CSS), served via Nginx or static CDN with SPA routing rewrites.
* **Android:** Hybrid mobile app (Capacitor) consuming the same backend API.

---

## Deployment Options

### Option A: 1-Command Docker Compose (VPS / Server)
*Recommended for VPS hosting (DigitalOcean, Hetzner, Linode, AWS EC2, Ubuntu server).*

1. **Clone the repository on your server:**
   ```bash
   git clone https://github.com/ForkedArch/Forkathon2026-Team-KUET_MANTIS.git campus-share
   cd campus-share
   ```

2. **Generate a secure secret key:**
   ```bash
   python3 -c "import secrets; print(secrets.token_hex(32))"
   ```

3. **Configure environment variables:**
   Create a `.env` file in the project root or export variables:
   ```dotenv
   SECRET_KEY=your_generated_64_char_secret_key
   ALLOWED_ORIGINS=https://campusshare.yourdomain.com,http://localhost
   VITE_API_URL=https://campusshare.yourdomain.com/api
   ```

4. **Build and start the containers:**
   ```bash
   docker compose up -d --build
   ```

5. **Verify:**
   * Backend health: `curl http://localhost:8000/health`
   * Frontend: Open `http://your-server-ip` in your browser.
   * Named volumes `campusshare_db` and `campusshare_uploads` persist your database and uploaded images across container restarts.

---

### Option B: Cloud PaaS (Render / Railway + Vercel / Netlify)
*Recommended for zero-maintenance cloud hosting.*

#### Step 1: Deploy Backend (e.g. on [Render.com](https://render.com))
1. Connect your GitHub repository to Render.
2. Render detects `render.yaml` automatically, or create a new **Web Service**:
   * **Root Directory:** `backend`
   * **Runtime:** `Python 3`
   * **Build Command:** `pip install -r requirements.txt`
   * **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   * **Health Check Path:** `/health`
3. Under **Disks**, attach a persistent disk:
   * **Mount Path:** `/var/data`
   * **Size:** 1 GB (or as needed)
4. Configure **Environment Variables**:
   * `ENVIRONMENT`: `production`
   * `SECRET_KEY`: *(generate a 64-char random hex string)*
   * `DATABASE_URL`: `sqlite:////var/data/campus_share.db`
   * `UPLOAD_DIR`: `/var/data/uploads`
   * `ALLOWED_ORIGINS`: `https://your-frontend.vercel.app,http://localhost`
5. Click **Deploy**. Your backend will be live at `https://campusshare-backend.onrender.com`.

#### Step 2: Deploy Frontend (e.g. on [Vercel](https://vercel.com) or [Netlify](https://netlify.com))

##### On Vercel:
1. Import the repository in Vercel.
2. Set **Root Directory** to `frontend`.
3. Framework Preset: **Vite**.
4. Add Environment Variable:
   * `VITE_API_URL`: `https://campusshare-backend.onrender.com/api` (your backend URL from Step 1).
5. Deploy. The included `frontend/vercel.json` ensures all SPA routes (`/items`, `/profile`) resolve correctly.

##### On Netlify:
1. Import repository and set base directory to `frontend`.
2. Build command: `npm run build`
3. Publish directory: `dist`
4. Add Environment Variable: `VITE_API_URL`.
5. Deploy. The included `frontend/public/_redirects` handles client-side routing automatically.

---

## Production Security Checklist

- [ ] **Secret Key:** Ensure `SECRET_KEY` is a cryptographically strong random key and never committed to version control.
- [ ] **Allowed Origins:** Set `ALLOWED_ORIGINS` to your exact frontend domain(s) without trailing slashes.
- [ ] **HTTPS:** Always serve production traffic over HTTPS to protect JWT tokens in transit.
- [ ] **Data Persistence:** Ensure the SQLite database path and upload folder are stored on persistent storage.
