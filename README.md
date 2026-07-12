# AI-First CRM - HCP Interaction Logger

A full-stack proof of concept for logging pharmaceutical field-rep interactions with Healthcare Professionals (HCPs). Reps can use a structured form or a conversational interface; both paths save an AI-enriched interaction record.

## Features

- Structured interaction logging and conversational chat interface
- AI-generated interaction summaries, sentiment analysis, and entity extraction
- Compliance screening for potentially risky promotional language
- HCP interaction history and pre-call briefing support
- Follow-up scheduling, sample-drop tracking, and edit audit trails
- Live agent-tool trace streamed to the UI
- Voice dictation via the browser Web Speech API

## Tech stack

| Area | Technology |
| --- | --- |
| Frontend | React, Vite, Redux Toolkit |
| Backend | Python, FastAPI, SQLAlchemy |
| AI workflow | LangGraph, LangChain Groq |
| Database | SQLite by default; PostgreSQL and MySQL supported |

## Project structure

```text
hcp-crm/
├── frontend/              # React + Vite application
├── backend/
│   ├── app/               # FastAPI routes, models, and LangGraph agent
│   ├── requirements.txt   # Python dependencies
│   └── .env.example       # Safe environment-variable template
└── docs/                  # Agent design notes
```

## Prerequisites

- Node.js 18 or newer
- Python 3.10 or newer
- A Groq API key (required for AI-powered processing)

## Run locally

### 1. Configure and start the backend

From the repository root:

```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Open `backend/.env` and set `GROQ_API_KEY` to your own key. Do not commit this file.

Start the API:

```powershell
uvicorn app.main:app --reload --port 8000
```

The API runs at `http://localhost:8000`. Confirm it is available at `http://localhost:8000/api/health`.

Optionally seed the two demo HCP records:

```powershell
Invoke-RestMethod -Method Post http://localhost:8000/api/dev/seed
```

### 2. Start the frontend

Open a second terminal from the repository root:

```powershell
cd frontend
npm install
npm run dev
```

Open the address printed by Vite (normally `http://localhost:5173`). The development server proxies `/api` requests to the FastAPI backend on port 8000.

## Configuration

Copy `backend/.env.example` to `backend/.env` and set the required values:

```dotenv
GROQ_API_KEY=your_groq_api_key_here
DATABASE_URL=sqlite:///./hcp_crm.db
PRIMARY_MODEL=llama-3.3-70b-versatile
CONTEXT_MODEL=llama-3.3-70b-versatile
```

`DATABASE_URL` may instead use a PostgreSQL or MySQL SQLAlchemy connection string. SQLite is the default and requires no additional setup.

## Useful API endpoints

| Method | Endpoint | Description |
| --- | --- | --- |
| GET | `/api/health` | Health check |
| GET / POST | `/api/hcps` | List or create HCPs |
| GET / POST | `/api/interactions` | List or log interactions |
| PATCH | `/api/interactions/{id}` | Edit an interaction |
| POST | `/api/chat` | Run one chat turn |
| POST | `/api/chat/stream` | Run a streaming chat turn |
| POST | `/api/dev/seed` | Seed demo HCPs |

## Security and GitHub upload

The repository intentionally excludes `.env` files, databases, virtual environments, dependency directories, and build artifacts. Only `backend/.env.example` is included as a safe configuration template. Before pushing, verify that no API keys or other secrets are staged:

```powershell
git status
git diff --cached
```

## Further documentation

See [docs/agent_design.md](docs/agent_design.md) for the agent workflow and tool design.
