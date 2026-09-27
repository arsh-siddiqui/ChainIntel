# ChainIntel — API Reference

Base URL: `http://localhost:8000`

Interactive docs: **/docs** (Swagger UI) and **/redoc** (ReDoc).

## Response envelope

All endpoints return:

```json
{ "success": true,  "data": { }, "meta": { }, "error": null }
```

Errors:

```json
{ "success": false, "data": null, "meta": { }, "error": { "code": "PROVIDER_UNAVAILABLE", "message": "..." } }
```

Common error codes: `INVALID_WALLET` (400), `NOT_FOUND` family (404), `MONITOR_EXISTS` (409), `VALIDATION_ERROR` (422), `RATE_LIMITED` (429), `REQUEST_TOO_LARGE` / `FILE_TOO_LARGE` (413), `PROVIDER_UNAVAILABLE` / `REQUIRES_CONFIGURATION` (503), `INTERNAL_ERROR` (500).

## Health & meta

| Method | Path | Description |
|---|---|---|
| GET | `/api/health` | Service status, mode, database connectivity |
| GET | `/api` | API index |

## Dashboard & search

| Method | Path | Description |
|---|---|---|
| GET | `/api/dashboard/summary` | KPIs, 30-day activity series, threat/risk distributions, top suspicious counterparties, recent investigations & alerts |
| GET | `/api/search?q=` | Categorized global search: wallets, transactions, cases, threat findings |

## Wallets

| Method | Path | Description |
|---|---|---|
| GET | `/api/wallets/pipeline-steps` | The 9 investigation pipeline steps |
| POST | `/api/wallets/investigate` | Run the full pipeline. Body: `{ "address": "...", "blockchain": "auto\|bitcoin\|ethereum\|bsc" }`. Returns the complete investigation bundle (wallet summary, transactions, threats, OSINT, graph, fund flow, risk). |
| GET | `/api/wallets/{address}` | Cached latest investigation (validation, wallet row, investigation summary, full bundle) |
| GET | `/api/wallets/{address}/transactions` | Paginated/sorted/filtered transactions. Filters: `direction`, `min_amount`, `max_amount`, `start`, `end`; sort: `timestamp|amount` |
| GET | `/api/wallets/{address}/threats` | Wallet + counterparty threat records |
| GET | `/api/wallets/{address}/osint` | Persisted OSINT findings + live provider correlation |
| GET | `/api/wallets/{address}/graph` | Bounded graph. Query: `hops` (1–7), `max_nodes` (10–400) |
| PATCH | `/api/wallets/{address}/notes` | Save investigator notes on the latest investigation |

## Transactions

| Method | Path | Description |
|---|---|---|
| GET | `/api/transactions` | Explorer with `search`, `blockchain`, `status`, date/amount ranges, `sort_by=timestamp|amount|tx_hash`, pagination |
| GET | `/api/transactions/{tx_hash}` | Detail + explorer URL + link-only OSINT lookups (404 if not indexed) |

## Graph

| Method | Path | Description |
|---|---|---|
| POST | `/api/graph/trace` | Body: `{ wallet_address, direction: "outgoing"\|"incoming", target_address?, max_hops (1–7) }`. Returns shortest observed path, edges, alternative paths, hop levels, suspicious nodes, disclaimer. |

## Threat intelligence

| Method | Path | Description |
|---|---|---|
| GET | `/api/threats` | List with `search`, `category`, `source`, pagination |
| GET | `/api/threats/stats` | Totals, category distribution, source list, allowed categories |
| POST | `/api/threats/import` | Multipart `file` (CSV or JSON). Returns `{received, valid, invalid, duplicates, inserted, updated, errors[]}` |

Import schema (CSV header or JSON object keys):
`address, blockchain, label, category, source, reference_url, confidence, first_seen, last_seen, notes`

## OSINT

| Method | Path | Description |
|---|---|---|
| GET | `/api/osint/sources` | Provider capability/status list |
| GET | `/api/osint/search/{address}` | Run all wallet providers (simulated + link-only) |
| GET | `/api/osint/restricted/{address}` | Dark-web/restricted-source records + disclaimer |
| POST | `/api/osint/restricted` | Add analyst/imported restricted-source record |

OSINT result statuses: `FOUND`, `NOT_FOUND`, `UNAVAILABLE`, `ERROR`, `REQUIRES_CONFIGURATION`.

## Alerts & monitoring

| Method | Path | Description |
|---|---|---|
| GET | `/api/alerts` | Alerts with `status`, `severity`, `search`, pagination |
| PATCH | `/api/alerts/{id}` | Update alert status (`NEW` → `ACKNOWLEDGED` → `INVESTIGATING` → `RESOLVED`) |
| GET | `/api/alerts/monitors` | List monitored wallets + rules |
| POST | `/api/alerts/monitor` | Create monitor. Body: `{ wallet_address, blockchain, label?, rules: { direction, amount_threshold, on_threat_match, flagged_counterparty } }` |
| PATCH | `/api/alerts/monitors/{id}` | `ACTIVE` / `PAUSED` |
| DELETE | `/api/alerts/monitors/{id}` | Remove monitor |
| POST | `/api/alerts/simulate` | Demo: trigger one simulated event for a wallet |

## Cases

| Method | Path | Description |
|---|---|---|
| GET | `/api/cases` | List with `status`, `search`, pagination |
| POST | `/api/cases` | Create (`title`, `description?`, `priority`, `status`) — case number auto-assigned |
| GET | `/api/cases/{id}` | Detail: investigations, evidence, reports, timeline |
| PATCH | `/api/cases/{id}` | Update fields; status change is timeline-logged |
| POST | `/api/cases/{id}/investigations` | Link latest investigation for a wallet (runs pipeline if none) |
| POST | `/api/cases/{id}/notes` | Append analyst note to timeline |
| POST | `/api/cases/{id}/evidence` | Multipart: `file` (optional) + `title`, `evidence_type`, `description`, `content_text` |

## Evidence

| Method | Path | Description |
|---|---|---|
| GET | `/api/evidence` | Repository with `case_id`, `type`, `search`, pagination |
| GET | `/api/evidence/{id}` | Detail incl. `integrity_verified` (recomputed SHA-256) |
| GET | `/api/evidence/{id}/download` | File download (404 for note-only records) |

## Reports

| Method | Path | Description |
|---|---|---|
| GET | `/api/reports` | List generated reports |
| POST | `/api/reports/generate` | Body: `{ wallet_address, case_id?, title? }` |
| GET | `/api/reports/{id}` | Full payload |
| GET | `/api/reports/{id}/download?format=pdf\|json\|csv` | Export |

## Settings & audit

| Method | Path | Description |
|---|---|---|
| GET | `/api/settings/providers` | Provider status (never exposes key values) |
| GET | `/api/settings/overview` | Mode, redacted DB info, monitoring config, limits |
| GET | `/api/audit-log` | Paginated audit trail with optional `action` filter |
