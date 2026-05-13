# Requirement-to-Development Plan Generator

Hackathon MVP that turns raw requirement notes into a development-ready plan:

- Functional Requirement Document (FRD) and user stories
- draw.io / diagrams.net XML diagram
- Developer task backlog

The app uses a Next.js dashboard, a FastAPI backend, Azure OpenAI Responses API, and the hosted Draw.io MCP server.

## Project Structure

- `backend/` - FastAPI API, Azure OpenAI orchestration, Draw.io MCP tool wiring, Vercel entrypoint
- `frontend/` - Next.js, React, TypeScript, TailwindCSS dashboard

## Local Setup

Create the root `.env.local` from the example:

```bash
cp .env.example .env.local
```

Fill in the Azure OpenAI values:

```bash
LLM_PROVIDER=azure_openai
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
AZURE_OPENAI_BASE_URL=https://<your-resource>.services.ai.azure.com/api/projects/<project>/openai/v1/
AZURE_OPENAI_API_KEY=<your-api-key>
AZURE_OPENAI_DEPLOYMENT=<your-deployment-name>
AZURE_OPENAI_TEMPERATURE=0.2
AZURE_OPENAI_MAX_OUTPUT_TOKENS=6000
DRAWIO_MCP_URL=https://mcp.draw.io/mcp
DRAWIO_MCP_SERVER_LABEL=drawio
DRAWIO_MCP_REQUIRE_APPROVAL=never
DRAWIO_MCP_ALLOWED_TOOLS=create_diagram,search_shapes
```

Notes:

- `AZURE_OPENAI_DEPLOYMENT` is the deployment name in Azure AI Foundry. It may be `gpt-4.1` only if that is the exact deployment name.
- `AZURE_OPENAI_BASE_URL` must end at `/openai/v1/`. Do not append `/responses`.
- The backend uses API key auth only. It does not require `az login`.

## Run Backend

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
cd backend
../.venv/bin/uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Useful URLs:

- Health check: `http://127.0.0.1:8000/health`
- API docs: `http://127.0.0.1:8000/docs`
- Generate endpoint: `POST http://127.0.0.1:8000/api/generate-plan`

Request fields:

- `requirement_text` - raw requirement text
- `file` - optional PDF/DOCX upload placeholder

## Run Frontend

```bash
cd frontend
npm install
npm run dev
```

Open `http://127.0.0.1:3000`.

Optional frontend env:

```bash
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000
```

## Diagram Flow

The backend asks Azure OpenAI to generate a structured plan and `diagram_xml`. When `DRAWIO_MCP_URL` is configured, the model can use the Draw.io MCP server:

```text
Requirement text
  -> FastAPI backend
  -> Azure OpenAI Responses API
  -> Draw.io MCP server
  -> FRD JSON + draw.io XML + backlog JSON
```

The frontend can:

- Preview the XML
- Download the `.drawio` XML file
- Open the generated XML directly in diagrams.net with the `Open in Draw.io` button

## Vercel Deployment

Deploy this repo as two Vercel projects.

### Backend Project

- Root Directory: `backend`
- Framework Preset: Other / FastAPI
- Entrypoint: `backend/index.py`
- Build Command: leave empty
- Install Command: default, or `pip install -r requirements.txt`

Backend environment variables:

```bash
LLM_PROVIDER=azure_openai
CORS_ORIGINS=https://<your-frontend-domain>.vercel.app
AZURE_OPENAI_BASE_URL=https://<your-resource>.services.ai.azure.com/api/projects/<project>/openai/v1/
AZURE_OPENAI_API_KEY=<your-api-key>
AZURE_OPENAI_DEPLOYMENT=<your-deployment-name>
AZURE_OPENAI_TEMPERATURE=0.2
AZURE_OPENAI_MAX_OUTPUT_TOKENS=6000
DRAWIO_MCP_URL=https://mcp.draw.io/mcp
DRAWIO_MCP_SERVER_LABEL=drawio
DRAWIO_MCP_REQUIRE_APPROVAL=never
DRAWIO_MCP_ALLOWED_TOOLS=create_diagram,search_shapes
```

Use the stable domain from Vercel's Domains tab. Do not use a per-deployment URL.

### Frontend Project

- Root Directory: `frontend`
- Framework Preset: Next.js
- Install Command: `npm install`
- Build Command: `npm run build`

Frontend environment variable:

```bash
NEXT_PUBLIC_API_BASE_URL=https://<your-backend-domain>.vercel.app
```

Recommended deploy order:

1. Deploy backend.
2. Copy the backend domain.
3. Deploy frontend with `NEXT_PUBLIC_API_BASE_URL`.
4. Copy the frontend domain.
5. Update backend `CORS_ORIGINS` with the frontend domain.
6. Redeploy backend.

## Common Issues

### Azure OpenAI 405

Usually caused by a bad base URL. This is wrong:

```bash
AZURE_OPENAI_BASE_URL=https://.../openai/v1/responses
```

Use:

```bash
AZURE_OPENAI_BASE_URL=https://.../openai/v1/
```

### Browser CORS Error

Set `CORS_ORIGINS` in the backend project to the exact frontend domain:

```bash
CORS_ORIGINS=https://<your-frontend-domain>.vercel.app
```

Then redeploy the backend.

### Local Frontend Looks Unstyled

Restart the frontend dev server and clear Next's dev cache:

```bash
cd frontend
rm -rf .next
npm run dev
```

## Local Mock Mode

For UI-only development without calling Azure OpenAI:

```bash
LLM_PROVIDER=mock
```

Mock mode keeps the same response shape as Azure mode, so the frontend does not need to change.
