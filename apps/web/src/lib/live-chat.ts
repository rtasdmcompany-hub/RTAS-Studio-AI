import {
  PREMIUM_CREDITS,
  PREMIUM_PRICE_USD,
  STANDARD_CREDITS,
  STANDARD_PRICE_USD,
  TESTER_CREDITS,
  TESTER_DURATION_DAYS,
  TESTER_PRICE_USD,
} from "@rtas/shared";

export type ChatRole = "user" | "assistant";

export type ChatMessage = {
  role: ChatRole;
  content: string;
};

export const CHAT_QUICK_REPLIES = [
  "How do plans & credits work?",
  "How do I create a video?",
  "How long does rendering take?",
  "Talk to a human",
] as const;

const SUPPORT_EMAIL = "support@rtasdigital.com";

type FaqRule = {
  id: string;
  keywords: string[];
  reply: string;
};

const FAQ_RULES: FaqRule[] = [
  {
    id: "pricing",
    keywords: ["price", "pricing", "plan", "cost", "tester", "standard", "premium", "subscribe", "recharge", "payment", "$"],
    reply: `RTAS STUDIO AI plans:\n\n• Tester — $${TESTER_PRICE_USD} one-time, ${TESTER_CREDITS} seconds (${TESTER_DURATION_DAYS} days) to try the full studio.\n• Standard — $${STANDARD_PRICE_USD}/month, ${STANDARD_CREDITS} seconds/month, HD output + commercial rights.\n• Premium 4K — $${PREMIUM_PRICE_USD}/month, ${PREMIUM_CREDITS} seconds/month, cinematic 4K quality.\n\n1 credit = 1 second of video. See all plans on the Pricing page.`,
  },
  {
    id: "credits",
    keywords: ["credit", "seconds", "balance", "run out", "no credits", "6000", "2000"],
    reply: `Credits work simply: **1 credit = 1 second** of finished video. Your balance shows in the studio header (e.g. "Credits: 2000 — Premium 4K"). When credits run out, go to Pricing to recharge. Tester gives ${TESTER_CREDITS}s; monthly plans give ${STANDARD_CREDITS}s each month.`,
  },
  {
    id: "create",
    keywords: ["create", "studio", "generate", "how to", "start", "wizard", "step"],
    reply: `To create a video:\n1. Open **Studio** and sign in.\n2. Pick mode (Prompt or Image), category, and visual style.\n3. Follow the wizard — title, lyrics/prompt, length, face upload if needed.\n4. Click **Generate video** — you'll move to Preview with a progress bar.\n5. Download from Preview when ready.`,
  },
  {
    id: "time",
    keywords: ["long", "time", "wait", "how many minutes", "rendering", "processing", "slow", "minutes"],
    reply: `Render time depends on video length:\n\n• **15 sec or less** — often a few minutes.\n• **1–3 min** — can take roughly 15–45 minutes.\n• **5 min (300 sec)** — usually about **40–90+ minutes** (many parts render one after another, then stitch).\n\nYou can leave the Preview screen — we'll email you when it's ready.`,
  },
  {
    id: "long-video-fal",
    keywords: [
      "fal",
      "15 second",
      "15 sec",
      "5 min",
      "5 minute",
      "300",
      "segment",
      "stitch",
      "parts",
      "compile",
      "10 min",
    ],
    reply: `Cloud AI (Fal.ai) renders **up to ~15 seconds per clip** — that is normal for all AI video APIs.\n\nWhen you choose **5 minutes**, RTAS does not ask Fal for one 5-min file. Instead it:\n1. Splits your video into **20 × 15-second parts**\n2. Renders each part with the same story, face-lock, and style\n3. **Stitches** all parts into **one full 5-minute MP4** for download\n\nYou need **Standard or Premium** with enough credits (5 min = **300 credits**). Same idea for 3 min or 10 min — automatic parts + stitch.`,
  },
  {
    id: "premium",
    keywords: ["4k", "premium", "difference", "hd", "quality", "which plan"],
    reply: `**Standard** is best for regular HD social & brand content (${STANDARD_CREDITS}s/month).\n\n**Premium 4K** adds cinematic 4K output, stronger identity-lock for faces, and the richest scenes — ideal for music videos and brand films (${PREMIUM_CREDITS}s/month).`,
  },
  {
    id: "face",
    keywords: ["face", "identity", "lock", "photo", "upload", "real face"],
    reply: `For real-face videos, upload a clear front-facing photo in the studio wizard. RTAS uses identity-lock so your face stays consistent across scenes. Choose **Real face** under Visual style, or Avatar/Cartoon for other looks.`,
  },
  {
    id: "account",
    keywords: ["sign in", "login", "account", "google", "register", "signup", "password"],
    reply: `Sign in from the header using Google or email. New users can **Sign up** on the auth page. Your credits and videos stay linked to your account. Profile page shows your plan and balance.`,
  },
  {
    id: "legal",
    keywords: ["terms", "privacy", "cookie", "refund", "commercial"],
    reply: `Legal pages are under **Legal** in the menu (Terms, Privacy, Cookies). Standard and Premium paid plans include commercial rights on exports. For billing questions email ${SUPPORT_EMAIL}.`,
  },
  {
    id: "human",
    keywords: ["human", "agent", "person", "email", "support", "contact", "talk"],
    reply: `Our team is happy to help. Email **${SUPPORT_EMAIL}** and include your account email plus a short description. We typically reply within one business day.`,
  },
];

function scoreRule(rule: FaqRule, text: string): number {
  let score = 0;
  for (const kw of rule.keywords) {
    if (text.includes(kw)) score += kw.length > 4 ? 2 : 1;
  }
  return score;
}

export function buildWelcomeMessage(): string {
  return `Hi! I'm the RTAS STUDIO AI assistant. Ask about plans, credits, the studio wizard, or rendering — or tap a quick question below.`;
}

export function getChatReply(userMessage: string, _history: ChatMessage[] = []): string {
  const text = userMessage.toLowerCase().trim();
  if (!text) {
    return "Please type a question and I'll do my best to help.";
  }

  if (/^(hi|hello|hey|salam|aoa|assalam)/.test(text)) {
    return `Hello! Welcome to RTAS STUDIO AI. How can I help — pricing, creating a video, or credits?`;
  }

  if (/thank|shukriya|thanks/.test(text)) {
    return `You're welcome! If you need anything else, just ask. For urgent issues email ${SUPPORT_EMAIL}.`;
  }

  let best: FaqRule | null = null;
  let bestScore = 0;
  for (const rule of FAQ_RULES) {
    const s = scoreRule(rule, text);
    if (s > bestScore) {
      bestScore = s;
      best = rule;
    }
  }

  if (best && bestScore >= 2) {
    return best.reply;
  }

  return `I'm not fully sure about that. Try asking about **pricing**, **credits**, **how to create a video**, or **render time**. For account-specific help, email ${SUPPORT_EMAIL} and our team will assist you directly.`;
}
