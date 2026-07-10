"use client";

import { useCallback, useEffect, useState } from "react";
import type { GenerationMode, VideoCategory, VisualStyle } from "@rtas/shared";
import { Button, EmptyState } from "@rtas/ui";
import {
  addPromptToHistory,
  deleteSavedWorkflow,
  loadFavoritePrompts,
  loadPromptHistory,
  loadRecentProjects,
  loadSavedWorkflows,
  removeRecentProject,
  saveWorkflow,
  toggleFavoritePrompt,
  type RecentProject,
  type SavedWorkflow,
} from "@/lib/studio-workflow-store";
import { truncatePreview } from "@/lib/studio-form-backup";

type Tab = "recent" | "prompts" | "workflows";

type Props = {
  currentPrompt?: string;
  canSaveWorkflow?: boolean;
  onApplyPrompt: (prompt: string) => void;
  onLoadWorkflow: (workflow: SavedWorkflow) => void;
  onSelectRecent?: (project: RecentProject) => void;
  getWorkflowSnapshot: () => {
    mode: GenerationMode;
    category: VideoCategory | null;
    visualStyle: VisualStyle;
    text: Record<string, string>;
  } | null;
};

export function StudioWorkflowPanel({
  currentPrompt = "",
  canSaveWorkflow = false,
  onApplyPrompt,
  onLoadWorkflow,
  onSelectRecent,
  getWorkflowSnapshot,
}: Props) {
  const [tab, setTab] = useState<Tab>("recent");
  const [prompts, setPrompts] = useState<string[]>([]);
  const [favorites, setFavorites] = useState<string[]>([]);
  const [workflows, setWorkflows] = useState<SavedWorkflow[]>([]);
  const [recent, setRecent] = useState<RecentProject[]>([]);
  const [workflowName, setWorkflowName] = useState("");

  const refresh = useCallback(() => {
    setPrompts(loadPromptHistory());
    setFavorites(loadFavoritePrompts());
    setWorkflows(loadSavedWorkflows());
    setRecent(loadRecentProjects());
  }, []);

  useEffect(() => {
    refresh();
    const onStorage = () => refresh();
    window.addEventListener("storage", onStorage);
    return () => window.removeEventListener("storage", onStorage);
  }, [refresh]);

  const handleFavoriteCurrent = () => {
    if (!currentPrompt.trim()) return;
    addPromptToHistory(currentPrompt);
    toggleFavoritePrompt(currentPrompt);
    refresh();
  };

  const handleSaveWorkflow = () => {
    const snapshot = getWorkflowSnapshot();
    if (!snapshot) return;
    saveWorkflow(workflowName || "My workflow", snapshot);
    setWorkflowName("");
    refresh();
  };

  return (
    <section className="studio-workflow-panel" aria-label="Projects and prompts">
      <div className="studio-workflow-panel__tabs" role="tablist">
        {(
          [
            ["recent", "Recent"],
            ["prompts", "Prompts"],
            ["workflows", "Workflows"],
          ] as const
        ).map(([id, label]) => (
          <button
            key={id}
            type="button"
            role="tab"
            aria-selected={tab === id}
            className={`studio-workflow-panel__tab${tab === id ? " studio-workflow-panel__tab--active" : ""}`}
            onClick={() => setTab(id)}
          >
            {label}
          </button>
        ))}
      </div>

      {tab === "recent" ? (
        <div role="tabpanel" className="studio-workflow-panel__body">
          {recent.length === 0 ? (
            <EmptyState
              icon="🎬"
              title="No recent projects"
              description="Your latest renders will appear here for quick access."
              actionLabel="Start creating →"
              actionHref="/studio"
            />
          ) : (
            <ul className="studio-workflow-panel__list">
              {recent.map((project) => (
                <li key={project.id} className="studio-workflow-panel__item">
                  <button
                    type="button"
                    className="studio-workflow-panel__item-btn"
                    onClick={() => onSelectRecent?.(project)}
                  >
                    <span className="studio-workflow-panel__item-title">{project.title}</span>
                    <span className="studio-workflow-panel__item-meta">
                      {project.status} · {new Date(project.createdAt).toLocaleDateString()}
                    </span>
                  </button>
                  <button
                    type="button"
                    className="studio-workflow-panel__item-remove rtas-ui-focus-ring"
                    aria-label="Remove from recent"
                    onClick={() => {
                      removeRecentProject(project.id);
                      refresh();
                    }}
                  >
                    ×
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>
      ) : null}

      {tab === "prompts" ? (
        <div role="tabpanel" className="studio-workflow-panel__body">
          {currentPrompt.trim() ? (
            <div className="studio-workflow-panel__current">
              <p className="studio-workflow-panel__current-label">Current prompt</p>
              <p className="studio-workflow-panel__current-text">
                {truncatePreview(currentPrompt, 120)}
              </p>
              <Button variant="ghost" size="sm" onClick={handleFavoriteCurrent}>
                ★ Save to favorites
              </Button>
            </div>
          ) : null}

          {favorites.length > 0 ? (
            <>
              <p className="studio-workflow-panel__section-label">Favorites</p>
              <ul className="studio-workflow-panel__chips">
                {favorites.map((prompt) => (
                  <li key={`fav-${prompt}`}>
                    <button
                      type="button"
                      className="studio-workflow-panel__chip studio-workflow-panel__chip--favorite"
                      onClick={() => onApplyPrompt(prompt)}
                      title={prompt}
                    >
                      {truncatePreview(prompt, 48)}
                    </button>
                  </li>
                ))}
              </ul>
            </>
          ) : null}

          <p className="studio-workflow-panel__section-label">History</p>
          {prompts.length === 0 ? (
            <EmptyState
              className="studio-workflow-panel__empty-state"
              icon="📝"
              title="No prompt history"
              description="Prompts from past generations appear here after you create."
              actionLabel="How to write prompts →"
              actionHref="/how-to-use"
            />
          ) : (
            <ul className="studio-workflow-panel__list">
              {prompts.map((prompt) => (
                <li key={prompt} className="studio-workflow-panel__item">
                  <button
                    type="button"
                    className="studio-workflow-panel__item-btn"
                    onClick={() => onApplyPrompt(prompt)}
                    title={prompt}
                  >
                    <span className="studio-workflow-panel__item-title">
                      {truncatePreview(prompt, 64)}
                    </span>
                  </button>
                  <button
                    type="button"
                    className="studio-workflow-panel__item-fav rtas-ui-focus-ring"
                    aria-label="Toggle favorite"
                    onClick={() => {
                      toggleFavoritePrompt(prompt);
                      refresh();
                    }}
                  >
                    ★
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>
      ) : null}

      {tab === "workflows" ? (
        <div role="tabpanel" className="studio-workflow-panel__body">
          {canSaveWorkflow ? (
            <div className="studio-workflow-panel__save">
              <input
                type="text"
                className="rtas-ui-input"
                placeholder="Workflow name…"
                value={workflowName}
                onChange={(e) => setWorkflowName(e.target.value)}
                aria-label="Workflow name"
              />
              <Button variant="lavender" size="sm" onClick={handleSaveWorkflow}>
                Save current setup
              </Button>
            </div>
          ) : null}

          {workflows.length === 0 ? (
            <EmptyState
              icon="📋"
              title="No saved workflows"
              description="Save your mode, category, style, and field values as a reusable preset."
            />
          ) : (
            <ul className="studio-workflow-panel__list">
              {workflows.map((workflow) => (
                <li key={workflow.id} className="studio-workflow-panel__item">
                  <button
                    type="button"
                    className="studio-workflow-panel__item-btn"
                    onClick={() => onLoadWorkflow(workflow)}
                  >
                    <span className="studio-workflow-panel__item-title">{workflow.name}</span>
                    <span className="studio-workflow-panel__item-meta">
                      {workflow.mode} · {workflow.category ?? "—"} ·{" "}
                      {new Date(workflow.savedAt).toLocaleDateString()}
                    </span>
                  </button>
                  <button
                    type="button"
                    className="studio-workflow-panel__item-remove rtas-ui-focus-ring"
                    aria-label="Delete workflow"
                    onClick={() => {
                      deleteSavedWorkflow(workflow.id);
                      refresh();
                    }}
                  >
                    ×
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>
      ) : null}
    </section>
  );
}
