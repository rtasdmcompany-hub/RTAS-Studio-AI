"use client";

import dynamic from "next/dynamic";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  CATEGORY_META,
  creditsForDuration,
  FREE_TRIAL_DURATION_SECONDS,
  buildSegmentDirectionPrompt,
  computeSegmentPlan,
  estimateProcessingWindow,
  filenameFromVideoUrl,
  isPaidTier,
  shouldUseLongVideoPipeline,
  type GeneratedVideo,
  type GenerationMode,
  type VideoCategory,
  type VisualStyle,
} from "@rtas/shared";
import { useStudioProfile } from "@/context/StudioProfileContext";
import { GENERATION_LAST_STAGE_INDEX } from "@/lib/generation-progress-stages";
import {
  BACKEND_CONNECTION_ERROR,
  fetchBackendHealthStatus,
  type FalGuardStatus,
  getFastApiBase,
  isBackendConnectionError,
  isFalAuthError,
  isFalCreditError,
  isReplicateAuthError,
  isReplicateCreditError,
  isPipelineFailureError,
  FAL_AUTH_ERROR,
  FAL_AUTH_HINT,
  FAL_CREDIT_ERROR,
  FAL_CREDIT_HINT,
  REPLICATE_AUTH_ERROR,
  REPLICATE_AUTH_HINT,
  REPLICATE_CREDIT_ERROR,
  REPLICATE_CREDIT_HINT,
  runBackendGeneration,
  type GenerateRequestBody,
} from "@/lib/backend-client";
import {
  FREE_TRIAL_ABUSE_MESSAGE,
  hasPremiumAccess,
  paywallReasonMessage,
  shouldConfirmEarlyResubscribe,
  shouldShowPaywall,
} from "@/lib/monetization";
import { getDeviceFingerprint } from "@/lib/device-fingerprint";
import {
  loadVideosForUser,
  saveProfile,
  saveVideosForUser,
} from "@/lib/store";
import { useUserVideoGallery } from "@/hooks/useUserVideoGallery";
import {
  mergeServerAssetsWithLocal,
  userVideoAssetToGeneratedVideo,
} from "@/lib/gallery-display";
import { resolveVideoPlaybackUrl } from "@/lib/video-playback";
import {
  CUSTOMER_CLOUD_MAINTENANCE,
  CUSTOMER_CONNECTION_ISSUE,
  CUSTOMER_GENERIC_FAILURE,
  CUSTOMER_PREVIEW_READY,
  CUSTOMER_STUDIO_BUSY,
  isCloudCapacityMessage,
  isOwnerDiagnosticMessage,
  isStudioOwner,
  noticeForOwnerOrCustomer,
  type CustomerNotice,
} from "@/lib/customer-messages";
import {
  buildGeneratePayload,
  buildMissingFieldsMessage,
  buildVideoTitle,
  buildVisualSceneAutoFill,
  collectRequiredFieldErrors,
  createInitialFormState,
  DURATION_PROMPT_GROUP_ID,
  extractCreativePrompt,
  getWizardGroupAtStep,
  getWizardStepCount,
  pruneFormToVisible,
  scrollToFirstFieldError,
  syncIdentityPipeline,
  validateWizardGroup,
  VIDEO_TITLE_FIELD_ID,
  WIZARD_FIRST_GROUP_STEP,
  WIZARD_SETUP_STEP,
  type FieldValidationError,
  type StudioFormState,
} from "@/lib/studio-form";
import { FacialConsistencyShield } from "./cinematic/FacialConsistencyShield";
import { FacialReferenceHero } from "./cinematic/FacialReferenceHero";
import { StudioDiagnosticsHud } from "./cinematic/StudioDiagnosticsHud";
import { StudioScreenRail, type StudioScreen } from "./cinematic/StudioScreenRail";
import { StudioVideoCarousel } from "./cinematic/StudioVideoCarousel";
import { startCheckout, type CheckoutPlan } from "@/lib/checkout-client";
import { BackendConnectionNotice } from "./BackendConnectionNotice";
import { CategoryWizardGroup } from "./CategoryFieldsSection";
import {
  getMaxVideoDurationSeconds,
  validateDurationSelection,
} from "@/lib/duration-limits";
import { notifyVideoReady } from "@/lib/video-notify";
import {
  AutosaveIndicator,
  DraftRestoreBanner,
  GenerationPipelinePanel,
  StudioWorkflowPanel,
} from "@/components/studio/pipeline";
import { StudioToast, type StudioToastState } from "@/components/studio/StudioToast";
import { StudioShortcutsHint } from "@/components/studio/StudioShortcutsHint";
import { StudioSkeleton } from "@/components/ui/skeletons";
import { Button, EmptyState } from "@rtas/ui";
import { VideoPlayer } from "./VideoPlayer";
import { VisualStyleSelector } from "./VisualStyleSelector";
import { useStudioFormBackup } from "@/hooks/useStudioFormBackup";
import { useStudioKeyboardShortcuts } from "@/hooks/useStudioKeyboardShortcuts";
import {
  resumeStudioDraftSave,
  saveStudioDraft,
  suppressStudioDraftSave,
} from "@/lib/studio-form-backup";
import {
  addPromptToHistory,
  upsertRecentProject,
  type SavedWorkflow,
} from "@/lib/studio-workflow-store";

const PremiumPaywallModal = dynamic(
  () => import("./PremiumPaywallModal").then((mod) => mod.PremiumPaywallModal),
  { ssr: false },
);
const ShareVideoModal = dynamic(
  () => import("./ShareVideoModal").then((mod) => mod.ShareVideoModal),
  { ssr: false },
);
const DurationLimitModal = dynamic(
  () => import("./DurationLimitModal").then((mod) => mod.DurationLimitModal),
  { ssr: false },
);
const EarlyResubscribeModal = dynamic(
  () => import("./EarlyResubscribeModal").then((mod) => mod.EarlyResubscribeModal),
  { ssr: false },
);
const GenerationStartedModal = dynamic(
  () => import("./GenerationStartedModal").then((mod) => mod.GenerationStartedModal),
  { ssr: false },
);

type GenUiState = {
  active: boolean;
  percent: number;
  message: string;
  stageIndex: number;
};

type GenPhase = "idle" | "running" | "error" | "success" | "cancelled";

type GenerateAttemptSnapshot = {
  form: StudioFormState;
  mode: GenerationMode;
  category: VideoCategory;
  visualStyle: VisualStyle;
  durationSeconds: number;
};

type PipelineDiagnostic = {
  error: string;
  details: string;
  code?: string;
  at: string;
};

const IDLE_GEN: GenUiState = {
  active: false,
  percent: 0,
  message: "",
  stageIndex: 0,
};

/** Minimum generated clips before Compile Video is enabled (~10–15 × 15s → 5 min). */
const MIN_CLIPS_TO_COMPILE = 10;

type CompileUiState = {
  active: boolean;
  percent: number;
  message: string;
};

/** Legacy provider-auth banners cleared when backend health confirms Fal is ready. */
const STALE_PROVIDER_AUTH_MESSAGES = new Set([
  FAL_AUTH_ERROR,
  FAL_CREDIT_ERROR,
  REPLICATE_AUTH_ERROR,
  REPLICATE_CREDIT_ERROR,
]);

function buildGenerationPatienceMessage(
  durationSeconds: number,
  segmentCount = 1,
  simulationMode = false
): string {
  const eta = estimateProcessingWindow(durationSeconds, {
    simulationMode,
    segmentCount,
  });
  if (durationSeconds >= 60 || segmentCount > 1) {
    return `This is a longer video, so it may take more time than usual (about ${eta.minMinutes}–${eta.maxMinutes} minutes). You can leave this window — we'll email you and notify you when your video is ready.`;
  }
  return "You can leave this window and do other work — we'll email you and send a notification when your video is ready.";
}

