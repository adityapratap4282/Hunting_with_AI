# Hunting_with_AI

Hunting with AI is a local-first job search operating system built around three workflows:

- **Resume Conveyor** for targeted resume analysis and paste-ready rewrites.
- **Job Intake + Ranking** for CSV/XLSX ingestion, normalization, deduplication, and hybrid scoring.
- **Referral Copilot** for manual lead import, saved LinkedIn search tracking, and message drafting.

## Chosen v1 architecture

- **Backend:** Python 3.11 + FastAPI modular monolith.
- **Frontend:** React + Vite + Tailwind, built and served by FastAPI for local one-click usage.
- **Database:** SQLite for zero-setup local persistence.
- **AI:** ChatGPT/OpenAI for higher-value summarization and drafting, plus hybrid rules for fast scoring.
- **Extension:** Planned for phase 2 after the core app is stable.

## What changed from the original scaffold

The app no longer needs to run as two separate long-lived processes in normal usage. The intended flow is now:

1. Build the frontend.
2. Let FastAPI serve both the API and the frontend build.
3. Launch everything through `start_app.bat` on Windows or `python start_app.py` elsewhere.

## One-click Windows startup

### First-time requirements

Install these once on your PC:

- **Python 3.11**
- **Node.js + npm**

### Then launch

Double-click `start_app.bat` from File Explorer.

What it does:

- creates `backend/.venv` if needed
- installs backend packages from `backend/requirements.txt`
- installs frontend packages if needed
- builds the React app
- starts the FastAPI server on `http://127.0.0.1:8000`
- opens the browser automatically

## Manual terminal startup

### Prepare only

```bash
python start_app.py --prepare-only
```

### Launch locally

```bash
python start_app.py
```

## Developer mode

### Backend only

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # On Windows PowerShell use: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend only

```bash
cd frontend
npm install
npm run dev
```

In developer mode, Vite proxies `/api` and `/health` to the backend at `http://127.0.0.1:8000`.
