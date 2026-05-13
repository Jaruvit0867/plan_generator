"use client";

import { FormEvent, useState } from "react";
import {
  ArrowRight,
  AlertTriangle,
  Calendar,
  ClipboardList,
  Code2,
  Download,
  ExternalLink,
  FileUp,
  Layers,
  Loader2,
  Map,
  Network,
  Shield,
  Sparkles,
  Target,
  Zap,
} from "lucide-react";
import clsx from "clsx";
import { deflateRaw } from "pako";

type FeaturePriority = "must_have" | "should_have" | "nice_to_have";
type RiskCategory = "business" | "technical" | "timeline" | "integration";
type TabKey = "frd" | "diagram";

type Feature = {
  name: string;
  description: string;
  module: string;
  priority: FeaturePriority;
};

type TimelinePhase = {
  phase: string;
  duration: string;
  deliverables: string[];
};

type Risk = {
  risk: string;
  category: RiskCategory;
  mitigation: string;
};

type Frd = {
  problem_summary: string;
  proposed_solution: string;
  scope_of_work: string;
  user_flow: string;
  initial_architecture: string;
  feature_breakdown: Feature[];
  timeline_estimation: TimelinePhase[];
  risk_analysis: Risk[];
};

type GeneratePlanResponse = {
  frd: Frd;
  diagram_xml: string;
  metadata: Record<string, string>;
};

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

const tabs: Array<{ key: TabKey; label: string; icon: typeof ClipboardList }> = [
  { key: "frd", label: "Proposal", icon: ClipboardList },
  { key: "diagram", label: "System Diagram", icon: Network },
];

