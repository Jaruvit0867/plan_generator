# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Hackathon MVP: Requirement-to-Development Plan Generator. Takes raw requirement text and produces a structured development plan (FRD with user stories, draw.io XML diagram, task backlog). Uses Azure OpenAI Responses API with optional Draw.io MCP server integration.

## Commands

### Backend (Python / FastAPI)

```bash
# Setup
python3 -m venv .venv && source .venv/bin/activate
pip install -r backend/requirements.txt

# Run dev server
cd backend && ../.venv/bin/uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

### Frontend (Next.js / TypeScript / TailwindCSS)

```bash
cd frontend
npm install
npm run dev          # dev server on localhost:3000
npm run build        # production build
npm run lint         # ESLint
npm run typecheck    # tsc --noEmit
```

### Environment

Copy `.env.example` to `.env.local` and fill in Azure OpenAI values. Set `LLM_PROVIDER=mock` for UI-only work without an API key.

## Architecture

Monorepo with two independent services, each deployed as a separate Vercel project.

### Backend (`backend/`)

- `main.py` — FastAPI app with `GET /health` and `POST /api/generate-plan` (accepts `requirement_text` form field + optional `file` upload)
- `index.py` — Vercel serverless entrypoint (re-exports `app` from `main`)
- `services/llm_service.py` — All LLM logic:
  - Pydantic response models (`DevelopmentPlanResponse`, `FunctionalRequirementDocument`, `BacklogTask`, `UserStory`)
  - Two providers: `mock` (hardcoded sample) and `azure_openai` (structured JSON schema via OpenAI Responses API)
  - Draw.io MCP tool wiring (optional, configured via `DRAWIO_MCP_*` env vars)
  - Fallback from structured schema to raw JSON on `BadRequestError`
  - Env loading from `.env.local` then `.env` at project root

### Frontend (`frontend/`)

- Single-page app in `app/page.tsx` (~600 lines, `"use client"`)
- Three output tabs: FRD & Stories, System Diagram (draw.io XML preview/download/open-in-diagrams.net), Task Board (Kanban)
- Uses `pako` to compress XML into draw.io edit URLs
- API calls go to `NEXT_PUBLIC_API_BASE_URL` (defaults to `http://localhost:8000`)

### Data Flow

```
Frontend (textarea + file upload)
  → POST /api/generate-plan (multipart/form-data)
  → FastAPI backend
  → Azure OpenAI Responses API (structured JSON schema, optional Draw.io MCP tool calls)
  → JSON response {frd, diagram_xml, tasks, metadata}
  → Frontend renders three tabs
```

## Key Conventions

- No test suite exists yet
- No CI/CD pipeline — manual Vercel deployments
- `AZURE_OPENAI_BASE_URL` must end at `/openai/v1/` (never append `/responses`)
- API uses API key auth only, no `az login`
- The `file` upload field is a placeholder — text extraction is not implemented
- Backend loads env from project root (two levels up from `llm_service.py`)
