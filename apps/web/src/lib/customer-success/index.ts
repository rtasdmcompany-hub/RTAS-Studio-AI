export {
  HELP_CATEGORIES,
  HELP_ARTICLES,
  searchHelpArticles,
  articlesByCategory,
  type HelpArticle,
  type HelpCategoryId,
} from "@/lib/customer-success/help-kb";

export {
  TICKET_CATEGORIES,
  TICKET_PRIORITIES,
  TICKET_STATUSES,
  createSupportTicket,
  listUserTickets,
  getUserTicket,
  addCustomerReply,
  serializeTicketForCustomer,
  isTicketCategory,
  isTicketPriority,
  isTicketStatus,
  type TicketCategory,
  type TicketPriority,
  type TicketStatus,
} from "@/lib/customer-success/tickets";

export {
  getCustomerHealth,
  type CustomerHealthSnapshot,
} from "@/lib/customer-success/customer-health";

export {
  buildChurnSignals,
  type RiskLevel,
  type ChurnSignal,
} from "@/lib/customer-success/churn-prevention";

export { getRetentionBundle } from "@/lib/customer-success/retention";
