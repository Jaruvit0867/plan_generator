from __future__ import annotations

import asyncio
import json
import os
from datetime import datetime, UTC
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv
from openai import BadRequestError, OpenAI, OpenAIError
from pydantic import BaseModel, Field


ROOT_DIR = Path(__file__).resolve().parents[2]
load_dotenv(ROOT_DIR / ".env.local")
load_dotenv(ROOT_DIR / ".env")

FeaturePriority = Literal["must_have", "should_have", "nice_to_have"]
RiskCategory = Literal["business", "technical", "timeline", "integration"]


class Feature(BaseModel):
    name: str
    description: str
    module: str
    priority: FeaturePriority


class TimelinePhase(BaseModel):
    phase: str
    duration: str
    deliverables: list[str]


class Risk(BaseModel):
    risk: str
    category: RiskCategory
    mitigation: str


class FunctionalRequirementDocument(BaseModel):
    problem_summary: str
    proposed_solution: str
    scope_of_work: str
    user_flow: str
    initial_architecture: str
    feature_breakdown: list[Feature]
    timeline_estimation: list[TimelinePhase]
    risk_analysis: list[Risk]


class DevelopmentPlanResponse(BaseModel):
    frd: FunctionalRequirementDocument
    diagram_xml: str
    metadata: dict[str, str]


class LLMConfigurationError(RuntimeError):
    """Raised when required LLM environment configuration is missing."""


class LLMGenerationError(RuntimeError):
    """Raised when the configured LLM call fails or returns invalid output."""


def _summarize_requirement(requirement_text: str) -> str:
    normalized = " ".join(requirement_text.split())
    if not normalized:
        return "No requirement text was provided."
    return normalized[:260] + ("..." if len(normalized) > 260 else "")


def _dummy_drawio_xml() -> str:
    return """<mxfile host="app.diagrams.net" modified="2026-05-13T00:00:00.000Z" agent="mock-llm-service" version="24.7.17">
  <diagram id="requirement-plan" name="System Architecture">
    <mxGraphModel dx="1200" dy="800" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="1100" pageHeight="850" math="0" shadow="0">
      <root>
        <mxCell id="0"/>
        <mxCell id="1" parent="0"/>
        <mxCell id="frontend" value="Next.js Dashboard" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#dbeafe;strokeColor=#2563eb;fontColor=#1e3a8a;" vertex="1" parent="1">
          <mxGeometry x="80" y="120" width="180" height="80" as="geometry"/>
        </mxCell>
        <mxCell id="backend" value="FastAPI Backend" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#dcfce7;strokeColor=#16a34a;fontColor=#14532d;" vertex="1" parent="1">
          <mxGeometry x="380" y="120" width="180" height="80" as="geometry"/>
        </mxCell>
        <mxCell id="llm" value="OpenAI Responses API" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#fef3c7;strokeColor=#d97706;fontColor=#78350f;" vertex="1" parent="1">
          <mxGeometry x="680" y="80" width="200" height="80" as="geometry"/>
        </mxCell>
        <mxCell id="mcp" value="Draw.io MCP Server" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#fce7f3;strokeColor=#db2777;fontColor=#831843;" vertex="1" parent="1">
          <mxGeometry x="680" y="210" width="200" height="80" as="geometry"/>
        </mxCell>
        <mxCell id="edge-frontend-backend" value="multipart/form-data" style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;strokeColor=#64748b;" edge="1" parent="1" source="frontend" target="backend">
          <mxGeometry relative="1" as="geometry"/>
        </mxCell>
        <mxCell id="edge-backend-llm" value="structured prompt" style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;strokeColor=#64748b;" edge="1" parent="1" source="backend" target="llm">
          <mxGeometry relative="1" as="geometry"/>
        </mxCell>
        <mxCell id="edge-llm-mcp" value="mcp tool call" style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;strokeColor=#64748b;" edge="1" parent="1" source="llm" target="mcp">
          <mxGeometry relative="1" as="geometry"/>
        </mxCell>
      </root>
    </mxGraphModel>
  </diagram>
</mxfile>"""


