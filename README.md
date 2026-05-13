# Requirement-to-Development Plan Generator

Rapid hackathon scaffold for turning raw requirements into a Functional Requirement Document, a draw.io diagram XML payload, and a developer task backlog.

## Structure

- `backend/` - FastAPI REST API with mock LLM orchestration.
- `frontend/` - Next.js, React, TypeScript, and TailwindCSS dashboard.

## Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

API endpoint:

```http
POST http://localhost:8000/api/generate-plan
Content-Type: multipart/form-data
```

Fields:

- `requirement_text` - raw requirement text.
- `file` - optional PDF/DOCX placeholder upload.

## Frontend

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:3000`.

Set a custom backend URL with:

```bash
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

## Azure OpenAI Setup

The backend reads environment variables from the repo-root `.env.local`. It uses API key auth only, so no `az login` or Azure credential setup is required.

```bash
cp .env.example .env.local
```

Fill these values:

```bash
LLM_PROVIDER=azure_openai
CORS_ORIGINS=http://localhost:3000,https://your-frontend.vercel.app
AZURE_OPENAI_BASE_URL=https://<your-resource-name>.openai.azure.com/openai/v1/
AZURE_OPENAI_API_KEY=<your-api-key>
AZURE_OPENAI_DEPLOYMENT=<your-deployment-name>
```

`AZURE_OPENAI_DEPLOYMENT` must be the deployment name from Azure AI Foundry. It may be `gpt-4.1`, but only if that is the exact deployment name you created.

For UI-only local development, set:

```bash
LLM_PROVIDER=mock
```

## Draw.io MCP Integration

When the remote Draw.io MCP server is ready, add:

```bash
DRAWIO_MCP_URL=https://your-drawio-mcp-server.example/mcp
DRAWIO_MCP_REQUIRE_APPROVAL=never
```

The frontend response shape stays the same whether the backend is using mock mode, Azure OpenAI without MCP, or Azure OpenAI with MCP.

## Vercel Deployment Notes

Deploy the monorepo as two Vercel projects:

- Backend project root: `backend`
- Frontend project root: `frontend`

The backend includes `backend/index.py` so Vercel can discover the FastAPI app. In the backend project, set `CORS_ORIGINS` to include the deployed frontend URL.
