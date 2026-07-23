# Executive Reporting

**Phase:** 13 · Sprint 7  
**UI:** `/admin/executive` → Reports  
**API:** `GET /api/admin/executive-reports?type=...&format=csv|html&period=...`

## Auth

Same admin secret header as other `/api/admin/*` routes.

## Report types

| `type` | Contents |
|--------|----------|
| `executive_summary` | KPI flat table |
| `revenue` | Period current/previous compare |
| `customer` | Customer analytics flat table |
| `ai_usage` | AI usage + daily series + providers |
| `business_alerts` | All alert rules + triggered flag |
| `full_pack` | Compact multi-section CSV |

## Formats

| Format | Status |
|--------|--------|
| **CSV** | Required · primary machine-readable export |
| **HTML** | Printable summary · use browser **Print → Save as PDF** |
| Excel / native PDF libs | **Not bundled** — avoided heavy deps (xlsx/puppeteer). Documented alternative: CSV + printable HTML |

## Example

```
GET /api/admin/executive-reports?type=executive_summary&format=csv
Header: x-rtas-admin-secret: <secret>
```

Response: attachment download (`Content-Disposition`).