def _mock_development_plan(requirement_text: str) -> DevelopmentPlanResponse:
    summary = _summarize_requirement(requirement_text)

    return DevelopmentPlanResponse(
        frd=FunctionalRequirementDocument(
            problem_summary=(
                f"Mock analysis for the submitted requirement. Input snapshot: {summary} "
                "Teams currently struggle to turn raw ideas, meeting notes, and messy stakeholder "
                "requirements into structured project proposals without manual effort."
            ),
            proposed_solution=(
                "A Requirement-to-Development Plan Generator that transforms raw input into a "
                "structured early project proposal including problem analysis, architecture diagram, "
                "feature breakdown, timeline estimation, and risk analysis."
            ),
            scope_of_work=(
                "In scope: requirement parsing, FRD generation, draw.io diagram generation, "
                "feature prioritization, timeline estimation, risk identification. "
                "Out of scope: automated resource allocation, budget estimation, CI/CD pipeline setup."
            ),
            user_flow=(
                "1. User pastes raw requirement text or uploads a document. "
                "2. System sends input to the backend API. "
                "3. Backend calls Azure OpenAI to generate a structured plan. "
                "4. Frontend displays the proposal across two tabs: FRD and System Diagram. "
                "5. User can open the diagram in draw.io for further editing."
            ),
            initial_architecture=(
                "Next.js frontend (TypeScript, TailwindCSS) → FastAPI backend (Python) → "
                "Azure OpenAI Responses API (structured JSON schema output) → optional Draw.io MCP server "
                "for diagram rendering. Two Vercel deployments."
            ),
            feature_breakdown=[
                Feature(
                    name="Requirement Input",
                    description="Textarea and file upload for raw requirement text.",
                    module="Frontend",
                    priority="must_have",
                ),
                Feature(
                    name="Plan Generation API",
                    description="FastAPI endpoint that orchestrates LLM calls and returns structured JSON.",
                    module="Backend",
                    priority="must_have",
                ),
                Feature(
                    name="FRD Display",
                    description="Render all proposal sections: problem, solution, scope, flow, architecture, features, timeline, risks.",
                    module="Frontend",
                    priority="must_have",
                ),
                Feature(
                    name="Diagram Generation",
                    description="Generate draw.io XML via LLM and display preview with open-in-draw.io support.",
                    module="Backend + Frontend",
                    priority="must_have",
                ),
                Feature(
                    name="Draw.io MCP Integration",
                    description="Use MCP tools to search shapes and render diagrams.",
                    module="Backend",
                    priority="should_have",
                ),
                Feature(
                    name="Document Parsing",
                    description="Extract text from uploaded PDF and DOCX files.",
                    module="Backend",
                    priority="nice_to_have",
                ),
            ],
            timeline_estimation=[
                TimelinePhase(
                    phase="Phase 1 — Core API",
                    duration="1-2 days",
                    deliverables=[
                        "FastAPI endpoint with mock provider",
                        "Pydantic response models",
                        "Health check route",
                    ],
                ),
                TimelinePhase(
                    phase="Phase 2 — LLM Integration",
                    duration="1-2 days",
                    deliverables=[
                        "Azure OpenAI Responses API wiring",
                        "Structured JSON schema output",
                        "Draw.io MCP tool integration",
                    ],
                ),
                TimelinePhase(
                    phase="Phase 3 — Frontend Dashboard",
                    duration="2-3 days",
                    deliverables=[
                        "Requirement input form",
                        "FRD proposal view (all 8 sections)",
                        "System diagram preview and draw.io integration",
                    ],
                ),
                TimelinePhase(
                    phase="Phase 4 — Deploy & Polish",
                    duration="1 day",
                    deliverables=[
                        "Vercel deployment (2 projects)",
                        "CORS and env configuration",
                        "Error handling and loading states",
                    ],
                ),
            ],
            risk_analysis=[
                Risk(
                    risk="LLM output may not conform to the expected JSON schema.",
                    category="technical",
                    mitigation="Use structured JSON schema output with fallback to raw JSON parsing.",
                ),
                Risk(
                    risk="Draw.io MCP server may be unavailable or rate-limited.",
                    category="integration",
                    mitigation="Fallback to LLM-generated XML without MCP tool calls.",
                ),
                Risk(
                    risk="Generated diagrams may be too complex or malformed.",
                    category="technical",
                    mitigation="Enforce simple diagram rules (8-16 nodes, orthogonal connectors) in the prompt.",
                ),
                Risk(
                    risk="Project timeline may not allow all features to be delivered on schedule.",
                    category="timeline",
                    mitigation="Prioritize must-have features; defer nice-to-have items to a later iteration.",
                ),
                Risk(
                    risk="Stakeholder requirements may be too vague for meaningful output.",
                    category="business",
                    mitigation="Include clear problem summary and scope sections to surface ambiguity early.",
                ),
            ],
        ),
        diagram_xml=_dummy_drawio_xml(),
        metadata={
            "mode": "mock",
            "recommended_model": "gpt-4.1",
            "provider": "mock",
            "generated_at": datetime.now(UTC).isoformat(),
        },
    )


