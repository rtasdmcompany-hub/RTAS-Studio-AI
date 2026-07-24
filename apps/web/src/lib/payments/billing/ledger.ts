import type { PaymentProvider, PaymentWebhookEvent } from "@rtas/shared";
import type { LedgerAction } from "@rtas/utils/payments";
import { prisma, isPrismaConfigured } from "@/lib/prisma";
import {
  readJsonDocument,
  writeJsonDocument,
} from "@/lib/server/persistent-store";
import { AnalyticsEvents, trackServerEvent } from "@/lib/analytics";

const LEDGER_STORE = "billing-ledger";

type LedgerFile = {
  webhooks: Array<{
    provider: string;
    eventId: string;
    eventType: string;
    userId?: string;
    processed: boolean;
    duplicate?: boolean;
    createdAt: string;
  }>;
  transactions: Array<{
    id: string;
    userId: string;
    provider: string;
    externalId?: string;
    eventType: string;
    status: string;
    amountUsd: number;
    planKey?: string;
    creditsGranted: number;
    createdAt: string;
  }>;
  invoices: Array<{
    id: string;
    invoiceNumber: string;
    userId: string;
    provider: string;
    status: string;
    amountUsd: number;
    planKey?: string;
    periodEnd?: string;
    paidAt?: string;
    createdAt: string;
  }>;
  subscriptions: Array<{
    userId: string;
    planKey: string;
    status: string;
    billingCycle: string;
    externalSubscriptionId?: string;
    periodEnd?: string;
    cancelAtPeriodEnd?: boolean;
    updatedAt: string;
  }>;
};

function emptyLedger(): LedgerFile {
  return { webhooks: [], transactions: [], invoices: [], subscriptions: [] };
}

function invoiceNumber(): string {
  const d = new Date();
  const stamp = d.toISOString().slice(0, 10).replace(/-/g, "");
  const rand = Math.random().toString(36).slice(2, 8).toUpperCase();
  return `RTAS-${stamp}-${rand}`;
}

export async function recordWebhookAudit(input: {
  provider: string;
  eventId: string;
  eventType: string;
  userId?: string;
  signatureValid: boolean;
  processed: boolean;
  duplicate?: boolean;
  error?: string;
  payload?: unknown;
}): Promise<void> {
  if (await isPrismaConfigured()) {
    try {
      await prisma.billingWebhookEvent.upsert({
        where: {
          provider_eventId: {
            provider: input.provider,
            eventId: input.eventId,
          },
        },
        create: {
          provider: input.provider,
          eventId: input.eventId,
          eventType: input.eventType,
          userId: input.userId || null,
          signatureValid: input.signatureValid,
          processed: input.processed,
          duplicate: input.duplicate ?? false,
          error: input.error ?? null,
          payloadJson: input.payload as object | undefined,
        },
        update: {
          processed: input.processed,
          duplicate: input.duplicate ?? false,
          error: input.error ?? null,
        },
      });
      return;
    } catch (err) {
      console.error("[billing-ledger] webhook audit prisma failed", err);
    }
  }

  const store = await readJsonDocument<LedgerFile>(LEDGER_STORE, emptyLedger());
  store.webhooks.unshift({
    provider: input.provider,
    eventId: input.eventId,
    eventType: input.eventType,
    userId: input.userId,
    processed: input.processed,
    duplicate: input.duplicate,
    createdAt: new Date().toISOString(),
  });
  store.webhooks = store.webhooks.slice(0, 500);
  await writeJsonDocument(LEDGER_STORE, store);
}

