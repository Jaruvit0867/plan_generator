from __future__ import annotations

import os
from typing import Annotated

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from services.llm_service import (
    DevelopmentPlanResponse,
    LLMConfigurationError,
    LLMGenerationError,
    generate_development_plan,
)


DEFAULT_CORS_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:3001",
    "http://127.0.0.1:3001",
]


def get_cors_origins() -> list[str]:
    configured_origins = os.getenv("CORS_ORIGINS", "").strip()
    if not configured_origins:
        return DEFAULT_CORS_ORIGINS

    return [
        origin.strip()
        for origin in configured_origins.split(",")
        if origin.strip()
    ]


app = FastAPI(
    title="Requirement-to-Development Plan Generator API",
    description="FastAPI backend for generating FRDs, draw.io XML diagrams, and task backlogs.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/generate-plan", response_model=DevelopmentPlanResponse)
async def generate_plan(
    requirement_text: Annotated[str | None, Form()] = None,
    file: Annotated[UploadFile | None, File()] = None,
) -> DevelopmentPlanResponse:
    """Generate a development plan from raw text and an optional upload.

    PDF/DOCX parsing is intentionally scaffolded as a placeholder for the MVP.
    The uploaded file is read to validate the multipart path without performing
    production extraction yet.
    """

    text_parts: list[str] = []

    if requirement_text and requirement_text.strip():
        text_parts.append(requirement_text.strip())

    if file is not None:
        file_bytes = await file.read()
        file_summary = (
            f"Uploaded file placeholder: {file.filename or 'unnamed file'} "
            f"({len(file_bytes)} bytes, content extraction pending)."
        )
        text_parts.append(file_summary)

    if not text_parts:
        raise HTTPException(
            status_code=400,
            detail="Provide requirement_text or upload a PDF/DOCX file.",
        )

    combined_text = "\n\n".join(text_parts)
    try:
        return await generate_development_plan(combined_text)
    except LLMConfigurationError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except LLMGenerationError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
