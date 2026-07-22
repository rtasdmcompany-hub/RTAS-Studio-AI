/**

 * Soften raw pipeline / API errors for studio UI.

 * Keeps technical text available via disclosure, never invents backend signals.

 */

import { SITE_SUPPORT_EMAIL } from "@/lib/site-links";

export type SoftenedGenerationError = {

  title: string;

  summary: string;

  details: string | null;

};



const REPORT_ISSUE_MAILTO =

  `mailto:${SITE_SUPPORT_EMAIL}?subject=` +

  encodeURIComponent("RTAS Studio AI — Generation Issue");



export function getReportIssueMailto(context?: string): string {

  if (!context?.trim()) return REPORT_ISSUE_MAILTO;

  const body = encodeURIComponent(`Details:\n\n${context.trim().slice(0, 1500)}`);

  return `${REPORT_ISSUE_MAILTO}&body=${body}`;

}



export function softenGenerationError(raw: string): SoftenedGenerationError {

  const trimmed = raw?.trim() ?? "";

  if (!trimmed) {

    return {

      title: "Generation failed",

      summary: "Something went wrong while rendering. You can resume when you are ready.",

      details: null,

    };

  }



  const lower = trimmed.toLowerCase();



  if (lower.includes("duration") && lower.includes("literal_error")) {

    return {

      title: "Duration could not be read",

      summary:

        "The cloud renderer could not read the video length. Confirm your duration, then resume generation.",

      details: trimmed,

    };

  }

  if (lower.includes("insufficient fal.ai balance")) {

    return {

      title: "Provider balance is low",

      summary: "Add credit in your Fal.ai billing dashboard, then resume generation.",

      details: trimmed,

    };

  }

  if (lower.includes("aborted") || lower.includes("cancelled")) {

    return {

      title: "Generation was cancelled",

      summary: "Your draft is saved — resume whenever you are ready.",

      details: trimmed.length > 80 ? trimmed : null,

    };

  }

  if (lower.includes("backend server connection") || lower.includes("failed to fetch")) {

    return {

      title: "Connection interrupted",

      summary: "We could not reach the render service. Check that the API is running, then resume.",

      details: trimmed,

    };

  }



  const firstLine = trimmed.split("\n")[0]?.trim() ?? trimmed;

  const summary =

    firstLine.length > 160 ? `${firstLine.slice(0, 157)}…` : firstLine;



  return {

    title: "Generation failed",

    summary,

    details: trimmed !== summary || trimmed.includes("\n") ? trimmed : null,

  };

}