export default function Home() {
  const [requirementText, setRequirementText] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [activeTab, setActiveTab] = useState<TabKey>("frd");
  const [result, setResult] = useState<GeneratePlanResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);

    if (!requirementText.trim() && !file) {
      setError("Add requirement text or attach a file before generating.");
      return;
    }

    const formData = new FormData();
    if (requirementText.trim()) {
      formData.append("requirement_text", requirementText.trim());
    }
    if (file) {
      formData.append("file", file);
    }

    setIsLoading(true);
    try {
      const response = await fetch(`${API_BASE_URL}/api/generate-plan`, {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        const body = await response.json().catch(() => null);
        throw new Error(body?.detail ?? `Request failed with ${response.status}`);
      }

      const payload = (await response.json()) as GeneratePlanResponse;
      setResult(payload);
      setActiveTab("frd");
    } catch (requestError) {
      setError(
        requestError instanceof Error
          ? requestError.message
          : "Unable to generate the plan.",
      );
    } finally {
      setIsLoading(false);
    }
  }

  function downloadDiagramXml() {
    if (!result?.diagram_xml) {
      return;
    }

    const blob = new Blob([result.diagram_xml], {
      type: "application/xml;charset=utf-8",
    });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "generated-system-diagram.drawio";
    link.click();
    URL.revokeObjectURL(url);
  }

  function openDiagramInDrawio() {
    if (!result?.diagram_xml) {
      return;
    }

    const url = buildDrawioEditUrl(result.diagram_xml);
    window.open(url, "_blank", "noopener,noreferrer");
  }

  return (
    <main className="min-h-screen px-4 py-5 sm:px-6 lg:px-8">
      <div className="mx-auto flex max-w-7xl flex-col gap-5">
        <header className="flex flex-col gap-4 rounded-lg border border-slate-200 bg-white/85 px-5 py-4 shadow-soft backdrop-blur md:flex-row md:items-center md:justify-between">
          <div>
            <div className="flex items-center gap-2 text-sm font-semibold text-ocean">
              <Sparkles className="h-4 w-4" aria-hidden="true" />
              Requirement-to-Development Plan Generator
            </div>
            <h1 className="mt-2 text-2xl font-semibold tracking-normal text-ink sm:text-3xl">
              Convert rough requirements into a build-ready MVP plan.
            </h1>
          </div>
          <div className="grid grid-cols-2 gap-2 text-center text-xs text-slate-600 sm:min-w-56">
            <Metric
              label="Provider"
              value={result?.metadata.provider ?? "Azure OpenAI"}
            />
            <Metric
              label="Model"
              value={
                result?.metadata.model ??
                result?.metadata.recommended_model ??
                "gpt-4.1"
              }
            />
          </div>
        </header>

        <div className="grid gap-5 lg:grid-cols-[minmax(320px,0.8fr)_minmax(0,1.2fr)]">
          <section className="rounded-lg border border-slate-200 bg-white p-4 shadow-soft">
            <div className="mb-4 flex items-center justify-between gap-3">
              <div>
                <h2 className="text-base font-semibold text-ink">
                  Requirement Input
                </h2>
                <p className="mt-1 text-sm text-slate-500">
                  Paste product notes, upload a brief, then generate the plan.
                </p>
              </div>
              <Code2 className="h-5 w-5 text-mint" aria-hidden="true" />
            </div>

            <form onSubmit={handleSubmit} className="flex flex-col gap-4">
              <label className="flex flex-col gap-2 text-sm font-medium text-slate-700">
                Raw requirement text
                <textarea
                  value={requirementText}
                  onChange={(event) => setRequirementText(event.target.value)}
                  rows={14}
                  className="min-h-72 resize-y rounded-md border border-slate-200 bg-panel p-3 text-sm leading-6 text-slate-800 outline-none transition focus:border-ocean focus:ring-4 focus:ring-blue-100"
                  placeholder="Paste stakeholder notes, project brief, acceptance criteria, or meeting notes..."
                />
              </label>

              <label className="group flex cursor-pointer flex-col items-center justify-center gap-2 rounded-md border border-dashed border-slate-300 bg-slate-50 px-4 py-5 text-center transition hover:border-ocean hover:bg-blue-50">
                <FileUp
                  className="h-6 w-6 text-slate-500 group-hover:text-ocean"
                  aria-hidden="true"
                />
                <span className="text-sm font-medium text-slate-700">
                  {file ? file.name : "Attach PDF or DOCX"}
                </span>
                <span className="text-xs text-slate-500">
                  Optional source document for the planning request.
                </span>
                <input
                  type="file"
                  accept=".pdf,.doc,.docx"
                  className="sr-only"
                  onChange={(event) => setFile(event.target.files?.[0] ?? null)}
                />
              </label>

              {error ? (
                <div className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
                  {error}
                </div>
              ) : null}

              <button
                type="submit"
                disabled={isLoading}
                className="inline-flex h-11 items-center justify-center gap-2 rounded-md bg-ink px-4 text-sm font-semibold text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-70"
              >
                {isLoading ? (
                  <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
                ) : (
                  <ArrowRight className="h-4 w-4" aria-hidden="true" />
                )}
                {isLoading ? "Generating plan" : "Generate development plan"}
              </button>
            </form>
          </section>

          <section className="rounded-lg border border-slate-200 bg-white p-4 shadow-soft">
            <div className="flex flex-col gap-3 border-b border-slate-200 pb-4 md:flex-row md:items-center md:justify-between">
              <div>
                <h2 className="text-base font-semibold text-ink">
                  Generated Outputs
                </h2>
                <p className="mt-1 text-sm text-slate-500">
                  Azure OpenAI returns structured outputs for planning and diagramming.
                </p>
              </div>
              <div className="flex rounded-md bg-slate-100 p-1">
                {tabs.map((tab) => {
                  const Icon = tab.icon;
                  return (
                    <button
                      key={tab.key}
                      type="button"
                      onClick={() => setActiveTab(tab.key)}
                      className={clsx(
                        "inline-flex h-9 items-center gap-2 rounded px-3 text-sm font-medium transition",
                        activeTab === tab.key
                          ? "bg-white text-ink shadow-sm"
                          : "text-slate-500 hover:text-slate-800",
                      )}
                    >
                      <Icon className="h-4 w-4" aria-hidden="true" />
                      <span className="hidden sm:inline">{tab.label}</span>
                    </button>
                  );
                })}
              </div>
            </div>

            <div className="min-h-[640px] pt-4">
              {!result && !isLoading ? <EmptyState /> : null}
              {isLoading ? <LoadingState /> : null}
              {result && !isLoading ? (
                <>
                  {activeTab === "frd" ? <FrdView frd={result.frd} /> : null}
                  {activeTab === "diagram" ? (
                    <DiagramView
                      xml={result.diagram_xml}
                      onDownload={downloadDiagramXml}
                      onOpenInDrawio={openDiagramInDrawio}
                    />
                  ) : null}
                </>
              ) : null}
            </div>
          </section>
        </div>
      </div>
    </main>
  );
}

/* ─── Shared helpers ─── */

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border border-slate-200 bg-slate-50 px-3 py-2">
      <div className="text-[11px] uppercase tracking-wide text-slate-400">
        {label}
      </div>
      <div className="mt-1 truncate font-semibold text-ink">{value}</div>
    </div>
  );
}

