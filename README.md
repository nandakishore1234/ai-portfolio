# Nanda Kishore — Portfolio

Personal site with RAG chat, a LiveKit voice call (Cartesia + Gemini), contact form, admin document upload, and mixed call recordings in SeaweedFS + PostgreSQL.

This README is the full path from a fresh clone to a running app.

## What you get

| Piece | What it does |
| --- | --- |
| Frontend (`frontend/`) | React + Vite portfolio, chat modal, voice call UI, `/admin` |
| FastAPI (`backend/`) | Chat RAG, contact email, LiveKit tokens, admin JWT, recordings list |
| Voice worker (`backend/voice/`) | Joins LiveKit rooms, STT → RAG → TTS, hangup, one mixed WAV per call |
| LiveKit server | Local WebRTC rooms on `ws://127.0.0.1:7880` |
| PostgreSQL | `admins` + `assets` tables |
| SeaweedFS | Stores the mixed call WAV |
| Gemini | Chat answers and embeddings (`gemini-embedding-001`) |
| Qdrant | Embedded on disk at `backend/data/qdrant` when `QDRANT_PATH=qdrant` |

Chat and voice share the same knowledge files. Voice does **not** call `/api/chat`.

## Layout

```text
frontend/
  public/
    nanda.jpg                 # portrait (Hero, About, call UI)
    nanda-kishore-cv.pdf      # Download CV
    ring.mp3                  # call ringing sound
  src/                        # React app
  .env.example                # copy to .env for GA only
backend/
  app/knowledge/nanda.md      # RAG notes (add more .md / .txt here or via /admin)
  app/                        # FastAPI
  agent/                      # LangGraph chat + voice graphs
  voice/                      # LiveKit worker
  scripts/                    # download LiveKit and SeaweedFS (Windows .ps1 / Unix .sh)
  livekit.yaml                # local LiveKit config
  requirements.txt            # all Python packages
  .env.example                # copy to .env
```

## Prerequisites (install these yourself)

Do these once. Python packages are **not** installed one by one; they all come from `requirements.txt` later. Use **Python 3.13** (not 3.15). Chat and embeddings use Gemini. Voice uses Cartesia. No local LLM, Whisper, or Piper.

### Windows