export async function applyLedgerActions(input: {
  userId: string;
  provider: PaymentProvider;
  event: PaymentWebhookEvent;
  actions: LedgerAction[];
}): Promise<void> {
  const { userId, provider, actions } = input;
  let invoiceId: string | null = null;

  for (const action of actions) {
    if (action.kind === "invoice") {
      const number = invoiceNumber();
      if (await isPrismaConfigured()) {
        try {
          const inv = await prisma.billingInvoice.create({
            data: {
              userId,
              invoiceNumber: number,
              provider,
              externalId: action.paymentId ?? null,
              status: action.status,
              amountUsd: action.amountUsd,
              planKey: action.planKey,
              periodEnd: action.periodEnd ? new Date(action.periodEnd) : null,
              paidAt: action.status === "paid" ? new Date() : null,
            },
          });
          invoiceId = inv.id;
          trackServerEvent(AnalyticsEvents.INVOICE_CREATED, {
            userId,
            provider,
            invoiceId: inv.id,
            amountUsd: action.amountUsd,
            planKey: action.planKey,
            status: action.status,
          });
          continue;
        } catch (err) {
          console.error("[billing-ledger] invoice prisma failed", err);
        }
      }
      const store = await readJsonDocument<LedgerFile>(LEDGER_STORE, emptyLedger());
      const id = `inv_${Date.now()}`;
      invoiceId = id;
      store.invoices.unshift({
        id,
        invoiceNumber: number,
        userId,
        provider,
        status: action.status,
        amountUsd: action.amountUsd,
        planKey: action.planKey,
        periodEnd: action.periodEnd,
        paidAt: action.status === "paid" ? new Date().toISOString() : undefined,
        createdAt: new Date().toISOString(),
      });
      store.invoices = store.invoices.slice(0, 500);
      await writeJsonDocument(LEDGER_STORE, store);
      trackServerEvent(AnalyticsEvents.INVOICE_CREATED, {
        userId,
        provider,
        invoiceId: id,
        amountUsd: action.amountUsd,
        planKey: action.planKey,
        status: action.status,
      });
    }

    if (action.kind === "transaction") {
      if (await isPrismaConfigured()) {
        try {
          await prisma.billingTransaction.create({
            data: {
              userId,
              provider,
              externalId: action.paymentId ?? null,
              eventType: action.eventType,
              status: action.status,
              amountUsd: action.amountUsd,
              planKey: action.planKey ?? null,
              creditsGranted: action.creditsGranted,
              externalSubscriptionId: action.externalSubscriptionId ?? null,
              invoiceId,
            },
          });
          if (action.creditsGranted > 0) {
            trackServerEvent(AnalyticsEvents.CREDITS_PURCHASED, {
              userId,
              provider,
              credits: action.creditsGranted,
              amountUsd: action.amountUsd,
              planKey: action.planKey ?? undefined,
              eventType: action.eventType,
            });
          }
          continue;
        } catch (err) {
          console.error("[billing-ledger] transaction prisma failed", err);
        }
      }
      const store = await readJsonDocument<LedgerFile>(LEDGER_STORE, emptyLedger());
      store.transactions.unshift({
        id: `txn_${Date.now()}`,
        userId,
        provider,
        externalId: action.paymentId,
        eventType: action.eventType,
        status: action.status,
        amountUsd: action.amountUsd,
        planKey: action.planKey,
        creditsGranted: action.creditsGranted,
        createdAt: new Date().toISOString(),
      });
      store.transactions = store.transactions.slice(0, 500);
      await writeJsonDocument(LEDGER_STORE, store);
      if (action.creditsGranted > 0) {
        trackServerEvent(AnalyticsEvents.CREDITS_PURCHASED, {
          userId,
          provider,
          credits: action.creditsGranted,
          amountUsd: action.amountUsd,
          planKey: action.planKey ?? undefined,
          eventType: action.eventType,
        });
      }
    }

    if (action.kind === "subscription_upsert") {
      if (await isPrismaConfigured()) {
        try {
          const existing = await prisma.userSubscription.findFirst({
            where: { userId, status: { in: ["active", "past_due", "cancelled"] } },
            orderBy: { updatedAt: "desc" },
          });
          const data = {
            planKey: action.planKey,
            billingCycle: action.billingCycle,
            status: action.status,
            externalSubscriptionId: action.externalSubscriptionId ?? null,
            currentPeriodEnd: action.periodEnd
              ? new Date(action.periodEnd)
              : null,
            cancelAtPeriodEnd: action.cancelAtPeriodEnd ?? false,
          };
          if (existing) {
            await prisma.userSubscription.update({
              where: { id: existing.id },
              data,
            });
          } else {
            await prisma.userSubscription.create({
              data: { userId, ...data },
            });
          }
          continue;
        } catch (err) {
          console.error("[billing-ledger] subscription prisma failed", err);
        }
      }
      const store = await readJsonDocument<LedgerFile>(LEDGER_STORE, emptyLedger());
      const idx = store.subscriptions.findIndex((s) => s.userId === userId);
      const row = {
        userId,
        planKey: action.planKey,
        status: action.status,
        billingCycle: action.billingCycle,
        externalSubscriptionId: action.externalSubscriptionId,
        periodEnd: action.periodEnd,
        cancelAtPeriodEnd: action.cancelAtPeriodEnd,
        updatedAt: new Date().toISOString(),
      };
      if (idx >= 0) store.subscriptions[idx] = row;
      else store.subscriptions.unshift(row);
      await writeJsonDocument(LEDGER_STORE, store);
    }
  }
}

export async function getUserBillingSummary(userId: string) {
  if (await isPrismaConfigured()) {
    try {
      const [transactions, invoices, subscription] = await Promise.all([
        prisma.billingTransaction.findMany({
          where: { userId },
          orderBy: { createdAt: "desc" },
          take: 50,
        }),
        prisma.billingInvoice.findMany({
          where: { userId },
          orderBy: { createdAt: "desc" },
          take: 50,
        }),
        prisma.userSubscription.findFirst({
          where: { userId },
          orderBy: { updatedAt: "desc" },
        }),
      ]);
      return {
        transactions: transactions.map((t) => ({
          id: t.id,
          provider: t.provider,
          eventType: t.eventType,
          status: t.status,
          amountUsd: t.amountUsd,
          planKey: t.planKey,
          creditsGranted: t.creditsGranted,
          createdAt: t.createdAt.toISOString(),
        })),
        invoices: invoices.map((i) => ({
          id: i.id,
          invoiceNumber: i.invoiceNumber,
          provider: i.provider,
          status: i.status,
          amountUsd: i.amountUsd,
          planKey: i.planKey,
          periodEnd: i.periodEnd?.toISOString() ?? null,
          paidAt: i.paidAt?.toISOString() ?? null,
          createdAt: i.createdAt.toISOString(),
        })),
        subscription: subscription
          ? {
              planKey: subscription.planKey,
              status: subscription.status,
              billingCycle: subscription.billingCycle,
              renewsAt: subscription.currentPeriodEnd?.toISOString() ?? null,
              cancelAtPeriodEnd: subscription.cancelAtPeriodEnd,
            }
          : null,
      };
    } catch (err) {
      console.error("[billing-ledger] summary prisma failed", err);
    }
  }

  const store = await readJsonDocument<LedgerFile>(LEDGER_STORE, emptyLedger());
  const sub = store.subscriptions.find((s) => s.userId === userId) ?? null;
  return {
    transactions: store.transactions.filter((t) => t.userId === userId),
    invoices: store.invoices.filter((i) => i.userId === userId),
    subscription: sub
      ? {
          planKey: sub.planKey,
          status: sub.status,
          billingCycle: sub.billingCycle,
          renewsAt: sub.periodEnd ?? null,
          cancelAtPeriodEnd: sub.cancelAtPeriodEnd ?? false,
        }
      : null,
  };
}
