# Nanda Kishore — Portfolio

Personal portfolio site with a RAG chat assistant that answers as Nanda, grounded in local knowledge notes.

## Stack

- **Frontend:** React 19, Vite, Plus Jakarta Sans
- **Backend:** FastAPI
- **Agent:** LangChain + LangGraph
- **LLM:** Ollama (`qwen2`)
- **Embeddings / vectors:** `nomic-embed-text` + Qdrant (embedded local store by default)
- **Contact form:** FastAPI → Resend or Gmail SMTP

## Project layout

```text
frontend/     Vite React app
backend/      FastAPI API, RAG agent, knowledge notes
  agent/      LangGraph graph + prompts
  app/
    api/      /api/chat, /api/contact, /api/health
    knowledge/  Seed markdown used for RAG (not a public upload API)
    rag/      Document load + Qdrant store
```

## Prerequisites

- Node.js 20+
- Python 3.13 (recommended; 3.15 may fail some wheels)
- [Ollama](https://ollama.com) with models pulled:

```bash
ollama pull qwen2
ollama pull nomic-embed-text
```

## Setup

### 1. Backend env

```bash
cd backend
copy .env.example .env
```

Edit `backend/.env`. At minimum, Ollama + Qdrant settings work as-is for local chat.  
For the contact form, set either `RESEND_API_KEY` **or** `SMTP_USER` + `SMTP_PASSWORD`.

### 2. Backend install & run

```bash
cd backend
py -3.13 -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
python -m uvicorn app.main:app --port 8000
```

Health check: [http://127.0.0.1:8000/api/health](http://127.0.0.1:8000/api/health)

### 3. Frontend install & run

```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:5173](http://localhost:5173). Vite proxies `/api` to the backend on port 8000.

## Features

- Portfolio sections: About, Services, Projects, Experience, Contact
- **Let's Talk** opens a chat modal backed by real RAG (not a mock)
- **Hire Me** scrolls to the contact form and prefills a hiring template
- **Send Message** posts to `/api/contact` and emails you when mail is configured

## Environment variables

See [`backend/.env.example`](backend/.env.example). Copy it to `backend/.env` (gitignored).

| Variable | Purpose |
| --- | --- |
| `OLLAMA_*` | Chat + embedding models |
| `QDRANT_*` | Vector DB URL or local embedded path |
| `RAG_TOP_K` | How many chunks to retrieve |
| `CORS_ORIGINS` | Allowed frontend origins |
| `CONTACT_TO_EMAIL` | Inbox for form messages |
| `RESEND_*` | Resend email provider |
| `SMTP_*` | Gmail / SMTP fallback |

## Notes

- Do not commit `backend/.env`, `backend/.venv`, `backend/data`, or `node_modules`.
- Knowledge for the chat lives in `backend/app/knowledge/`. Restart the API after changing notes so the index can refresh.
- The chat API does not auto-reload; restart uvicorn after Python/prompt changes.
