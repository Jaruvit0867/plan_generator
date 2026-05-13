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

TaskStatus = Literal["todo", "in_progress", "done"]
TaskPriority = Literal["low", "medium", "high"]


class UserStory(BaseModel):
    id: str
    title: str
    as_a: str
    i_want: str
    so_that: str
    acceptance_criteria: list[str]
    priority: TaskPriority


class FunctionalRequirementDocument(BaseModel):
    title: str
    summary: str
    functional_requirements: list[str]
    non_functional_requirements: list[str]
    user_stories: list[UserStory]


class BacklogTask(BaseModel):
    id: str
    title: str
    description: str
    status: TaskStatus
    priority: TaskPriority
    estimate_points: int = Field(ge=1, le=13)
    owner_role: str
    tags: list[str]


class DevelopmentPlanResponse(BaseModel):
    frd: FunctionalRequirementDocument
    diagram_xml: str
    tasks: list[BacklogTask]
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
  <diagram id="requirement-plan" name="MVP Architecture">
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

    user_stories = [
        UserStory(
            id="US-001",
            title="Submit raw requirements",
            as_a="product owner",
            i_want="to paste or upload requirement material",
            so_that="the team can generate a usable development plan quickly",
            acceptance_criteria=[
                "The user can submit free-form requirement text.",
                "The user can attach a PDF or DOCX placeholder file.",
                "The system validates that at least one input source exists.",
            ],
            priority="high",
        ),
        UserStory(
            id="US-002",
            title="Review generated FRD",
            as_a="business analyst",
            i_want="to see functional requirements and user stories",
            so_that="I can validate scope before development starts",
            acceptance_criteria=[
                "The FRD is returned as structured JSON.",
                "User stories include acceptance criteria and priority.",
            ],
            priority="high",
        ),
        UserStory(
            id="US-003",
            title="Inspect generated architecture diagram",
            as_a="technical lead",
            i_want="to receive draw.io XML",
            so_that="I can refine the architecture diagram in diagrams.net",
            acceptance_criteria=[
                "The API response contains a draw.io-compatible XML string.",
                "The frontend provides a readable preview and download option.",
            ],
            priority="medium",
        ),
    ]

    tasks = [
        BacklogTask(
            id="TASK-001",
            title="Implement FastAPI generation endpoint",
            description="Create the multipart endpoint and response schema for plan generation.",
            status="done",
            priority="high",
            estimate_points=3,
            owner_role="Backend Developer",
            tags=["api", "fastapi"],
        ),
        BacklogTask(
            id="TASK-002",
            title="Build dashboard input experience",
            description="Create the requirement textarea, file upload, and submit states.",
            status="in_progress",
            priority="high",
            estimate_points=5,
            owner_role="Frontend Developer",
            tags=["nextjs", "tailwind"],
        ),
        BacklogTask(
            id="TASK-003",
            title="Render FRD and user stories",
            description="Display generated requirements in a review-friendly structure.",
            status="todo",
            priority="high",
            estimate_points=5,
            owner_role="Frontend Developer",
            tags=["ui", "json"],
        ),
        BacklogTask(
            id="TASK-004",
            title="Wire OpenAI Responses orchestration",
            description="Replace mock output with a structured OpenAI Responses API call.",
            status="todo",
            priority="medium",
            estimate_points=8,
            owner_role="AI Engineer",
            tags=["llm", "responses-api"],
        ),
        BacklogTask(
            id="TASK-005",
            title="Connect Draw.io MCP server",
            description="Allow the LLM to call the diagram generation MCP tool and persist returned XML.",
            status="todo",
            priority="medium",
            estimate_points=8,
            owner_role="AI Engineer",
            tags=["mcp", "diagram"],
        ),
    ]

    return DevelopmentPlanResponse(
        frd=FunctionalRequirementDocument(
            title="Requirement-to-Development Plan Generator MVP",
            summary=(
                "Mock analysis generated from the submitted requirement. "
                f"Input snapshot: {summary}"
            ),
            functional_requirements=[
                "Accept raw requirement text from the dashboard.",
                "Accept optional PDF or DOCX uploads for future extraction.",
                "Generate an FRD, user stories, a system diagram XML payload, and backlog tasks.",
                "Return one stable JSON response that the frontend can render immediately.",
            ],
            non_functional_requirements=[
                "Keep orchestration behind the FastAPI backend to protect API keys.",
                "Prefer deterministic schemas for predictable frontend rendering.",
                "Keep the MVP deployable as two simple services for hackathon speed.",
            ],
            user_stories=user_stories,
        ),
        diagram_xml=_dummy_drawio_xml(),
        tasks=tasks,
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

Generate a build-ready MVP plan from the raw requirement below.

Return JSON only. The response must include:
- frd.title
- frd.summary
- frd.functional_requirements
- frd.non_functional_requirements
- frd.user_stories with id, title, as_a, i_want, so_that, acceptance_criteria, priority
- diagram_xml as a draw.io / diagrams.net mxfile XML string
- tasks with id, title, description, status, priority, estimate_points, owner_role, tags
- metadata as an object

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
- Use task status values only: todo, in_progress, done.
- Use priority values only: low, medium, high.
- Keep estimates between 1 and 13 points.
- Make the output useful for a 2-day hackathon team.
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
