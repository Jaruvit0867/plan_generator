# Requirement-to-Development Plan Generator

Turns raw requirement notes into a structured project proposal with a system diagram. The proposal covers problem summary, proposed solution, scope, user flow, architecture, feature breakdown, timeline, and risks. Export as DOCX or PDF.

Stack: Next.js 15 (TypeScript, TailwindCSS) + FastAPI (Python) + Azure OpenAI Responses API + Draw.io MCP server.

## Local Setup

```bash
cp .env.example .env.local
```

Edit `.env.local` with your Azure OpenAI credentials. Then:

```bash
# Backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r backend/requirements.txt
cd backend && ../.venv/bin/uvicorn main:app --reload --port 8000

# Frontend (separate terminal)
cd frontend && npm install && npm run dev
```

- Frontend: http://localhost:3000
- Backend docs: http://127.0.0.1:8000/docs

Set `LLM_PROVIDER=mock` in `.env.local` for UI-only development without Azure OpenAI.

## API Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/health` | GET | Health check |
| `/api/generate-plan` | POST | Generate proposal from `requirement_text` (form field) + optional `file` upload |
| `/api/export/docx` | POST | Export FRD as DOCX (JSON body) |
| `/api/export/pdf` | POST | Export FRD as PDF (JSON body) |

## Environment Variables

All variables live in `.env.local` at the project root.

| Variable | Default | Notes |
|---|---|---|
| `LLM_PROVIDER` | `mock` | `azure_openai` or `mock` |
| `CORS_ORIGINS` | `http://localhost:3000` | Comma-separated origins |
| `AZURE_OPENAI_BASE_URL` | — | Must end at `/openai/v1/`, never append `/responses` |
| `AZURE_OPENAI_API_KEY` | — | API key auth only, no `az login` |
| `AZURE_OPENAI_DEPLOYMENT` | — | Deployment name in Azure AI Foundry |
| `AZURE_OPENAI_TEMPERATURE` | `0.2` | |
| `AZURE_OPENAI_MAX_OUTPUT_TOKENS` | `6000` | |
| `DRAWIO_MCP_URL` | — | e.g. `https://mcp.draw.io/mcp` |
| `DRAWIO_MCP_SERVER_LABEL` | `drawio` | |
| `DRAWIO_MCP_REQUIRE_APPROVAL` | `never` | |
| `DRAWIO_MCP_ALLOWED_TOOLS` | — | e.g. `create_diagram,search_shapes` |
| `NEXT_PUBLIC_API_BASE_URL` | `http://localhost:8000` | Frontend only |

## Vercel Deployment

Deploy as two Vercel projects:

**Backend** — Root: `backend`, Entrypoint: `backend/index.py`, no build command.

**Frontend** — Root: `frontend`, standard Next.js build.

Deploy order: backend first → copy backend domain → deploy frontend with `NEXT_PUBLIC_API_BASE_URL` → copy frontend domain → update backend `CORS_ORIGINS` → redeploy backend.

## Troubleshooting

**Azure OpenAI 405** — `AZURE_OPENAI_BASE_URL` must end at `/openai/v1/`. Do not append `/responses`.

**Browser CORS error** — Set `CORS_ORIGINS` to the exact frontend domain, then redeploy the backend.

**Frontend unstyled** — Clear the dev cache: `cd frontend && rm -rf .next && npm run dev`.
