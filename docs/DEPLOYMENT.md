# ChainIntel Deployment Guide

This guide provides step-by-step instructions for deploying the **ChainIntel** application:
- **Backend**: FastAPI on [Render](https://render.com) (with Render PostgreSQL).
- **Frontend**: Next.js 14 on [Vercel](https://vercel.com).

---

## 1. Deploying the Backend on Render

### Option A: 1-Click Blueprint Deployment (Recommended)

1. Log into your [Render Dashboard](https://dashboard.render.com).
2. Click **New +** -> **Blueprint**.
3. Connect your GitHub repository `arsh-siddiqui/ChainIntel`.
4. Render will automatically detect `render.yaml` and prompt you to create:
   - **PostgreSQL Database**: `chainintel-postgres`
   - **Web Service**: `chainintel-backend`
5. Click **Apply**. Render will provision the database, build the FastAPI backend, run Alembic migrations, and launch the service.
6. Once deployed, note down your backend live URL (e.g. `https://chainintel-backend.onrender.com`).

---

### Option B: Manual Web Service Deployment

If you prefer to configure manually:

1. **Create PostgreSQL Database on Render**:
   - Go to **New +** -> **PostgreSQL**.
   - Name: `chainintel-postgres`
   - Database: `chainintel`
   - User: `chainintel`
   - Copy the **Internal Database URL** (or External Database URL).

2. **Create Web Service on Render**:
   - Go to **New +** -> **Web Service**.
   - Connect repository `arsh-siddiqui/ChainIntel`.
   - **Root Directory**: `backend`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `alembic upgrade head && gunicorn app.main:app -w 2 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT`
   - **Health Check Path**: `/api/health`

3. **Configure Environment Variables in Render**:
   - `DATABASE_URL`: *<Your Render PostgreSQL Connection String>*
   - `APP_MODE`: `DEMO` (or `LIVE`)
   - `CORS_ORIGINS`: `https://your-app.vercel.app,*`
   - Optional API Keys for LIVE mode:
     - `ETHERSCAN_API_KEY`
     - `MORALIS_API_KEY`
     - `ANKR_API_KEY`

---

## 2. Deploying the Frontend on Vercel

1. Log into your [Vercel Dashboard](https://vercel.com).
2. Click **Add New...** -> **Project**.
3. Import your GitHub repository `arsh-siddiqui/ChainIntel`.
4. Configure Project Settings:
   - **Framework Preset**: Next.js
   - **Root Directory**: Select `frontend` (Click Edit -> select `frontend`).
   - **Build Command**: `npm run build`
   - **Output Directory**: `.next`
5. **Environment Variables**:
   Add the following environment variable under Project Settings -> Environment Variables:
   - **Name**: `NEXT_PUBLIC_API_URL`
   - **Value**: `https://chainintel-backend.onrender.com` (replace with your actual Render backend URL, without trailing slash).
6. Click **Deploy**.

---

## 3. Post-Deployment Verification

1. **Backend Health Check**:
   Visit `https://chainintel-backend.onrender.com/api/health` in your browser.
   Expected response:
   ```json
   {
     "success": true,
     "data": {
       "status": "healthy",
       "mode": "DEMO",
       "version": "1.0.0",
       "database": "connected"
     }
   }
   ```

2. **Frontend Check**:
   Open your Vercel deployment URL (e.g. `https://chainintel.vercel.app`).
   - Search target wallets (e.g., `1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa`).
   - Verify Dashboard, Transactions, Threat Intelligence, Graph, and OSINT pages load data smoothly.