def _required_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value or value.startswith("<"):
        raise LLMConfigurationError(f"Missing required environment variable: {name}")
    return value


def _optional_float_env(name: str, default: float) -> float:
    value = os.getenv(name, "").strip()
    if not value:
        return default
    try:
        return float(value)
    except ValueError as exc:
        raise LLMConfigurationError(f"{name} must be a number.") from exc


def _optional_int_env(name: str, default: int) -> int:
    value = os.getenv(name, "").strip()
    if not value:
        return default
    try:
        return int(value)
    except ValueError as exc:
        raise LLMConfigurationError(f"{name} must be an integer.") from exc


def _response_schema() -> dict:
    schema = DevelopmentPlanResponse.model_json_schema()
    schema["additionalProperties"] = False
    return schema


def _azure_tools() -> list[dict]:
    drawio_mcp_url = os.getenv("DRAWIO_MCP_URL", "").strip()
    if not drawio_mcp_url:
        return []

    tool: dict = {
        "type": "mcp",
        "server_label": os.getenv("DRAWIO_MCP_SERVER_LABEL", "drawio"),
        "server_url": drawio_mcp_url,
        "require_approval": os.getenv("DRAWIO_MCP_REQUIRE_APPROVAL", "never"),
    }

    authorization = os.getenv("DRAWIO_MCP_AUTHORIZATION", "").strip()
    if authorization:
        tool["headers"] = {"Authorization": authorization}

    allowed_tools = [
        item.strip()
        for item in os.getenv("DRAWIO_MCP_ALLOWED_TOOLS", "").split(",")
        if item.strip()
    ]
    if allowed_tools:
        tool["allowed_tools"] = allowed_tools

    return [tool]


def _extract_json_payload(raw_text: str) -> dict:
    try:
        return json.loads(raw_text)
    except json.JSONDecodeError:
        start = raw_text.find("{")
        end = raw_text.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise
        return json.loads(raw_text[start : end + 1])


def _looks_like_drawio_xml(text: str) -> bool:
    """Quick sanity check — not full XML parsing, just structural markers."""
    t = text.strip()
    return "<mxfile" in t and "</mxfile>" in t and "<mxCell" in t


def _normalize_plan_payload(payload: dict, deployment: str) -> DevelopmentPlanResponse:
    xml = payload.get("diagram_xml", "")
    if not xml or not _looks_like_drawio_xml(xml):
        payload["diagram_xml"] = _dummy_drawio_xml()

    raw_metadata = payload.setdefault("metadata", {})
    metadata = {
        str(key): value if isinstance(value, str) else json.dumps(value)
        for key, value in raw_metadata.items()
    }
    metadata.update(
        {
            "mode": "azure_openai",
            "provider": "azure_openai",
            "model": deployment,
            "generated_at": datetime.now(UTC).isoformat(),
        }
    )
    payload["metadata"] = metadata

    return DevelopmentPlanResponse.model_validate(payload)


