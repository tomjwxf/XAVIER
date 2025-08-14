# Incident Codes (Receipts-Only MVP)

- **SKIP_NO_PERMITS** — No travel-rule/permits in place for the route; skip receipt emission.
- **FAIL_APPROVAL** — Internal approval failed.
- **ROUTE_DEGRADED** — Corridor routing degraded; expect delayed emission.
- **RELAY_DEGRADED** — External relay dependency degraded; expect delayed emission.
- **POLICY_BLOCK** — Blocked by compliance policy.
- **TRAVEL_RULE_UNAVAILABLE** — Travel rule provider unavailable; emit when restored.
