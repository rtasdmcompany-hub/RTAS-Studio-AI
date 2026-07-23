# Customer Segmentation — RTAS Studio AI

**Phase:** 13 · Sprint 4  
**Integrity:** Counts from real DB fields. Empty/zero OK.

## Segments

| ID | Name | Source |
|----|------|--------|
| `visitors` | Visitors | Proxy: `emailVerified=false` (anonymous visitors = N/A) |
| `free_unpaid` | Free (unpaid) | `subscriptionActive=false` |
| `paid` | Paid | `subscriptionActive=true` |
| `enterprise_leads` | Enterprise Leads | `CommercialLead` / `EnterpriseLead` |
| `cancelled` | Cancelled | `paymentProvider` set + not active |
| `inactive` | Inactive | Paid/formerly paid, no jobs in 30d |
| `beta` | Beta | Beta lead rows |
| `newsletter_subscribers` | Newsletter Subscribers | `NewsletterSubscriber.status=subscribed` |

Implementation: `apps/web/src/lib/marketing/segmentation.ts`  
Exposed on: `/api/admin/marketing`