function EmptyState() {
  return (
    <div className="flex h-full min-h-[560px] flex-col items-center justify-center rounded-lg border border-dashed border-slate-300 bg-slate-50 px-6 text-center">
      <div className="flex h-12 w-12 items-center justify-center rounded-md bg-white shadow-sm">
        <ClipboardList className="h-6 w-6 text-ocean" aria-hidden="true" />
      </div>
      <h3 className="mt-4 text-lg font-semibold text-ink">
        Ready for the first generated plan
      </h3>
      <p className="mt-2 max-w-md text-sm leading-6 text-slate-500">
        Add a requirement brief on the left, then generate a proposal and system
        diagram from the connected backend.
      </p>
    </div>
  );
}

function LoadingState() {
  return (
    <div className="flex h-full min-h-[560px] flex-col items-center justify-center rounded-lg bg-slate-50 text-center">
      <Loader2 className="h-9 w-9 animate-spin text-ocean" aria-hidden="true" />
      <h3 className="mt-4 text-lg font-semibold text-ink">
        Generating with Azure OpenAI
      </h3>
      <p className="mt-2 text-sm text-slate-500">
        Shaping proposal, draw.io XML, and risk analysis.
      </p>
    </div>
  );
}

/* ─── Section card ─── */

function SectionCard({
  icon: Icon,
  title,
  children,
}: {
  icon: typeof ClipboardList;
  title: string;
  children: React.ReactNode;
}) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-4">
      <div className="flex items-center gap-2 text-sm font-semibold text-ink">
        <Icon className="h-4 w-4 text-ocean" aria-hidden="true" />
        {title}
      </div>
      <div className="mt-3">{children}</div>
    </div>
  );
}

/* ─── FRD view ─── */