def _build_generation_prompt(requirement_text: str, has_mcp: bool) -> str:
    mcp_instruction = (
        "You have access to draw.io MCP tools. "
        "Use search_shapes to find style strings for specific shapes (cloud, database, user, etc.) "
        "before writing XML. After generating the XML yourself, call create_diagram to render it. "
        "The diagram_xml field must contain YOUR raw XML, not the rendered output."
        if has_mcp
        else "Produce a valid draw.io mxfile XML string yourself."
    )

    return f"""
You are an expert business analyst, software architect, and delivery lead.

Generate a build-ready development plan from the raw requirement below.

Return JSON only. The response must include:
- frd.problem_summary — a clear explanation of the actual problem, pain points, and business impact.
- frd.proposed_solution — a high-level explanation of the recommended system or application.
- frd.scope_of_work — what is included, what is excluded, and project limitations.
- frd.user_flow — a structured step-by-step flow showing how users interact with the system.
- frd.initial_architecture — a high-level technical architecture description (frontend, backend, database, integrations, infrastructure).
- frd.feature_breakdown — an array of features, each with name, description, module, and priority (must_have, should_have, nice_to_have).
- frd.timeline_estimation — an array of phases, each with phase name, duration, and deliverables list.
- frd.risk_analysis — an array of risks, each with risk description, category (business, technical, timeline, integration), and mitigation.
- diagram_xml — a valid draw.io mxfile XML string representing the system architecture.
- metadata — an object.

Diagram rules:
- You MUST generate the diagram_xml yourself as valid, uncompressed draw.io XML.
- Keep it simple: 8-16 nodes, left-to-right or top-to-bottom flow, clear short labels.
- Include relevant actors, services, and data stores from the requirement.
- Use edgeStyle=orthogonalEdgeStyle for connectors.
- Adequate spacing between nodes (at least 160 px horizontal, 100 px vertical).

Mandatory XML structure:
- Wrap in <mxfile><diagram name="..."><mxGraphModel ...><root>...</root></mxGraphModel></diagram></mxfile>
- First two cells: <mxCell id="0"/> and <mxCell id="1" parent="0"/>
- Vertex cells: vertex="1" with <mxGeometry x="" y="" width="" height="" as="geometry"/>
- Edge cells: edge="1" with source="id" target="id" and <mxGeometry relative="1" as="geometry"/>
- Style strings use key=value; format (e.g. "rounded=1;whiteSpace=wrap;html=1;")
- All id values must be unique.

Rules:
- Feature priority values: must_have, should_have, nice_to_have.
- Risk category values: business, technical, timeline, integration.
- Make the output realistic and actionable for a development team.
- {mcp_instruction}

Raw requirement:
{requirement_text}
""".strip()


async def _generate_with_azure_openai(requirement_text: str) -> DevelopmentPlanResponse:
    api_key = _required_env("AZURE_OPENAI_API_KEY")
    base_url = _required_env("AZURE_OPENAI_BASE_URL").rstrip("/") + "/"
    deployment = _required_env("AZURE_OPENAI_DEPLOYMENT")
    max_output_tokens = _optional_int_env("AZURE_OPENAI_MAX_OUTPUT_TOKENS", 6000)
    temperature = _optional_float_env("AZURE_OPENAI_TEMPERATURE", 0.2)
    tools = _azure_tools()

    client = OpenAI(api_key=api_key, base_url=base_url)
    prompt = _build_generation_prompt(requirement_text, has_mcp=bool(tools))

    request: dict = {
        "model": deployment,
        "input": prompt,
        "max_output_tokens": max_output_tokens,
        "temperature": temperature,
        "text": {
            "format": {
                "type": "json_schema",
                "name": "development_plan_response",
                "schema": _response_schema(),
                "strict": False,
            }
        },
    }

    if tools:
        request["tools"] = tools

    try:
        response = await asyncio.to_thread(client.responses.create, **request)
    except BadRequestError:
        fallback_request = dict(request)
        fallback_request.pop("text", None)
        fallback_request["input"] = (
            f"{prompt}\n\nReturn only one raw JSON object. Do not wrap it in Markdown."
        )
        try:
            response = await asyncio.to_thread(client.responses.create, **fallback_request)
        except OpenAIError as exc:
            raise LLMGenerationError(f"Azure OpenAI request failed: {exc}") from exc
    except OpenAIError as exc:
        raise LLMGenerationError(f"Azure OpenAI request failed: {exc}") from exc

    raw_text = getattr(response, "output_text", None)
    if not raw_text:
        raise LLMGenerationError("Azure OpenAI returned no output_text.")

    try:
        payload = _extract_json_payload(raw_text)
    except json.JSONDecodeError as exc:
        raise LLMGenerationError("Azure OpenAI did not return valid JSON.") from exc

    try:
        return _normalize_plan_payload(payload, deployment)
    except ValueError as exc:
        raise LLMGenerationError(f"Azure OpenAI JSON did not match the app schema: {exc}") from exc


async def generate_development_plan(requirement_text: str) -> DevelopmentPlanResponse:
    """Generate a development plan with the configured LLM provider."""

    provider = os.getenv("LLM_PROVIDER", "mock").strip().lower()

    if provider == "mock":
        return _mock_development_plan(requirement_text)

    if provider in {"azure", "azure_openai"}:
        return await _generate_with_azure_openai(requirement_text)

    raise LLMConfigurationError(
        f"Unsupported LLM_PROVIDER '{provider}'. Use 'azure_openai' or 'mock'."
    )