- Python 3.13 — [python.org](https://www.python.org/downloads/)
- Node.js 20+ — [nodejs.org](https://nodejs.org/)
- PostgreSQL 16+ — [postgresql.org](https://www.postgresql.org/download/windows/)
- Docker Desktop (optional) — [docker.com](https://www.docker.com/products/docker-desktop/)
- Git

### Ubuntu

```bash
sudo apt update
sudo apt install -y git curl build-essential
# Python 3.13 (deadsnakes if your Ubuntu does not ship it)
sudo add-apt-repository -y ppa:deadsnakes/ppa
sudo apt install -y python3.13 python3.13-venv python3.13-dev
# Node 20
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs
# PostgreSQL
sudo apt install -y postgresql postgresql-contrib
sudo systemctl enable --now postgresql
# Docker (optional, for SeaweedFS)
sudo apt install -y docker.io
sudo usermod -aG docker "$USER"
# then log out and back in
```

### macOS

Install [Homebrew](https://brew.sh) first, then:

```bash
brew install git python@3.13 node postgresql@16
brew install --cask docker
brew services start postgresql@16
```

If `python3.13` is not on your PATH:

```bash
export PATH="$(brew --prefix python@3.13)/bin:$PATH"
```

## 1. Clone

```bash
git clone <YOUR_REPO_URL> port
cd port
```

## 2. Put static files here

These are served from `frontend/public/` (URL path = filename).

| File | Put it at | Used by |
| --- | --- | --- |
| Portrait | `frontend/public/nanda.jpg` | Hero, About, voice call avatar |
| Resume / CV | `frontend/public/nanda-kishore-cv.pdf` | About → **Download CV** (`profile.about.cv` in `frontend/src/data/profile.js`) |
| Ring sound | `frontend/public/ring.mp3` | Incoming-call UI |

If you rename the PDF or photo, change the path in `frontend/src/data/profile.js` (`about.cv`) and the `<img src="/nanda.jpg">` references.

## 3. RAG knowledge

Put notes as `.md` or `.txt` in:

```text
backend/app/knowledge/
```

`nanda.md` ships with the repo. You can also upload more later at `http://localhost:5173/admin`. Keep at least one file.

## 4. Backend Python env + pip

All Python deps live in `backend/requirements.txt`. Do **not** `pip install fastapi` (etc.) by hand.

**Windows**

```powershell
cd backend
py -3.13 -m venv .venv
.\.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

**Ubuntu / macOS**

```bash
cd backend
python3.13 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

What that file installs:

| Package | Why |
| --- | --- |
| `fastapi`, `uvicorn[standard]`, `python-multipart`, `pydantic-settings` | API |
| `langchain-*`, `langgraph`, `qdrant-client` | RAG |
| `livekit-agents`, `livekit-plugins-*`, `livekit-api` | Voice |
| `httpx` | SeaweedFS / Resend HTTP |
| `psycopg[binary]` | PostgreSQL |
| `PyJWT` | Admin JWT |
| `numpy` | Mix visitor + agent into one WAV |

Stay in the venv for API and voice commands: `.\.venv\Scripts\activate` (Windows) or `source .venv/bin/activate` (Ubuntu / macOS).

## 5. Frontend npm

```bash
cd frontend
npm install
```

Copy env: `copy .env.example .env` (Windows) or `cp .env.example .env` (Ubuntu / macOS).

Edit `frontend/.env` only if you want Google Analytics:

```env
VITE_GA_MEASUREMENT_ID=G-XXXXXXXX
```

Leave it empty to disable GA.

**Build:** Vite inlines `VITE_*` at `npm run build`. Changing `.env` after a build does nothing until you build again. Never put API keys in the frontend `.env` (they would ship to the browser).

Dev server proxies `/api` → `http://127.0.0.1:8000` (see `frontend/vite.config.js`).

## 6. Backend `.env`

Windows: `cd backend` then `copy .env.example .env`  
Ubuntu / macOS: `cd backend` then `cp .env.example .env`

Edit `backend/.env`. Minimum for a full local run:

```env
DATABASE_URL=postgresql://nandu:nandu123@127.0.0.1:5432/nanda_port
ADMIN_USERNAME=nandu
ADMIN_PASSWORD=nandu123
ADMIN_SECRET=change-this-to-a-long-random-jwt-secret
LIVEKIT_URL=ws://127.0.0.1:7880
LIVEKIT_API_KEY=devkey
LIVEKIT_API_SECRET=secretsecretsecretsecretsecretsecret12
SEAWEEDFS_FILER_URL=http://127.0.0.1:8888
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

`ADMIN_SECRET` must be **at least 32 characters** (JWT signing).

Gemini and Cartesia are required. Chat and embeddings use Gemini. Voice uses Cartesia.

```env
GEMINI_MODEL=gemini-2.5-flash
GEMINI_EMBED_MODEL=gemini-embedding-001
GEMINI_API_KEY_1=
GEMINI_API_KEY_2=

CARTESIA_API_KEY_1=
CARTESIA_TTS_VOICE_ID_1=
CARTESIA_API_KEY_2=
CARTESIA_TTS_VOICE_ID_2=
CARTESIA_TTS_VOICE_ID=          # fallback if a numbered voice id is blank
```

Key 1 uses voice id 1, key 2 uses voice id 2, and so on. At least one Gemini key and one Cartesia key must be set.

Contact form needs **one** of:

- `RESEND_API_KEY` + `CONTACT_TO_EMAIL`, or
- `SMTP_USER` + `SMTP_PASSWORD` (Gmail: App Password)

## 7. PostgreSQL

Create a user and database (names must match `DATABASE_URL`).

**Windows** — open SQL Shell (`psql`) as `postgres`, or:

```powershell
& "C:\Program Files\PostgreSQL\18\bin\psql.exe" -U postgres
```

**Ubuntu**

```bash
sudo -u postgres psql
```

**macOS** (Homebrew)

```bash
psql postgres
```

Then:

```sql
CREATE USER nandu WITH PASSWORD 'nandu123';
CREATE DATABASE nanda_port OWNER nandu;
GRANT ALL PRIVILEGES ON DATABASE nanda_port TO nandu;
```

If `nandu` cannot create databases, as superuser:

```sql
CREATE DATABASE nanda_port OWNER nandu;
```

On API start, `init_db()` creates:

- `assets` — one row per mixed call recording
- `admins` — seeded from `ADMIN_USERNAME` / `ADMIN_PASSWORD` (password hashed)

SQLite is not used.

## 8. LiveKit binary and SeaweedFS binary

Writes binaries under `backend/bin/`.

**Windows**

```powershell
cd backend
powershell -ExecutionPolicy Bypass -File .\scripts\download_livekit_server.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\download_seaweedfs.ps1
```

**Ubuntu / macOS**

```bash
cd backend
chmod +x scripts/download_deps.sh
./scripts/download_deps.sh
```

## 9. LiveKit server

Leave this terminal open. Ports: `7880` (WS), `7881` (TCP), UDP `50000–50100`.  
Keys in `livekit.yaml` must match `LIVEKIT_API_KEY` / `LIVEKIT_API_SECRET` (secret ≥ 32 chars).

**Windows**

```powershell
cd backend
.\bin\livekit-server.exe --config livekit.yaml
```

**Ubuntu / macOS**

```bash
cd backend
./bin/livekit-server --config livekit.yaml
```

**Any OS, Docker**

```bash
cd backend
docker run --rm -p 7880:7880 -p 7881:7881 -p 7882:7882/udp \
  -v "$PWD/livekit.yaml:/livekit.yaml" \
  livekit/livekit-server --config /livekit.yaml
```

On Windows PowerShell, use `${PWD}` instead of `$PWD`.

## 10. SeaweedFS (recordings)

Filer: [http://127.0.0.1:8888](http://127.0.0.1:8888). If it is down, WAVs go to `backend/data/recordings/` and the path is still stored in Postgres.

**Any OS, Docker (preferred)**

```bash
docker run --name seaweed -p 9333:9333 -p 8888:8888 -p 8080:8080 chrislusf/seaweedfs server -filer -s3
```

Later: `docker start seaweed`

**Windows without Docker**

```powershell
cd backend
.\bin\weed.exe --% server -dir=C:\Users\<YOU>\path\to\port\backend\data\seaweed\volume -master.dir=C:\Users\<YOU>\path\to\port\backend\data\seaweed\master -filer -s3 -ip=127.0.0.1 -ip.bind=127.0.0.1
```

`--%` stops PowerShell from dropping `-dir`.

**Ubuntu / macOS without Docker**

```bash
cd backend
mkdir -p data/seaweed/volume data/seaweed/master
./bin/weed server -dir="$PWD/data/seaweed/volume" -master.dir="$PWD/data/seaweed/master" -filer -s3 -ip=127.0.0.1 -ip.bind=127.0.0.1
```

## 11. Run everything (six terminals)

Start in this order. New terminal for each.

**A — PostgreSQL**

- Windows: Services → `postgresql` running  
- Ubuntu: `sudo systemctl start postgresql`  
- macOS: `brew services start postgresql@16`

**B — SeaweedFS:** `docker start seaweed` (or the `weed` command above)

**C — LiveKit** (see section 9)

**D — FastAPI**

Windows:

```powershell
cd backend
.\.venv\Scripts\activate
python -m uvicorn app.main:app --port 8000
```

Ubuntu / macOS:

```bash
cd backend
source .venv/bin/activate
python -m uvicorn app.main:app --port 8000
```

**E — Voice worker** (needs LiveKit + API up)

Windows: same venv, then `python -m voice.agent start`  
Ubuntu / macOS: `source .venv/bin/activate` then `python -m voice.agent start`

**F — Frontend** (same on all OS)

```bash
cd frontend
npm run dev
```

Open [http://localhost:5173](http://localhost:5173).

| Action | What happens |
| --- | --- |
| **Let's Talk → Chat with me** | RAG chat via FastAPI |
| **Let's Talk → Call me** | LiveKit room + voice worker |
| **Hire Me** | Contact form, focuses **Send Message** |
| **Download CV** | `frontend/public/nanda-kishore-cv.pdf` |
| [http://localhost:5173/admin](http://localhost:5173/admin) | Admin JWT login (`ADMIN_USERNAME` / `ADMIN_PASSWORD`) |

After a call ends: one stereo WAV (visitor left, agent right) in SeaweedFS, one `assets` row, listed in `/admin`.

Restart **uvicorn** after Python/API changes. Restart **voice worker** after `voice/` or prompt changes. Restart **`npm run dev`** after frontend `.env` changes.

## 12. Production build (frontend)

```bash
cd frontend
npm run build
npm run preview
```

`dist/` is static files. Serve them behind the same host as FastAPI (or proxy `/api`) so `/api` still works. Rebuild after changing `VITE_GA_MEASUREMENT_ID`.

## Environment variables

Full comments: [`backend/.env.example`](backend/.env.example), [`frontend/.env.example`](frontend/.env.example).

| Variable | Where | Purpose |
| --- | --- | --- |
| `GEMINI_MODEL` / `GEMINI_EMBED_MODEL` / `GEMINI_API_KEY_1`…`5` | backend | Chat, voice RAG, and embeddings. At least one key |
| `CARTESIA_API_KEY_1`…`5` | backend | STT + TTS, key fallback |
| `CARTESIA_TTS_VOICE_ID_1`…`5` | backend | Voice id for that key |
| `CARTESIA_TTS_VOICE_ID` | backend | Voice id if a numbered slot is empty |
| `QDRANT_*` | backend | Vector DB URL or local `QDRANT_PATH` |
| `RAG_TOP_K` | backend | Retrieval depth |
| `CORS_ORIGINS` | backend | Allowed frontend origins |
| `CONTACT_TO_EMAIL` / `RESEND_*` / `SMTP_*` | backend | Contact form mail |
| `LIVEKIT_URL` / `LIVEKIT_API_KEY` / `LIVEKIT_API_SECRET` | backend | Must match `livekit.yaml` |
| `LIVEKIT_ROOM_PREFIX` | backend | Room name prefix |
| `VOICE_IDLE_PROCESSES` | backend | Concurrent voice jobs |
| `ADMIN_USERNAME` / `ADMIN_PASSWORD` / `ADMIN_SECRET` | backend | Seeds `admins`; JWT (`ADMIN_SECRET` ≥ 32 chars) |
| `SEAWEEDFS_FILER_URL` / `SEAWEEDFS_PREFIX` | backend | Recording store |
| `DATABASE_URL` | backend | PostgreSQL (`nanda_port`) |
| `VITE_GA_MEASUREMENT_ID` | **frontend** `.env` | GA4; empty = off |

## If something fails

| Symptom | Check |
| --- | --- |
| `docker` not recognized | Start Docker Desktop (Windows/macOS) or `sudo systemctl start docker` (Ubuntu); new terminal |
| LiveKit secret too short | Secret ≥ 32 chars in `.env` **and** `livekit.yaml` |
| Port 8000 / 7880 in use | Windows: `netstat -ano \| findstr :8000`. Ubuntu/macOS: `lsof -i :8000` then stop that PID |
| Voice worker missing `LIVEKIT_URL` | `backend/.env` + restart worker |
| `Event loop is closed` | Finalize recordings then restart worker (do not leave old workers running) |
| Admin 503 JWT | Lengthen `ADMIN_SECRET`, restart API |
| Postgres connect error | User, password, DB name vs `DATABASE_URL`; Postgres service running |
| No CV download | File at `frontend/public/nanda-kishore-cv.pdf` |
| Broken portrait | File at `frontend/public/nanda.jpg` |
| Contact 503 | Resend or SMTP in `.env` |

## Do not commit

`backend/.env`, `frontend/.env`, `backend/.venv`, `backend/data`, `backend/bin`, `node_modules`, `dist`.