export function StudioClient() {
  const {
    profile,
    setProfile,
    activatePremium,
    syncFromServer,
    studioMetrics,
    generationLimitReached,
    generationLimitMessage,
  } = useStudioProfile();
  const [videos, setVideos] = useState<GeneratedVideo[]>([]);
  const serverGallery = useUserVideoGallery(profile?.id, {
    pageSize: 12,
    pollActive: true,
  });
  const carouselItems = useMemo(
    () => mergeServerAssetsWithLocal(serverGallery.items, videos),
    [serverGallery.items, videos]
  );
  const [mode, setMode] = useState<GenerationMode | null>(null);
  const [category, setCategory] = useState<VideoCategory | null>(null);
  const [visualStyle, setVisualStyle] = useState<VisualStyle | null>(null);
  const [form, setForm] = useState<StudioFormState>(() => createInitialFormState());
  const [setupPhase, setSetupPhase] = useState<"mode" | "category" | "style" | "title">(
    "mode"
  );
  const setupCategoryRef = useRef<HTMLDivElement>(null);
  const setupStyleRef = useRef<HTMLDivElement>(null);
  const setupTitleRef = useRef<HTMLDivElement>(null);
  const [processing, setProcessing] = useState(false);
  const [genPhase, setGenPhase] = useState<GenPhase>("idle");
  const [genUi, setGenUi] = useState<GenUiState>(IDLE_GEN);
  const [statusText, setStatusText] = useState("Ready to create");
  const [activeVideo, setActiveVideo] = useState<GeneratedVideo | null>(null);
  const [shareVideo, setShareVideo] = useState<GeneratedVideo | null>(null);
  const [showPaywall, setShowPaywall] = useState(false);
  const [paywallMessage, setPaywallMessage] = useState<string | undefined>();
  const [pendingCheckoutPlan, setPendingCheckoutPlan] =
    useState<CheckoutPlan>("standard");
  const [showDurationLimit, setShowDurationLimit] = useState(false);
  const [durationLimitMessage, setDurationLimitMessage] = useState("");
  const [durationLimitMax, setDurationLimitMax] = useState<number | undefined>();
  const [showEarlyResubscribe, setShowEarlyResubscribe] = useState(false);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const [formNotice, setFormNotice] = useState<string | null>(null);
  const [wizardStep, setWizardStep] = useState(0);
  const [formSessionKey, setFormSessionKey] = useState(0);
  const [studioScreen, setStudioScreen] = useState<StudioScreen>("create");
  const [compileUi, setCompileUi] = useState<CompileUiState>({
    active: false,
    percent: 0,
    message: "",
  });
  const [backendOutputClipCount, setBackendOutputClipCount] = useState(0);
  const [compileStatusReady, setCompileStatusReady] = useState(false);
  const [backendOnline, setBackendOnline] = useState<boolean | null>(null);
  const [falGuard, setFalGuard] = useState<FalGuardStatus | null>(null);
  const [connectionError, setConnectionError] = useState<string | null>(null);
  const [studioDebugOpen, setStudioDebugOpen] = useState(false);
  const [pipelineDiagnostic, setPipelineDiagnostic] =
    useState<PipelineDiagnostic | null>(null);
  const [connectionNoticeTitle, setConnectionNoticeTitle] = useState(
    "API connection issue"
  );
  const [connectionNoticeHint, setConnectionNoticeHint] = useState<
    string | null | undefined
  >(undefined);
  const [studioToast, setStudioToast] = useState<StudioToastState | null>(null);
  const [retryLoading, setRetryLoading] = useState(false);
  const previewPanelRef = useRef<HTMLDivElement>(null);
  const progressRef = useRef<HTMLDivElement>(null);
  const genPhaseRef = useRef<GenPhase>("idle");
  const durationPromptAutoFillStepRef = useRef<number | null>(null);
  const generationStartedAtRef = useRef<number | null>(null);
  const lastGenerateAttemptRef = useRef<GenerateAttemptSnapshot | null>(null);
  const generationAbortRef = useRef<AbortController | null>(null);
  const toastIdRef = useRef(0);
  const handleRetryGenerationRef = useRef<(() => Promise<void>) | null>(null);
  const onGenerateClickRef = useRef<(() => void) | null>(null);
  const [showGenStartedModal, setShowGenStartedModal] = useState(false);

  const scrollToProgress = useCallback(() => {
    const target = progressRef.current ?? previewPanelRef.current;
    target?.scrollIntoView({
      behavior: "smooth",
      block: "center",
    });
  }, []);

  const durationSeconds = useMemo(() => {
    const d = parseInt(form.text.duration ?? "", 10);
    return Number.isFinite(d) && d > 0 ? d : 30;
  }, [form.text.duration]);

  const setupComplete = Boolean(
    mode &&
      category &&
      visualStyle &&
      (form.text[VIDEO_TITLE_FIELD_ID]?.trim()?.length ?? 0) > 0
  );

  const scrollToSetupRef = useCallback((ref: React.RefObject<HTMLDivElement | null>) => {
    window.setTimeout(() => {
      ref.current?.scrollIntoView({ behavior: "smooth", block: "nearest" });
    }, 100);
  }, []);

  const creditsNeeded = creditsForDuration(durationSeconds);

  const maxDurationSeconds = useMemo(() => {
    if (!profile) return 30;
    return getMaxVideoDurationSeconds(profile);
  }, [profile]);

  const applyBackendHealth = useCallback((status: Awaited<ReturnType<typeof fetchBackendHealthStatus>>) => {
    setBackendOnline(status.online);
    setFalGuard(status.falGuard);
    if (!status.online) return;

    const guard = status.falGuard;
    const ownerView = isStudioOwner(profile);
    const falReady =
      status.falConfigured &&
      status.falValid !== false &&
      !guard?.billingBlocked &&
      (guard?.liveCallsAllowed ?? true);

    if (ownerView && guard?.billingBlocked && guard.blockedReason) {
      if (!processing && genPhase !== "running") {
        setConnectionNoticeTitle("Fal.ai paused (owner)");
        setConnectionNoticeHint(FAL_CREDIT_HINT);
        setConnectionError(guard.blockedReason);
      }
      return;
    }

    if (ownerView && status.falConfigured && status.falValid === false && status.falError) {
      if (!processing && genPhase !== "running") {
        setConnectionNoticeTitle("Fal.ai API key");
        setConnectionNoticeHint(FAL_AUTH_HINT);
        setConnectionError(status.falError);
      }
      return;
    }

    if (falReady || !ownerView) {
      setConnectionError(null);
      setConnectionNoticeHint(undefined);
      if (!processing && genPhase === "idle") {
        setStatusText((prev) =>
          STALE_PROVIDER_AUTH_MESSAGES.has(prev) ? "Ready to create" : prev
        );
      }
    } else if (ownerView) {
      setConnectionError((prev) =>
        prev && STALE_PROVIDER_AUTH_MESSAGES.has(prev) ? null : prev
      );
      setConnectionNoticeHint(undefined);
    }
  }, [processing, genPhase, profile]);

  useEffect(() => {
    if (!isStudioOwner(profile)) {
      setConnectionError(null);
      setConnectionNoticeHint(undefined);
    }
  }, [profile?.id, profile?.email]);

  useEffect(() => {
    const poll = () => {
      if (document.visibilityState === "hidden") return;
      void fetchBackendHealthStatus().then(applyBackendHealth);
    };
    poll();
    const interval = window.setInterval(poll, 30_000);
    const onFocus = () => poll();
    const onVisibility = () => {
      if (document.visibilityState === "visible") poll();
    };
    window.addEventListener("focus", onFocus);
    document.addEventListener("visibilitychange", onVisibility);
    return () => {
      window.clearInterval(interval);
      window.removeEventListener("focus", onFocus);
      document.removeEventListener("visibilitychange", onVisibility);
    };
  }, [applyBackendHealth]);

  useEffect(() => {
    if (!processing || !genUi.active) return;
    const timer = window.setTimeout(() => scrollToProgress(), 100);
    return () => window.clearTimeout(timer);
  }, [processing, genUi.active, scrollToProgress]);

  useEffect(() => {
    if (!profile?.id) return;
    setVideos(loadVideosForUser(profile.id));
  }, [profile?.id]);

  const refreshCompileStatus = useCallback(async (): Promise<number> => {
    try {
      const res = await fetch("/api/compile", { cache: "no-store" });
      const data = (await res.json().catch(() => ({}))) as {
        clipCount?: number;
        canCompile?: boolean;
      };
      const count =
        typeof data.clipCount === "number" ? data.clipCount : 0;
      setBackendOutputClipCount(count);
      setCompileStatusReady(Boolean(data.canCompile));
      return count;
    } catch {
      setBackendOutputClipCount(0);
      setCompileStatusReady(false);
      return 0;
    }
  }, []);

  useEffect(() => {
    const poll = () => {
      if (document.visibilityState === "hidden") return;
      void refreshCompileStatus();
    };
    poll();
    const interval = window.setInterval(poll, 12_000);
    const onFocus = () => poll();
    const onVisibility = () => {
      if (document.visibilityState === "visible") poll();
    };
    window.addEventListener("focus", onFocus);
    document.addEventListener("visibilitychange", onVisibility);
    return () => {
      window.clearInterval(interval);
      window.removeEventListener("focus", onFocus);
      document.removeEventListener("visibilitychange", onVisibility);
    };
    // Intentionally omit videos.length / processing / genPhase — those were
    // restarting the interval on every generation tick.
  }, [refreshCompileStatus]);

  const { rememberTextField, pendingDraft, restoreDraft, dismissDraft, lastSavedAt, saving, showDraftBanner } =
    useStudioFormBackup({
    mode,
    category,
    visualStyle,
    form,
    setMode,
    setCategory,
    setVisualStyle,
    setForm,
    setWizardStep,
  });

  const pushToast = useCallback(
    (toast: Omit<StudioToastState, "id">) => {
      toastIdRef.current += 1;
      setStudioToast({ ...toast, id: toastIdRef.current });
    },
    []
  );

  const dismissToast = useCallback(() => setStudioToast(null), []);

  const clearFieldError = useCallback((id: string) => {
    setFieldErrors((prev) => {
      if (!prev[id]) return prev;
      const next = { ...prev };
      delete next[id];
      return next;
    });
  }, []);

  const setTextField = useCallback(
    (id: string, value: string) => {
      if (processing || genPhase === "running") return;

      if (id === "duration" && profile) {
        const secs = Number.parseInt(value, 10);
        if (Number.isFinite(secs) && secs > 0) {
          const check = validateDurationSelection(profile, secs);
          if (!check.allowed) {
            setDurationLimitMessage(
              check.message ??
                "Please recharge your account to select a longer video."
            );
            setDurationLimitMax(check.maxAllowedSeconds);
            setShowDurationLimit(true);
            return;
          }
        }
      }

      setForm((prev) => ({
        ...prev,
        text: { ...prev.text, [id]: value },
      }));
      rememberTextField(id, value);
      clearFieldError(id);
    },
    [rememberTextField, clearFieldError, processing, genPhase, profile]
  );

  const setFileField = useCallback(
    (id: string, value: import("@/lib/studio-form").FileFieldValue | null) => {
      if (processing || genPhase === "running") return;
      setForm((prev) => ({
        ...prev,
        files: { ...prev.files, [id]: value },
      }));
      if (value) clearFieldError(id);
    },
    [clearFieldError, processing, genPhase]
  );

  const handleCategorySelect = useCallback(
    (c: VideoCategory) => {
      if (processing || genPhase === "running" || !mode) return;
      setCategory(c);
      setVisualStyle(null);
      setSetupPhase("style");
      setForm((prev) =>
        pruneFormToVisible(
          { ...prev, text: { ...prev.text, duration: prev.text.duration ?? "" } },
          c,
          mode,
          "avatar"
        )
      );
      scrollToSetupRef(setupStyleRef);
    },
    [processing, genPhase, mode]
  );

  const handleModeSelect = useCallback(
    (m: GenerationMode) => {
      if (processing || genPhase === "running") return;
      setMode(m);
      setCategory(null);
      setVisualStyle(null);
      setSetupPhase("category");
      setForm((prev) => {
        const next = createInitialFormState();
        const title = prev.text[VIDEO_TITLE_FIELD_ID]?.trim();
        if (title) next.text[VIDEO_TITLE_FIELD_ID] = title;
        return next;
      });
      scrollToSetupRef(setupCategoryRef);
    },
    [processing, genPhase]
  );

  const handleVisualStyleSelect = useCallback(
    (style: VisualStyle) => {
      if (processing || genPhase === "running" || !mode || !category) return;
      setVisualStyle(style);
      setSetupPhase("title");
      setForm((prev) => {
        const synced = syncIdentityPipeline(prev, style);
        return pruneFormToVisible(synced, category, mode, style);
      });
      scrollToSetupRef(setupTitleRef);
    },
    [processing, genPhase, mode, category]
  );

  const applyProgress = useCallback((step: {
    percent: number;
    message: string;
    stageIndex: number;
  }) => {
    if (genPhaseRef.current === "success" || genPhaseRef.current === "error") {
      return;
    }
    genPhaseRef.current = "running";
    setGenPhase("running");
    setGenUi({
      active: true,
      percent: step.percent,
      message: step.message,
      stageIndex: step.stageIndex,
    });
    setStatusText(`${step.percent}% — ${step.message}`);
  }, []);

  const resetGenerationView = useCallback(() => {
    setConnectionError(null);
    setConnectionNoticeHint(undefined);
    setGenUi(IDLE_GEN);
    genPhaseRef.current = "idle";
    setGenPhase("idle");
    setProcessing(false);
    setStatusText("Ready to create");
    void fetchBackendHealthStatus().then(applyBackendHealth);
  }, [applyBackendHealth]);

  const resetFormForNextVideo = useCallback(() => {
    suppressStudioDraftSave();
    setWizardStep(WIZARD_SETUP_STEP);
    setCategory(null);
    setMode(null);
    setVisualStyle(null);
    setSetupPhase("mode");
    setForm(createInitialFormState());
    setFieldErrors({});
    setFormNotice(null);
    setFormSessionKey((key) => key + 1);
    window.setTimeout(() => {
      setWizardStep(WIZARD_SETUP_STEP);
      setCategory(null);
      setMode(null);
      setVisualStyle(null);
      setSetupPhase("mode");
      resumeStudioDraftSave();
    }, 250);
  }, []);

  useEffect(() => {
    genPhaseRef.current = genPhase;
  }, [genPhase]);

  useEffect(() => {
    if (studioScreen !== "preview" || !processing) return;
    const id = window.requestAnimationFrame(() => scrollToProgress());
    return () => window.cancelAnimationFrame(id);
  }, [studioScreen, processing, scrollToProgress]);

  useEffect(() => {
    if (!category || !mode || !visualStyle) return;
    setWizardStep((step) => {
      const maxStep = getWizardStepCount(category, mode, visualStyle) - 1;
      if (step > maxStep) {
        return Math.max(WIZARD_FIRST_GROUP_STEP, maxStep);
      }
      return step;
    });
  }, [category, mode, visualStyle]);

  useEffect(() => {
    if (wizardStep !== WIZARD_SETUP_STEP) return;
    if (!setupComplete) return;
    const timer = window.setTimeout(() => {
      setFieldErrors({});
      setFormNotice(null);
      setWizardStep(WIZARD_FIRST_GROUP_STEP);
    }, 500);
    return () => window.clearTimeout(timer);
  }, [wizardStep, setupComplete]);

  useEffect(() => {
    if (!category || !mode || mode !== "prompt" || !visualStyle) return;
    const group = getWizardGroupAtStep(wizardStep, category, mode, visualStyle);
    if (group?.id !== DURATION_PROMPT_GROUP_ID) {
      durationPromptAutoFillStepRef.current = null;
      return;
    }
    if (durationPromptAutoFillStepRef.current === wizardStep) return;
    if (form.text.mainPrompt?.trim()) {
      durationPromptAutoFillStepRef.current = wizardStep;
      return;
    }
    const autoFill = buildVisualSceneAutoFill(form);
    if (autoFill) {
      setForm((prev) => ({
        ...prev,
        text: { ...prev.text, mainPrompt: autoFill },
      }));
      rememberTextField("mainPrompt", autoFill);
    }
    durationPromptAutoFillStepRef.current = wizardStep;
  }, [wizardStep, category, mode, visualStyle, form, rememberTextField]);

  const stopGenerationUi = useCallback(() => {
    setProcessing(false);
    genPhaseRef.current = "idle";
    setGenPhase("idle");
    setGenUi(IDLE_GEN);
  }, []);

  const startGenerationUi = useCallback(
    (message: string, percent = 3) => {
      generationAbortRef.current?.abort();
      generationAbortRef.current = new AbortController();
      generationStartedAtRef.current = Date.now();
      setProcessing(true);
      genPhaseRef.current = "running";
      setGenPhase("running");
      setActiveVideo(null);
      setFormNotice(null);
      setGenUi({
        active: true,
        percent,
        message,
        stageIndex: 0,
      });
      setStatusText(message);
      scrollToProgress();
    },
    [scrollToProgress]
  );

  const notifyValidationFailure = useCallback(
    (errors: FieldValidationError[]) => {
      if (!category || !mode || !visualStyle) return;
      const errorMap = Object.fromEntries(
        errors.map((e) => [e.fieldId, e.message])
      );
      setFieldErrors(errorMap);
      setFormNotice(
        buildMissingFieldsMessage(errors, category, mode, visualStyle)
      );
      scrollToFirstFieldError(errors[0].fieldId);
      if (typeof document !== "undefined") {
        document
          .querySelector(".shashka-wizard-step__body")
          ?.scrollTo({ top: 0, behavior: "smooth" });
      }
    },
    [category, mode, visualStyle]
  );

  const showCustomerNotice = useCallback(
    (
      notice: CustomerNotice,
      phase: "error" | "success" = "error",
      subject?: import("@rtas/shared").UserProfile | null
    ) => {
      const user = subject ?? profile;
      const ownerView = isStudioOwner(user);
      let displayPhase = phase;

      if (!ownerView) {
        setConnectionError(null);
        setConnectionNoticeHint(null);
        if (
          phase === "error" &&
          isOwnerDiagnosticMessage(notice.message, notice.title)
        ) {
          displayPhase = "success";
        }
      } else {
        setConnectionNoticeTitle(notice.title);
        setConnectionNoticeHint(notice.hint);
        if (phase === "error") {
          setConnectionError(notice.message);
        } else {
          setConnectionError(null);
        }
      }

      genPhaseRef.current = displayPhase;
      setGenPhase(displayPhase);
      setGenUi((prev) => ({
        active: true,
        percent: displayPhase === "success" ? 100 : prev.percent || 0,
        message: notice.message,
        stageIndex: displayPhase === "success" ? GENERATION_LAST_STAGE_INDEX : prev.stageIndex,
      }));
      if (ownerView) {
        setConnectionNoticeTitle(notice.title);
      }
      setStatusText(notice.message);
      scrollToProgress();

      if (displayPhase === "error") {
        pushToast({
          tone: "error",
          title: notice.title,
          message: notice.hint ? `${notice.message} ${notice.hint}` : notice.message,
          actionLabel: "Retry",
          onAction: () => {
            dismissToast();
            void handleRetryGenerationRef.current?.();
          },
        });
      } else if (displayPhase === "success") {
        pushToast({
          tone: "success",
          title: notice.title,
          message: notice.message,
        });
      }
    },
    [scrollToProgress, profile, pushToast, dismissToast]
  );

  const showGenerationFailure = useCallback(
    (title: string, message: string, hint?: string | null) => {
      showCustomerNotice({ title, message, hint: hint ?? null }, "error");
    },
    [showCustomerNotice]
  );

  const handleCancelGeneration = useCallback(() => {
    generationAbortRef.current?.abort();
    generationAbortRef.current = null;
    genPhaseRef.current = "cancelled";
    setGenPhase("cancelled");
    setProcessing(false);
    setGenUi((prev) => ({
      ...prev,
      active: true,
      message: "Stopped waiting locally. Cloud render may continue — check Your Videos.",
    }));
    setFormNotice(
      "Waiting cancelled. If the job already reached the GPU, it may still finish in Your Videos."
    );
    pushToast({
      tone: "info",
      title: "Stopped waiting",
      message: "Draft kept. Cloud jobs already queued may still complete.",
    });
    void serverGallery.refresh();
  }, [serverGallery, pushToast]);

  const handleDismissPipeline = useCallback(() => {
    generationAbortRef.current = null;
    setGenUi(IDLE_GEN);
    genPhaseRef.current = "idle";
    setGenPhase("idle");
    setProcessing(false);
    generationStartedAtRef.current = null;
  }, []);

  const runGenerate = useCallback(
    async (opts?: {
      previewOnly?: boolean;
      freeTrial?: boolean;
      gracefulDegrade?: boolean;
      skipValidation?: boolean;
      uiAlreadyStarted?: boolean;
      segmentMode?: boolean;
      overrideDurationSeconds?: number;
      overrideForm?: StudioFormState;
      overrideMode?: GenerationMode;
      overrideCategory?: VideoCategory;
      overrideVisualStyle?: VisualStyle;
    }): Promise<GeneratedVideo | null> => {
      const activeCategory = opts?.overrideCategory ?? category;
      const activeMode = opts?.overrideMode ?? mode;
      const activeVisualStyle = opts?.overrideVisualStyle ?? visualStyle;
      if (!profile || !activeCategory || !activeMode || !activeVisualStyle) return null;

      const activeForm = opts?.overrideForm ?? form;
      const requestedDuration = opts?.overrideDurationSeconds ?? durationSeconds;

      if (!opts?.skipValidation) {
        const validationErrors = collectRequiredFieldErrors(
          activeCategory,
          activeMode,
          activeVisualStyle,
          activeForm
        );
        if (validationErrors.length > 0) {
          notifyValidationFailure(validationErrors);
          return null;
        }
      }

      const activeProfile = (await syncFromServer(profile.id)) ?? profile;

      setFieldErrors({});
      setConnectionError(null);
      setPipelineDiagnostic(null);

      const isPreview = !!opts?.previewOnly;
      const usePremiumPipeline = hasPremiumAccess(activeProfile, requestedDuration);
      const isFreeTrial =
        !!opts?.freeTrial && !usePremiumPipeline && !isPreview;
      const effectiveDuration = isFreeTrial
        ? Math.min(requestedDuration, FREE_TRIAL_DURATION_SECONDS)
        : requestedDuration;
      const capturedTitle = buildVideoTitle(activeCategory, activeMode, activeForm);
      const capturedPrompt = extractCreativePrompt(activeForm);

      const deviceFingerprint = getDeviceFingerprint();

      if (isFreeTrial) {
        const verifyRes = await fetch("/api/trial/verify", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            deviceFingerprint,
          }),
        });
        const verifyData = (await verifyRes.json().catch(() => ({}))) as {
          message?: string;
        };
        if (!verifyRes.ok) {
          showGenerationFailure(
            "Free trial limit",
            verifyData.message ?? FREE_TRIAL_ABUSE_MESSAGE
          );
          return null;
        }
      }

      const payload = buildGeneratePayload(activeForm, activeCategory, activeMode, activeVisualStyle);

      const requestBody: GenerateRequestBody = {
        ...payload,
        identityPipeline: payload.identityPipeline as unknown as Record<string, unknown>,
        durationSeconds: effectiveDuration,
        userId: activeProfile.id,
        deviceFingerprint,
        profile: {
          subscriptionActive: activeProfile.subscriptionActive,
          credits: activeProfile.credits,
          freeTrialUsed: activeProfile.freeTrialUsed,
          hasUsedFreeTrial: activeProfile.hasUsedFreeTrial ?? activeProfile.freeTrialUsed,
          tier: activeProfile.tier,
        },
        previewOnly: isPreview,
        useFreeTrial: isFreeTrial,
      };

      setConnectionError(null);
      if (!opts?.uiAlreadyStarted) {
        startGenerationUi(
          isPreview
            ? "AI preview rendering…"
            : isFreeTrial
              ? `Free ${FREE_TRIAL_DURATION_SECONDS}s trial rendering…`
              : "AI video rendering…",
          5
        );
      } else {
        setGenUi((prev) => ({
          ...prev,
          percent: Math.max(prev.percent, 8),
          message: isPreview
            ? "AI preview rendering…"
            : isFreeTrial
              ? `Free ${FREE_TRIAL_DURATION_SECONDS}s trial rendering…`
              : "AI video rendering…",
        }));
        setStatusText(
          isPreview
            ? "AI preview rendering…"
            : isFreeTrial
              ? `Free ${FREE_TRIAL_DURATION_SECONDS}s trial rendering…`
              : "AI video rendering…"
        );
      }

      try {
        const backendRes = await runBackendGeneration(
          requestBody,
          applyProgress,
          {
            animationMs: 6500 + Math.floor(Math.random() * 1500),
            uploadables: activeForm.files,
            signal: generationAbortRef.current?.signal,
          }
        );

        setBackendOnline(true);

        const isSimulation = backendRes.simulationMode ?? false;

        let nextProfile = { ...activeProfile };
        if (isFreeTrial) {
          nextProfile.freeTrialUsed = true;
          nextProfile.hasUsedFreeTrial = true;
          nextProfile.deviceFingerprint = deviceFingerprint;
          void fetch("/api/trial/consume", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              deviceFingerprint,
            }),
          });
        } else if (
          !backendRes.previewOnly &&
          !isSimulation &&
          backendRes.creditsUsed > 0 &&
          (nextProfile.subscriptionActive || isPaidTier(nextProfile.tier))
        ) {
          nextProfile.credits = Math.max(
            0,
            nextProfile.credits - backendRes.creditsUsed
          );
        }

        const playbackUrl = resolveVideoPlaybackUrl(backendRes.videoUrl, {
          simulationMode: isSimulation,
          preferSample: isSimulation,
        });

        const isPaidGeneration =
          (activeProfile.tier === "premium" ||
            activeProfile.tier === "standard" ||
            activeProfile.subscriptionActive) &&
          !isPreview &&
          !isSimulation;

        const video: GeneratedVideo = {
          id: backendRes.jobId,
          userId: activeProfile.id,
          title: capturedTitle,
          category: activeCategory,
          mode: activeMode,
          visualStyle: activeVisualStyle,
          durationSeconds: backendRes.durationSeconds,
          creditsUsed: backendRes.creditsUsed,
          previewOnly: isPreview || (!isPaidGeneration && backendRes.previewOnly),
          canDownload: isPaidGeneration || backendRes.canDownload,
          status: "ready",
          videoUrl: playbackUrl,
          simulationMode: isSimulation,
          creativePrompt: capturedPrompt || backendRes.promptPreview || undefined,
          createdAt: new Date().toISOString(),
        };

        const all = [video, ...videos.filter((v) => v.id !== video.id)];
        setVideos(all);
        saveVideosForUser(activeProfile.id, all);
        saveProfile(nextProfile);
        setProfile(nextProfile);
        setActiveVideo(video);
        genPhaseRef.current = "success";
        setGenPhase("success");
        setGenUi({
          active: true,
          percent: 100,
          message: backendRes.message || "Done ✓",
          stageIndex: GENERATION_LAST_STAGE_INDEX,
        });
        if (capturedPrompt && !opts?.segmentMode) addPromptToHistory(capturedPrompt);
        if (!opts?.segmentMode) {
          upsertRecentProject({
            id: video.id,
            title: capturedTitle,
            prompt: capturedPrompt || undefined,
            category: activeCategory,
            durationSeconds: video.durationSeconds,
            createdAt: video.createdAt,
            status: "ready",
          });
        }
        if (!opts?.segmentMode) {
          resetFormForNextVideo();
          setStudioScreen("preview");
        }
        void refreshCompileStatus();

        if (opts?.gracefulDegrade || (backendRes.previewOnly && opts?.previewOnly)) {
          const previewNotice = noticeForOwnerOrCustomer(
            activeProfile,
            {
              title: "Preview render",
              message: backendRes.message || "Preview sample ready.",
              hint: FAL_CREDIT_HINT,
            },
            CUSTOMER_PREVIEW_READY
          );
          showCustomerNotice(previewNotice, "success");
        } else {
          setStatusText(backendRes.message || "Video ready");
          pushToast({
            tone: "success",
            title: "Your video is ready",
            message: "Preview, download, or create a variation from the success panel.",
          });
        }
        return video;
      } catch (e) {
        if (
          (e instanceof DOMException && e.name === "AbortError") ||
          (e instanceof Error && /cancelled|aborted/i.test(e.message))
        ) {
          genPhaseRef.current = "cancelled";
          setGenPhase("cancelled");
          setProcessing(false);
          setGenUi((prev) => ({
            ...prev,
            active: true,
            message: "Stopped waiting locally. Check Your Videos if a cloud job was already queued.",
          }));
          return null;
        }

        if (isPipelineFailureError(e)) {
          const failure = e;
          setPipelineDiagnostic({
            error: failure.message,
            details: failure.details,
            code: failure.code,
            at: new Date().toISOString(),
          });
          setStudioDebugOpen(true);
          genPhaseRef.current = "error";
          setGenPhase("error");
          setGenUi((prev) => ({
            ...prev,
            active: true,
            message: failure.message,
          }));
          setStatusText(failure.message);
          setConnectionError(failure.details);
          showGenerationFailure("GPU pipeline failed", failure.message, failure.details);
          return null;
        }

        const msg =
          e instanceof Error ? e.message : "Video generation failed. Please try again.";

        const cloudUnavailable =
          isFalAuthError(e) ||
          isFalCreditError(e) ||
          isReplicateAuthError(e) ||
          isReplicateCreditError(e) ||
          isCloudCapacityMessage(msg);

        if (isFalAuthError(e)) {
          const notice = noticeForOwnerOrCustomer(
            activeProfile,
            { title: "Fal.ai API key", message: FAL_AUTH_ERROR, hint: FAL_AUTH_HINT },
            CUSTOMER_STUDIO_BUSY
          );
          showCustomerNotice(notice, "error");
        } else if (isReplicateAuthError(e)) {
          const notice = noticeForOwnerOrCustomer(
            activeProfile,
            {
              title: "Replicate API token",
              message: REPLICATE_AUTH_ERROR,
              hint: REPLICATE_AUTH_HINT,
            },
            CUSTOMER_STUDIO_BUSY
          );
          showCustomerNotice(notice, "error");
        } else if (isFalCreditError(e)) {
          const notice = noticeForOwnerOrCustomer(
            activeProfile,
            { title: "Fal.ai billing", message: FAL_CREDIT_ERROR, hint: FAL_CREDIT_HINT },
            CUSTOMER_CLOUD_MAINTENANCE
          );
          showCustomerNotice(notice, "error");
        } else if (isReplicateCreditError(e)) {
          const notice = noticeForOwnerOrCustomer(
            activeProfile,
            {
              title: "Replicate billing",
              message: REPLICATE_CREDIT_ERROR,
              hint: REPLICATE_CREDIT_HINT,
            },
            CUSTOMER_CLOUD_MAINTENANCE
          );
          showCustomerNotice(notice, "error");
        } else if (isBackendConnectionError(e)) {
          setBackendOnline(false);
          const notice = noticeForOwnerOrCustomer(
            activeProfile,
            {
              title: "API connection issue",
              message: BACKEND_CONNECTION_ERROR,
              hint: null,
            },
            CUSTOMER_CONNECTION_ISSUE
          );
          showCustomerNotice(notice, "error");
        } else if (isCloudCapacityMessage(msg) || cloudUnavailable) {
          const notice = noticeForOwnerOrCustomer(
            activeProfile,
            { title: "Cloud render", message: msg, hint: FAL_CREDIT_HINT },
            CUSTOMER_STUDIO_BUSY
          );
          showCustomerNotice(notice, "error");
        } else if (msg.toLowerCase().includes("already in progress")) {
          showGenerationFailure(
            "Generation in progress",
            msg,
            "Wait for the current render to finish before starting another."
          );
        } else if (msg.toLowerCase().includes("face") || msg.toLowerCase().includes("facereference")) {
          showGenerationFailure(
            "Real face setup required",
            msg,
            "Upload Face Photo, type YES in Face Consent, then generate again."
          );
        } else {
          const notice = noticeForOwnerOrCustomer(
            activeProfile,
            { title: "Video generation failed", message: msg, hint: null },
            CUSTOMER_GENERIC_FAILURE
          );
          showCustomerNotice(notice, "error");
        }
        return null;
      } finally {
        if (!opts?.segmentMode) {
          setProcessing(false);
        }
      }
    },
    [
      profile,
      syncFromServer,
      category,
      mode,
      visualStyle,
      durationSeconds,
      form,
      videos,
      creditsNeeded,
      setProfile,
      applyProgress,
      scrollToProgress,
      showGenerationFailure,
      showCustomerNotice,
      notifyValidationFailure,
      startGenerationUi,
      stopGenerationUi,
      resetFormForNextVideo,
      pushToast,
    ]
  );

  const handleRetryGeneration = useCallback(async () => {
    const snapshot = lastGenerateAttemptRef.current;
    setPipelineDiagnostic(null);
    setConnectionError(null);
    dismissToast();
    setRetryLoading(true);

    if (!snapshot || !profile) {
      setRetryLoading(false);
      genPhaseRef.current = "idle";
      setGenPhase("idle");
      setGenUi(IDLE_GEN);
      setProcessing(false);
      setStatusText("Ready to retry generation");
      if (profile) void syncFromServer(profile.id);
      return;
    }

    setForm(snapshot.form);
    setMode(snapshot.mode);
    setCategory(snapshot.category);
    setVisualStyle(snapshot.visualStyle);
    setStudioScreen("preview");
    startGenerationUi("Retrying generation…", 8);
    pushToast({
      tone: "info",
      title: "Retrying generation",
      message: "Restored your last inputs and re-queued the render.",
    });

    try {
      const video = await runGenerate({
        skipValidation: true,
        uiAlreadyStarted: true,
        overrideForm: snapshot.form,
        overrideDurationSeconds: snapshot.durationSeconds,
        overrideMode: snapshot.mode,
        overrideCategory: snapshot.category,
        overrideVisualStyle: snapshot.visualStyle,
      });
      if (video) void notifyVideoReady(profile, video);
    } catch {
      /* runGenerate handles errors */
    } finally {
      setRetryLoading(false);
    }
  }, [profile, runGenerate, startGenerationUi, syncFromServer, pushToast, dismissToast]);

  handleRetryGenerationRef.current = handleRetryGeneration;

  const isLiveFalBlocked = useCallback((guard: FalGuardStatus | null) => {
    if (!guard) return false;
    if (!guard.liveEnabled) return true;
    if (guard.billingBlocked) return true;
    if (!guard.liveCallsAllowed && guard.retryAfterSec > 0) return true;
    return false;
  }, []);

  const runLongVideoGeneration = useCallback(
    async (freshProfile: NonNullable<typeof profile>) => {
      if (!category || !mode || !visualStyle) return;

      const plan = computeSegmentPlan(durationSeconds);
      const capturedTitle = buildVideoTitle(category, mode, form);
      const clipFiles: string[] = [];

      setStudioScreen("preview");
      setProcessing(true);
      startGenerationUi(
        `Part 1 of ${plan.segmentCount} — preparing segments…`,
        plan.segmentCount + 2
      );

      try {
        for (let i = 0; i < plan.segments.length; i++) {
          const segDuration = plan.segments[i];
          const baseDirection = form.text.directionPrompt ?? "";
          const segDirection = buildSegmentDirectionPrompt(
            baseDirection,
            i,
            plan.segmentCount,
            segDuration,
            plan.totalSeconds
          );
          const segForm: StudioFormState = {
            ...form,
            text: { ...form.text, directionPrompt: segDirection },
          };

          setGenUi((prev) => ({
            ...prev,
            active: true,
            percent: Math.round((i / plan.segmentCount) * 70),
            message: `Rendering...`,
            stageIndex: 5,
          }));
          setStatusText(`Part ${i + 1}/${plan.segmentCount} rendering…`);

          const segmentVideo = await runGenerate({
            skipValidation: true,
            uiAlreadyStarted: true,
            segmentMode: true,
            overrideDurationSeconds: segDuration,
            overrideForm: segForm,
          });

          if (!segmentVideo?.videoUrl) {
            throw new Error(`Part ${i + 1} failed — please try again.`);
          }

          const filename = filenameFromVideoUrl(segmentVideo.videoUrl);
          if (filename) clipFiles.push(filename);
        }

        setGenUi((prev) => ({
          ...prev,
          percent: 82,
          message: "Stitching your full video…",
        }));

        const compileRes = await fetch("/api/compile", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            clipFiles,
            targetDurationSec: plan.totalSeconds,
          }),
        });
        const compileData = (await compileRes.json().catch(() => ({}))) as {
          ok?: boolean;
          videoUrl?: string;
          message?: string;
          error?: string;
        };

        if (!compileRes.ok || !compileData.ok || !compileData.videoUrl) {
          throw new Error(compileData.error ?? "Stitching failed");
        }

        const finalVideo: GeneratedVideo = {
          id: `long-${Date.now()}`,
          userId: freshProfile.id,
          title: capturedTitle,
          category,
          mode,
          visualStyle,
          durationSeconds: plan.totalSeconds,
          creditsUsed: plan.totalSeconds,
          previewOnly: false,
          canDownload: true,
          status: "ready",
          videoUrl: compileData.videoUrl,
          simulationMode: false,
          creativePrompt: extractCreativePrompt(form),
          createdAt: new Date().toISOString(),
        };

        const all = [finalVideo, ...videos.filter((v) => v.id !== finalVideo.id)];
        setVideos(all);
        saveVideosForUser(freshProfile.id, all);
        setActiveVideo(finalVideo);
        resetFormForNextVideo();
        genPhaseRef.current = "success";
        setGenPhase("success");
        setGenUi({
          active: true,
          percent: 100,
          message: compileData.message ?? "Done ✓",
          stageIndex: GENERATION_LAST_STAGE_INDEX,
        });
        const longPrompt = extractCreativePrompt(form);
        if (longPrompt) addPromptToHistory(longPrompt);
        upsertRecentProject({
          id: finalVideo.id,
          title: capturedTitle,
          prompt: longPrompt || undefined,
          category,
          durationSeconds: plan.totalSeconds,
          createdAt: finalVideo.createdAt,
          status: "ready",
        });
        setStatusText(compileData.message ?? "Full video ready");
        void notifyVideoReady(freshProfile, finalVideo);
      } catch (e) {
        const msg = e instanceof Error ? e.message : "Long video failed.";
        showGenerationFailure("Video build failed", msg);
        stopGenerationUi();
      } finally {
        setProcessing(false);
      }
    },
    [
      category,
      durationSeconds,
      form,
      mode,
      resetFormForNextVideo,
      runGenerate,
      showGenerationFailure,
      startGenerationUi,
      stopGenerationUi,
      videos,
      visualStyle,
    ]
  );

  const handleShareVideo = useCallback((video: GeneratedVideo) => {
    if (video.status !== "ready" || !video.videoUrl) return;
    setShareVideo(video);
  }, []);

  const handleSharePublished = useCallback(
    (videoId: string) => {
      if (!profile) return;
      const nextVideos = videos.map((v) =>
        v.id === videoId ? { ...v, isPublic: true } : v
      );
      setVideos(nextVideos);
      saveVideosForUser(profile.id, nextVideos);
      if (activeVideo?.id === videoId) {
        setActiveVideo({ ...activeVideo, isPublic: true });
      }
    },
    [profile, videos, activeVideo]
  );

  const onGenerateClick = async () => {
    if (!profile) {
      setFormNotice("Please sign in to generate videos.");
      return;
    }
    if (processing || genPhase === "running") {
      setFormNotice("A render is already in progress — please wait.");
      return;
    }

    if (!category) {
      setFormNotice("Please select a category first (Song, Religious, Business, etc.).");
      return;
    }
    if (!mode) {
      setFormNotice("Please choose a mode first.");
      return;
    }
    if (!visualStyle) {
      setFormNotice("Please choose a visual style first.");
      return;
    }

    const validationErrors = collectRequiredFieldErrors(
      category,
      mode,
      visualStyle,
      form
    );
    if (validationErrors.length > 0) {
      notifyValidationFailure(validationErrors);
      return;
    }

    const openPaywall = (subject: typeof profile, required: number) => {
      setFormNotice(null);
      setPaywallMessage(paywallReasonMessage(subject, required));
      setShowPaywall(true);
    };

    if (shouldShowPaywall(profile, durationSeconds)) {
      openPaywall(profile, creditsNeeded);
      return;
    }

    if (generationLimitReached) {
      setFormNotice(
        generationLimitMessage ??
          "Generation limit reached. Check your credits and active render queue."
      );
      return;
    }

    setFieldErrors({});
    setStudioScreen("preview");
    lastGenerateAttemptRef.current = {
      form: { ...form, text: { ...form.text }, files: { ...form.files } },
      mode,
      category,
      visualStyle,
      durationSeconds,
    };
    startGenerationUi("Preparing your video…", 2);

    const segmentPlan = computeSegmentPlan(durationSeconds);
    if (durationSeconds >= 60 || segmentPlan.segmentCount > 1) {
      setShowGenStartedModal(true);
    }

    try {
      const freshProfile = (await syncFromServer(profile.id)) ?? profile;

      if (shouldShowPaywall(freshProfile, durationSeconds)) {
        stopGenerationUi();
        setStudioScreen("create");
        openPaywall(freshProfile, creditsNeeded);
        return;
      }

      if (generationLimitReached) {
        stopGenerationUi();
        setStudioScreen("create");
        setFormNotice(
          generationLimitMessage ??
            "Generation limit reached. Check your credits and active render queue."
        );
        return;
      }

      const durationCheck = validateDurationSelection(freshProfile, durationSeconds);
      if (!durationCheck.allowed) {
        stopGenerationUi();
        setStudioScreen("create");
        setFormNotice(null);
        setDurationLimitMessage(
          durationCheck.message ??
            "Please recharge your account to select this video length."
        );
        setDurationLimitMax(durationCheck.maxAllowedSeconds);
        setShowDurationLimit(true);
        return;
      }

      setGenUi((prev) => ({
        ...prev,
        message: "Checking studio connection…",
      }));

      const health = await fetchBackendHealthStatus();
      applyBackendHealth(health);
      const liveBlocked =
        health.falConfigured && isLiveFalBlocked(health.falGuard);

      if (liveBlocked) {
        stopGenerationUi();
        if (isStudioOwner(profile)) {
          const reason =
            health.falGuard?.blockedReason ??
            `Cloud render paused. Retry in ${health.falGuard?.retryAfterSec ?? 0}s.`;
          showGenerationFailure("Fal.ai paused (owner)", reason, FAL_CREDIT_HINT);
        } else {
          showCustomerNotice(CUSTOMER_STUDIO_BUSY, "error");
        }
        return;
      }

      if (shouldUseLongVideoPipeline(freshProfile.tier, durationSeconds)) {
        await runLongVideoGeneration(freshProfile);
        return;
      }

      setGenUi((prev) => ({
        ...prev,
        message: "Rendering your video…",
      }));
      const video = await runGenerate({ skipValidation: true, uiAlreadyStarted: true });
      if (video) {
        void notifyVideoReady(freshProfile, video);
      }
    } catch (e) {
      const msg =
        e instanceof Error ? e.message : "Something went wrong. Please try again.";
      showGenerationFailure("Could not start", msg);
      stopGenerationUi();
    }
  };

  onGenerateClickRef.current = () => {
    void onGenerateClick();
  };

  const canCompileVideo =
    compileStatusReady &&
    backendOutputClipCount >= MIN_CLIPS_TO_COMPILE &&
    !processing &&
    genPhase !== "running" &&
    !compileUi.active;

  const onCompileClick = async () => {
    if (!profile || !mode || !visualStyle || !canCompileVideo || compileUi.active) return;

    const clipCount = await refreshCompileStatus();
    if (clipCount < MIN_CLIPS_TO_COMPILE) {
      showGenerationFailure(
        "Not enough clips",
        `Need at least ${MIN_CLIPS_TO_COMPILE} MP4 files in apps/backend/data/outputs (found ${clipCount}).`
      );
      return;
    }

    setCompileUi({
      active: true,
      percent: 8,
      message: "Scanning generated clips…",
    });

    const progressTimer = window.setInterval(() => {
      setCompileUi((prev) => ({
        ...prev,
        percent: Math.min(prev.percent + 4, 92),
        message:
          prev.percent < 40
            ? "Merging clips with FFmpeg…"
            : "Building 5-minute master…",
      }));
    }, 2500);

    try {
      const res = await fetch("/api/compile", { method: "POST" });
      const data = (await res.json().catch(() => ({}))) as {
        ok?: boolean;
        message?: string;
        videoUrl?: string;
        error?: string;
        clipCount?: number;
      };

      if (!res.ok || !data.ok || !data.videoUrl) {
        throw new Error(data.error ?? "Compile failed");
      }

      setCompileUi({
        active: false,
        percent: 100,
        message: data.message ?? "5-minute video ready",
      });
      setStatusText(data.message ?? "Compiled video ready");
      setStudioScreen("preview");
      setActiveVideo({
        id: `compiled-${Date.now()}`,
        userId: profile.id,
        title: form.text[VIDEO_TITLE_FIELD_ID]?.trim() || "Compiled 5-minute video",
        category: category ?? "song",
        mode,
        visualStyle,
        durationSeconds: 300,
        creditsUsed: 0,
        previewOnly: false,
        canDownload: true,
        status: "ready",
        videoUrl: data.videoUrl,
        simulationMode: false,
        createdAt: new Date().toISOString(),
      });
      void refreshCompileStatus();
    } catch (e) {
      const msg = e instanceof Error ? e.message : "Compile failed";
      setCompileUi({ active: false, percent: 0, message: "" });
      showGenerationFailure("Compile failed", msg);
    } finally {
      window.clearInterval(progressTimer);
    }
  };

  const proceedToCheckout = async (
    plan: CheckoutPlan = "standard",
    options?: { rolloverRemaining?: boolean }
  ) => {
    if (!profile) return;
    const result = await startCheckout(profile, plan, options);
    if (result.message && !result.activated && !result.openedUrl) {
      setStatusText(result.message);
      return;
    }
    if (result.profile) {
      setProfile(result.profile);
      saveProfile(result.profile);
    }
    setShowPaywall(false);
    setPaywallMessage(undefined);
    setShowEarlyResubscribe(false);
    if (result.message) setStatusText(result.message);
  };

  const handleSubscribeStandard = () => {
    if (!profile) return;
    if (shouldConfirmEarlyResubscribe(profile) && profile.tier === "standard") {
      setPendingCheckoutPlan("standard");
      setShowEarlyResubscribe(true);
      return;
    }
    void proceedToCheckout("standard");
  };

  const handleSubscribePremium = () => {
    if (!profile) return;
    if (shouldConfirmEarlyResubscribe(profile) && profile.tier === "premium") {
      setPendingCheckoutPlan("premium");
      setShowEarlyResubscribe(true);
      return;
    }
    void proceedToCheckout("premium");
  };

  const handleSubscribeTester = () => {
    window.open("http://localhost:3001", "_blank", "noopener,noreferrer");
  };

  const handleClosePaywall = useCallback(() => {
    setShowPaywall(false);
    setPaywallMessage(undefined);
  }, []);

  const goPreviousWizard = useCallback(() => {
    if (processing || genPhase === "running") return;
    if (wizardStep <= WIZARD_SETUP_STEP) return;
    setFieldErrors({});
    setFormNotice(null);
    setWizardStep((step) => {
      const next = Math.max(WIZARD_SETUP_STEP, step - 1);
      if (next === WIZARD_SETUP_STEP) {
        if (mode && category && visualStyle) setSetupPhase("title");
        else if (mode && category) setSetupPhase("style");
        else if (mode) setSetupPhase("category");
        else setSetupPhase("mode");
      }
      return next;
    });
  }, [processing, genPhase, wizardStep, mode, category, visualStyle]);

  const advanceWizard = () => {
    if (processing || genPhase === "running") return;

    if (wizardStep === WIZARD_SETUP_STEP) {
      if (!mode) {
        setFormNotice("Please choose a mode — Prompt → Video or Image → Video.");
        return;
      }
      if (!category) {
        setFormNotice("Please select a category (Song, Religious, Business, etc.).");
        return;
      }
      if (!visualStyle) {
        setFormNotice("Please choose a visual style — Real face, Avatar, or Cartoon.");
        return;
      }
      if (!form.text[VIDEO_TITLE_FIELD_ID]?.trim()) {
        setFormNotice("Please enter a video title.");
        scrollToSetupRef(setupTitleRef);
        return;
      }
      setFieldErrors({});
      setFormNotice(null);
      setWizardStep(WIZARD_FIRST_GROUP_STEP);
      return;
    }

    if (!category || !mode || !visualStyle) return;

    const currentGroup = getWizardGroupAtStep(
      wizardStep,
      category,
      mode,
      visualStyle
    );
    if (!currentGroup) return;

    const groupErrors = validateWizardGroup(
      currentGroup,
      category,
      mode,
      visualStyle,
      form
    );
    if (groupErrors.length > 0) {
      setFieldErrors(Object.fromEntries(groupErrors.map((e) => [e.fieldId, e.message])));
      setFormNotice(
        buildMissingFieldsMessage(groupErrors, category, mode, visualStyle)
      );
      scrollToFirstFieldError(groupErrors[0].fieldId);
      return;
    }

    const maxStep = getWizardStepCount(category, mode, visualStyle) - 1;
    setFieldErrors({});
    setFormNotice(null);
    if (wizardStep < maxStep) {
      setWizardStep(wizardStep + 1);
    }
  };

  const isGenerating = processing && genPhase === "running";
  const generationPatienceMessage = isGenerating
    ? buildGenerationPatienceMessage(
        durationSeconds,
        computeSegmentPlan(durationSeconds).segmentCount,
        false
      )
    : "";
  /** True while generate is in flight — locks entire create form */
  const formLocked = processing || genPhase === "running";
  const isLoading = formLocked;
  const apiBase = getFastApiBase() || "http://localhost:8000";
  const showConnectionBanner =
    Boolean(connectionError) && isStudioOwner(profile);

  const isPaidUser =
    profile?.tier === "premium" ||
    profile?.tier === "standard" ||
    Boolean(profile?.subscriptionActive);
  const effectiveRemainingSeconds = profile?.credits ?? 0;
  const currentPrompt =
    form.text.directionPrompt?.trim() ||
    form.text.prompt?.trim() ||
    form.text[VIDEO_TITLE_FIELD_ID]?.trim() ||
    "—";
  const currentInputImage =
    form.files.sourceImage?.name ||
    form.files.imageReference?.name ||
    form.files.faceReference?.name ||
    "—";
  const currentGeneratedVideoUrl = activeVideo?.videoUrl ?? "—";
  const currentGenerationStatus = pipelineDiagnostic
    ? `failed — ${pipelineDiagnostic.error}`
    : genPhase;

  const activePlaybackSrc = activeVideo?.videoUrl
    ? resolveVideoPlaybackUrl(activeVideo.videoUrl, {
        simulationMode: activeVideo.simulationMode ?? false,
        preferSample: activeVideo.simulationMode ?? false,
      })
    : undefined;

  const handleSelectVideo = useCallback(
    (video: GeneratedVideo) => {
      if (processing) return;
      setStudioScreen("preview");
      setActiveVideo({
        ...video,
        videoUrl: resolveVideoPlaybackUrl(video.videoUrl, {
          simulationMode: video.simulationMode ?? false,
          preferSample: video.simulationMode ?? false,
        }),
      });
    },
    [processing]
  );

  const handleCarouselSelect = useCallback(
    (item: Parameters<typeof userVideoAssetToGeneratedVideo>[0]) => {
      handleSelectVideo(userVideoAssetToGeneratedVideo(item, profile?.id));
    },
    [handleSelectVideo, profile?.id]
  );

  const handleCarouselShare = useCallback(
    (item: Parameters<typeof userVideoAssetToGeneratedVideo>[0]) => {
      handleShareVideo(userVideoAssetToGeneratedVideo(item, profile?.id));
    },
    [handleShareVideo, profile?.id]
  );

  const handleCarouselLoadMore = useCallback(() => {
    void serverGallery.loadMore();
  }, [serverGallery]);

  const handleCarouselRefresh = useCallback(() => {
    void serverGallery.refresh();
  }, [serverGallery]);

  const handlePipelineRetry = useCallback(() => {
    void handleRetryGeneration();
  }, [handleRetryGeneration]);

  const generationModelLabel = useMemo(() => {
    if (activeVideo?.simulationMode) return "RTAS Preview Engine";
    if (falGuard?.billingBlocked) return "RTAS Cloud (paused)";
    if (profile && hasPremiumAccess(profile, durationSeconds)) {
      return "RTAS Cinematic Engine · Premium";
    }
    return "RTAS Cinematic Engine";
  }, [activeVideo?.simulationMode, falGuard?.billingBlocked, profile, durationSeconds]);

  const handleSuccessPreview = useCallback(() => {
    const frame = previewPanelRef.current;
    frame?.scrollIntoView({ behavior: "smooth", block: "center" });
    const videoEl = frame?.querySelector("video");
    if (videoEl instanceof HTMLVideoElement) {
      void videoEl.play().catch(() => undefined);
    }
    pushToast({
      tone: "info",
      title: "Preview ready",
      message: "Playing in the canvas on the right.",
    });
  }, [pushToast]);

  const handleSuccessDownload = useCallback(() => {
    const url = activeVideo?.videoUrl;
    if (!url || !activeVideo?.canDownload) {
      pushToast({
        tone: "warning",
        title: "Download unavailable",
        message: "Upgrade or wait for a paid render to unlock download.",
      });
      return;
    }
    const a = document.createElement("a");
    a.href = url;
    a.download = `${(activeVideo.title || "rtas-video").replace(/[^\w\-]+/g, "-").slice(0, 48)}.mp4`;
    a.rel = "noopener";
    a.target = "_blank";
    document.body.appendChild(a);
    a.click();
    a.remove();
    pushToast({
      tone: "success",
      title: "Download started",
      message: "Your video file is on the way.",
    });
  }, [activeVideo, pushToast]);

  const handleEditPrompt = useCallback(() => {
    const snapshot = lastGenerateAttemptRef.current;
    if (snapshot) {
      setForm(snapshot.form);
      setMode(snapshot.mode);
      setCategory(snapshot.category);
      setVisualStyle(snapshot.visualStyle);
    }
    setStudioScreen("create");
    const promptStep = Math.min(
      Math.max(WIZARD_FIRST_GROUP_STEP, 1),
      Math.max(
        0,
        getWizardStepCount(
          snapshot?.category ?? category,
          snapshot?.mode ?? mode,
          snapshot?.visualStyle ?? visualStyle
        ) - 1
      )
    );
    setWizardStep(promptStep);
    pushToast({
      tone: "info",
      title: "Edit your prompt",
      message: "Your last inputs are restored. Adjust the scene, then generate again.",
    });
    requestAnimationFrame(() => {
      const el =
        document.getElementById("mainPrompt") ||
        document.getElementById("directionPrompt") ||
        document.querySelector(".prompt-editor__textarea");
      if (el instanceof HTMLElement) el.focus();
    });
  }, [category, mode, visualStyle, pushToast]);

  const handleCreateVariation = useCallback(() => {
    const snapshot = lastGenerateAttemptRef.current;
    const text = snapshot?.form.text ?? form.text;
    const base =
      text.mainPrompt?.trim() ||
      text.directionPrompt?.trim() ||
      text.prompt?.trim() ||
      "";
    const variationHint =
      "Variation: slightly different camera angle, lighting, and pacing while keeping the same subject.";
    const next = base
      ? `${base.replace(/\s*Variation:.*$/i, "").trim()}\n\n${variationHint}`
      : variationHint;

    if (snapshot) {
      setMode(snapshot.mode);
      setCategory(snapshot.category);
      setVisualStyle(snapshot.visualStyle);
      setForm({
        ...snapshot.form,
        text: {
          ...snapshot.form.text,
          mainPrompt: next.slice(0, 4000),
          ...(snapshot.form.text.directionPrompt !== undefined
            ? { directionPrompt: snapshot.form.text.directionPrompt }
            : {}),
        },
      });
    } else {
      const fieldId =
        form.text.mainPrompt !== undefined ? "mainPrompt" : "directionPrompt";
      setTextField(fieldId, next.slice(0, 4000));
    }

    setStudioScreen("create");
    pushToast({
      tone: "success",
      title: "Variation ready",
      message: "Prompt updated with a gentle variation cue. Review, then generate.",
    });
  }, [form.text, setTextField, pushToast]);

  const forceSaveDraft = useCallback(() => {
    if (!mode || !visualStyle) {
      pushToast({
        tone: "warning",
        title: "Nothing to save yet",
        message: "Choose a mode and visual style first.",
      });
      return;
    }
    saveStudioDraft({
      mode,
      category,
      visualStyle,
      text: form.text,
    });
    pushToast({
      tone: "success",
      title: "Draft saved",
      message: "Your prompts and settings are stored on this device.",
    });
  }, [mode, category, visualStyle, form.text, pushToast]);

  useStudioKeyboardShortcuts({
    enabled: Boolean(profile),
    onGenerate: () => {
      if (processing || genPhase === "running") return;
      if (studioScreen !== "create") setStudioScreen("create");
      onGenerateClickRef.current?.();
    },
    onCancel: () => {
      if (genPhase === "running") handleCancelGeneration();
      else if (studioToast) dismissToast();
    },
    onRetry: () => {
      if (genPhase === "error") void handleRetryGeneration();
    },
    onToggleScreen: () => {
      if (processing || genPhase === "running") return;
      setStudioScreen((prev) => (prev === "create" ? "preview" : "create"));
    },
    onSaveDraft: forceSaveDraft,
  });

  const handleRestoreDraft = useCallback(() => {
    restoreDraft();
    pushToast({
      tone: "success",
      title: "Draft restored",
      message: "Your autosaved prompts and settings are back.",
    });
  }, [restoreDraft, pushToast]);

  const handleApplyPrompt = useCallback(
    (prompt: string) => {
      const fieldId =
        mode === "prompt" ? "directionPrompt" : form.text.mainPrompt !== undefined ? "mainPrompt" : "prompt";
      setTextField(fieldId, prompt);
      setStudioScreen("create");
    },
    [form.text.mainPrompt, mode, setTextField]
  );

  const handleLoadWorkflow = useCallback(
    (workflow: SavedWorkflow) => {
      setMode(workflow.mode);
      setCategory(workflow.category);
      setVisualStyle(workflow.visualStyle);
      setForm((prev) => {
        const merged: StudioFormState = {
          ...prev,
          text: { ...createInitialFormState().text, ...workflow.text },
        };
        if (!workflow.category) return merged;
        return pruneFormToVisible(
          merged,
          workflow.category,
          workflow.mode,
          workflow.visualStyle
        );
      });
      setWizardStep(WIZARD_FIRST_GROUP_STEP);
      setStudioScreen("create");
    },
    []
  );

  const handleSelectRecent = useCallback(
    (project: { id: string }) => {
      const item = carouselItems.find((entry) => entry.id === project.id);
      if (item && profile) {
        handleSelectVideo(userVideoAssetToGeneratedVideo(item, profile.id));
        return;
      }
      setStudioScreen("preview");
      void serverGallery.refresh();
    },
    [carouselItems, profile, serverGallery]
  );

  const getWorkflowSnapshot = useCallback(() => {
    if (!mode || !visualStyle) return null;
    return {
      mode,
      category,
      visualStyle,
      text: { ...form.text },
    };
  }, [category, form.text, mode, visualStyle]);

  const segmentPlan = useMemo(
    () => computeSegmentPlan(durationSeconds),
    [durationSeconds]
  );
  const generationEtaWindow = useMemo(
    () => estimateProcessingWindow(durationSeconds, { segmentCount: segmentPlan.segmentCount }),
    [durationSeconds, segmentPlan.segmentCount]
  );
  const queueActiveCount =
    studioMetrics?.concurrentTracks ?? studioMetrics?.renderingQueues ?? 0;
  const queueMaxCount = studioMetrics?.maxConcurrentGenerations ?? 3;
  const pipelineVisible =
    processing ||
    genUi.active ||
    genPhase === "error" ||
    genPhase === "success" ||
    genPhase === "cancelled";

  const premiumPipeline = profile
    ? hasPremiumAccess(profile, durationSeconds)
    : false;
  const wizardTotalSteps = getWizardStepCount(category, mode, visualStyle);
  const currentWizardGroup = getWizardGroupAtStep(
    wizardStep,
    category,
    mode,
    visualStyle
  );
  const maxWizardStep = wizardTotalSteps - 1;
  const isLastWizardStep =
    wizardStep >= WIZARD_FIRST_GROUP_STEP && wizardStep === maxWizardStep;
  const canGoPrevious = wizardStep > WIZARD_SETUP_STEP && !isLoading;
  const uploadDisabled =
    isLoading || !category || Boolean(generationLimitReached);
  const showStudioDebugPanel =
    process.env.NODE_ENV === "development" ||
    (pipelineDiagnostic !== null && isStudioOwner(profile));
  const wizardStepLabel =
    wizardStep === WIZARD_SETUP_STEP
      ? "Mode, category & style"
      : currentWizardGroup?.label ?? "Create";
  const wizardProgressPct = Math.round(((wizardStep + 1) / wizardTotalSteps) * 100);

  if (!profile) {
    return <StudioSkeleton />;
  }

  return (
    <>
      <PremiumPaywallModal
        open={showPaywall}
        message={paywallMessage}
        onSubscribeTester={handleSubscribeTester}
        onSubscribeStandard={handleSubscribeStandard}
        onSubscribePremium={handleSubscribePremium}
        onClose={handleClosePaywall}
      />

      <ShareVideoModal
        open={Boolean(shareVideo)}
        video={shareVideo}
        onClose={() => setShareVideo(null)}
        onPublished={handleSharePublished}
      />

      <DurationLimitModal
        open={showDurationLimit}
        message={durationLimitMessage}
        maxAllowedSeconds={durationLimitMax}
        onClose={() => setShowDurationLimit(false)}
        onRecharge={() => {
          setShowDurationLimit(false);
          setShowPaywall(true);
          setPaywallMessage(durationLimitMessage);
        }}
      />

      <EarlyResubscribeModal
        open={showEarlyResubscribe}
        remainingCredits={profile.credits}
        creditsExpireAt={profile.creditsExpireAt}
        onConfirm={() =>
          void proceedToCheckout(pendingCheckoutPlan, { rolloverRemaining: true })
        }
        onCancel={() => setShowEarlyResubscribe(false)}
      />

      <GenerationStartedModal
        open={showGenStartedModal}
        title="Generation started"
        message="Your video is rendering in our cloud pipeline. You can keep editing or browse past renders while you wait."
        minMinutes={generationEtaWindow.minMinutes}
        maxMinutes={generationEtaWindow.maxMinutes}
        segmentCount={segmentPlan.segmentCount}
        onClose={() => setShowGenStartedModal(false)}
      />

      <div
        className={`shashka-studio shashka-studio--screen-${studioScreen}${mode ? " shashka-studio--has-mode" : ""}${isLoading ? " shashka-studio--locked" : ""}`}
      >
        {showStudioDebugPanel ? (
          <aside
            className={`studio-debug-panel${studioDebugOpen ? " studio-debug-panel--open" : ""}${pipelineDiagnostic ? " studio-debug-panel--alert" : ""}`}
            aria-label="Studio debug panel"
          >
            <button
              type="button"
              className="studio-debug-panel__toggle"
              onClick={() => setStudioDebugOpen((open) => !open)}
            >
              {studioDebugOpen ? "Hide Studio Metrics" : "Show Studio Metrics"}
            </button>
            {studioDebugOpen ? (
              <div className="studio-debug-panel__body">
                <h3>Studio Metrics</h3>
                {pipelineDiagnostic ? (
                  <div className="studio-debug-panel__alert" role="alert">
                    <strong>{pipelineDiagnostic.error}</strong>
                    <p>{pipelineDiagnostic.details}</p>
                    {pipelineDiagnostic.code ? (
                      <span className="studio-debug-panel__code">
                        code: {pipelineDiagnostic.code}
                      </span>
                    ) : null}
                  </div>
                ) : null}
                <dl className="studio-debug-panel__grid">
                  <div>
                    <dt>renderingQueues</dt>
                    <dd>
                      {studioMetrics?.renderingQueues ?? 0} /{" "}
                      {studioMetrics?.maxConcurrentGenerations ?? 3}
                    </dd>
                  </div>
                  <div>
                    <dt>videoGenerationCredits</dt>
                    <dd>{studioMetrics?.videoGenerationCredits ?? profile.credits}</dd>
                  </div>
                  <div>
                    <dt>prompt</dt>
                    <dd>{currentPrompt}</dd>
                  </div>
                  <div>
                    <dt>inputImage</dt>
                    <dd>{currentInputImage}</dd>
                  </div>
                  <div>
                    <dt>generatedVideoUrl</dt>
                    <dd>{currentGeneratedVideoUrl}</dd>
                  </div>
                  <div
                    className={
                      pipelineDiagnostic ? "studio-debug-panel__row--failed" : undefined
                    }
                  >
                    <dt>status</dt>
                    <dd
                      className={
                        pipelineDiagnostic
                          ? "studio-debug-panel__status--failed"
                          : undefined
                      }
                    >
                      {currentGenerationStatus}
                    </dd>
                  </div>
                </dl>
                {pipelineDiagnostic ? (
                  <button
                    type="button"
                    className="studio-debug-panel__action studio-debug-panel__action--retry"
                    onClick={handleRetryGeneration}
                  >
                    Retry Generation
                  </button>
                ) : null}
              </div>
            ) : null}
          </aside>
        ) : null}
        <StudioScreenRail
          screen={studioScreen}
          onScreenChange={setStudioScreen}
          createLocked={isLoading}
        />
        <div className="shashka-lock-veil" aria-hidden />

        <div className="shashka-studio__content">
          {studioScreen === "create" ? (
            <div className="shashka-studio__create-screen">
            <div
              className={`shashka-studio__sidebar${formLocked ? " shashka-studio__sidebar--locked" : ""}`}
              aria-busy={formLocked}
            >
              {formLocked ? (
                <div
                  className="studio-sidebar-lock-overlay"
                  aria-hidden
                  onClick={(e) => e.preventDefault()}
                />
              ) : null}
            <div
              key={`create-wizard-${formSessionKey}`}
              className="shashka-holo-stack create-panel"
            >
              <div className="shashka-holo-widget create-panel-unified">
              <header className="create-panel-unified__bar">
                <div className="create-panel-unified__bar-top">
                  <h2>Create your video</h2>
                  <AutosaveIndicator savedAt={lastSavedAt} saving={saving} />
                </div>
                {showDraftBanner && pendingDraft ? (
                  <DraftRestoreBanner
                    draft={pendingDraft}
                    onRestore={handleRestoreDraft}
                    onDismiss={dismissDraft}
                  />
                ) : null}
                <p className="create-panel-unified__tagline">
                  Describe your scene, generate, then preview the result.
                </p>
                {!mode && !showDraftBanner ? (
                  <EmptyState
                    className="studio-empty-project"
                    icon="✦"
                    title="Start a new project"
                    description="Choose a mode below. Your draft autosaves as you go — nothing is lost if you leave."
                    actionLabel="60-second category guide →"
                    actionHref="/how-to-use#categories"
                    actionVariant="ghost"
                    secondaryActionLabel="View pricing"
                    secondaryActionHref="/pricing"
                  />
                ) : null}
                <div className="studio-wizard-progress-wrap">
                  <div
                    className="studio-wizard-progress"
                    role="progressbar"
                    aria-valuenow={wizardStep + 1}
                    aria-valuemin={1}
                    aria-valuemax={wizardTotalSteps}
                    aria-label={`Step ${wizardStep + 1} of ${wizardTotalSteps}`}
                  >
                    <div
                      className="studio-wizard-progress__fill"
                      style={{ width: `${wizardProgressPct}%` }}
                    />
                  </div>
                  <div className="studio-wizard-progress__meta">
                    <span>
                      Step <strong>{wizardStep + 1}</strong> of {wizardTotalSteps}
                    </span>
                    <span className="studio-wizard-progress__step-name">{wizardStepLabel}</span>
                  </div>
                </div>
                <details className="studio-advanced">
                  <summary>Keyboard shortcuts</summary>
                  <div className="studio-advanced__body">
                    <StudioShortcutsHint className="studio-shortcuts-hint--create" />
                  </div>
                </details>
                {formNotice ? (
                  <p className="studio-form-notice" role="alert">
                    {formNotice}
                  </p>
                ) : null}
                {isLoading ? (
                  <p className="create-panel-lock-notice" role="status">
                    Rendering — fields locked until complete.
                  </p>
                ) : null}
              </header>

              {wizardStep === WIZARD_SETUP_STEP ? (
                <div className="shashka-wizard-step shashka-wizard-step--setup">
                  <div className="shashka-wizard-step__head">
                    <p className="shashka-wizard-step__label">Mode, category &amp; style</p>
                    <p className="shashka-wizard-step__hint">
                      Choose each option in order — nothing is pre-selected.
                    </p>
                  </div>
                  <div className="shashka-wizard-step__body">
                    <fieldset className="create-panel-fieldset" disabled={isLoading}>
                      {isStudioOwner(profile) ? (
                        <details className="studio-advanced studio-advanced--connection">
                          <summary>Connection</summary>
                          <div className="studio-advanced__body">
                            <p className="api-status" title={apiBase}>
                              API:{" "}
                              {backendOnline === null
                                ? "checking…"
                                : backendOnline
                                  ? "connected"
                                  : "offline"}
                              {falGuard?.billingBlocked ? (
                                <span className="api-status-warn"> · Fal paused</span>
                              ) : null}
                            </p>
                          </div>
                        </details>
                      ) : null}

                      <section
                        className={`studio-setup-section studio-setup-section--mode${
                          setupPhase === "mode" ? " studio-setup-section--active" : ""
                        }`}
                      >
                        <p className="section-label">Mode</p>
                        <p className="studio-setup-section__prompt">
                          {mode ? "Selected — you can change anytime." : "Pick how your video starts."}
                        </p>
                        <div className="chip-row">
                          {(
                            [
                              ["prompt", "Prompt → Video"],
                              ["image", "Image → Video"],
                            ] as const
                          ).map(([m, label]) => (
                            <button
                              key={m}
                              type="button"
                              className={`chip ${mode === m ? "active" : ""}`}
                              onClick={() => handleModeSelect(m)}
                              disabled={isLoading}
                              aria-pressed={mode === m}
                            >
                              {label}
                            </button>
                          ))}
                        </div>
                      </section>

                      {mode ? (
                        <section
                          ref={setupCategoryRef}
                          className={`studio-setup-section studio-setup-section--category${
                            setupPhase === "category" ? " studio-setup-section--active" : ""
                          }`}
                        >
                          <p className="section-label">Category</p>
                          <p className="studio-setup-section__prompt">
                            {category
                              ? "Selected — pick another to change."
                              : "Choose your video type."}
                          </p>
                          <div className="chip-row">
                            {(Object.keys(CATEGORY_META) as VideoCategory[]).map((c) => (
                              <button
                                key={c}
                                type="button"
                                className={`chip ${category === c ? "active" : ""}`}
                                onClick={() => handleCategorySelect(c)}
                                title={CATEGORY_META[c].description}
                                disabled={isLoading}
                                aria-pressed={category === c}
                              >
                                {CATEGORY_META[c].shortLabel}
                              </button>
                            ))}
                          </div>
                        </section>
                      ) : null}

                      {mode && category ? (
                        <section
                          ref={setupStyleRef}
                          className={`studio-setup-section studio-setup-section--style${
                            setupPhase === "style" ? " studio-setup-section--active" : ""
                          }`}
                        >
                          <VisualStyleSelector
                            value={visualStyle}
                            onChange={handleVisualStyleSelect}
                            disabled={isLoading}
                            compact
                          />
                        </section>
                      ) : null}

                      {mode && category && visualStyle ? (
                        <section
                          ref={setupTitleRef}
                          className={`studio-setup-section studio-setup-section--title${
                            setupPhase === "title" ? " studio-setup-section--active" : ""
                          }`}
                        >
                          <div className="field field--video-title">
                            <label htmlFor={VIDEO_TITLE_FIELD_ID}>Video Title</label>
                            <input
                              id={VIDEO_TITLE_FIELD_ID}
                              type="text"
                              className={
                                fieldErrors[VIDEO_TITLE_FIELD_ID] ? "field-error" : undefined
                              }
                              placeholder="Name shown in Your videos list"
                              value={form.text[VIDEO_TITLE_FIELD_ID] ?? ""}
                              onChange={(e) => setTextField(VIDEO_TITLE_FIELD_ID, e.target.value)}
                              disabled={isLoading}
                              aria-invalid={Boolean(fieldErrors[VIDEO_TITLE_FIELD_ID])}
                            />
                            {fieldErrors[VIDEO_TITLE_FIELD_ID] ? (
                              <p className="field-error">{fieldErrors[VIDEO_TITLE_FIELD_ID]}</p>
                            ) : (
                              <p className="help">
                                This exact name appears in Your videos and the preview player.
                              </p>
                            )}
                          </div>
                        </section>
                      ) : null}
                    </fieldset>
                  </div>
                  <div className="shashka-wizard-step__footer">
                    <div className="shashka-wizard-nav">
                      <button
                        type="button"
                        className="shashka-wizard-nav__prev"
                        disabled={!canGoPrevious}
                        onClick={goPreviousWizard}
                      >
                        ← Previous
                      </button>
                      <button
                        type="button"
                        className="shashka-wizard-nav__next"
                        disabled={isLoading || !setupComplete}
                        onClick={advanceWizard}
                      >
                        Next →
                      </button>
                    </div>
                  </div>
                </div>
              ) : null}

              {currentWizardGroup && category ? (
                <div
                  className={`shashka-wizard-step shashka-wizard-step--${currentWizardGroup.id}`}
                >
                  <div className="shashka-wizard-step__head">
                    <p className="shashka-wizard-step__label">
                      {currentWizardGroup.label}
                    </p>
                  </div>
                  <div className="shashka-wizard-step__body">
                    {currentWizardGroup.id === "face-lock" &&
                    visualStyle === "real" ? (
                      <div className="shashka-face-lock-stage">
                        <FacialReferenceHero
                          faceFile={form.files.faceReference ?? null}
                          visible
                        />
                        <FacialConsistencyShield premium showTagline />
                      </div>
                    ) : null}
                    {currentWizardGroup.fields.length > 0 ? (
                      <fieldset
                        className="create-panel-fieldset"
                        disabled={isLoading}
                      >
                        <CategoryWizardGroup
                          fields={currentWizardGroup.fields}
                          form={form}
                          fieldErrors={fieldErrors}
                          disabled={isLoading}
                          maxDurationSeconds={maxDurationSeconds}
                          onTextChange={setTextField}
                          onFileChange={setFileField}
                        />
                      </fieldset>
                    ) : null}
                  </div>
                  <div className="shashka-wizard-step__footer">
                    {isLastWizardStep ? (
                      <>
                        {formNotice ? (
                          <p
                            className="studio-form-notice studio-form-notice--generate"
                            role="alert"
                          >
                            {formNotice}
                          </p>
                        ) : null}
                        {generationLimitReached && generationLimitMessage ? (
                          <p
                            className="studio-form-notice studio-form-notice--generate"
                            role="alert"
                          >
                            {generationLimitMessage}
                          </p>
                        ) : null}
                        <div className="shashka-wizard-actions">
                          <button
                            type="button"
                            className="shashka-wizard-nav__prev"
                            disabled={!canGoPrevious}
                            onClick={goPreviousWizard}
                          >
                            ← Previous
                          </button>
                          <button
                            type="button"
                            className="shashka-console__generate"
                            disabled={uploadDisabled}
                            aria-busy={isLoading}
                            onClick={() => void onGenerateClick()}
                            title={generationLimitReached ? generationLimitMessage ?? undefined : undefined}
                          >
                            {isLoading ? "Rendering…" : "Generate video"}
                          </button>
                        </div>
                        <details className="studio-advanced studio-advanced--more-actions">
                          <summary>More actions</summary>
                          <div className="studio-advanced__body">
                            <button
                              type="button"
                              className="shashka-console__compile"
                              disabled={!canCompileVideo}
                              aria-busy={compileUi.active}
                              title={
                                backendOutputClipCount < MIN_CLIPS_TO_COMPILE
                                  ? `Need ${MIN_CLIPS_TO_COMPILE}+ clips in apps/backend/data/outputs (${backendOutputClipCount}/${MIN_CLIPS_TO_COMPILE})`
                                  : compileStatusReady
                                    ? "Merge clips into one 5-minute video"
                                    : "Waiting for FFmpeg or stitcher setup"
                              }
                              onClick={() => void onCompileClick()}
                            >
                              {compileUi.active ? "Compiling…" : "Compile video"}
                            </button>
                            <p className="shashka-console__footnote shashka-console__footnote--compile">
                              Merge saved clips into one longer video when you have enough renders.
                            </p>
                          </div>
                        </details>
                        {compileUi.active ? (
                          <div
                            className="shashka-console__compile-progress"
                            role="progressbar"
                            aria-valuenow={compileUi.percent}
                            aria-valuemin={0}
                            aria-valuemax={100}
                          >
                            <div className="shashka-console__compile-track">
                              <div
                                className="shashka-console__compile-fill"
                                style={{ width: `${compileUi.percent}%` }}
                              />
                            </div>
                            <p className="shashka-console__compile-label">
                              {compileUi.message} ({compileUi.percent}%)
                            </p>
                          </div>
                        ) : null}
                        <p className="shashka-console__footnote">
                          Est. {creditsNeeded} credits
                          {isPaidUser
                            ? ` · ${effectiveRemainingSeconds} left`
                            : " · Subscribe"}
                          {` · ${backendOutputClipCount}/${MIN_CLIPS_TO_COMPILE} backend clips`}
                        </p>
                      </>
                    ) : (
                      <div className="shashka-wizard-nav">
                        <button
                          type="button"
                          className="shashka-wizard-nav__prev"
                          disabled={!canGoPrevious}
                          onClick={goPreviousWizard}
                        >
                          ← Previous
                        </button>
                        <button
                          type="button"
                          className="shashka-wizard-nav__next"
                          disabled={isLoading}
                          onClick={advanceWizard}
                        >
                          Next →
                        </button>
                      </div>
                    )}
                  </div>
                </div>
              ) : null}
              </div>
            </div>
            </div>
            </div>
          ) : null}

          {studioScreen === "preview" ? (
          <div className="shashka-preview-layout">
            <div
              ref={previewPanelRef}
              id="studio-preview"
              className="shashka-preview-main studio-preview-panel"
              aria-label="Video preview"
            >
              <div className="shashka-preview-header">
                <h2>{isLoading ? "Rendering" : "Preview"}</h2>
                <Button
                  type="button"
                  variant="secondary"
                  className="studio-back-to-editor"
                  onClick={() => setStudioScreen("create")}
                  disabled={isLoading}
                  title={isLoading ? "Wait for render to finish" : "Return to create wizard"}
                >
                  {isLoading ? "Rendering…" : "← Create"}
                </Button>
              </div>

              {showConnectionBanner && isStudioOwner(profile) && (
                <BackendConnectionNotice
                  title={connectionNoticeTitle}
                  message={connectionError!}
                  hint={connectionNoticeHint}
                  onDismiss={resetGenerationView}
                />
              )}

              <div className="shashka-preview-frame">
                <VideoPlayer
                  src={activePlaybackSrc}
                  title={isGenerating ? undefined : activeVideo?.title}
                  isGenerating={isGenerating}
                  showProgressOverlay={isGenerating}
                  generationPercent={genUi.percent}
                  generationMessage={genUi.message}
                  generationStageIndex={genUi.stageIndex}
                  generationPatienceMessage={generationPatienceMessage}
                />
              </div>
              {activeVideo?.status === "ready" && activeVideo.videoUrl && !isGenerating ? (
                <div className="shashka-preview-share-row">
                  <Button
                    type="button"
                    variant="secondary"
                    className="btn-share-video"
                    onClick={() => handleShareVideo(activeVideo)}
                  >
                    Share Video
                  </Button>
                  {activeVideo.isPublic ? (
                    <span className="shashka-preview-share-note">Public link active</span>
                  ) : null}
                </div>
              ) : null}
            </div>

            <aside
              className="shashka-preview-side"
              aria-label="Generation status and your videos"
            >
              <GenerationPipelinePanel
                ref={progressRef}
                active={pipelineVisible}
                phase={
                  genPhase === "error"
                    ? "error"
                    : genPhase === "success"
                      ? "success"
                      : genPhase === "cancelled"
                        ? "cancelled"
                        : "running"
                }
                percent={genUi.percent}
                message={genUi.message}
                stageIndex={genUi.stageIndex}
                durationSeconds={durationSeconds}
                segmentCount={segmentPlan.segmentCount}
                startedAt={generationStartedAtRef.current}
                queueActive={queueActiveCount}
                queueMax={queueMaxCount}
                modelLabel={generationModelLabel}
                videoTitle={activeVideo?.title}
                canDownload={Boolean(activeVideo?.canDownload)}
                downloadUrl={activeVideo?.videoUrl}
                onCancel={genPhase === "running" ? handleCancelGeneration : undefined}
                onRetry={genPhase === "error" ? handlePipelineRetry : undefined}
                retryLoading={retryLoading}
                onPreview={
                  genPhase === "success" && activeVideo?.videoUrl
                    ? handleSuccessPreview
                    : undefined
                }
                onDownload={
                  genPhase === "success" && activeVideo?.videoUrl
                    ? handleSuccessDownload
                    : undefined
                }
                onRegenerate={genPhase === "success" ? handlePipelineRetry : undefined}
                onEditPrompt={genPhase === "success" ? handleEditPrompt : undefined}
                onCreateVariation={
                  genPhase === "success" ? handleCreateVariation : undefined
                }
                onDismiss={
                  genPhase === "success" || genPhase === "error" || genPhase === "cancelled"
                    ? handleDismissPipeline
                    : undefined
                }
              />

              <details className="studio-side-card">
                <summary>Workflow</summary>
                <div className="studio-side-card__body">
                  <StudioWorkflowPanel
                    currentPrompt={currentPrompt === "—" ? "" : currentPrompt}
                    canSaveWorkflow={Boolean(mode && visualStyle && !isLoading)}
                    onApplyPrompt={handleApplyPrompt}
                    onLoadWorkflow={handleLoadWorkflow}
                    onSelectRecent={handleSelectRecent}
                    getWorkflowSnapshot={getWorkflowSnapshot}
                  />
                </div>
              </details>

              <details className="studio-side-card">
                <summary>Library</summary>
                <div className="studio-side-card__body">
                  <StudioVideoCarousel
                    items={carouselItems}
                    activeVideoId={activeVideo?.id}
                    profile={profile}
                    disabled={processing}
                    hasMore={serverGallery.hasMore}
                    loadingMore={serverGallery.loadingMore}
                    onLoadMore={handleCarouselLoadMore}
                    onRefresh={handleCarouselRefresh}
                    onSelect={handleCarouselSelect}
                    onShare={handleCarouselShare}
                  />
                </div>
              </details>

              {isStudioOwner(profile) ? (
                <details className="studio-side-card">
                  <summary>Diagnostics</summary>
                  <div className="studio-side-card__body">
                    <StudioDiagnosticsHud
                      profile={profile}
                      backendOnline={backendOnline}
                      premiumPipeline={premiumPipeline}
                      statusText={statusText}
                      apiBase={apiBase}
                      falBillingBlocked={Boolean(falGuard?.billingBlocked)}
                      diagnosticLock={isLoading}
                      onTrialSkip={() => void runGenerate({ previewOnly: true })}
                    />
                  </div>
                </details>
              ) : null}
            </aside>
          </div>
          ) : null}
        </div>
      </div>
      <StudioToast toast={studioToast} onDismiss={dismissToast} />
    </>
  );
}