function FrdView({ frd }: { frd: Frd }) {
  const moduleGroups = frd.feature_breakdown.reduce<
    Record<string, Feature[]>
  >((groups, feature) => {
    (groups[feature.module] ??= []).push(feature);
    return groups;
  }, {});

  return (
    <div className="grid gap-4">
      <SectionCard icon={Target} title="Problem Summary">
        <p className="text-sm leading-7 text-slate-600">
          {frd.problem_summary}
        </p>
      </SectionCard>

      <SectionCard icon={Zap} title="Proposed Solution">
        <p className="text-sm leading-7 text-slate-600">
          {frd.proposed_solution}
        </p>
      </SectionCard>

      <SectionCard icon={Layers} title="Scope of Work">
        <p className="whitespace-pre-line text-sm leading-7 text-slate-600">
          {frd.scope_of_work}
        </p>
      </SectionCard>

      <SectionCard icon={Map} title="User Flow">
        <p className="whitespace-pre-line text-sm leading-7 text-slate-600">
          {frd.user_flow}
        </p>
      </SectionCard>

      <SectionCard icon={Network} title="Initial Architecture">
        <p className="whitespace-pre-line text-sm leading-7 text-slate-600">
          {frd.initial_architecture}
        </p>
      </SectionCard>

      <SectionCard icon={ClipboardList} title="Feature Breakdown">
        <div className="grid gap-4">
          {Object.entries(moduleGroups).map(([module, features]) => (
            <div key={module}>
              <h4 className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-400">
                {module}
              </h4>
              <div className="grid gap-2">
                {features.map((feature) => (
                  <div
                    key={feature.name}
                    className="flex items-start justify-between gap-3 rounded-md border border-slate-100 bg-slate-50 px-3 py-2"
                  >
                    <div>
                      <div className="text-sm font-semibold text-ink">
                        {feature.name}
                      </div>
                      <div className="mt-1 text-sm text-slate-600">
                        {feature.description}
                      </div>
                    </div>
                    <FeaturePriorityBadge priority={feature.priority} />
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      </SectionCard>

      <SectionCard icon={Calendar} title="Timeline Estimation">
        <div className="grid gap-3">
          {frd.timeline_estimation.map((phase, index) => (
            <div
              key={phase.phase}
              className="flex gap-4 rounded-md border border-slate-100 bg-slate-50 p-3"
            >
              <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-ocean text-sm font-bold text-white">
                {index + 1}
              </div>
              <div>
                <div className="text-sm font-semibold text-ink">
                  {phase.phase}
                </div>
                <div className="mt-1 text-xs font-medium text-ocean">
                  {phase.duration}
                </div>
                <ul className="mt-2 grid gap-1">
                  {phase.deliverables.map((deliverable) => (
                    <li
                      key={deliverable}
                      className="flex gap-2 text-sm text-slate-600"
                    >
                      <span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-mint" />
                      {deliverable}
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          ))}
        </div>
      </SectionCard>

      <SectionCard icon={Shield} title="Risk Analysis">
        <div className="grid gap-2">
          {frd.risk_analysis.map((item, index) => (
            <div
              key={index}
              className="flex items-start gap-3 rounded-md border border-slate-100 bg-slate-50 p-3"
            >
              <AlertTriangle
                className="mt-0.5 h-4 w-4 shrink-0 text-amberline"
                aria-hidden="true"
              />
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-semibold text-ink">
                    {item.risk}
                  </span>
                  <RiskCategoryBadge category={item.category} />
                </div>
                <div className="mt-1 text-sm text-slate-600">
                  <strong>Mitigation:</strong> {item.mitigation}
                </div>
              </div>
            </div>
          ))}
        </div>
      </SectionCard>
    </div>
  );
}

function FeaturePriorityBadge({ priority }: { priority: FeaturePriority }) {
  const label = priority.replace("_", " ");
  return (
    <span
      className={clsx(
        "shrink-0 rounded px-2 py-1 text-xs font-semibold capitalize",
        priority === "must_have" && "bg-red-50 text-red-700",
        priority === "should_have" && "bg-amber-50 text-amber-700",
        priority === "nice_to_have" && "bg-emerald-50 text-emerald-700",
      )}
    >
      {label}
    </span>
  );
}

function RiskCategoryBadge({ category }: { category: RiskCategory }) {
  return (
    <span
      className={clsx(
        "rounded px-2 py-0.5 text-xs font-semibold capitalize",
        category === "business" && "bg-blue-50 text-blue-700",
        category === "technical" && "bg-purple-50 text-purple-700",
        category === "timeline" && "bg-amber-50 text-amber-700",
        category === "integration" && "bg-teal-50 text-teal-700",
      )}
    >
      {category}
    </span>
  );
}

/* ─── Diagram view ─── */

function DiagramView({
  xml,
  onDownload,
  onOpenInDrawio,
}: {
  xml: string;
  onDownload: () => void;
  onOpenInDrawio: () => void;
}) {
  return (
    <div className="grid gap-4">
      <div className="grid gap-3 rounded-lg border border-slate-200 bg-panel p-4 md:grid-cols-[1fr_auto] md:items-center">
        <div>
          <h3 className="text-lg font-semibold text-ink">
            Draw.io XML Payload
          </h3>
          <p className="mt-1 text-sm leading-6 text-slate-600">
            Diagram XML is generated for diagrams.net import and download.
          </p>
        </div>
        <div className="flex flex-col gap-2 sm:flex-row md:justify-end">
          <button
            type="button"
            onClick={onOpenInDrawio}
            className="inline-flex h-10 items-center justify-center gap-2 rounded-md bg-ink px-3 text-sm font-semibold text-white transition hover:bg-slate-800"
          >
            <ExternalLink className="h-4 w-4" aria-hidden="true" />
            Open in Draw.io
          </button>
          <button
            type="button"
            onClick={onDownload}
            className="inline-flex h-10 items-center justify-center gap-2 rounded-md border border-slate-300 bg-white px-3 text-sm font-semibold text-ink transition hover:border-ocean hover:text-ocean"
          >
            <Download className="h-4 w-4" aria-hidden="true" />
            Download XML
          </button>
        </div>
      </div>
      <pre className="max-h-[520px] overflow-auto rounded-lg border border-slate-200 bg-slate-950 p-4 text-xs leading-5 text-slate-100">
        <code>{xml}</code>
      </pre>
    </div>
  );
}

/* ─── Draw.io URL builder ─── */

function buildDrawioEditUrl(xml: string) {
  const encodedXml = encodeURIComponent(xml);
  const compressed = deflateRaw(encodedXml);
  const binary = Array.from(compressed, (byte) =>
    String.fromCharCode(byte),
  ).join("");
  const createPayload = {
    type: "xml",
    compressed: true,
    data: btoa(binary),
  };

  return `https://app.diagrams.net/?pv=0&grid=0#create=${encodeURIComponent(
    JSON.stringify(createPayload),
  )}`;
}
