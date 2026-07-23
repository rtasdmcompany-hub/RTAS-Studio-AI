# System Status — RTAS Studio AI

**Public page:** https://rtasstudio.com/status  
**Date:** 23 July 2026  

---

## Surfaces

| Surface | Purpose |
|---------|---------|
| `/status` | Human-readable subsystem cards, maintenance, incident history structure, live probes |
| `/api/health` | Liveness — process up |
| `/api/ready` | Readiness — critical deps (public body minimal; admin for detail) |
| `/api/status/summary` | Public labels for web / API / GPU / DB / storage / email / auth / billing |
| `/api/auth/config` | Auth configuration probe |

---

## Subsystems (status page)

Web App · Generation API / GPU · Database · Persistent storage · Email · Auth · Billing  

Cards are **probe-backed** descriptions; overall “green” marketing claims are avoided — users are directed to live probe results.

---

## Maintenance & incidents

- Maintenance block: publish windows when scheduled (`MAINTENANCE` in status page source).  
- Incident history: empty until a real incident is recorded — do not invent entries.

---

## Ops cadence

See [FOUNDER_OPERATIONS.md](../operations/FOUNDER_OPERATIONS.md) daily checks for health/ready/status.
